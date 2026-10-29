from collections.abc import Iterator

import pytest
from django.core.cache import cache


@pytest.fixture(autouse=True)
def _clear_cache() -> Iterator[None]:
    # Bộ đếm throttle nằm trong cache: không để hạn mức của test này ảnh hưởng test khác
    cache.clear()
    yield
    cache.clear()
