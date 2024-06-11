import logfire

from nestipy.core import NestipyFactory

from app_module import AppModule

logfire.configure()
logfire.info('Starting app, {name}!', name='Nestipy-CLI')
app = NestipyFactory.create(AppModule)
