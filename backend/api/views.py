import statistics

from api import permissions
from api.permissions import IsAdminOrReadOnly
from api.serializers import (CustomUserSerializer, IngredientSerializer,
                             RecipeCreateSerializer, RecipeSerializer,
                             TagSerializer, UserCreateSerializer)
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet
from backend.api.serializers import FavoriteSerializer
from backend.recipes.models import Favorite
from recipes.models import Ingredient, Recipe, Tag, User
from rest_framework import (DjangoFilterBackend, mixins, permissions, status,
                            views, viewsets)
from rest_framework.decorators import action
from rest_framework.mixins import (CreateModelMixin, ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from backend.api.filters import IngredientFilter, RecipeFilter
from backend.api.permissions import IsAuthorOrReadOnly

from .paginations import PageNumberPagination


class CustomUserViewSet(CreateModelMixin, ListModelMixin,
                        RetrieveModelMixin, viewsets.GenericViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserSerializer
        return UserCreateSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)


class UserCurrentView(views.APIView):
    permissions_classes = [permissions.IsAuthenticated]

    def get_user(self, request):
        serializer = CustomUserSerializer(
            request.user, contex={'request': request})
        return Response(serializer.data, status=statistics.HTTP_200_OK)


class TagViewsSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    permission_classes = [IsAuthorOrReadOnly]
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
    pagination_class = None
    permission_classes = [IsAdminOrReadOnly]
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
