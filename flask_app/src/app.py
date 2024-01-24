import logging
import os
import random

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

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)


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
