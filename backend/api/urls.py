from django.urls import include, path
from rest_framework import routers

from api.views import (CustomUserViewSet, RecipeViewSet,
                       TagViewsSet, IngredientViewSet,
                       SubscribeViewSet, ShoppingCartViewSet, FavoriteViewSet)

router = routers.DefaultRouter()
router.register(r"users", CustomUserViewSet, basename="users")
router.register("tags", TagViewsSet, basename="tags")
router.register("recipes", RecipeViewSet, basename="recipes")
router.register("ingredients", IngredientViewSet, basename="ingredients")

urlpatterns = [
    path(
        "recipes/<int:pk>/shopping_cart/",
        ShoppingCartViewSet.as_view(
            {"post": "shopping_cart", "delete": "shopping_cart"}
        ),
    ),
    path(
        "recipes/download_shopping_cart/",
        ShoppingCartViewSet.as_view({"get": "download_shopping_cart"}),
    ),
    path(
        "recipes/<int:pk>/favorite/",
        FavoriteViewSet.as_view({"post": "favorite", "delete": "favorite"}),
    ),
    path("users/subscriptions/",
         SubscribeViewSet.as_view({"get": "subscriptions"})),
    path(
        "users/<int:pk>/subscribe/",
        SubscribeViewSet.as_view({"post": "subscribe", "delete": "subscribe"}),
    ),
    path("", include(router.urls)),
    path("auth/", include("djoser.urls.authtoken")),
]
