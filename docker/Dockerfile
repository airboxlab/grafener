ARG GRAFANA_VERSION="latest"

FROM grafana/grafana:${GRAFANA_VERSION}-ubuntu

USER root

RUN apt update && \
    apt install -y python3-pip && \
    pip3 install -U pip

COPY ./requirements.txt /usr/local/grafener/
RUN  pip3 install -r /usr/local/grafener/requirements.txt

COPY ./docker/all_run.sh /
COPY ./grafener /usr/local/grafener/grafener
RUN  chmod +x /all_run.sh

ENV PYTHONUNBUFFERED 1
ENV PYTHONPATH /usr/local/grafener
ENV GF_INSTALL_PLUGINS grafana-simple-json-datasource

ENTRYPOINT /all_run.sh