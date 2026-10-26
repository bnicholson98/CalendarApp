import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def clear_throttle_history():
    """Throttle counts live in the cache; reset them so tests don't affect each other."""
    cache.clear()
