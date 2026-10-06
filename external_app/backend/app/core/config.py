"""App settings. Values are read from environment variables (and `.env`), once per process."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Besides the environment, read the .env file of this folder (other keys of it, like API_PORT, are ignored).
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "External App"
    app_description: str = "A simple API to create, read, update and delete contacts."
    api_v1_prefix: str = "/api/v1"
    # Websites allowed to call this API from a browser (CORS).
    # Set as a JSON list in the CORS_ORIGINS environment variable.
    cors_origins: list[str] = ["http://localhost:3000"]
    # Human review requests sent by the flow host (CrewAI AMP) through a webhook.
    # The secret of the webhook, shown in the AMP dashboard (`whsec_...`). Every webhook must carry a valid
    # HMAC-SHA256 signature made with it (see verify_signature in api/webhook.py). Without it,
    # the webhook is refused.
    crewai_hitl_webhook_secret: str = ""
    # The secret of the kickoff webhook (Webhook Streaming, POST /flow-webhook). Any secret you choose: the Next.js
    # proxy gives it to AMP in each kickoff, and AMP sends it back as `Authorization: Bearer <secret>`, so the
    # frontend needs the same value. Without it, the events are refused.
    crewai_kickoff_webhook_secret: str = ""
    # SQLite: one file inside the project (relative to where the app runs: `external_app/backend/`, so
    # the file ends up in `external_app/backend/data/`). Created on the first start, not versioned.
    database_url: str = "sqlite:///./data/external_app.db"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load the settings once per process and reuse them.

    Use it anywhere a value is needed (`get_settings().database_url`). In tests, call
    `get_settings.cache_clear()` after changing an environment variable.
    """
    return Settings()
