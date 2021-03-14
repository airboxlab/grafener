ARG GRAFANA_VERSION="latest"

FROM grafana/grafana:${GRAFANA_VERSION}-ubuntu

COPY rootfs /
RUN chmod +x /usr/local/bin/backend.py /all_run.sh

ENTRYPOINT /all_run.sh