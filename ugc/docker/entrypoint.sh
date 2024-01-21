#!/bin/bash

set -e

# Check for ENV existence
vars=("PROJECT_STAGE")
errors=()

for t in "${vars[@]}"; do
  if [[ -z "${!t}" ]]; then
    errors+=( "$t" )
  fi
done

if [ ${#errors[@]} -ne 0 ]; then
    echo "Missing ENV:"
    echo "${errors[@]}"
    exit 1
fi

# Wait for Elasticsearch
until curl -s --fail -k "${ELASTIC_HOST}" 2>&1 > /dev/null
do
  echo "Waiting for Elasticsearch at ${ELASTICSEARCH_HOST}";
  sleep 1;
done

# Wait for Redis
until redis-cli -h "${CACHE_HOST}" -p "${CACHE_PORT}" ping | grep "PONG" 2>&1 > /dev/null
do
  echo "Waiting for Redis at ${CACHE_HOST}";
  sleep 1;
done

if [ "$START_MODE" == "BACKEND" ]
  then
    if [ "$PROJECT_STAGE" == "local" ]; then
      uvicorn main:app --reload  --host 0.0.0.0 --port 8000
    else
      gunicorn main:app -k uvicorn.workers.UvicornWorker
    fi
  elif [ "$START_MODE" == "TESTS" ]
  then
    pytest . -s -vvv --disable-warnings
  else
    echo "Unknown START_MODE!";
    exit 1;
fi

exec "$@"
