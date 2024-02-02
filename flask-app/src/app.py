import logging
import os
import random

import sentry_sdk
from flask import Flask, request
from sentry_sdk.integrations.flask import FlaskIntegration
from logstash import LogstashHandler

SENTRY_DSN = os.getenv("SENTRY_FLASK_DSN")
sentry_sdk.init(
    dsn=SENTRY_DSN,
    traces_sample_rate=1.0,
    profiles_sample_rate=1.0,
    enable_tracing=True,
    integrations=[FlaskIntegration()],
)


class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request.headers.get("X-Request-Id")
        return True


app = Flask(__name__)

logstash_handler = LogstashHandler(host="logstash", port=5044, version=0, tags=["flask"])
app.logger.setLevel(logging.INFO)
app.logger.addFilter(RequestIdFilter())
app.logger.addHandler(logstash_handler)


@app.before_request
def before_request() -> None:
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        raise RuntimeError("request id is required")


@app.route("/")
def index() -> str:
    result = random.randint(1, 50)
    app.logger.info(
        f"Пользователю досталось число {result}",
        extra={
            'service_name': 'flask',
            'request_id': request.headers.get("X-Request-Id")
        })
    return f"Ваше число {result}!"
