from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central app config. All values overridable via environment / .env file."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Core
    environment: str = "local"  # local | staging | production
    database_url: str = "postgresql://optivault:optivault@localhost:5432/optivault"
    redis_url: str = "redis://localhost:6379/0"

    # Auth (Auth0)
    # auth0_domain: your tenant domain, e.g. "dev-xxxx.us.auth0.com" (no scheme)
    # auth0_audience: the Identifier of the Auth0 API you created
    auth0_domain: str = ""
    auth0_audience: str = ""
    auth0_algorithms: list[str] = ["RS256"]

    # AWS (only used for demo/local scanning against a real bucket;
    # in production, per-customer credentials come from Cloud_Account rows)
    aws_default_region: str = "us-east-1"


settings = Settings()
