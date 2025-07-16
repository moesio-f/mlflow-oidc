"""OpenID Connect Client."""

import json
import os
import random
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import requests
from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings

from . import utils
from .jwt import Jwt
from .redirect_server import RedirectServer
from .well_known import OpenIDConfiguration


class ClientConfig(BaseSettings):
    """OIDC client configuration.

    :param provider_wk_url: identity provider
        .well-known endpoint.
    :param client_id:
    :param credential_output:
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    provider_wk_url: str
    client_id: str
    credential_output: Path = Path("oidc_credentials.json")


class UserCredentials(BaseModel):
    """User credentials (tokens).

    :param timestamp: client time during
        last refresh/token acquisition.
    :param access_token: access token.
    :param access_token_expiration: access token
        expiration period (seconds).
    :param refresh_token: refresh token.
    :param refresh_token_expiration: refresh token
        expiration period (seconds).
    :param scope: scopes associated with tokens.
    """

    model_config = ConfigDict(extra="ignore", frozen=True)

    timestamp: datetime
    access_token: Jwt
    access_token_expiration: int
    refresh_token: Jwt
    refresh_token_expiration: int
    scope: str


class Client:
    def __init__(
        self,
        config: ClientConfig | None = None,
        delay_refresh_until_percentage_lifetime: float = 0.5,
    ):
        """Initialize client.

        :param config: client configuration.
        :param delay_refresh_until_percentage_lifetime: how much
            of the lifetime of the token must have passed
            to actually refresh with provider (default=0.5,
            token has <= (1/2 * expiration) seconds left).
        """
        assert delay_refresh_until_percentage_lifetime >= 0.0
        assert delay_refresh_until_percentage_lifetime <= 1.0
        if config is None:
            config = ClientConfig()

        self._lifetime_percentage = delay_refresh_until_percentage_lifetime
        self._client_config = config
        self._provider_config = OpenIDConfiguration.from_provider(
            self._client_config.provider_wk_url
        )
        self._user = None
        if self._client_config.credential_output.exists():
            self._user = self._read_credentials()
            self.refresh()

    @property
    def is_logged(self) -> bool:
        return self._user is not None

    @property
    def user(self) -> UserCredentials:
        assert self.is_logged
        self.refresh()
        return self._user

    def login(self):
        assert not self.is_logged, "User already logged-in."
        server = RedirectServer(
            self._provider_config.token_endpoint,
            self._client_config.client_id,
        )

        # TODO: use logger instead
        print(f"[Client] Openning {server.url} in the browser...")
        print(
            "[Client] If the browser hasn't opened automatically, "
            "copy and paste the URL above into a browser of choice."
        )
        webbrowser.open_new_tab(
            self._auth_endpoint(
                self._provider_config.authorization_endpoint,
                server.url,
                self._client_config.client_id,
            )
        )

        # Blocking call until server receives token
        token = server.read_token()
        self._update_user_from_dict(token, datetime.now())

    def logout(self):
        if not self.is_logged:
            return

        requests.get(
            utils.add_query_params(
                self._provider_config.end_session_endpoint,
                ("id_token_hint", self._user.access_token.encoded),
                ("client_id", self._client_config.client_id),
            )
        )
        self._client_config.credential_output.unlink(missing_ok=False)
        self._user = None

    def refresh(self):
        if not self.is_logged:
            print("[Client] User not logged. Starting login flow instead.")
            self.login()
            return

        now = datetime.now()
        seconds_elapsed = (now - self._user.timestamp).total_seconds()
        lifetime = seconds_elapsed / self._user.access_token_expiration
        if lifetime <= self._lifetime_percentage:
            return

        response = requests.post(
            self._provider_config.token_endpoint,
            data={
                "grant_type": "refresh_token",
                "refresh_token": self._user.refresh_token.encoded,
                "client_id": self._client_config.client_id,
                "scope": self._user.scope,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

        # TODO: add handler for failure and potentially
        #   start login again.
        response.raise_for_status()
        self._update_user_from_dict(response.json(), datetime.now())

    def _update_user_from_dict(self, data: dict, timestamp: datetime):
        data = data.copy()
        data["timestamp"] = timestamp
        for k in ["access_token", "refresh_token"]:
            data[k] = Jwt.decode(data[k])
        # TODO: those fields might be Keycloak-specific
        data["access_token_expiration"] = data["expires_in"]
        data["refresh_token_expiration"] = data["refresh_expires_in"]
        self._user = UserCredentials(**data)
        self._save_credentials()

    def _save_credentials(self):
        cred_file = self._client_config.credential_output
        self._get_file_lock(cred_file)
        with cred_file.open("w+") as f:
            json.dump(
                self._user.model_dump(mode="json"), f, indent=2, ensure_ascii=False
            )
        self._release_file_lock(cred_file)

    def _read_credentials(self) -> UserCredentials:
        cred_file = self._client_config.credential_output
        self._get_file_lock(cred_file)
        with cred_file.open("r") as f:
            credentials = UserCredentials(**json.load(f))
        self._release_file_lock(cred_file)
        return credentials

    @staticmethod
    def _get_file_lock(fname: Path):
        lock = fname.with_suffix(".lock")
        # TODO: add timeout
        while lock.exists():
            # Sleep between [0, 10]cs (centisecond)
            time.sleep(random.random() / 100)
        lock.write_text(f"OWNED BY PID {os.getpid()}")

    @staticmethod
    def _release_file_lock(fname: Path):
        lock = fname.with_suffix(".lock")
        if lock.exists():
            contents = lock.read_text()
            assert contents.split(" ")[-1] == str(
                os.getpid()
            ), "Attempted to release a non-owned lock."
            lock.unlink(missing_ok=False)

    @staticmethod
    def _auth_endpoint(base: str, redirect_uri: str, client_id: str) -> str:
        """Construct authentication endpoint.

        :param base: base URL.
        :param redirect_uri: redirection URL. Should point
            to localhost to exchange auth code for ID+Access.
        :return: authentication endpoint with query parameters.
        """
        return utils.add_query_params(
            base,
            ("client_id", client_id),
            ("response_type", "code"),
            ("redirect_uri", redirect_uri),
            first_delimiter="?",
        )
