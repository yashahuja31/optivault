"""Auth dependency.

Auth0 owns the login flow now. This module no longer exposes signup/login
routes -- it just verifies the Auth0 access token on each request and maps it
to a local User row (auto-provisioned on first sight) so the rest of the app
can keep using foreign keys to users.id.
"""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import AuthError, verify_auth0_token
from app.database import get_db
from app.models import User

bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        claims = verify_auth0_token(credentials.credentials)
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )

    auth0_sub = claims.get("sub")
    if not auth0_sub:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing sub")

    user = db.query(User).filter(User.auth0_sub == auth0_sub).first()
    if user is None:
        # First time we've seen this Auth0 user -- create a local row.
        # Email may be absent from the access token depending on scopes/rules;
        # fall back to the sub so the unique email column is still satisfied.
        user = User(auth0_sub=auth0_sub, email=claims.get("email") or auth0_sub)
        db.add(user)
        db.commit()
        db.refresh(user)

    return user
