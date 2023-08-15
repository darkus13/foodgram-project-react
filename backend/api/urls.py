from api.views import CustomUserViewSet, RecipeViewSet, TagViewsSet
from django.urls import include, path
from rest_framework import routers

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tag', TagViewsSet)
router.register('recipe', RecipeViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]
