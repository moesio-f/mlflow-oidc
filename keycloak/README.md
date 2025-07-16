# Keycloak

This directory contains the Keycloak configuration. 

The `Dockerfile` contains instructions to build an optimized image for Keycloak. The following variables are required:

| Variable | Type | Description |
| --- | --- | --- |
| `KC_DB` | string | identifier for the database used (e.g., `postgres`) |
| `KC_DB_URL` | URL | connection URL for the database (e.g., `jdbc:postgresql://<db_host>/<db>`)
| `KC_DB_USERNAME` | string | database username
| `KC_DB_PASSWORD` | string | database password
| `KC_HOSTNAME` | string | Keycloak hostname (e.g., `localhost`)
| `KEYCLOAK_ADMIN` | string | Keycloak admin username |
| `KEYCLOAK_ADMIN_PASSWORD` | string | Keycloak admin password |

The file [`mlflow-realm.json`](./realms/mlflow-realm.json) contains a pre-defined realm for Keycloak. It is pre-configured to run with the default configuration of all other components.
