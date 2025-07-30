from typing import Optional, Any

import click


class CliStyle:
    @classmethod
    def info(cls, info: Optional[Any] = None, **styles: dict):
        click.secho(info, fg="green", **styles)

    @classmethod
    def error(cls, info: Optional[Any] = None, **styles: dict):
        click.secho(info, fg="red", err=True, **styles)

    @classmethod
    def warning(cls, info: Optional[Any] = None, **styles: dict):
        click.secho(info, fg="orange", **styles)

    @classmethod
    def success(cls, info: Optional[Any] = None, **styles: dict):
        click.secho(info, fg="green", bold=True, **styles)


echo = CliStyle()
