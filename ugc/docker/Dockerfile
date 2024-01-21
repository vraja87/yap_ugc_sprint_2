ARG BUILD_IMAGE=3.11-buster
ARG BASE_IMAGE=3.11-slim-buster

# modules
FROM python:${BUILD_IMAGE} as modules
WORKDIR /wheels
COPY ./conf/requirements.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache --mount=type=cache,target=/pkg pip install -U pip && pip wheel -r requirements.txt -w /pkg

# tests modules
FROM python:${BUILD_IMAGE} as test_modules
WORKDIR /wheels_tests
COPY ./conf/requirements_tests.txt requirements.txt
RUN --mount=type=cache,target=/root/.cache --mount=type=cache,target=/pkg_tests pip install -U pip && pip wheel -r requirements.txt -w /pkg_tests

### builder
FROM python:${BASE_IMAGE} as builder
RUN apt-get update && apt-get upgrade -y \
  && apt-get install --no-install-recommends -y \
    gettext curl \
    # used in entrypoint to wait for redis
    redis-tools \
  && apt-get purge -y --auto-remove \
  && apt-get clean -y && rm -rf /var/lib/apt/lists/*

COPY --from=modules /wheels /wheels
RUN --mount=type=cache,target=/pkg pip install -U pip \
       && pip install --no-index -r /wheels/requirements.txt -f /pkg \
       && rm -rf /wheels \
       && rm -rf /root/.cache/pip/*

### dev build base app image
FROM builder as base

ARG APP_DIR
WORKDIR ${APP_DIR}

COPY ./conf/gunicorn-asgi.conf.py /gunicorn-asgi.conf.py


USER web
EXPOSE 8000
CMD ["uvicorn", "--reload", "--host", "0.0.0.0", "--port", "8000", "main:app"]

### prod build
FROM base AS prod
COPY --chown=web:web ./src ./
RUN cd ./ && rm -rf tests

### tests stage
FROM base AS tests

USER root

COPY --chown=web:web ./src ./

COPY --from=test_modules /wheels_tests /wheels_tests
RUN --mount=type=cache,target=/pkg_tests pip install -U pip \
       && pip install --no-index -r /wheels_tests/requirements.txt -f /pkg_tests \
       && rm -rf /wheels_tests \
       && rm -rf /root/.cache/pip/* \
USER web
