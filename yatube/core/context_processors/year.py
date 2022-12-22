import datetime


def year(request):
    """Добавляет переменную с текущим годом."""
    year: int = datetime.date.today().year
    return {
        'year': year
    }
