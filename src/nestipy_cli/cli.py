import importlib
import os.path
import sys
from pathlib import Path
from subprocess import DEVNULL, check_call
import questionary
import rich_click as click
import uvicorn
from click_aliases import ClickAliasedGroup
from yaspin import yaspin

from .config import PROD_LOGGING_CONFIG
from .handler import NestipyCliHandler
from .style import CliStyle

handler = NestipyCliHandler()
echo = CliStyle()


@click.group(cls=ClickAliasedGroup)
def main():
    click.clear()


@main.command()
@click.argument('name')
def new(name):
    """ Create new project """
    # if not shutil.which('poetry'):
    # curl -sSL https://install.python-poetry.org | python3 -
    click.clear()
    created = handler.create_project(name)
    if not created:
        echo.error(f"Folder {name} already exist.")
    echo.info(f"Project {name} created successfully.\nStart your project by running:\n\tcd {name}"
              f"\n\tpython -m pip install -r requirements.py\n\tpython main.py")
    # else:
    #     echo.error(f"Nestipy need poetry as dependency manager.")


@main.group(cls=ClickAliasedGroup, name='generate', aliases=['g', 'gen'])
def make():
    """ Generate resource, module, controller, service, resolver, graphql input """
    pass


@main.command(name="start")
@click.argument('app_path', default='main:app')
@click.option('-D', '--dev', is_flag=True, default=False, help="Development server")
@click.option('-P', '--port', required=False, default=8000, help="Server port")
@click.option('-H', '--host', required=False, default="0.0.0.0", help="Server host")
@click.option('--workers', default=1, type=int, help='Number of worker processes.')
@click.option('--ssl-keyfile', type=str, help='SSL certificate key.')
@click.option('--ssl-cert-file', type=str, help='SSL certificate file.')
def start(app_path: str, dev: bool, port: int, host: str, workers: int, ssl_keyfile: str, ssl_cert_file) -> None:
    """ Starting nestipy server """
    try:
        import nestipy
    except ImportError:
        with yaspin(text="Installing nestipy ...", color="blue") as spinner:
            spinner.color = 'blue'
            check_call([sys.executable, "-m", "pip", "install", "pip", "--upgrade"], stdout=DEVNULL)
            check_call([sys.executable, "-m", "pip", "install", "nestipy", "--upgrade"], stdout=DEVNULL)
            spinner.color = 'green'
            spinner.ok("✔")

    module_path, app_name = app_path.split(":")
    module_file_path = Path(module_path).resolve()
    module_name = module_file_path.stem
    sys.path.append(str(module_file_path.parent))
    m = importlib.import_module(module_name)
    app = getattr(m, app_name)
    config = uvicorn.config.LOGGING_CONFIG
    if not dev:
        config = PROD_LOGGING_CONFIG
        log_dir = os.path.join(os.getcwd(), 'logs')
        if not os.path.exists(log_dir):
            os.mkdir(log_dir)
            open(os.path.join(log_dir, 'default.log'), 'a').close()
            open(os.path.join(log_dir, 'access.log'), 'a').close()
    uvicorn.run(
        app_path,
        reload=dev,
        host=host,
        port=port,
        workers=workers,
        log_config=config,
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_cert_file,
        use_colors=True
    )


@make.command(name='resource', aliases=['r', 'res'])
@click.argument('name')
def resource(name: str) -> None:
    """Create new resource for project.
    :rtype: object
    :param name:
    :type name: 
    """
    name = str(name).lower()
    choice = questionary.select('Select resource type:', choices=['api', 'graphql']).ask()
    if choice == 'graphql':
        handler.generate_resource_graphql(name)
    else:
        handler.generate_resource_api(name)
    echo.success(f"Resource created successfully inside src/{name}.")


@make.command(aliases=['mod'])
@click.argument('name')
def module(name):
    """Create new module"""
    name = str(name).lower()
    handler.generate_module(name, prefix='single')
    echo.success(f"Module created successfully inside src/{name}.")


@make.command(aliases=['ctrl'])
@click.argument('name')
def controller(name):
    """ Create new controller """
    name = str(name).lower()
    handler.generate_controller(name, prefix='single')
    echo.success(f"Controller created successfully inside src/{name}.")


@make.command()
@click.argument('name')
def resolver(name):
    """ Create new graphql resolver """
    handler.generate_resolver(name, prefix='single')
    echo.success(f"Resolver created successfully inside src/{name}.")


@make.command()
@click.argument('name')
def service(name):
    """ Create new service """
    name = str(name).lower()
    handler.generate_service(name, prefix='single')
    echo.success(f"Service created successfully inside src/{name}.")


@make.command(name='input')
@click.argument('name')
def graphql_input(name):
    """ Create new service """
    name = str(name).lower()
    handler.generate_service(name, prefix='single')
    echo.success(f"Graphql Input created successfully inside src/{name}.")


if __name__ == "__main__":
    main()
