import os
from typing import Any

log_dir = os.path.join(os.getcwd(), "logs")
LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s   %(asctime)s   [MSG]   %(message)s",
            "datefmt": "%Y/%m/%d, %H:%M:%S",
            "use_colors": True,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s   %(asctime)s   [HTTP]  %(client_addr)s - "%(request_line)s" %(status_code)s',
            "datefmt": "%Y/%m/%d, %H:%M:%S",
            "use_colors": True,
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
        "uvicorn": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {
            "handlers": ["console-access"],
            "level": "INFO",
            "propagate": False,
        },
    },
}

PROD_LOGGER = {
    "uvicorn": {
        "handlers": ["default", "console"],
        "level": "INFO",
        "propagate": False,
    },
    "uvicorn.error": {"level": "INFO"},
    "uvicorn.access": {
        "handlers": ["access", "console-access"],
        "level": "INFO",
        "propagate": False,
    },
}
