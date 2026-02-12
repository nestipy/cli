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
    return h.div(
        h.nav(
            Link("Home", to="/"),
            Link("Counter", to="/counter"),
            Link("API", to="/api"),
            class_name="flex gap-4 text-sm",
        ),
        h.h2("Counter", class_name="text-lg font-semibold"),
        h.p(title, class_name="text-sm"),
        h.div(
            h.button(
                "+1",
                on_click=inc,
                class_name="px-3 py-1 rounded bg-blue-600 text-white",
            ),
            h.button(
                "-1",
                on_click=dec,
                class_name="px-3 py-1 rounded bg-slate-700 text-white",
            ),
            class_name="flex gap-3",
        ),
        h.p(f"Theme: {theme['theme']}", class_name="text-xs opacity-70"),
        class_name="space-y-4",
    )
