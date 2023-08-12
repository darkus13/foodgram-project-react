from djoser.serializers import UserCreateSerializer, UserSerializer
from backend.api.views import FavoriteViewSet
from backend.recipes.models import Favorite
from recipes.models import Ingredient, Recipe, RecipeIngredient, Tag, User
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


class RecipeIngredientCreateSerializer(serializers.ModelSerializer):
    id = serializers.PrimaryKeyRelatedField(
        source='ingredient',
        queryset=Ingredient.objects.all()
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeCreateSerializer(serializers.ModelSerializer):
    ingredients = RecipeIngredientCreateSerializer(many=True)

    class Meta:
        model = Recipe
        fields = ('name', 'cooking_time', 'text', 'tags')

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

    def get_subscribed(self, objects):
        request = self.context.get('request')
        if not request or request.user_is_anonymus:
            return False
        else:
            return objects.following.filter(user=request.user).exists()


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
