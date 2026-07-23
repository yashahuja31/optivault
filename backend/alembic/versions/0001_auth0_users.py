"""replace user password_hash with auth0_sub

Revision ID: 0001_auth0_users
Revises:
Create Date: 2026-07-17

Switches the users table from local password auth to Auth0: drops
password_hash and adds a unique auth0_sub that maps a local row to an Auth0
identity. Existing rows (if any) have no auth0_sub, so they must be cleared
before the NOT NULL/unique constraint is added -- acceptable for dev where
users are re-provisioned on first Auth0 login.
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "0001_auth0_users"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Legacy password-auth rows can't be mapped to an Auth0 identity; remove
    # them so the new NOT NULL auth0_sub column can be enforced.
    op.execute("DELETE FROM users")
    op.add_column("users", sa.Column("auth0_sub", sa.String(), nullable=False))
    op.create_index(op.f("ix_users_auth0_sub"), "users", ["auth0_sub"], unique=True)
    op.drop_column("users", "password_hash")


def downgrade() -> None:
    op.add_column("users", sa.Column("password_hash", sa.String(), nullable=False))
    op.drop_index(op.f("ix_users_auth0_sub"), table_name="users")
    op.drop_column("users", "auth0_sub")
