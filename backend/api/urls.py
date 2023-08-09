from rest_framework import routers
from django.urls import path, include

from api.views import CustomUserViewSet, TagViewsSet, RecipeViewSet

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tag', TagViewsSet)
router.register('recipe', RecipeViewSet)


urlpatterns = [
    path('', include(router.urls))
]

