ARG GRAFANA_VERSION="latest"

FROM grafana/grafana:${GRAFANA_VERSION}-ubuntu

COPY ./docker/all_run.sh /
COPY ./grafener /usr/local/grafener
COPY ./requirements.txt /usr/local/grafener/

RUN apt update && \
    apt install -y python3-pip && \
    pip3 install -U pip && \
    pip3 install -r /usr/local/grafener/requirements.txt && \
    chmod +x /all_run.sh

ENTRYPOINT /all_run.sh