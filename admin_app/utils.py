from django.conf import settings
from django.core.cache import cache
from .models import SystemSetting


def get_setting(key: str):
    cache_key = f'setting_{key}'

    # Check Redis cache first
    cached_value = cache.get(cache_key)
    if cached_value is not None:
        return cached_value

    # If not in cache, get from the database
    try:
        db_value = SystemSetting.objects.get(pk=key).value
        # Save the value to Redis for next time
        cache.set(cache_key, db_value, timeout=3600)
        return db_value
    except SystemSetting.DoesNotExist:
        # Fallback to a default in settings.py
        return getattr(settings, 'DEFAULT_SYSTEM_SETTINGS', {}).get(key)