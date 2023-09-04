import re

from django.core.exceptions import ValidationError


def username_validator(value):
    symb = "".join(set(re.findall(r"[^\w.@+-]", value)))
    if symb:
        raise ValidationError(f"Недопустимые символы в имени: {symb}")
    return value
