import statistics

from api import permissions
from api.permissions import IsAdminOrReadOnly
from api.serializers import (CustomUserSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             TagSerializer)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from recipes.models import Ingredient, Recipe, Tag, User
from rest_framework import (DjangoFilterBackend, permissions, status, views,
                            viewsets)
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.api.filters import IngredientFilter, RecipeFilter
from backend.api.permissions import IsAuthorOrReadOnly
from backend.api.serializers import (FavoriteSerializer,
                                     ShoppingCartSerializer,
                                     SubscribeSerializer)
from backend.recipes.models import (Favorite, RecipeIngredient, ShoppingCart,
                                    Subscribe)

from .paginations import PageNumberPagination


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly,]
    pagination_class = PageNumberPagination

    @action(detail=True, methods=['post', 'delete'], serializer_class=SubscribeSerializer)
    def subscribe(self, request, id):
        author = get_object_or_404(User, pk=id)
        if self.request.method == 'POST':
            Subscribe.objects.create(User=request.user, author=author)
            return Response(status=statistics.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            subscribe_list = author.following.first()
            if not subscribe_list:
                return Response(status=statistics.HTTP_204_NO_CONTENT)
            subscribe_list.delete()

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        user = self.request.user()
        subscribe_list = user.subscriber.all()
        queryset = User.objects.filter(
            pk__in=subscribe_list.values('author_id'))
        paginate = self.paginate_queryset(queryset)
        serializer = SubscribeSerializer(paginate, many=True)
        return self.get_paginated_response(serializer.data)


class UserCurrentView(views.APIView):
    permissions_classes = [permissions.IsAuthenticated,]

    def get_user(self, request):
        serializer = CustomUserSerializer(
            request.user, contex={'request': request})
        return Response(serializer.data, status=statistics.HTTP_200_OK)


class TagViewsSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly,]


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly,]
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        recipe = Recipe.objects.prefetch_related(
            'recipe_ingredients__ingredient', 'tags'
        ).all()
        return recipe

    def get_serializer_class(self):
        if self.action == 'create':
            return RecipeCreateSerializer
        return RecipeSerializer

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAdminOrReadOnly,]
    filterset_class = IngredientFilter
    filter_backends = (DjangoFilterBackend,)


class FavoriteViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = Favorite.objects.filter(
            user=request.user, recipe=recipe).first()
        serializer = FavoriteSerializer(
            recipe, data=request.data, context={'request': request})

        if request.method == 'DELETE' and favorite:
            favorite.delete()
            return Response({'message': 'Рецепт удалён из избранного'}, status=status.HTTP_204_NO_CONTENT)

        if serializer.is_valid():
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_cart = ShoppingCart.objects.filter(user=request.user,
                                                    recipe=recipe).first()
        serializer = ShoppingCartSerializer(recipe, data=request.data,
                                            context={'request': request})
        if request.method == 'DELETE' and shopping_cart:
            shopping_cart.delete()
            return Response({'message': 'Рецепт успешно удалён.'},
                            status=status.HTTP_204_NO_CONTENT)
        serializer.is_valid(raise_exception=True)
        ShoppingCart.objects.create(user=request.user, recipe=recipe)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated,])
    def download_shopping_cart(self, request):
        ingredients = RecipeIngredient.objects.filter(
            recipe__shopping_cart__user=request.user).values(
                'ingredient__name',
                'ingredient__measurement_unit',
                'amount').order_by('ingredient__name')
        shopping_list = self.create_ingredient_list(ingredients)
        response = HttpResponse(shopping_list, content_type='text/plain')
        response['Content-Disposition'] = (
            'attachment; filename={0}'.format('Список_покупок.txt')
        )
        return response
