from django.utils import timezone


def year(request):
    """Добавляет переменную с текущим годом."""
    year: int = timezone.now().year
    return {
        'year': year
    }
