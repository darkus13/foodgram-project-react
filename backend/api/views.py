from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Exists, OuterRef, Sum
from djoser.views import UserViewSet

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter

from api.filters import RecipeFilter
from api.permissions import IsAdminOrReadOnly
from api.serializers import (
    FavoriteSerializer,
    IngredientSerializer,
    SubscribeSerializer,
    TagSerializer,
    UserСreateSerializer,
    CreateRecipeSerializer,
    ActionRecipeSerializer,
    SubscriptionSerializer,
    UserSerializer,
)
from api.utils import create_shopping_cart

from recipes.models import (
    Favorite,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingCart,
    Tag,
    User,
)
from users.models import Subscribe
from .paginations import PageNumberPagination


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method == "POST":
            return UserСreateSerializer
        return UserSerializer


class SubscribeViewSet(ModelViewSet):
    serializer_class = SubscriptionSerializer
    queryset = User.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=["post", "delete"],
            serializer_class=SubscribeSerializer)
    def subscribe(self, request, pk=None):
        if self.request.method == 'POST':
            author = get_object_or_404(User, pk=pk)
            Subscribe.objects.create(user=request.user, author=author)
            return Response(status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            author = get_object_or_404(User, pk=pk)
            del_count, _ = Subscribe.objects.filter(
                user=request.user, author=author
            ).delete()

            if del_count:
                return Response(status=status.HTTP_204_NO_CONTENT)
            return Response(status=status.HTTP_404_NOT_FOUND)

    @action(methods=['get'], detail=False,
            permission_classes=[IsAuthenticated])
    def subscriptions(self, request):
        subscriptions = User.objects.filter(following__user=request.user).all()
        paginator = PageNumberPagination()
        paginated_subscriptions = paginator.paginate_queryset(subscriptions,
                                                              request)
        serializer = self.get_serializer(paginated_subscriptions, many=True)
        return paginator.get_paginated_response(serializer.data)


class TagViewsSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [
        IsAdminOrReadOnly,
    ]
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = CreateRecipeSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = (
            super().get_queryset()
            .select_related("author")
            .prefetch_related("tags")
        )

        if self.request.user.is_authenticated:
            queryset = queryset.annotate(
                is_favorited=Exists(
                    Favorite.objects.filter(
                        user=self.request.user,
                        recipe_id=OuterRef("pk"),
                    )
                ),
                is_in_shopping_cart=Exists(
                    ShoppingCart.objects.filter(
                        user=self.request.user,
                        recipe_id=OuterRef("pk"),
                    )
                ),
            )
        return queryset


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    pagination_class = None
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        "^name",
    ]


class FavoriteViewSet(viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = Favorite.objects.filter(
            user=request.user, recipe=recipe).first()
        serializer = FavoriteSerializer(
            favorite, data=request.data,
            context={"request": request}
        )
        user = self.request.user

        if request.method == "DELETE" and favorite:
            favorite.delete()
            return Response(
                {"message": "Рецепт успешно удален из избранного"},
                status=status.HTTP_204_NO_CONTENT,
            )

        if self.request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({"message": "Рецепт уже в избранном"})
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ActionRecipeSerializer(
                recipe, context={"request": request})
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        serializer.is_valid(raise_exception=True)
        Favorite.objects.create(user=request.user, recipe=recipe)

        return Response(serializer.errors,
                        status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    @action(methods=["post", "delete"], detail=True)
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = self.request.user
        shopping_cart = ShoppingCart.objects.filter(
            user=request.user, recipe=recipe
        ).first()

        serializer = ActionRecipeSerializer(
            recipe, context={"request": request})

        if self.request.method == "POST":
            if ShoppingCart.objects.filter(user=user,
                                           recipe=recipe).exists():
                return Response(
                    {"message": "Рецепт уже находится в списке покупок."},
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

        if request.method == "DELETE" and shopping_cart:
            shopping_cart.delete()
            return Response(
                {"message": "Рецепт успешно удалён."},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)

    @action(detail=False, methods=("get",),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):
        shopping_cart = list(
            ShoppingCart.objects.filter(user=self.request.user))
        recipes = [item.recipe.id for item in shopping_cart]
        buy_list = (
            RecipeIngredient.objects.filter(recipe__in=recipes)
            .values("ingredient")
            .annotate(amount=Sum("amount"))
        )
        buy_list_text = create_shopping_cart(buy_list)
        response = FileResponse(buy_list_text, content_type="text/plain")
        response[
            "Content-Disposition"
        ] = "attachment; filename=shopping-list.txt"
        return response
