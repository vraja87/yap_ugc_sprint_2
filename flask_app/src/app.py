import logging
import os
import random
from logstash import LogstashHandler


import sentry_sdk
from flask import Flask, request
from sentry_sdk.integrations.flask import FlaskIntegration

SENTRY_DSN = os.getenv("SENTRY_FLASK_DSN")
sentry_sdk.init(
    dsn=SENTRY_DSN,
    # Set traces_sample_rate to 1.0 to capture 100% of transactions for performance monitoring.
    traces_sample_rate=1.0,
    # Set profiles_sample_rate to 1.0 to profile 100% of sampled transactions.
    profiles_sample_rate=1.0,
    enable_tracing=True,
    integrations=[FlaskIntegration()],
)

class RequestIdFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request.headers.get('X-Request-Id')
        return True

app = Flask(__name__)
app.logger = logging.getLogger(__name__)
app.logger.setLevel(logging.INFO)
app.logger.addFilter(RequestIdFilter())
logstash_handler = LogstashHandler(host='logstash', port=5044, version=0)
app.logger.addHandler(logstash_handler)


@app.before_request
def before_request() -> None:
    request_id = request.headers.get("X-Request-Id")
    if not request_id:
        raise RuntimeError("request id is requred")


@app.route("/")
def index() -> str:
    result = random.randint(1, 50)
    app.logger.info(f"Пользователю досталось число {result}")
    return f"Ваше число {result}!"
