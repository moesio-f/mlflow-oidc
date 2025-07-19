"""Auto refresh module
for user credentials.
"""

import os
import threading
import time
from datetime import datetime

from .config import OIDC_CLIENT as client

# Multiplier that defines how much
#   of the remaining lifetime of
#   the access token should the thread
#   sleep prior to refreshing it again.
# Smaller values make the thread refresh
#   the token more frequently.
_WAIT_MULTIPLIER = 1 / 250


class TokenAutoRefresh:
    """Token auto refresh context.

    This context starts a new thread that automatically
    updates the `MLFLOW_TRACKING_TOKEN` environment variables
    with a new (refreshed) access token.
    """

    def __init__(self):
        self._thread = None
        self._stop = False

    def __enter__(self):
        assert self._thread is None and not self._stop
        # Guarantee that the environment variable is set
        self._base_refresh()

        # Schedule threads to periodic update tokens
        self._thread = threading.Thread(target=self._refresh_mlflow_token)
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._thread is not None:
            self._stop = True
            self._thread.join()
            self._stop = False
            self._thread = None

    def _refresh_mlflow_token(self):
        """Infinite loop that refreshes the access
        token and updates the MLFlow token variable.
        """
        while not self._stop:
            self._base_refresh()

            # Sleep for some time smaller than the expiration
            remaining_lifetime = (
                datetime.now() - client.user.timestamp
            ).total_seconds()
            time.sleep(remaining_lifetime * _WAIT_MULTIPLIER)

    def _base_refresh(self):
        # Refresh token
        client.refresh()

        # Update MLFlow environment variable
        os.environ["MLFLOW_TRACKING_TOKEN"] = client.user.access_token.encoded
