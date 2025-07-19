"""Sample MLFlow logging."""

import mlflow

from . import auto_refresh, utils
from .config import CONFIG as config

if __name__ == "__main__":
    mlflow.set_tracking_uri(config.MLFLOW_REMOTE_TRACKING_URL)
    with auto_refresh.TokenAutoRefresh():
        with mlflow.start_run(run_name="test-log"):
            utils.set_oidc_user()
            mlflow.log_metric("foo", 1)
            mlflow.log_metric("bar", 2)
