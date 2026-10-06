"""Settings for the flow, read from environment variables and from the `.env` file.

Use `get_settings()` anywhere you need a value:

    from crewai_flow.config import get_settings

    flag = get_settings().flow_include_duplicate_email

Why a function and not plain constants? The values are read when the function is called, not when
the module is imported. And thanks to the cache, the environment and the `.env` file are read only
once per process. On CrewAI AMP the values come from the environment variables of the deployment.
"""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# The project root (the folder that contains pyproject.toml).
PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Flow settings. Each field can be set with an environment variable of the same name."""

    # Real environment variables win over the `.env` file.
    # extra="ignore" lets `.env` hold other keys without errors.
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        env_ignore_empty=True,
        case_sensitive=False,
        extra="ignore",
    )

    max_contacts_per_run: int = 10
    """Limit of contacts generated in one run."""

    flow_default_count: int = 3
    """Default number of contacts to generate in one run."""

    external_app_api_url: str = "http://localhost:8000"
    """Where the External App backend runs. The flow sends the selected contacts here.

    On AMP, `localhost` is the flow's own container, so set the public (tunnel) address of the backend in
    the environment variables of the deployment. Otherwise every import fails with `Connection refused`.
    """

    flow_include_duplicate_email: bool = False
    """Teaching aid: one generated contact reuses another contact's email.

    Saving both makes the contacts API answer 409 for the second one, so you can see a failure in the
    UI. Set to false to turn it off.
    """


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Load the settings once per process and reuse them.

    In tests, call `get_settings.cache_clear()` after changing an environment variable.
    """
    return Settings()
