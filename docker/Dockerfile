ARG GRAFANA_VERSION="latest"

FROM grafana/grafana:${GRAFANA_VERSION}-ubuntu

COPY ./docker/all_run.sh /
COPY ./grafener /usr/local/grafener/grafener
COPY ./requirements.txt /usr/local/grafener/

USER root

RUN apt update && \
    apt install -y python3-pip && \
    pip3 install -U pip && \
    pip3 install -r /usr/local/grafener/requirements.txt && \
    chmod +x /all_run.sh

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /usr/local/grafener
ENV GF_INSTALL_PLUGINS grafana-simple-json-datasource

ENTRYPOINT /all_run.sh