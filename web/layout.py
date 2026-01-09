"""
Shared layout helpers for the Tolkien KG web UI.
"""


def render_header(active: str = "home") -> str:
    """Return the top navigation bar with an active tab."""
    links = [
        ("home", "Home", "/"),
        ("browse", "Browse", "/browse"),
        ("api", "API", "/docs"),
    ]
    items = []
    for key, label, href in links:
        cls = "active" if key == active else ""
        items.append(f'<a href="{href}" class="{cls}">{label}</a>')
    nav_links = "".join(items)
    return f"""
    <div class="header">
        <div class="header-content">
            <a href="/" class="logo">Tolkien KG</a>
            <div class="nav-links">{nav_links}</div>
        </div>
    </div>
    """


def render_footer() -> str:
    """Return the shared footer links."""
    return (
        '<div class="footer">'
        "<p>Tolkien Knowledge Graph | "
        '<a href="/docs">API Docs</a> | '
        '<a href="https://github.com">GitHub</a></p>'
        "</div>"
    )
