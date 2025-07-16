"""Discovery of Identity Provider
configuration through the
well-known endpoint.
"""

import requests
from pydantic import BaseModel, ConfigDict


class OpenIDConfiguration(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    introspection_endpoint: str
    userinfo_endpoint: str
    end_session_endpoint: str

    @classmethod
    def from_provider(cls, provider_wk_url: str) -> "OpenIDConfiguration":
        """Queries the OpenID Connect configuration from the
        .well-known endpoint of the provider.

        :param provider_wk_url: provider well-known
            endpoint URL.
        :return: provider configuration.
        """
        response = requests.get(provider_wk_url)
        response.raise_for_status()
        return cls(**response.json())
