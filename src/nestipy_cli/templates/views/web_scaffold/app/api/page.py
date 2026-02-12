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

    if status == "Loading...":
        status_label = h.span("Waiting for response...", class_name="text-sm text-slate-400")
    else:
        status_label = h.span(f"Ping: {status}", class_name="text-sm text-slate-300")

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
                h.h2("Typed API", class_name="text-2xl font-semibold text-slate-100"),
                h.p(
                    "Generated HTTP client powered by RouterSpec.",
                    class_name="text-sm text-slate-400",
                ),
                class_name="space-y-2",
            ),
            h.div(
                status_label,
                h.button(
                    "Refresh",
                    on_click=refresh,
                    class_name=(
                        "mt-4 rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white "
                        "hover:bg-blue-500"
                    ),
                ),
                class_name="rounded-2xl border border-slate-800 bg-slate-900/60 p-6",
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
