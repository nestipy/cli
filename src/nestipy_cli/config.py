import os
from typing import Any
log_dir = os.path.join(os.getcwd(), 'logs')
PROD_LOGGING_CONFIG: dict[str, Any] = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": '%(levelprefix)s %(client_addr)s - "%(request_line)s" %(status_code)s',  # noqa: E501
        },
    },
    "handlers": {
        "default": {
                "formatter": "default",
                "class": "logging.FileHandler",
                "filename": os.path.join(log_dir, 'default.log'),
            },
            "access": {
                "formatter": "access",
                "class": "logging.FileHandler",
                "filename": os.path.join(log_dir, 'access.log'),
            },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO", "propagate": False},
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["access"], "level": "INFO", "propagate": False},
    },
}