FROM python:3.11-slim

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir "mlflow[auth]>=3.0.0" "psycopg2-binary>=2.9.10"

COPY ./scripts /scripts

ENV MLFLOW_PORT=8080
ENV MLFLOW_DB=
ENV MLFLOW_ARTIFACT_STORAGE=

CMD ["./scripts/run.sh"]
