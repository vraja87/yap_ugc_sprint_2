import json
import logging
from typing import Any

from loguru import logger

LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

LOG_DEFAULT_HANDLERS = ["console"]

fmt = "{process.id} - {thread.id} - {time} - {name} - {level} - {message}"
logger.add("server.log", format=fmt, rotation="10MB", compression="zip", enqueue=True)

LOG_FORMAT_JSON = '{"level":"{level}", "message":"{message}", "request_id": 123}'


def serialize(record):
    subset = {"timestamp": record["time"].timestamp(), "message": record["message"]}
    return json.dumps(subset)


def formatter(record):
    record["extra"]["serialized"] = serialize(record)
    return "{extra[serialized]}\n"


logger.add(
    "/var/log/ugc/rotated.json",
    level="DEBUG",
    format=formatter,
    rotation="10 MB",
    retention="10 days",
    compression="zip",
    serialize=True,
)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": LOG_FORMAT},
        "default": {"()": "uvicorn.logging.DefaultFormatter", "fmt": "%(levelprefix)s %(message)s", "use_colors": None},
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": "%(levelprefix)s %(client_addr)s - '%(request_line)s' %(status_code)s",
        },
    },
    "handlers": {
        "console": {"level": "DEBUG", "class": "logging.StreamHandler", "formatter": "verbose"},
        "default": {"formatter": "default", "class": "logging.StreamHandler", "stream": "ext://sys.stdout"},
    },
    "loggers": {
        "": {"handlers": LOG_DEFAULT_HANDLERS, "level": "INFO"},
        "uvicorn.error": {"level": "INFO"},
    },
    "root": {"level": "INFO", "formatter": "verbose", "handlers": LOG_DEFAULT_HANDLERS},
}


class LoggerAdapter:
    """A LoggerAdapter adapts a `loguru` logger to be compatible with the standard `logging` library."""

    def __init__(self, logger: "logger"):
        """Initialize a LoggerAdapter.

        :param logger: The logger object from `loguru` to be adapted.
        """
        self.logger = logger

    def log(self, level: int, message: str, *args, **kwargs):
        """Logs a message with the specified severity.

        :param level: The severity level of the log.
        :param message: The message to be logged.
        :param args: Arguments for string formatting of the message.
        :param kwargs: Keyword arguments for the logger.
        """
        if args:
            message = message % args
        if level == logging.INFO:
            self.logger.info(message, **kwargs)
        elif level == logging.WARNING:
            self.logger.warning(message, **kwargs)
        elif level == logging.ERROR:
            self.logger.error(message, **kwargs)
        else:
            self.logger.debug(message, **kwargs)

    def __getattr__(self, name: str) -> Any:
        """Retrieves an attribute from the logger object.

        :param name: Name of the attribute.
        :returns: The attribute value.
        """
        return getattr(self.logger, name)
