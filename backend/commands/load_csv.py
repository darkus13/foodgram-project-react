import csv

from django.conf import settings
from django.core.management.base import BaseCommand
from recipes.models import Ingredient, Tag, User

CSV_FILES = {
    'users': User,
    'tag': Tag,
    'ingredient': Ingredient
}

CONTENT_DIR = settings.BASE_DIR / 'backend/data'


class Command(BaseCommand):
    """
    Импортирует данные для конкретных моделей из .csv файлов.
    """

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-existing',
            action='store_true',
            dest='delete_existing',
            default=False,
            help='Удаляет существующие данные конкретной Модели',
        )

    def handle(self, *args, **options):
        for file, model in CSV_FILES.items():
            with open(CONTENT_DIR / f'{file}.csv', newline='',
                      encoding='UTF-8') as f:
                reader = csv.DictReader(f)
                if options["delete_existing"]:
                    model.objects.all().delete()
                self.stdout.write(self.style.SUCCESS(
                    f'Удалены старые записи {file.capitalize()}.'))
                for row in reader:
                    model.objects.create(**row)
                self.stdout.write(self.style.SUCCESS(
                    f'Записи {file.capitalize()} созданы.'))

        self.stdout.write(self.style.SUCCESS(
            'Поздравляем! Ваша БД наполнена!. '))
