from django.contrib import admin
from users.models import Subscribe, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    fields = ("username", "email", "first_name", "last_name", "password")
    list_display = ("id", "username", "email", "first_name", "last_name")
    search_fields = (
        "username",
        "email",
    )
    list_filter = (
        "username",
        "email",
    )
    empty_value_display = "-пусто-"


@admin.register(Subscribe)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "author")
    search_fields = ("user", "author")
    empty_value_display = "-пусто-"
