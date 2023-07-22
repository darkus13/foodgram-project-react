from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth import validators

from backend.users.validators import no_me_username_validator


class User(AbstractUser):
    USER = 'user'
    MODERATOR = 'moderator'
    ADMIN = 'admin'
    ROLES = [
        (USER, 'пользователь'),
        (MODERATOR, 'модератор'),
        (ADMIN, 'администратор'),
    ]
    username_validator = validators.UnicodeUsernameValidator()
    username = models.CharField(
        'username',
        max_length=150,
        unique=True,
        help_text='Введите уникальный username пользователя',
        validators=[username_validator, no_me_username_validator],
        error_messages={
            'unique': "Пользователь с таким именем уже существует",
        },
    )
    email = models.EmailField(
        'email адрес', max_length=254, unique=True,
        help_text='Введите email адрес')
    role = models.CharField(
        'Роль', max_length=64, choices=ROLES, default=USER,
        help_text='Выберите роль пользователя')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(username='me'),
                name='no_username_me',
            ),
        ]

    def __str__(self) -> str:
        return self.username

    def is_admin(self):
        return self.role == self.ADMIN or self.is_staff

    def is_moderator(self):
        return self.role == self.MODERATOR



class User_list(models.Model):
    """Model for a list of users."""
    page = models.ImageField(max_length=225)
    limit = models.IntegerField(max_length=255)

def __str__(self):
        return self.page

class Meta:
      verbose_name = 'Cписок пользователей'
      verbose_name_plural = 'Список пользователей'


class Register_user(models.Model):
     """Model for register user."""
     email = models.EmailField(
          max_length=254,
          blank=True,
          verbose_name='Адрес электронной почты'
          )
     username = models.SlugField(
          max_length=150,
          unique=True,
          blank=True,
          verbose_name='Уникальное имя пользователя'
          )
     first_name = models.CharField(
          max_length=150,
          blank=True,
          verbose_name='Имя'
          )
     last_name = models.CharField(
          max_length=150,
          blank=True,
          verbose_name='Фамилия'
     )
     password = models.SlugField(
          max_length=150,
          blank=True,
          verbose_name='Пароль'
     )


class Profile_user(models.Model):
     """Profile for user."""
     ...
