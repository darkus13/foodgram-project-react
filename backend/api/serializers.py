import base64

from django.core.files.base import ContentFile
from djoser.serializers import UserCreateSerializer, UserSerializer
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, User)
from rest_framework import serializers


class TagSerializer(serializers.ModelSerializer):

    class Meta:
        model = Tag
        fields = '__all__'


class RecipeIngredientSerializer(serializers.ModelSerializer):
    name = serializers.ReadOnlyField(source='ingredirnt.name')
    measurement_unit = serializers.ReadOnlyField(
        source='ingredient.measerements_unit')

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecepiseSerializer(serializers.ModelSerializer):

    class Model:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeSerializer(serializers.ModelSerializer):
    tags = TagSerializer(many=True)
    ingredients = RecipeIngredientSerializer(
        many=True, source='recipe_ingredients')

    class Meta:
        model = Recipe
        fields = '__all__'

    def get_ingredients(self, instance):
        return RecipeIngredientSerializer(
            instance.recipe_ingredients.all(),
            many=True
        ).data

    def create(self, validated_data):
        ingredients = validated_data.pop('ingredients')
        instance = super().create(validated_data)

        for ingredient_data in ingredients:
            RecipeIngredient(
                recipe=instance,
                ingredient=ingredient_data['ingredient'],
                amount=ingredient_data['amount']
            ).save()

        return instance

    def update(self, instance, validated_data):
        tags = validated_data.pop('tags')
        ingredients = validated_data.pop('recipeingredients')
        instance.ingredients.clear()
        instance.tags.clear()
        super().update(instance, validated_data)
        instance.tags.set(tags)
        self.create_recipe_ingredient(instance, ingredients)

        return instance

    def validate(self, data):
        for field in ('tags', 'ingredients', 'name', 'text', 'cooking_time'):
            if not self.initial_data.get(field):
                raise serializers.ValidationError(
                    f'Поле `{field}` не заполнено')
        ingredients = self.initial_data['ingredients']
        ingredients_set = set()
        for ingredient in ingredients:
            if not ingredient.get('amount') or not ingredient.get('id'):
                raise serializers.ValidationError(
                    'Укажите `amount` и `id` для ингредиента.')
            if not int(ingredient['amount']) > 0:
                raise serializers.ValidationError(
                    'Количество ингредиентов не может быть меньше 1.')
            if ingredient['id'] in ingredients_set:
                raise serializers.ValidationError(
                    'Исключите повторяющиеся ингредиенты.')
            ingredients_set.add(ingredient['id'])
        return data


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class UserCreateSerializer(UserCreateSerializer):

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'password'
        )

    def validate_username(self, value):
        if value.lower() == 'usernmame':
            raise serializers.ValidationError(
                'Имя пользователя "username" нельзя использовать.'
            )
        return value


class CustomUserSerializer(UserSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed'
        )

    def get_subscribed(self, obj):
        request = self.context.get('request')
        if not request or request.user_is_anonymus:
            return False
        else:
            return obj.following.filter(user=request.user).exists()


class IngredientSerializer(serializers.ModelSerializer):

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class FavoriteSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        extra_kwargs = {
            'name': {'required': False},
            'image': {'required': False},
            'cooking_time': {'required': False},
        }

        def validate(self, data):
            request = self.context.get('request')
            recipe = self.instance
            favorite = Favorite.objects.filter(
                user=request.user, recipe=recipe).exists()
            if request.method == 'DELETE' and not favorite:
                raise serializers.ValidationError(
                    'Рецепт удален из избранного.')
            if favorite:
                raise serializers.ValidationError(
                    'Рецепт добавлен в избранное.')
            return data


class ShoppingCartSerializer(serializers.ModelSerializer):

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        extra_kwargs = {
            'name': {'required': False},
            'image': {'required': False},
            'cooking_time': {'required': False},
        }

    def validate(self, data):
        request = self.context.get('request')
        recipe = self.instance
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe).exists()
        if request.method == 'DELETE' and not shopping_cart:
            raise serializers.ValidationError(
                'Рецепт удален из корзины покупок.')
        if shopping_cart:
            raise serializers.ValidationError(
                'Рецепт добавлен в корзину покупок.')
        return data


class Base64ImageField(serializers.ImageField):
    def internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            name = {self.context["request"].user.username}
            data = ContentFile(base64.b64decode(imgstr), name=f'{name}.' + ext)
        return super().to_internal_value(data)


class SubscribeSerializer(serializers.ModelSerializer):
    recipes_count = serializers.SerializerMethodField(
        method_name='number_of_recipes')
    recipes = serializers.SerializerMethodField(method_name='get_recipes')

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name',
                  'email', 'subscriber', 'recipes', 'recipes_count')

    def number_of_recipes(self, obj):
        return obj.author.count()

    def get_recipes(self, obj):
        recipes = obj.author.all()
        serializer = RecepiseSerializer(recipes, many=True, read_only=True)
        return serializer.data
