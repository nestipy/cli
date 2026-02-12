from nestipy.web import (
    component,
    h,
    use_state,
    use_memo,
    use_callback,
    use_context,
    external,
)
from layout import ThemeContext

Link = external("react-router-dom", "Link")


@component
def Page():
    theme = use_context(ThemeContext)
    count, set_count = use_state(0)

    def increment():
        set_count(count + 1)

    def decrement():
        set_count(count - 1)

    inc = use_callback(increment, deps=[count])
    dec = use_callback(decrement, deps=[count])

    def label():
        return f"Count: {count}"

    title = use_memo(label, deps=[count])

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

    if count % 2 == 0:
        parity = h.span("Even", class_name="text-xs text-emerald-400")
    else:
        parity = h.span("Odd", class_name="text-xs text-amber-400")

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
                h.h2("Counter", class_name="text-2xl font-semibold text-slate-100"),
                h.p(
                    "Use hooks to keep state and memoize values.",
                    class_name="text-sm text-slate-400",
                ),
                class_name="space-y-2",
            ),
            h.div(
                h.p(title, class_name="text-base text-slate-200"),
                parity,
                h.div(
                    h.button(
                        "+1",
                        on_click=inc,
                        class_name=(
                            "rounded-lg bg-blue-600 px-4 py-2 text-sm font-medium text-white "
                            "hover:bg-blue-500"
                        ),
                    ),
                    h.button(
                        "-1",
                        on_click=dec,
                        class_name=(
                            "rounded-lg bg-slate-700 px-4 py-2 text-sm font-medium text-white "
                            "hover:bg-slate-600"
                        ),
                    ),
                    class_name="mt-4 flex gap-3",
                ),
                class_name="rounded-2xl border border-slate-800 bg-slate-900/60 p-6",
            ),
            class_name="space-y-6",
        ),
        h.div(
            h.span("Theme", class_name="text-xs uppercase text-slate-500"),
            h.p(
                f"{theme['theme']} mode active",
                class_name="text-sm text-slate-300",
            ),
            class_name="rounded-2xl border border-slate-800 bg-slate-900/50 p-4",
        ),
        class_name="space-y-8",
    )
