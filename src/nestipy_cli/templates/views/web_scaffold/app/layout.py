from nestipy.web import component, h, Slot, use_state, use_callback, create_context

ThemeContext = create_context({"theme": "dark", "toggle": None})


@component
def Layout():
    theme, set_theme = use_state("dark")

    def toggle_theme():
        set_theme("light" if theme == "dark" else "dark")

    toggle_handler = use_callback(toggle_theme, deps=[theme])
    return h(
        ThemeContext.Provider,
        h.div(
            h.div(
                h.div(
                    h.span("Nestipy Web", class_name="text-sm uppercase tracking-[0.3em] text-slate-400"),
                    h.h1(
                        "Python-first UI",
                        class_name="text-2xl font-semibold text-slate-100",
                    ),
                    h.p(
                        "Hooks, actions, and typed API clients — all in Python.",
                        class_name="text-sm text-slate-400",
                    ),
                    class_name="space-y-2",
                ),
                h.button(
                    f"Switch to {'light' if theme == 'dark' else 'dark'} mode",
                    on_click=toggle_handler,
                    class_name=(
                        "rounded-full border border-slate-700 bg-slate-900/70 px-4 py-2 "
                        "text-xs font-medium text-slate-200 hover:bg-slate-800"
                    ),
                ),
                class_name="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between",
            ),
            h.div(h(Slot), class_name="mt-10"),
            class_name="mx-auto flex min-h-screen max-w-5xl flex-col px-6 py-10",
        ),
        value={"theme": theme, "toggle": toggle_handler},
    )
