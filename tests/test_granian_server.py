import inspect
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.append(str(Path(__file__).resolve().parents[1] / "src"))

from nestipy_cli.config import PROD_LOGGER  # noqa: E402
from nestipy_cli.server import (  # noqa: E402
    GranianStartConfig,
    build_granian_options,
    build_logging_config,
    rewrite_granian_line,
    resolve_granian_init_args,
    select_port,
)


class TestGranianServer(unittest.TestCase):
    def test_build_granian_options_dev(self) -> None:
        cfg = GranianStartConfig(
            app_path="main:app",
            dev=True,
            host="0.0.0.0",
            port=8000,
            workers=2,
            ssl_keyfile=None,
            ssl_cert_file=None,
            loop="auto",
            http="auto",
            is_microservice=False,
            log_config_path=Path("/tmp/granian.json"),
        )
        options = build_granian_options(cfg)
        self.assertTrue(options["reload"])
        self.assertTrue(options["access_log"])
        self.assertFalse(options["no_access_log"])
        self.assertEqual(options["host"], "0.0.0.0")
        self.assertEqual(options["port"], 8000)

    def test_build_granian_options_microservice(self) -> None:
        cfg = GranianStartConfig(
            app_path="main:app",
            dev=False,
            host="127.0.0.1",
            port=9000,
            workers=1,
            ssl_keyfile="key.pem",
            ssl_cert_file="cert.pem",
            loop="asyncio",
            http="1",
            is_microservice=True,
            log_config_path=Path("/tmp/granian.json"),
        )
        options = build_granian_options(cfg)
        self.assertTrue(options["no_access_log"])
        self.assertEqual(options["log_level"], "critical")
        self.assertEqual(options["ssl_keyfile"], "key.pem")
        self.assertEqual(options["ssl_certificate"], "cert.pem")

    def test_resolve_granian_init_args_uses_app_param(self) -> None:
        cfg = GranianStartConfig(
            app_path="main:app",
            dev=False,
            host="127.0.0.1",
            port=9000,
            workers=1,
            ssl_keyfile=None,
            ssl_cert_file=None,
            loop="asyncio",
            http="1",
            is_microservice=False,
            log_config_path=Path("/tmp/granian.json"),
        )

        class DummyGranian:
            def __init__(
                self,
                app,
                interface="asgi",
                host="127.0.0.1",
                port=8000,
                workers=1,
                loop="auto",
                http="auto",
                log_config=None,
                access_log=True,
                reload=False,
            ) -> None:
                pass

        args, kwargs = resolve_granian_init_args(
            cfg, inspect.signature(DummyGranian)
        )
        self.assertEqual(kwargs.get("app"), "main:app")
        self.assertEqual(kwargs.get("host"), "127.0.0.1")
        self.assertEqual(kwargs.get("port"), 9000)

    def test_select_port_microservice_uses_random(self) -> None:
        with mock.patch("nestipy_cli.server.random.randint", return_value=6123):
            self.assertEqual(select_port(8000, True), 6123)
        self.assertEqual(select_port(8000, False), 8000)

    def test_build_logging_config_prod_uses_prod_loggers(self) -> None:
        config = build_logging_config(dev=False)
        self.assertEqual(config["loggers"], PROD_LOGGER)

    def test_rewrite_granian_line(self) -> None:
        self.assertEqual(
            rewrite_granian_line("[INFO] Starting granian"),
            "[NESTIPY] INFO Starting granian",
        )
        self.assertEqual(
            rewrite_granian_line("[NESTIPY] INFO Already formatted"),
            "[NESTIPY] INFO Already formatted",
        )
        self.assertEqual(rewrite_granian_line("plain log"), "plain log")


if __name__ == "__main__":
    unittest.main()
