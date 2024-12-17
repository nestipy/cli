import os.path
import re

import autoflake
import autopep8
import isort

from .templates.generator import TemplateGenerator


class NestipyCliHandler:
    generator: TemplateGenerator

    def __init__(self):
        self.generator = TemplateGenerator()

    def create_project(self, name) -> bool:
        destination = os.path.join(os.getcwd(), name)
        if name == '.':
            destination = os.getcwd()
        if os.path.exists(destination) and name != '.':
            return False
        self.generator.copy_project(destination)
        return True

    @classmethod
    def mkdir(cls, name):
        path = os.path.join(os.getcwd(), 'src', name)
        if not os.path.exists(path):
            os.mkdir(path)
            open(os.path.join(path, '__init__.py'), 'a').close()
        return path

    def generate_resource_api(self, name):
        self.generate_dto(name)
        self.generate_service(name)
        self.generate_controller(name)
        self.generate_module(name)

    def generate_resource_graphql(self, name):
        self.generate_input(name)
        self.generate_service(name, prefix='graphql')
        self.generate_resolver(name)
        self.generate_module(name, prefix='graphql')

    def generate_command(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, 'command', prefix=prefix)

    def generate_module(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, 'module', prefix=prefix)
        self.modify_app_module(name)

    def generate_controller(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, 'controller', prefix=prefix)

    def generate_service(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, 'service', prefix=prefix)

    def generate_resolver(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, 'resolver', prefix=prefix)

    def generate_dto(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, 'dto', prefix=prefix)

    def generate_input(self, name: str, prefix: str = None):
        path = self.mkdir(name)
        self.generate(name, path, 'input', prefix=prefix)

    def generate(self, name, parent_path, template, prefix: str = None):
        pref = f"{f'{prefix}_' if prefix is not None else ''}"
        content = self.generator.render_template(f"{pref}{template}.txt", name=name)
        file_path = str(os.path.join(parent_path, f"{name.lower()}_{template}.py"))
        f = open(file_path, 'w+')
        f.write(content)
        f.close()

    @classmethod
    def modify_app_module(cls, name):
        module_name = str(name).capitalize() + "Module"
        app_path = os.path.join(os.getcwd(), 'app_module.py')
        new_import_statement = f'from src.{name.lower()}.{name.lower()}_module import {module_name}'

        if os.path.exists(app_path):
            with open(app_path, 'r') as file:
                file_content = file.read()
            # Check if the import statement already exists; if not, add it
            if new_import_statement not in file_content:
                file_content = new_import_statement + '\n' + file_content

            # Match the @Module decorator
            module_pattern = r'@Module\s*\(\s*(.*?)\s*\)\s*class'
            match = re.search(module_pattern, file_content, re.DOTALL)

            if match:
                # Extract the current content inside the @Module decorator
                module_body = match.group(1)
                # Search for the 'imports' property in the @Module body
                imports_match = re.search(
                    r'imports\s*=\s*\[\s*((?:[^\[\]]+|\[[^\[\]]*\])*)\s*\]',
                    module_body, re.DOTALL
                )

                if imports_match:
                    # 'imports' exists; extract its content
                    imports_content = imports_match.group(1).strip()

                    # If the module is not already in the imports, add it
                    if module_name not in imports_content:
                        if imports_content and not imports_content.endswith(','):
                            imports_content += ','  # Ensure comma before adding new import

                        new_imports = f'{imports_content}\n\t{module_name}'
                        updated_module_body = re.sub(
                            r'imports\s*=\s*\[\s*((?:[^\[\]]+|\[[^\[\]]*\])*)\s*\]',
                            f'imports=[\n\t{new_imports}\n]',
                            module_body,
                            flags=re.DOTALL
                        )
                    else:
                        updated_module_body = module_body
                else:
                    # If 'imports' doesn't exist, add it to the @Module properties
                    updated_module_body = module_body.strip() + f',\n\timports=[\n\t{module_name}\n]'

                # Replace the old @Module body with the updated one
                updated_content = file_content.replace(module_body, updated_module_body)

                # Clean, sort, and format the final code
                cleaned_code = autoflake.fix_code(updated_content)
                sorted_code = isort.code(cleaned_code)
                formatted_code = autopep8.fix_code(sorted_code)

                # Write the updated content back to the file
                with open(app_path, 'w') as file:
                    file.write(formatted_code)
            else:
                print("No @Module decorator found in app_module.py.")
