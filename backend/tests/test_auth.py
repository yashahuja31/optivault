"""Tests for Auth0 token verification (app.core.security.verify_auth0_token).

We generate a throwaway RSA keypair, sign tokens with the private key, and
monkeypatch the module's JWKS client to hand back the matching public key --
so no network call to Auth0 is made.
"""
import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import rsa

from app.core import security
from app.core.security import AuthError, verify_auth0_token

DOMAIN = "test-tenant.us.auth0.com"
AUDIENCE = "https://api.optivault.test"
ISSUER = f"https://{DOMAIN}/"


@pytest.fixture(autouse=True)
def _configure(monkeypatch):
    monkeypatch.setattr(security.settings, "auth0_domain", DOMAIN)
    monkeypatch.setattr(security.settings, "auth0_audience", AUDIENCE)
    monkeypatch.setattr(security.settings, "auth0_algorithms", ["RS256"])


@pytest.fixture
def keypair():
    return rsa.generate_private_key(public_exponent=65537, key_size=2048)


@pytest.fixture(autouse=True)
def _mock_jwks(monkeypatch, keypair):
    """Make verify_auth0_token resolve the signing key to our public key."""
    public_key = keypair.public_key()

    class _FakeKey:
        key = public_key

    class _FakeClient:
        def get_signing_key_from_jwt(self, token):
            return _FakeKey()

    monkeypatch.setattr(security, "_jwk_client", lambda: _FakeClient())


def _make_token(keypair, *, aud=AUDIENCE, iss=ISSUER, alg="RS256"):
    claims = {"sub": "auth0|abc123", "aud": aud, "iss": iss, "email": "u@example.com"}
    return jwt.encode(claims, keypair, algorithm=alg)


def test_valid_token_returns_claims(keypair):
    token = _make_token(keypair)
    claims = verify_auth0_token(token)
    assert claims["sub"] == "auth0|abc123"
    assert claims["email"] == "u@example.com"


def test_wrong_audience_rejected(keypair):
    token = _make_token(keypair, aud="https://some-other-api")
    with pytest.raises(AuthError):
        verify_auth0_token(token)


def test_wrong_issuer_rejected(keypair):
    token = _make_token(keypair, iss="https://evil.example.com/")
    with pytest.raises(AuthError):
        verify_auth0_token(token)


def test_bad_signature_rejected(keypair):
    # Sign with a DIFFERENT key than the JWKS returns.
    other = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    token = _make_token(other)
    with pytest.raises(AuthError):
        verify_auth0_token(token)


def test_missing_audience_config_rejected(keypair, monkeypatch):
    monkeypatch.setattr(security.settings, "auth0_audience", "")
    token = _make_token(keypair)
    with pytest.raises(AuthError):
        verify_auth0_token(token)
