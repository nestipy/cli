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
        h.header(
            h.h1("Nestipy Web"),
            h.p(f"Theme: {theme}", class_name="text-sm opacity-80"),
            class_name="space-y-1",
        ),
        h(Slot),
        value={"theme": theme, "toggle": toggle_handler},
        class_name="min-h-screen bg-slate-950 text-white p-8 space-y-6",
    )
