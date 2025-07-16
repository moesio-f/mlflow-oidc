#!/bin/sh

# Exit on first error
set -e

mlflow server --host 0.0.0.0 --port $MLFLOW_PORT --backend-store-uri $MLFLOW_DB --artifacts-destination $MLFLOW_ARTIFACT_STORAGE
