from django.http import FileResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Exists, OuterRef, Sum
from djoser.views import UserViewSet

from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
    SAFE_METHODS,
)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.filters import SearchFilter

from api.filters import RecipeFilter
from api.permissions import IsAdminOrReadOnly
from api.serializers import (
    CustomUserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    SubscribeSerializer,
    TagSerializer,
    CreateRecipeSerializer,
    RecipeReadSerializer,
    ActionRecipeSerializer,
    UserCreateSerializer,
    SubscriptionSerializer,
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
            return UserCreateSerializer
        return CustomUserSerializer


class SubscribeViewSet(ModelViewSet):
    queryset = Subscribe.objects.all()
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=["post"],
            serializer_class=SubscribeSerializer)
    def get_subscribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        Subscribe.objects.create(user=request.user, author=author)
        return Response(status=status.HTTP_201_CREATED)

    @get_subscribe.mapping.delete
    def delete_subcsribe(self, request, id=None):
        author = get_object_or_404(User, id=id)
        del_count, _ = Subscribe.objects.filter(
            user=request.user, author=author
        ).delete()

        if del_count:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=["get"])
    def subscriptions(self, request):
        queryset = self.get_queryset().select_related("author")
        serializer = SubscriptionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response(serializer.data)


class TagViewsSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [
        IsAdminOrReadOnly,
    ]
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_queryset(self):
        queryset = (
            Recipe.objects
            .select_related("author")
            .prefetch_related("tags")
        )

        if self.request.user.is_authenticated:
            queryset = Recipe.objects.annotate(
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
            ).select_related("author").prefetch_related("tags")

        return queryset

    def get_serializer_class(self):
        if self.request.method == SAFE_METHODS:
            return RecipeReadSerializer
        return CreateRecipeSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [
        IsAuthenticatedOrReadOnly,
    ]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = [
        "$name",
    ]


class RecipeBaseMixin:

    def add_to_model(self, request, pk):
        obj = self.get_object()
        user = self.request.user
        model = self.model_class.objects.filter(
            user=request.user, **{self.model_field: obj}
        ).first()

        serializer = self.serializer_class(
            obj, context={"request": request})

        if self.request.method == "POST":
            if self.model_class.objects.filter(user=user,
                                               **{self.model_field: obj}).exists():
                return Response(
                    {"message": f"{self.model_name} уже добавлен."},
                )
            self.model_class.objects.create(
                user=user, **{self.model_field: obj})
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)

    def delete_to_model(self, request, pk):
        obj = self.get_object()
        user = self.request.user
        model = self.model_class.objects.filter(
            user=request.user, **{self.model_field: obj}
        ).first()

        serializer = self.serializer_class(
            obj, context={"request": request})

        if request.method == "DELETE" and model:
            model.delete()
            return Response(
                {"message": f"{self.model_name} успешно удален."},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(serializer.data,
                        status=status.HTTP_201_CREATED)


class FavoriteViewSet(RecipeBaseMixin, viewsets.ModelViewSet):
    serializer_class = FavoriteSerializer

    @action(detail=True, methods=["post", "delete"])
    def favorite(self, request, pk):

        if request.method == "DELETE":
            return self.delete_to_model(request, pk)

        if self.request.method == "POST":
            return self.add_to_model(request, pk)


class ShoppingCartViewSet(RecipeBaseMixin, viewsets.ModelViewSet):
    @action(methods=["post", "delete"], detail=True)
    def shopping_cart(self, request, pk):
        if self.request.method == "POST":
            return self.add_to_model(request, pk)

        if request.method == "DELETE":
            self.delete_to_model(request, pk)

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
