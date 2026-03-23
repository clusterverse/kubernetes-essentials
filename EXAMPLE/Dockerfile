FROM ubuntu:24.04
ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Europe/London
SHELL ["/bin/bash", "-c"]

RUN apt-get update \
    && apt-get install -y git iproute2 python3-pip python3-jmespath python3-jinja2 python3-boto3 python3-netaddr python3-dev python3-setuptools python3-wheel \
    && pip3 --no-cache-dir install --break-system-packages pymongo ansible>=10.4.0

WORKDIR /usr/src/app

COPY . .

RUN ansible-galaxy install -r requirements.yml
