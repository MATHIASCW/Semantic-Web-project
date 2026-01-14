"""
Home page and navigation interface rendering.
"""

from html import escape
from urllib.parse import quote

from .layout import render_header, render_footer
from .styles import get_home_css


def generate_home_page(stats: dict, type_facets: list | None = None) -> str:
    """Generate the home page HTML with dynamic type tiles."""
    facets = type_facets or []
    total = sum(f.get("count", 0) for f in facets) if facets else stats.get("total", 0)
    
    characters = 0
    locations = 0
    works = 0
    for facet in facets:
        ftype = facet.get("type", "")
        fcount = facet.get("count", 0)
        if "Character" in ftype:
            characters = fcount
        elif "Location" in ftype:
            locations = fcount
        elif "CreativeWork" in ftype:
            works = fcount

    tiles_html = ""
    if facets:
        for facet in facets:
            facet_type = facet.get("type", "")
            count = facet.get("count", 0)
            label = _prettify_type_label(facet_type)
            tiles_html += f"""
                <a href="/browse?type={quote(facet_type)}" class="category-card">
                    <div class="category-icon">{_type_icon(facet_type)}</div>
                    <div class="category-name">{escape(label)}</div>
                    <div class="category-count">{count} entries</div>
                    <div class="category-desc">Browse all {escape(label.lower())}</div>
                </a>
            """
    else:
        tiles_html = f"""
            <a href="/browse?type=Character" class="category-card">
                <div class="category-icon">{_type_icon('Character')}</div>
                <div class="category-name">Characters</div>
                <div class="category-count">{characters} entries</div>
                <div class="category-desc">Heroes, sages, villains, and creatures</div>
            </a>

            <a href="/browse?type=Location" class="category-card">
                <div class="category-icon">{_type_icon('Location')}</div>
                <div class="category-name">Locations</div>
                <div class="category-count">{locations} entries</div>
                <div class="category-desc">Kingdoms, cities, and legendary lands</div>
            </a>

            <a href="/browse?type=Work" class="category-card">
                <div class="category-icon">{_type_icon('Work')}</div>
                <div class="category-name">Works</div>
                <div class="category-count">{works} entries</div>
                <div class="category-desc">Books, movies, games, and adaptations</div>
            </a>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tolkien Knowledge Graph - Home</title>
        <style>{get_home_css()}</style>
    </head>
    <body>
        {render_header("home")}

        <div class="container">
            <div class="hero">
                <h1>Welcome to the Tolkien Knowledge Graph</h1>
                <p>Explore the rich universe of Middle-earth across characters, places, and works</p>
            </div>

            <div class="stats">
                <div class="stat-card">
                    <div class="number">{total}</div>
                    <div class="label">Total entities</div>
                </div>
                <div class="stat-card">
                    <div class="number">{characters}</div>
                    <div class="label">Characters</div>
                </div>
                <div class="stat-card">
                    <div class="number">{locations}</div>
                    <div class="label">Locations</div>
                </div>
                <div class="stat-card">
                    <div class="number">{works}</div>
                    <div class="label">Works</div>
                </div>
            </div>

            <h2 class="section-title">All entity types</h2>
            <div class="categories-grid">{tiles_html}</div>
        </div>

        {render_footer()}
    </body>
    </html>
    """
    return html


def _prettify_type_label(type_uri: str) -> str:
    """Human-friendly label from a type URI."""
    if not type_uri:
        return "Unknown"
    label = type_uri.rsplit("/", 1)[-1]
    return label.replace("_", " ")


def _type_icon(type_uri: str) -> str:
    """Return a compact icon marker based on type URI."""
    if not type_uri:
        return "[ ]"
    if "Character" in type_uri:
        return "[C]"
    if "Location" in type_uri:
        return "[L]"
    if "CreativeWork" in type_uri or "Work" in type_uri:
        return "[W]"
    if "Organization" in type_uri:
        return "[O]"
    if "Artifact" in type_uri or "Object" in type_uri:
        return "[A]"
    if "Event" in type_uri:
        return "[E]"
    return f"[{_prettify_type_label(type_uri)[:1]}]"


def generate_browse_page(
    entities: list,
    entity_type: str = None,
    page: int = 1,
    total_pages: int = 1,
    search_query: str = None,
    type_facets: list | None = None,
) -> str:
    """Generate the entity browsing page with dynamic type filters."""

    current_type_label = _prettify_type_label(entity_type) if entity_type else "All entities"
    current_desc = (
        f"Browsing all {current_type_label.lower()}" if entity_type else "Browse every entity in the knowledge graph"
    )

    grouped = {}
    if entities:
        for entity in entities:
            raw_name = entity.get("name") or ""
            entity_uri = entity.get("uri", "")
            entity_class_uri = entity.get("type", "")
            entity_class = _prettify_type_label(entity_class_uri)

            display_name = raw_name.strip() or (
                entity_uri.rsplit("/", 1)[-1] if entity_uri else "Resource"
            )
            display_name = display_name.strip('"').strip("'")
            if not display_name:
                continue

            slug = quote(display_name.replace(" ", "_"))
            type_icon = _type_icon(entity_class_uri)

            card_html = f"""
            <a href="/page/{slug}" class="character-card">
                <div class="character-card-content">
                    <div class="character-name">{escape(display_name)}</div>
                    <div class="character-type">{type_icon} {escape(entity_class)}</div>
                </div>
            </a>
            """
            grouped.setdefault(entity_class_uri or "Unknown", {"label": entity_class, "cards": []})["cards"].append(
                card_html
            )
    else:
        grouped["empty"] = {
            "label": "No entities",
            "cards": [
                """
                <div class="empty-state" style="grid-column: 1/-1;">
                    <h2>No entities found</h2>
                    <p>Try another search or pick a different category.</p>
                </div>
                """
            ],
        }

    pagination_html = ""
    if total_pages > 1:
        pagination_html = '<div class="pagination">'

        if page > 1:
            prev_page = page - 1
            query_param = f"&search={search_query}" if search_query else ""
            type_param = f"&type={quote(entity_type)}" if entity_type else ""
            pagination_html += (
                f'<a href="/browse?page={prev_page}{type_param}{query_param}">Previous</a>'
            )
        else:
            pagination_html += '<span class="disabled">Previous</span>'

        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)

        if start_page > 1:
            pagination_html += '<a href="/browse?page=1">1</a>'
            if start_page > 2:
                pagination_html += "<span>...</span>"

        for p in range(start_page, end_page + 1):
            if p == page:
                pagination_html += f'<span class="active">{p}</span>'
            else:
                type_param = f"&type={quote(entity_type)}" if entity_type else ""
                query_param = f"&search={search_query}" if search_query else ""
                pagination_html += (
                    f'<a href="/browse?page={p}{type_param}{query_param}">{p}</a>'
                )

        if end_page < total_pages:
            if end_page < total_pages - 1:
                pagination_html += "<span>...</span>"
            type_param = f"&type={quote(entity_type)}" if entity_type else ""
            query_param = f"&search={search_query}" if search_query else ""
            pagination_html += (
                f'<a href="/browse?page={total_pages}{type_param}{query_param}">'
                f"{total_pages}</a>"
            )

        if page < total_pages:
            next_page = page + 1
            query_param = f"&search={search_query}" if search_query else ""
            type_param = f"&type={quote(entity_type)}" if entity_type else ""
            pagination_html += (
                f'<a href="/browse?page={next_page}{type_param}{query_param}">Next</a>'
            )
        else:
            pagination_html += '<span class="disabled">Next</span>'

        pagination_html += "</div>"

    filter_items = [
        f'<a href="/browse" class="filter-btn {"active" if not entity_type else ""}">All</a>'
    ]
    facets = type_facets or []
    for facet in facets:
        facet_type = facet.get("type", "")
        facet_count = facet.get("count", 0)
        label = _prettify_type_label(facet_type)
        active_cls = "active" if entity_type == facet_type or entity_type == label else ""
        filter_items.append(
            f'<a href="/browse?type={quote(facet_type)}" class="filter-btn {active_cls}">{escape(label)} ({facet_count})</a>'
        )

    filter_html = f"<div class=\"filters\">{''.join(filter_items)}</div>"

    search_value = search_query if search_query else ""
    search_form = f"""
    <form class="search-box" action="/browse" method="get" style="margin-bottom: 20px;">
        <input type="text" name="search" placeholder="Search an entity..." value="{search_value}">
        <button type="submit">Search</button>
    </form>
    """

    sections_html = ""
    for type_uri, group in grouped.items():
        cards_joined = "".join(group["cards"])
        sections_html += f"""
        <div class="group-block">
            <div class="group-header">
                <h2>{escape(group['label'])}</h2>
                <span class="group-count">{len(group['cards'])} items</span>
            </div>
            <div class="characters-grid">{cards_joined}</div>
        </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{current_type_label} - Tolkien Knowledge Graph</title>
        <style>{get_home_css()}</style>
    </head>
    <body>
        {render_header("browse")}

        <div class="container">
            <div class="characters-header">
                <h1>{current_type_label}</h1>
                <p>{current_desc}</p>
                {search_form}
                {filter_html}
            </div>

            {sections_html}

            {pagination_html}
        </div>

        {render_footer()}
    </body>
    </html>
    """
    return html
