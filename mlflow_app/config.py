"""Configuration."""

import json
import os
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from oidc_client import Client, ClientConfig


class AppConfig(BaseSettings):
    model_config = SettingsConfigDict(extra="ignore")

    MLFLOW_REMOTE_TRACKING_URL: str
    PROVIDER_WK_URL: str
    CLIENT_ID: str
    CREDENTIAL_OUTPUT: Path = Path("credentials.json")

    @model_validator(mode="after")
    def check_urls(self):
        for k, v in zip(
            ["MLFlow remote tracking URL", "Identity provider .well-known URL"],
            [self.MLFLOW_REMOTE_TRACKING_URL, self.PROVIDER_WK_URL],
        ):
            if not v.endswith("/"):
                raise ValueError(f"{k} must end with '/'.")
        return self


# Load configuration on import
_LOCAL_CONFIG = os.getenv("USER_CONFIG_PATH", "mlflow_config.json")
if _LOCAL_CONFIG is not None:
    config = Path(_LOCAL_CONFIG)
    if config.exists():
        CONFIG = AppConfig(**json.loads(config.read_text("utf-8")))
    else:
        CONFIG = AppConfig()
    del config
del _LOCAL_CONFIG

# Create global OIDC client
OIDC_CLIENT = Client(
    ClientConfig(
        provider_wk_url=CONFIG.PROVIDER_WK_URL,
        client_id=CONFIG.CLIENT_ID,
        credential_output=CONFIG.CREDENTIAL_OUTPUT,
    )
)
