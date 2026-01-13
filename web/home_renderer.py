"""
Home page and navigation interface rendering.
"""

from html import escape
from urllib.parse import quote

from .layout import render_header, render_footer
from .styles import get_home_css


def generate_home_page(stats: dict) -> str:
    """Generate the home page HTML."""
    characters = stats.get("characters", 0)
    locations = stats.get("locations", 0)
    works = stats.get("works", 0)
    total = stats.get("total", 0)

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

            <h2 class="section-title">Main categories</h2>
            <div class="categories-grid">
                <a href="/browse?type=Character" class="category-card">
                    <div class="category-icon"></div>
                    <div class="category-name">Characters</div>
                    <div class="category-count">{characters} entries</div>
                    <div class="category-desc">Heroes, sages, villains, and creatures</div>
                </a>

                <a href="/browse?type=Location" class="category-card">
                    <div class="category-icon"></div>
                    <div class="category-name">Locations</div>
                    <div class="category-count">{locations} entries</div>
                    <div class="category-desc">Kingdoms, cities, and legendary lands</div>
                </a>

                <a href="/browse?type=Work" class="category-card">
                    <div class="category-icon"></div>
                    <div class="category-name">Works</div>
                    <div class="category-count">{works} entries</div>
                    <div class="category-desc">Books, movies, games, and adaptations</div>
                </a>
            </div>
        </div>

        {render_footer()}
    </body>
    </html>
    """
    return html


def generate_browse_page(
    entities: list,
    entity_type: str = None,
    page: int = 1,
    total_pages: int = 1,
    search_query: str = None,
) -> str:
    """Generate the entity browsing page."""

    type_labels = {
        "Character": "Characters",
        "Location": "Locations",
        "Work": "Works",
        None: "All entities",
    }

    type_descriptions = {
        "Character": "Explore the characters of Tolkien's legendarium",
        "Location": "Discover the places and realms of Middle-earth",
        "Work": "Browse the books, movies, and adaptations",
        None: "Browse every entity in the knowledge graph",
    }

    current_type = type_labels.get(entity_type, type_labels[None])
    current_desc = type_descriptions.get(entity_type, type_descriptions[None])

    cards_html = ""
    if entities:
        for entity in entities:
            raw_name = entity.get("name") or ""
            entity_uri = entity.get("uri", "")
            entity_class = entity.get("type", "Unknown").split("/")[-1]

            display_name = raw_name.strip() or (
                entity_uri.rsplit("/", 1)[-1] if entity_uri else "Resource"
            )
            display_name = display_name.strip('"').strip("'")
            if not display_name:
                continue

            slug = quote(display_name.replace(" ", "_"))
            type_icon = (
                "[C]"
                if "Character" in entity_class
                else "[L]"
                if "Location" in entity_class
                else "[W]"
            )

            cards_html += f"""
            <a href="/page/{slug}" class="character-card">
                <div class="character-card-content">
                    <div class="character-name">{escape(display_name)}</div>
                    <div class="character-type">{type_icon} {escape(entity_class)}</div>
                </div>
            </a>
            """
    else:
        cards_html = """
        <div class="empty-state" style="grid-column: 1/-1;">
            <h2>No entities found</h2>
            <p>Try another search or pick a different category.</p>
        </div>
        """

    pagination_html = ""
    if total_pages > 1:
        pagination_html = '<div class="pagination">'

        if page > 1:
            prev_page = page - 1
            query_param = f"&search={search_query}" if search_query else ""
            type_param = f"&type={entity_type}" if entity_type else ""
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
                type_param = f"&type={entity_type}" if entity_type else ""
                query_param = f"&search={search_query}" if search_query else ""
                pagination_html += (
                    f'<a href="/browse?page={p}{type_param}{query_param}">{p}</a>'
                )

        if end_page < total_pages:
            if end_page < total_pages - 1:
                pagination_html += "<span>...</span>"
            type_param = f"&type={entity_type}" if entity_type else ""
            query_param = f"&search={search_query}" if search_query else ""
            pagination_html += (
                f'<a href="/browse?page={total_pages}{type_param}{query_param}">'
                f"{total_pages}</a>"
            )

        if page < total_pages:
            next_page = page + 1
            query_param = f"&search={search_query}" if search_query else ""
            type_param = f"&type={entity_type}" if entity_type else ""
            pagination_html += (
                f'<a href="/browse?page={next_page}{type_param}{query_param}">Next</a>'
            )
        else:
            pagination_html += '<span class="disabled">Next</span>'

        pagination_html += "</div>"

    filter_html = f"""
    <div class="filters">
        <a href="/browse" class="filter-btn {'active' if not entity_type else ''}">All</a>
        <a href="/browse?type=Character" class="filter-btn {'active' if entity_type == 'Character' else ''}">Characters</a>
        <a href="/browse?type=Location" class="filter-btn {'active' if entity_type == 'Location' else ''}"> Locations</a>
        <a href="/browse?type=Work" class="filter-btn {'active' if entity_type == 'Work' else ''}">Works</a>
    </div>
    """

    search_value = search_query if search_query else ""
    search_form = f"""
    <form class="search-box" action="/browse" method="get" style="margin-bottom: 20px;">
        <input type="text" name="search" placeholder="Search an entity..." value="{search_value}">
        <button type="submit">Search</button>
    </form>
    """

    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{current_type} - Tolkien Knowledge Graph</title>
        <style>{get_home_css()}</style>
    </head>
    <body>
        {render_header("browse")}

        <div class="container">
            <div class="characters-header">
                <h1>{current_type}</h1>
                <p>{current_desc}</p>
                {search_form}
                {filter_html}
            </div>

            <div class="characters-grid">
                {cards_html}
            </div>

            {pagination_html}
        </div>

        {render_footer()}
    </body>
    </html>
    """
    return html
