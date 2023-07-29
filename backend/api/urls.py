from rest_framework import routers
from django.urls import path, include

from api.views import index, CustonUserViewSet, TagViewsSet, RecipeViewSet

router = routers.DefaultRouter()
router.register('users', CustonUserViewSet)
router.register('tag', TagViewsSet)
router.register('recipe', RecipeViewSet)


urlpatterns = [
    path('index', index),
    path('auth/', include('djoser.urls.authtoken')),
    path('', include(router.urls))
]

