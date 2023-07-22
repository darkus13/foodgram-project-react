from django.core.exceptions import ValidationError
from django.utils import timezone


def no_me_username_validator(username):
    if username.lower() == 'me':
        raise ValidationError('username не может быть me')


def validate_year(value):
    now = timezone.now().year
    if value > now:
        raise ValidationError(
            f'{value} не может быть больше {now}'
        )