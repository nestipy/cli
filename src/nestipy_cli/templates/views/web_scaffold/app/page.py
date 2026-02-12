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
        links.append(
            Link(
                item["label"],
                to=item["to"],
                class_name=(
                    "rounded-full px-4 py-2 text-xs font-medium text-slate-300 "
                    "hover:bg-slate-800 hover:text-white"
                ),
            )
        )

    if ping == "Loading...":
        ping_status = h.span("Loading...", class_name="text-sm text-slate-400")
    else:
        ping_status = h.span(f"API ping: {ping}", class_name="text-sm text-slate-300")

    return h.div(
        h.nav(
            links,
            class_name=(
                "inline-flex items-center gap-2 rounded-full border border-slate-800 "
                "bg-slate-900/60 p-1"
            ),
        ),
        h.section(
            h.div(
                h.h2(
                    "Overview",
                    class_name="text-2xl font-semibold text-slate-100",
                ),
                h.p(
                    "A minimal fullstack starter with actions + typed clients.",
                    class_name="text-sm text-slate-400",
                ),
                class_name="space-y-2",
            ),
            h.div(
                h.div(
                    h.p("Server Actions", class_name="text-xs uppercase text-slate-500"),
                    h.p(action_label, class_name="text-base text-slate-200"),
                    h.div(
                        h.button(
                            "Reload Action",
                            on_click=reload_action,
                            class_name=(
                                "rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white "
                                "hover:bg-blue-500"
                            ),
                        ),
                        class_name="mt-4",
                    ),
                    class_name=(
                        "rounded-2xl border border-slate-800 bg-slate-900/60 p-6 "
                        "shadow-[0_0_40px_-20px_rgba(59,130,246,0.6)]"
                    ),
                ),
                h.div(
                    h.p("Typed API", class_name="text-xs uppercase text-slate-500"),
                    ping_status,
                    h.div(
                        h.button(
                            "Reload API",
                            on_click=reload_ping,
                            class_name=(
                                "rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-white "
                                "hover:bg-slate-600"
                            ),
                        ),
                        class_name="mt-4",
                    ),
                    class_name=(
                        "rounded-2xl border border-slate-800 bg-slate-900/60 p-6 "
                        "shadow-[0_0_40px_-20px_rgba(15,23,42,0.8)]"
                    ),
                ),
                class_name="grid gap-4 md:grid-cols-2",
            ),
            class_name="space-y-6",
        ),
        h.div(
            h.span("Theme", class_name="text-xs uppercase text-slate-500"),
            h.p(
                f"{theme['theme'].title()} mode active",
                class_name="text-sm text-slate-300",
            ),
            class_name="rounded-2xl border border-slate-800 bg-slate-900/50 p-4",
        ),
        class_name="space-y-8",
    )
