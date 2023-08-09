from rest_framework.mixins import CreateModelMixin, ListModelMixin, RetrieveModelMixin
import statistics

from rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from api.serializers import TagSerializer, RecipeSerializer, RecipeCreateSerializer, UserCreateSerializer, CustomUserSerializer, IngredientSerializer
from rest_framework.viewsets import ModelViewSet
from api import permissions
from rest_framework import mixins, permissions, status, views, viewsets
from backend.api.filters import IngredientFilter
from recipes.models import Ingredient
from recipes.models import Tag, Recipe, User
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import viewsets
from api.permissions import IsAdminOrReadOnly



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
        serializer = CustomUserSerializer(request.user, contex={'request': request})
        return Response(serializer.data, status=statistics.HTTP_200_OK)


class TagViewsSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly]
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer

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
