from api.views import CustomUserViewSet, RecipeViewSet, TagViewsSet
from django.urls import include, path
from rest_framework import routers

from backend.api.views import FavoriteViewSet, ShoppingCartViewSet, UserCurrentView

router = routers.DefaultRouter()
router.register('users', CustomUserViewSet, basename='users')
router.register('tag', TagViewsSet)
router.register('recipe', RecipeViewSet)


urlpatterns = [
    path('users/me/', UserCurrentView.as_view()),
    path('users/subscriptions/', SubscriptionsViewSet.as_view(
        {'get': 'subscriptions'})),
    path('users/<int:pk>/subscribe/', SubscriptionsViewSet.as_view(
        {'post': 'subscribe', 'delete': 'subscribe'})),
    path('recipes/<int:pk>/favorite/', FavoriteViewSet.as_view(
        {'post': 'favorite', 'delete': 'favorite'})),
    path('recipes/<int:pk>/shopping_cart/', ShoppingCartViewSet.as_view(
        {'post': 'shopping_cart', 'delete': 'shopping_cart'})),
    path('recipes/download_shopping_cart/', ShoppingCartViewSet.as_view(
        {'get': 'download_shopping_cart'})),
    path('', include(router.urls)),
    path('', include('djoser.urls')),
    path('auth/', include('djoser.urls.authtoken')),
]
