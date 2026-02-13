import os
import shutil

from minijinja import Environment


class TemplateGenerator:
    env: Environment

    def __init__(self):
        self.env = Environment(loader=self.loader)
        # self.env.add_filter('capitalize', str.capitalize)
        # self.env.add_filter('lower', str.lower)

    @classmethod
    def template_path(cls, name: str) -> str | None:
        segments = []
        for segment in name.split("/"):
            if "\\" in segment or segment in (".", ".."):
                return None
            segments.append(segment)
        path = os.path.join(os.path.dirname(__file__), "views", *segments)
        return path if os.path.isfile(path) else None

    @classmethod
    def loader(cls, name):
        path = cls.template_path(name)
        if not path:
            return None
        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
                return content
        except (IOError, OSError):
            return None

    def render_template(self, template, **kwargs):
        return self.env.render_template(template, **kwargs)

    @classmethod
    def copy_template_file(cls, template: str, destination: str) -> None:
        path = cls.template_path(template)
        if not path:
            raise FileNotFoundError(f"Template not found: {template}")
        os.makedirs(os.path.dirname(destination), exist_ok=True)
        shutil.copyfile(path, destination)

    @classmethod
    def copy_project(cls, destination):
        shutil.copytree(
            os.path.join(os.path.dirname(__file__), "project"),
            destination,
            dirs_exist_ok=True,
        )
