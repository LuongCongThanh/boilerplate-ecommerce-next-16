# Extension và hàm cho tìm kiếm không dấu (BR-CAT-13) và ràng buộc EXCLUDE (03 mục 0.7).
# Ba extension là trusted extension nên chủ database tự tạo được, không cần superuser

from django.contrib.postgres.operations import (
    BtreeGistExtension,
    TrigramExtension,
    UnaccentExtension,
)
from django.db import migrations

# unaccent() mặc định là STABLE nên không dùng được trong index. Gọi bản hai tham số với
# schema và từ điển ghi rõ, để kết quả không phụ thuộc search_path và khai báo IMMUTABLE được
CREATE_IMMUTABLE_UNACCENT = """
CREATE FUNCTION public.immutable_unaccent(text) RETURNS text
LANGUAGE sql IMMUTABLE PARALLEL SAFE STRICT
AS $$ SELECT public.unaccent('public.unaccent'::regdictionary, $1) $$;
"""

DROP_IMMUTABLE_UNACCENT = "DROP FUNCTION public.immutable_unaccent(text);"


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        UnaccentExtension(),
        TrigramExtension(),
        BtreeGistExtension(),
        migrations.RunSQL(CREATE_IMMUTABLE_UNACCENT, reverse_sql=DROP_IMMUTABLE_UNACCENT),
    ]
