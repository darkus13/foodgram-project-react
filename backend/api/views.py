from django.shortcuts import render, HttpResponse
from djoser.views import UserViewSet
from api.serializers import TagSerializer, RecipeSerializer, RecipeCreateSerializer, UserCreateSerializer, CustomUserSerializer
from rest_framework.viewsets import ModelViewSet
from backend.api import permissions
from recipes.models import Tag, Recipe, User
from rest_framework.response import Response


class CustomUserViewSet(ModelViewSet):
    queryset = User.objects.all()
    permission_classes = [permissions.AllowAny]

    def get_serializer_class(self):
        if self.action == 'create':
            return CustomUserSerializer
        return UserCreateSerializer
    
    def list(self, request):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    

class UserCurrentView(views.APIView):


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
