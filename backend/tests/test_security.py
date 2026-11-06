from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from backend.app.security import create_token, decode_token, hash_password, verify_password  # noqa: E402


def test_password_roundtrip() -> None:
    stored = hash_password("user123")
    assert stored.startswith("pbkdf2$")
    assert verify_password("user123", stored)
    assert not verify_password("wrong", stored)


def test_password_salt_is_random() -> None:
    assert hash_password("same") != hash_password("same")


def test_token_roundtrip() -> None:
    token = create_token(42)
    assert decode_token(token) == 42
    assert decode_token(token + "x") is None
