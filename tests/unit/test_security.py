from shared.fundit_common import decrypt_text, encrypt_text, sign_token, verify_token


def test_encrypt_roundtrip() -> None:
    secret = "demo-key"
    value = "sensitive backer message"
    encrypted = encrypt_text(value, secret)
    assert encrypted != value
    assert decrypt_text(encrypted, secret) == value



def test_token_roundtrip() -> None:
    token = sign_token({"sub": "BACK-101", "role": "backer"}, "jwt-secret", exp_minutes=5)
    payload = verify_token(token, "jwt-secret")
    assert payload is not None
    assert payload["sub"] == "BACK-101"
