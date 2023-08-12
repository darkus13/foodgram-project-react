from django.contrib import admin
from users.models import Subscription


class UserAdmin(admin.ModelAdmin):
    search_fields = ('email', 'username')


admin.site.register(Subscription)
