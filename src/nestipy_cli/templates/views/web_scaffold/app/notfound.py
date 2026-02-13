from nestipy.web import component, h


@component
def NotFound():
    return h.section(
        h.div(
            h.h1("Page not found", class_name="page-title"),
            h.p(
                "This route does not exist yet. We'll add nested notfound handling soon.",
                class_name="page-subtitle",
            ),
            class_name="page-header",
        ),
        h.div(
            h.p("Go back and explore the scaffolded routes.", class_name="card-subtitle"),
            class_name="card",
        ),
        class_name="page",
    )
