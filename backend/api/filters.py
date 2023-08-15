from django.contrib.auth import get_user_model
from django_filters import AllValuesMultipleFilter, CharFilter, FilterSet
from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe

User = get_user_model()


class IngredientFilter(FilterSet):
    name = filters.CharFilter(
        field_name='name',
        lookup_expr='istartswith'
    )

    class Meta:
        model = Ingredient
        fields = ['name']


class RecipeFilter(FilterSet):
    tags = AllValuesMultipleFilter(field_name='tags__slug')
    is_favorited = CharFilter(method='filter_is_favorited__in')
    is_in_shopping_cart = CharFilter(method='filter_is_in_shopping_cart__in')

    class Meta:
        model = Recipe
        fields = ('author', 'tags', 'is_favorited',)

    def filter_is_favorited__in(self, queryset, name, value):
        if value:
            return queryset.filter(favorites__user=self.request.user)
        return queryset

    def filter_is_in_shopping_cart__in(self, queryset, name, value):
        if value:
            return queryset.filter(carts__user=self.request.user)
        return queryset
