from rest_framework.pagination import PageNumberPagination


class PageNumberPagination(PageNumberPagination):
    page_size_param = 'limit'