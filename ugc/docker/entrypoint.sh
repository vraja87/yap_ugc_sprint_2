#!/bin/bash

if [ "$START_MODE" == "BACKEND" ]
  then
    if [ "$PROJECT_STAGE" == "local" ]; then
      uvicorn main:app --reload  --host 0.0.0.0 --port 8000
    else
      gunicorn main:app -k uvicorn.workers.UvicornWorker
    fi
  elif [ "$START_MODE" == "TESTS" ]
  then
    python -m pytest -s -vvv --disable-warnings
  else
    echo "Unknown START_MODE!";
    exit 1;
fi

exec "$@"
