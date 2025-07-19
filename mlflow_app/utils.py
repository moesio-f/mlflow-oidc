"""Utilities."""

import getpass

import mlflow

from .config import OIDC_CLIENT as client


def set_oidc_user():
    """Set a oidc.user
    tag from the current OIDC
    access_token. If not available,
    fallback to system username.

    This function should only be called
    on a MLFlow run context.
    """
    mlflow.set_tag(
        "oidc.user",
        client.user.access_token.payload.get("preferred_username", getpass.getuser()),
    )
