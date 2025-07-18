"""Sample MLFlow artifact logging."""

import os
from pathlib import Path

import mlflow

from . import auto_refresh
from .config import CONFIG as config

if __name__ == "__main__":
    mlflow.set_tracking_uri(config.MLFLOW_REMOTE_TRACKING_URL)
    with auto_refresh.TokenAutoRefresh():
        with mlflow.start_run(run_name="test-artifact"):
            p = Path("sample.txt")
            p.write_text("Hi! This is a sample artifact to be logged.")
            mlflow.log_metric("file_size", os.path.getsize(p))
            mlflow.log_artifact(p)
            p.unlink()
