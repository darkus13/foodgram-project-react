from django.db import models

from django.contrib.auth.models import AbstractUser

from users.validators import username_validator


class User(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    email = models.EmailField(
        'email адрес',
        max_length=254,
        unique=True,
    )
    first_name = models.CharField(
        verbose_name='Имя',
        max_length=150,
    )
    last_name = models.CharField(
        verbose_name='Фамилия',
        max_length=150,
    )

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
        return self.role == self.ADMIN
    

class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following'
    )

    class Meta:
        ordering = ('id', )
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_subsription',
            ),
            models.CheckConstraint(
                check=~models.Q(author=models.F('user')),
                name='check_not_self'
            ),
        ]

    def __str__(self) -> str:
        return (f'Подписка {self.user.get_username()} '
                f'на {self.author.get_username()}')
