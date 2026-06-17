"""Tests for password hashing utilities."""

from app.core.security import hash_password, verify_password


def test_hash_password_returns_string() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert isinstance(hashed, str)
    assert hashed


def test_hash_password_not_equal_to_plain_password() -> None:
    plain = "correct-horse-battery-staple"
    assert hash_password(plain) != plain


def test_verify_password_accepts_correct_password() -> None:
    plain = "correct-horse-battery-staple"
    hashed = hash_password(plain)
    assert verify_password(plain, hashed) is True


def test_verify_password_rejects_wrong_password() -> None:
    hashed = hash_password("correct-horse-battery-staple")
    assert verify_password("wrong-password", hashed) is False


def test_hash_password_uses_unique_salts() -> None:
    plain = "correct-horse-battery-staple"
    assert hash_password(plain) != hash_password(plain)
