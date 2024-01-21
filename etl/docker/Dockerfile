ARG BUILD_IMAGE=3.11-bookworm
ARG BASE_IMAGE=3.11-slim-bookworm

# modules
FROM python:${BUILD_IMAGE} AS modules
WORKDIR /wheels
COPY ./conf/requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache --mount=type=cache,target=/pkg pip install -U pip && pip wheel -r requirements.txt -w /pkg

### builder
FROM python:${BASE_IMAGE} AS builder
RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    gettext curl \
  && apt-get purge -y --auto-remove \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=modules /wheels /wheels
RUN --mount=type=cache,target=/pkg pip install -U pip \
       && pip install --no-index -r /wheels/requirements.txt -f /pkg \
       && rm -rf /wheels \
       && rm -rf /root/.cache/pip/*

### dev build base app image
FROM builder AS base

ARG APP_DIR
WORKDIR ${APP_DIR}

RUN groupadd -r web && useradd -r -g web web

USER web

COPY --chown=web:web ./src ./

ENTRYPOINT ["python", "main.py"]
