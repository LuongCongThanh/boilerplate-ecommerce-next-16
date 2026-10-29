import pytest
from django.db import connection


@pytest.mark.django_db
def test_extensions_and_immutable_unaccent_exist_after_migrate() -> None:
    with connection.cursor() as cursor:
        cursor.execute("SELECT extname FROM pg_extension")
        extensions = {row[0] for row in cursor.fetchall()}
        cursor.execute("SELECT provolatile FROM pg_proc WHERE proname = 'immutable_unaccent'")
        volatility = cursor.fetchone()
        cursor.execute("SELECT public.immutable_unaccent(lower('Áo Thun Đỏ'))")
        unaccented = cursor.fetchone()

    assert {"unaccent", "pg_trgm", "btree_gist"} <= extensions
    assert volatility == ("i",)
    assert unaccented == ("ao thun do",)
