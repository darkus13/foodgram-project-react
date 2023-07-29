from django.shortcuts import render, HttpResponse
from djoser.views import UserViewSet
from api.serializers import TagSerializer, RecipeSerializer, RecipeCreateSerializer
from rest_framework.viewsets import ModelViewSet
from recipes.models import Tag, Recipe


def index(request):
    return HttpResponse('index')


class CustonUserViewSet(UserViewSet):
    pass


class TagViewsSet(ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer


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
