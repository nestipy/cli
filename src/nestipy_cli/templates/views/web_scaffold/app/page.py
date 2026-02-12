from nestipy.web import (
    component,
    h,
    use_state,
    use_effect,
    use_memo,
    use_callback,
    use_context,
    external,
    new_,
)
from layout import ThemeContext

Link = external("react-router-dom", "Link")
create_actions = external("../actions.client", "createActions", alias="createActions")
ApiClient = external("../api/client", "ApiClient")


@component
def Page():
    theme = use_context(ThemeContext)
    message, set_message = use_state("Loading...")
    ping, set_ping = use_state("Loading...")

    actions = create_actions()
    api = new_(ApiClient, {"baseUrl": ""})

    def on_action(result):
        set_message(result.ok and result.data or "Error")

    def on_ping(value):
        set_ping(value)

    def load_action():
        actions.AppActions.hello({"name": "Nestipy"}).then(on_action)

    def load_ping():
        api.ping().then(on_ping)

    reload_action = use_callback(load_action, deps=[])
    reload_ping = use_callback(load_ping, deps=[])

    def label():
        return f"Action says: {message}"

    action_label = use_memo(label, deps=[message])
    use_effect(load_action, deps=[])
    use_effect(load_ping, deps=[])

    links = []
    for item in [
        {"label": "Home", "to": "/"},
        {"label": "Counter", "to": "/counter"},
        {"label": "API", "to": "/api"},
    ]:
        links.append(Link(item["label"], to=item["to"]))

    if ping == "Loading...":
        ping_status = h.span("Loading...", class_name="opacity-80")
    else:
        ping_status = h.span(f"API ping: {ping}", class_name="opacity-80")

    return h.div(
        h.nav(links, class_name="flex gap-4 text-sm"),
        h.h2("Overview", class_name="text-lg font-semibold"),
        h.p(action_label, class_name="text-sm"),
        ping_status,
        h.div(
            h.button(
                "Reload Action",
                on_click=reload_action,
                class_name="px-3 py-1 rounded bg-blue-600 text-white",
            ),
            h.button(
                "Reload API",
                on_click=reload_ping,
                class_name="px-3 py-1 rounded bg-slate-700 text-white",
            ),
            class_name="flex gap-3",
        ),
        h.p(f"Theme: {theme['theme']}", class_name="text-xs opacity-70"),
        class_name="space-y-4",
    )
