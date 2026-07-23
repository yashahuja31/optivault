"""Auth0 access-token verification.

Tokens are RS256-signed by Auth0. We fetch the tenant's public signing keys
(JWKS) once and cache them in-process, then verify each incoming token's
signature, audience, and issuer with PyJWT.
"""
from functools import lru_cache

import jwt
from jwt import PyJWKClient

from app.config import settings


class AuthError(Exception):
    """Raised when a token is missing, malformed, or fails verification."""


@lru_cache(maxsize=1)
def _jwk_client() -> PyJWKClient:
    if not settings.auth0_domain:
        raise AuthError("AUTH0_DOMAIN is not configured")
    jwks_url = f"https://{settings.auth0_domain}/.well-known/jwks.json"
    return PyJWKClient(jwks_url)


def verify_auth0_token(token: str) -> dict:
    """Validate an Auth0 access token and return its decoded claims.

    Raises AuthError on any failure (bad signature, wrong audience/issuer,
    expired, or malformed token).
    """
    if not settings.auth0_audience:
        raise AuthError("AUTH0_AUDIENCE is not configured")

    try:
        signing_key = _jwk_client().get_signing_key_from_jwt(token)
        return jwt.decode(
            token,
            signing_key.key,
            algorithms=settings.auth0_algorithms,
            audience=settings.auth0_audience,
            issuer=f"https://{settings.auth0_domain}/",
        )
    except jwt.PyJWTError as exc:
        raise AuthError(str(exc)) from exc
