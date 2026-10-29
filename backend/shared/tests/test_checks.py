from django.test import override_settings

from shared.checks import check_pii_hmac_key_length


@override_settings(PII_HMAC_KEYS=(("k2", "x" * 32), ("k1", "short")))
def test_deploy_check_flags_short_secret_by_kid() -> None:
    errors = check_pii_hmac_key_length()

    assert [e.id for e in errors] == ["shared.E001"]
    assert "k1" in errors[0].msg
    assert "short" not in errors[0].msg


@override_settings(PII_HMAC_KEYS=(("k1", "x" * 32),))
def test_deploy_check_passes_long_secret() -> None:
    assert check_pii_hmac_key_length() == []
