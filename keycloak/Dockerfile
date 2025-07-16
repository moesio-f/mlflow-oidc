FROM quay.io/keycloak/keycloak:latest AS builder

# Health checks and database
ENV KC_HEALTH_ENABLED=true
ENV KC_METRICS_ENABLED=true

# Required for optimized build
ARG KC_DB
ARG KC_HEALTH_ENABLED

WORKDIR /opt/keycloak
RUN /opt/keycloak/bin/kc.sh build

FROM quay.io/keycloak/keycloak:latest AS app
COPY --from=builder /opt/keycloak/ /opt/keycloak/

COPY realms/*.json /opt/keycloak/data/import/

ENTRYPOINT ["/opt/keycloak/bin/kc.sh"]
