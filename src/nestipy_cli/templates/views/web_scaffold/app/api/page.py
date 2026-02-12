from nestipy.web import (
    component,
    h,
    use_state,
    use_effect,
    use_callback,
    use_context,
    external,
    new_,
)
from layout import ThemeContext

Link = external("react-router-dom", "Link")
ApiClient = external("../../api/client", "ApiClient")


@component
def Page():
    theme = use_context(ThemeContext)
    status, set_status = use_state("Loading...")

    api = new_(ApiClient, {"baseUrl": ""})

    def on_ping(value):
        set_status(value)

    def load():
        api.ping().then(on_ping)

    refresh = use_callback(load, deps=[])
    use_effect(load, deps=[])
    return h.div(
        h.nav(
            Link("Home", to="/"),
            Link("Counter", to="/counter"),
            Link("API", to="/api"),
            class_name="flex gap-4 text-sm",
        ),
        h.h2("Typed API", class_name="text-lg font-semibold"),
        h.p(f"Ping: {status}", class_name="text-sm"),
        h.button(
            "Refresh",
            on_click=refresh,
            class_name="px-3 py-1 rounded bg-blue-600 text-white",
        ),
        h.p(f"Theme: {theme['theme']}", class_name="text-xs opacity-70"),
        class_name="space-y-4",
    )
