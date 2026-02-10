import os
from typing import Any
DEFAULT_LOG_FORMAT = "[NESTIPY] %(levelname)s %(message)s"
ACCESS_LOG_FORMAT = "[NESTIPY] %(levelname)s [%(asctime)s] %(message)s"
log_dir = os.path.join(os.getcwd(), "logs")
LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "format": DEFAULT_LOG_FORMAT,
        },
        "access": {
            "format": ACCESS_LOG_FORMAT,
            "datefmt": "%Y-%m-%d %H:%M:%S %z",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "stream": "ext://sys.stdout",
        },
        "console-access": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": "ext://sys.stdout",
        },
        "default": {
            "formatter": "default",
            "class": "logging.FileHandler",
            "filename": os.path.join(log_dir, "default.log"),
        },
        "access": {
            "formatter": "access",
            "class": "logging.FileHandler",
            "filename": os.path.join(log_dir, "access.log"),
        },
    },
    "loggers": {
        "_granian": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "granian": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "granian.access": {
            "handlers": ["console-access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

PROD_LOGGER = {
    "_granian": {
        "handlers": ["default", "console"],
        "level": "INFO",
        "propagate": False,
    },
    "granian": {
        "handlers": ["default", "console"],
        "level": "INFO",
        "propagate": False,
    },
    "granian.access": {
        "handlers": ["access", "console-access"],
        "level": "INFO",
        "propagate": False,
    },
}
