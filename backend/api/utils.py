from django.db.models import Sum

from recipes.models import RecipeIngredient, Ingredient


def get_ingredients_shopping_cart(user):
    ingredients = (
        RecipeIngredient.objects.filter(recipe__shopping_list__user=user)
        .order_by("ingredient__name")
        .values("ingredient__name", "ingredient__measurement_unit")
        .annotate(total_amount=Sum("amount"))
    )

    return ingredients


def create_shopping_cart(buy_list):
    ingredient_ids = [item["ingredient"] for item in buy_list]
    ingredients = Ingredient.objects.filter(id__in=ingredient_ids)

    ingredient_dict = {ingredient.id: ingredient for ingredient in ingredients}

    buy_list_text = "Список покупок с сайта Foodgram:\n\n"
    for item in buy_list:
        ingredient_id = item["ingredient"]
        ingredient = ingredient_dict.get(ingredient_id)
        amount = item["amount"]
        buy_list_text += (
            f"{ingredient.name}, {amount} " f"{ingredient.measurement_unit}\n"
        )
    return buy_list_text
