from api.views import CustomUserViewSet, RecipeViewSet, TagViewsSet, IngredientViewSet, SubscribeViewSet
from django.urls import include, path
from rest_framework import routers
from django.conf.urls.static import static
from api.views import ShoppingCartViewSet, FavoriteViewSet
from foodgram import settings

router = routers.DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='users')
router.register('tags', TagViewsSet, basename='tags')
router.register('recipes', RecipeViewSet, basename='recipes')
router.register('ingredients', IngredientViewSet, basename='ingredients')

urlpatterns = [
    path('recipes/<int:pk>/shopping_cart/', ShoppingCartViewSet.as_view(
        {'post': 'shopping_cart', 'delete': 'shopping_cart'})),
    path('recipes/download_shopping_cart/', ShoppingCartViewSet.as_view(
        {'get': 'download_shopping_cart'})),
    path('recipes/<int:pk>/favorite/', FavoriteViewSet.as_view(
        {'post': 'favorite', 'delete': 'favorite'})),
    path('users/subscriptions/', SubscribeViewSet.as_view(
        {'get': 'subscriptions'})),
    path('users/‹int:pk>/subscribe/', SubscribeViewSet.as_view(
        {'post': 'subscribe', 'delete': 'subscribe'})),
    path('', include(router.urls)),
    path('auth/', include('djoser.urls.authtoken')),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL,
        document_root=settings.MEDIA_ROOT
    )


# if self.request.method == 'POST':
#             seriaizer = SubscribeSerializer(
#                 author=author, data=request.data, context={'request': request})
#             seriaizer.is_valid(raise_exception=True)
#             Subscribe.objects.create(user=request.user, author=author)
#             return Response(seriaizer.data, status=status.HTTP_201_CREATED)

#         subscribe = get_object_or_404(
#             Subscribe, user=request.user, author=author)
#         seriaizer = SubscribeSerializer(
#             author=author, data=request.data, context={'request': request})
#         subscribe.delete()
#         return Response(status=status.HTTP_204_NO_CONTENT)
