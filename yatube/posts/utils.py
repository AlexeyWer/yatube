from django.conf import settings
from django.core.paginator import Paginator


def get_paginator(query, page_number):
    """Функция создания паджинатора."""
    paginator = Paginator(query, settings.PUB_COUNT)
    page_obj = paginator.get_page(page_number)
    return page_obj
