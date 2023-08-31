
from api.filters import RecipeFilter
from api.permissions import IsAdminOrReadOnly
from api.serializers import (CustomUserSerializer, FavoriteSerializer,
                             IngredientSerializer,
                             SubscribeSerializer,
                             TagSerializer, CreateRecipeSerializer, RecipeReadSerializer,
                             ActionRecipeSerializer, UserCreateSerializer, SubscriptionSerializer)
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet
from recipes.models import (Favorite, Ingredient, Recipe, RecipeIngredient,
                            ShoppingCart, Tag, User)
from rest_framework import status, views, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly, SAFE_METHODS)
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from users.models import Subscribe
from rest_framework.filters import SearchFilter

from .paginations import PageNumberPagination
from rest_framework import status
from django.db.models import Sum
from django.core import exceptions


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    pagination_class = PageNumberPagination

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return UserCreateSerializer
        return CustomUserSerializer


class SubscribeViewSet(ModelViewSet):
    queryset = Subscribe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, ]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    @action(detail=True, methods=['post', 'delete'],
            serializer_class=SubscribeSerializer)
    def subscribe(self, request, id):
        author = get_object_or_404(User, pk=id)

        if self.request.method == 'POST':
            Subscribe.objects.create(user=request.user, author=author)
            return Response(status=status.HTTP_201_CREATED)

        if self.request.method == 'DELETE':
            subscribe_list = author.following.first()
            if not subscribe_list:
                return Response(status=status.HTTP_204_NO_CONTENT)

            subscribe_list.delete()

    @action(detail=False, methods=['get'])
    def subscriptions(self, request):
        queryset = self.get_queryset().select_related('author')
        print(queryset, '!!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
        serializer = SubscriptionSerializer(
            queryset, many=True, context={'request': request})
        return Response(serializer.data)


class UserCurrentView(views.APIView):
    permissions_classes = [IsAuthenticated, ]

    def get_user(self, request):
        serializer = CustomUserSerializer(
            request.user, contex={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewsSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [IsAdminOrReadOnly, ]
    pagination_class = None


class RecipeViewSet(ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    pagination_class = PageNumberPagination
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.request.method == SAFE_METHODS:
            return RecipeReadSerializer
        return CreateRecipeSerializer


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, ]
    filter_backends = [DjangoFilterBackend, SearchFilter]
    search_fields = ['$name', ]


class FavoriteViewSet(viewsets.ModelViewSet):
    @action(detail=True, methods=['post', 'delete'])
    def favorite(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        favorite = Favorite.objects.filter(
            user=request.user, recipe=recipe).first()
        serializer = FavoriteSerializer(
            favorite, data=request.data, context={'request': request})
        user = self.request.user

        if request.method == 'DELETE' and favorite:
            favorite.delete()
            return Response({'message': 'Рецепт удалён из избранного'},
                            status=status.HTTP_204_NO_CONTENT)

        if serializer.is_valid():
            Favorite.objects.create(user=request.user, recipe=recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if self.request.method == "POST":
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response({'message': 'Рецепт уже в избранном'})
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = ActionRecipeSerializer(
                recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartViewSet(viewsets.ModelViewSet):
    @action(methods=['post', 'delete'], detail=True)
    def shopping_cart(self, request, pk):
        recipe = get_object_or_404(Recipe, id=pk)
        user = self.request.user
        shopping_cart = ShoppingCart.objects.filter(user=request.user,
                                                    recipe=recipe).first()

        if self.request.method == "POST":
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response({'message': 'Рецепт уже находиться в списке покупок.'}),
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = ActionRecipeSerializer(
                recipe, context={"request": request})
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        if request.method == 'DELETE' and shopping_cart:
            shopping_cart.delete()
            return Response({'message': 'Рецепт успешно удалён.'},
                            status=status.HTTP_204_NO_CONTENT)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=("get",),
            permission_classes=(IsAuthenticated,))
    def download_shopping_cart(self, request):

        shopping_cart = ShoppingCart.objects.filter(user=self.request.user)
        recipes = [item.recipe.id for item in shopping_cart]
        buy_list = RecipeIngredient.objects.filter(
            recipe__in=recipes).values("ingredient").annotate(
            amount=Sum("amount"))
        buy_list_text = "Список покупок с сайта Foodgram:\n\n"
        for item in buy_list:
            ingredient = Ingredient.objects.get(pk=item["ingredient"])
            amount = item["amount"]
            buy_list_text += (
                f"{ingredient.name}, {amount} "
                f"{ingredient.measurement_unit}\n")
        response = HttpResponse(buy_list_text, content_type="text/plain")
        response["Content-Disposition"] = (
            "attachment; filename=shopping-list.txt")
        return response
