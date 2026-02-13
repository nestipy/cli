<p align="center">
  <a target="_blank"><img src="https://raw.githubusercontent.com/nestipy/nestipy/release-v1/nestipy.png" width="200" alt="Nestipy Logo" /></a></p>
<p align="center">
    <a href="https://pypi.org/project/nestipy">
        <img src="https://img.shields.io/pypi/v/nestipy?color=%2334D058&label=pypi%20package" alt="Version">
    </a>
    <a href="https://pypi.org/project/nestipy">
        <img src="https://img.shields.io/pypi/pyversions/nestipy.svg?color=%2334D058" alt="Python">
    </a>
    <a href="https://github.com/tsiresymila1/nestipy/blob/main/LICENSE">
        <img src="https://img.shields.io/github/license/tsiresymila1/nestipy" alt="License">
    </a>
</p>

## Description

<p>Nestipy is a Python framework built on top of FastAPI that follows the modular architecture of NestJS</p>
<p>Under the hood, Nestipy makes use of <a href="https://fastapi.tiangolo.com/" target="_blank">FastAPI</a>, but also provides compatibility with a wide range of other libraries, like <a href="https://fastapi.tiangolo.com/" target="_blank">Blacksheep</a>, allowing for easy use of the myriad of third-party plugins which are available.</p>

## Getting started

```cmd
    pip install nestipy-cli
    nestipy new my_app
    cd my_app
    nestipy start --dev
```

```
    ├── src
    │    ├── __init__.py
    ├── app_module.py
    ├── app_controller.py
    ├── app_service.py
    ├── main.py
    ├── pyproject.toml
    ├── uv.lock
    ├── README.md
    
       
```

## Documentation

View full documentation from [here](https://nestipy.vercel.app).

## Support

Nestipy is an MIT-licensed open source project. It can grow thanks to the sponsors and support from the amazing backers.
If you'd like to join them, please [read more here].

## Stay in touch

- Author - [Tsiresy Mila](https://tsiresymila.vercel.app)

## License

Nestipy is [MIT licensed](LICENSE).


## Nestipy Web (Frontend)

Create a fullstack scaffold with the web UI:

```cmd
    nestipy new my_app --web
    cd my_app
    nestipy start --dev --web --web-args "--vite --install"
```

### Nested Layouts

You can add `layout.py` files in any folder under `app/`. The compiler nests
layouts to match the folder structure (similar to Next.js).

- `app/layout.py` wraps every page.
- `app/api/layout.py` wraps only `/api/*`.

Import rules:

- `from layout import X` resolves to the nearest layout.
- `from app.layout import X` forces the root layout.

### Action Security (Presets)

The CLI exposes flags to enable default Web Action security presets. These map
to environment variables consumed by `ActionsModule.for_root`.

Examples:

```
nestipy start --dev --action-security --action-origins "http://localhost:5173" --action-csrf
```

Available flags:

- `--action-security/--no-action-security`
- `--action-origins`
- `--action-allow-missing-origin/--no-action-allow-missing-origin`
- `--action-csrf/--no-action-csrf`
- `--action-signature-secret`
- `--action-permissions/--no-action-permissions`

### notfound.py (Planned)

We plan to add `notfound.py` at any level to define client-side 404 screens
for that subtree, mirroring Next.js behavior.
