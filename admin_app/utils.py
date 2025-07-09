from django.conf import settings
from django.core.cache import cache
from .models import SystemSetting


def get_setting(key: str):
    cache_key = f'setting_{key}'

    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    try:
        db_value = SystemSetting.objects.get(pk=key).value
        cache.set(cache_key, db_value, timeout=3600)
        return db_value
    except SystemSetting.DoesNotExist:
        return getattr(settings, 'DEFAULT_SYSTEM_SETTINGS', {}).get(key)