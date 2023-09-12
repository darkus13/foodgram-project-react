from django.db import transaction
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer
)
from djoser.serializers import UserSerializer as DjoserUserSerializer
from rest_framework import serializers

from users.models import Subscribe
from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User,
)

from drf_base64.fields import Base64ImageField


class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = "__all__"


class UserCreateSerializer(DjoserUserCreateSerializer):
    is_subscribed = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = ("email", "id", "username", "first_name",
                  "last_name", "is_subscribed")

    def get_is_subscribed(self, obj):
        user = self.context.get("request").user
        if user.is_anonymous:
            return False
        return Subscribe.objects.filter(user=user, author=obj).exists()


class UserSerializer(DjoserUserSerializer):
    class Meta:
        model = User
        fields = ("email", "id", "username",
                  "first_name", "last_name", "password")


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "name", "measurement_unit")


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source="ingredient.name")
    measurement_unit = serializers.ReadOnlyField(
        source="ingredient.measurement_unit")
    id = serializers.ReadOnlyField(source="ingredient.id")

    class Meta:
        model = RecipeIngredient
        fields = ("id", "name", "measurement_unit", "amount")


class CreateIngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ("id", "amount")


class RecipeReadSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source="recipe_ingredients")
    author = UserSerializer(read_only=True)
    is_in_shopping_cart = serializers.BooleanField(
        read_only=True, default=False)
    is_favorited = serializers.BooleanField(read_only=True, default=False)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "name",
            "text",
            "image",
            "tags",
            "ingredients",
            "cooking_time",
            "author",
            "is_favorited",
            "is_in_shopping_cart",
        )


class CreateRecipeSerializer(serializers.ModelSerializer):
    image = Base64ImageField(required=False, allow_null=True)
    ingredients = CreateIngredientSerializer(many=True)

    author = UserSerializer(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            "id",
            "author",
            "name",
            "text",
            "image",
            "tags",
            "ingredients",
            "cooking_time",
        )

    @transaction.atomic
    def create(self, validated_data):
        ingredients = validated_data.pop("ingredients")
        tags = validated_data.pop("tags")
        user = self.context.get("request").user
        recipe = Recipe.objects.create(author=user, **validated_data)
        recipe.tags.set(tags)
        RecipeIngredient.objects.bulk_create(
            [
                RecipeIngredient(
                    recipe=recipe,
                    ingredient_id=ingredient_data["id"],
                    amount=ingredient_data["amount"],
                )
                for ingredient_data in ingredients
            ]
        )

        return recipe

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            recipe_ingredient = RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient["id"],
                amount=ingredient["amount"]
            )
            recipe_ingredient.append(recipe_ingredient)

        RecipeIngredient.objects.bulk_create(recipe_ingredient)

    def create_tags(self, tags, recipe):
        for tag in tags:
            recipe.tags.set(tag)

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.recipe_ingredients.all().delete()
        ingredients = validated_data.pop("ingredients")

        ingredient_ids = [ingredient_data["id"]
                          for ingredient_data in ingredients]

        ingredient_mapping = {
            ingredient.id: ingredient
            for ingredient in Ingredient.objects.filter(pk__in=ingredient_ids)
        }

        recipe_ingredients = [
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient_mapping[ingredient_data["id"]],
                amount=ingredient_data["amount"],
            )
            for ingredient_data in ingredients
        ]

        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return super().update(instance, validated_data)

    def validate(self, data):
        for field in ("tags", "ingredients", "name", "text", "cooking_time"):
            if not self.initial_data.get(field):
                raise serializers.ValidationError(
                    f"Поле `{field}` не заполнено")
        ingredients = self.initial_data["ingredients"]
        ingredients_set = set()
        for ingredient in ingredients:
            if not ingredient.get("amount") or not ingredient.get("id"):
                raise serializers.ValidationError(
                    "Укажите `amount` и `id` для ингредиента."
                )
            if not int(ingredient["amount"]) > 0:
                raise serializers.ValidationError(
                    "Количество ингредиентов не может быть меньше 1."
                )
            if ingredient["id"] in ingredients_set:
                raise serializers.ValidationError(
                    "Исключите повторяющиеся ингредиенты."
                )
            ingredients_set.add(ingredient["id"])
        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={"request": self.context.get("request")}
        ).data


class FavoriteSerializer(serializers.ModelSerializer):
    id = serializers.ReadOnlyField(source="recipe.id")
    name = serializers.ReadOnlyField(source="recipe.name")
    image = Base64ImageField(required=False, allow_null=True)
    cooking_time = serializers.ReadOnlyField(source="recipe.cooking_time")

    class Meta:
        model = Favorite
        fields = ("user", "recipe", "id", "name", "image", "cooking_time")

    def validate(self, data):
        request = self.context.get("request")
        if not request or request.user.is_anonymous:
            return False
        recipe = data["recipe"]
        if Favorite.objects.filter(user=request.user, recipe=recipe).exists():
            raise serializers.ValidationError({"errors": "Уже в избранном."})
        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={"request": self.context.get("request")}
        ).data


class ShoppingCartSerializer(serializers.ModelSerializer):
    class Meta:
        model = ShoppingCart
        fields = ("id", "user", "recipe")

    def validate(self, data):
        request = self.context.get("request")
        recipe = self.instance
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).exists()
        if request.method == "DELETE" and not shopping_cart:
            raise serializers.ValidationError(
                "Рецепт удален из корзины покупок.")
        if shopping_cart:
            raise serializers.ValidationError(
                "Рецепт добавлен в корзину покупок.")
        return data

    def to_representation(self, instance):
        return RecipeReadSerializer(
            instance, context={"request": self.context.get("request")}
        ).data


class SubscribeSerializer(serializers.ModelSerializer):
    recipes_count = serializers.SerializerMethodField(
        method_name="number_of_recipes")
    recipes = serializers.SerializerMethodField(method_name="get_recipes")
    id = serializers.ReadOnlyField(source="author.id")

    class Meta:
        model = User
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def number_of_recipes(self, obj):
        return obj.author.count()

    def get_recipes(self, obj):
        recipes = obj.author.all()
        serializer = CreateRecipeSerializer(recipes, many=True, read_only=True)
        return serializer.data


class SubscriptionSerializer(serializers.ModelSerializer):
    email = serializers.ReadOnlyField(source="author.email")
    id = serializers.IntegerField(source="following.id", read_only=True)
    username = serializers.ReadOnlyField(source="author.username")
    first_name = serializers.ReadOnlyField(source="author.first_name")
    last_name = serializers.ReadOnlyField(source="author.last_name")
    is_subscribed = serializers.SerializerMethodField()
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = Subscribe
        fields = (
            "email",
            "id",
            "username",
            "first_name",
            "last_name",
            "is_subscribed",
            "recipes",
            "recipes_count",
        )

    def get_is_subscribed(self, username):
        user = self.context["request"].user
        return (
            not user.is_anonymous
            and Subscribe.objects.filter(user=user, author=username).exists()
        )

    def get_recipes(self, obj):
        return ActionRecipeSerializer(Recipe.objects.filter(author=obj),
                                      many=True).data

    def get_recipes_count(self, obj):
        return obj.following.recipe.count()


class ActionRecipeSerializer(serializers.ModelSerializer):
    """Cериализуются нужные поля для создания и
    удаления рецепта в избранном, списке покупок.
    """

    class Meta:
        model = Recipe
        fields = ("id", "name", "image", "cooking_time")
