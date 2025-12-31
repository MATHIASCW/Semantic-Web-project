"""
Home page and navigation interface rendering.
"""

from .layout import render_header, render_footer
from .styles import get_home_css


def generate_home_page(stats: dict) -> str:
    """Generate the home page HTML."""
    characters = stats.get('characters', 0)
    locations = stats.get('locations', 0)
    works = stats.get('works', 0)
    total = stats.get('total', 0)
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Tolkien Knowledge Graph - Accueil</title>
        <style>{get_home_css()}</style>
    </head>
    <body>
        {render_header('home')}
        
        <div class="container">
            <div class="hero">
                <h1>Bienvenue dans la Base de Connaissance Tolkien</h1>
                <p>Explorez l'univers riche et détaillé du Seigneur des Anneaux et du Hobbit</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="number">{total}</div>
                    <div class="label">Entités Totales</div>
                </div>
                <div class="stat-card">
                    <div class="number">{characters}</div>
                    <div class="label">Personnages</div>
                </div>
                <div class="stat-card">
                    <div class="number">{locations}</div>
                    <div class="label">Lieux</div>
                </div>
                <div class="stat-card">
                    <div class="number">{works}</div>
                    <div class="label">Œuvres</div>
                </div>
            </div>
            
            <h2 class="section-title">Catégories Principales</h2>
            <div class="categories-grid">
                <a href="/browse?type=Character" class="category-card">
                    <div class="category-icon">👤</div>
                    <div class="category-name">Personnages</div>
                    <div class="category-count">{characters} entrées</div>
                    <div class="category-desc">Explorateurs, guerriers, sages et créatures</div>
                </a>
                
                <a href="/browse?type=Location" class="category-card">
                    <div class="category-icon">🗺️</div>
                    <div class="category-name">Lieux</div>
                    <div class="category-count">{locations} entrées</div>
                    <div class="category-desc">Royaumes, cités et terres légendaires</div>
                </a>
                
                <a href="/browse?type=Work" class="category-card">
                    <div class="category-icon">📖</div>
                    <div class="category-name">Œuvres</div>
                    <div class="category-count">{works} entrées</div>
                    <div class="category-desc">Livres, films, jeux et adaptations</div>
                </a>
            </div>
        </div>
        
        {render_footer()}
    </body>
    </html>
    """
    return html


def generate_browse_page(entities: list, entity_type: str = None, page: int = 1, 
                        total_pages: int = 1, search_query: str = None) -> str:
    """Generate the entity browsing page."""
    
    type_labels = {
        'Character': '👤 Personnages',
        'Location': '🗺️ Lieux',
        'Work': '📖 Œuvres',
        None: '🔍 Toutes les entités'
    }
    
    type_descriptions = {
        'Character': 'Explorez les personnages de l\'univers Tolkien',
        'Location': 'Découvrez les lieux et royaumes du Monde Intermédiaire',
        'Work': 'Parcourez les livres, films et adaptations',
        None: 'Parcourez toutes les entités de la base de connaissance'
    }
    
    current_type = type_labels.get(entity_type, type_labels[None])
    current_desc = type_descriptions.get(entity_type, type_descriptions[None])
    
    cards_html = ""
    if entities:
        for entity in entities:
            name = entity.get('name', 'Inconnu')
            entity_uri = entity.get('uri', '#')
            entity_class = entity.get('type', 'Unknown').split('/')[-1]
            
            type_icon = '👤' if 'Character' in entity_class else '🗺️' if 'Location' in entity_class else '📖'
            
            cards_html += f"""
            <a href="/resource/{name.replace(' ', '_')}" class="character-card">
                <div class="character-card-content">
                    <div class="character-name">{name}</div>
                    <div class="character-type">{type_icon} {entity_class}</div>
                </div>
            </a>
            """
    else:
        cards_html = """
        <div class="empty-state" style="grid-column: 1/-1;">
            <h2>Aucune entité trouvée</h2>
            <p>Essayez une autre recherche ou consultez une autre catégorie.</p>
        </div>
        """
    
    pagination_html = ""
    if total_pages > 1:
        pagination_html = '<div class="pagination">'
        
        if page > 1:
            prev_page = page - 1
            query_param = f"&search={search_query}" if search_query else ""
            type_param = f"&type={entity_type}" if entity_type else ""
            pagination_html += f'<a href="/browse?page={prev_page}{type_param}{query_param}">← Précédent</a>'
        else:
            pagination_html += '<span class="disabled">← Précédent</span>'
        
        start_page = max(1, page - 2)
        end_page = min(total_pages, page + 2)
        
        if start_page > 1:
            pagination_html += f'<a href="/browse?page=1">1</a>'
            if start_page > 2:
                pagination_html += '<span>...</span>'
        
        for p in range(start_page, end_page + 1):
            if p == page:
                pagination_html += f'<span class="active">{p}</span>'
            else:
                type_param = f"&type={entity_type}" if entity_type else ""
                query_param = f"&search={search_query}" if search_query else ""
                pagination_html += f'<a href="/browse?page={p}{type_param}{query_param}">{p}</a>'
        
        if end_page < total_pages:
            if end_page < total_pages - 1:
                pagination_html += '<span>...</span>'
            type_param = f"&type={entity_type}" if entity_type else ""
            query_param = f"&search={search_query}" if search_query else ""
            pagination_html += f'<a href="/browse?page={total_pages}{type_param}{query_param}">{total_pages}</a>'
        
        if page < total_pages:
            next_page = page + 1
            query_param = f"&search={search_query}" if search_query else ""
            type_param = f"&type={entity_type}" if entity_type else ""
            pagination_html += f'<a href="/browse?page={next_page}{type_param}{query_param}">Suivant →</a>'
        else:
            pagination_html += '<span class="disabled">Suivant →</span>'
        
        pagination_html += '</div>'
    
    filter_html = f"""
    <div class="filters">
        <a href="/browse" class="filter-btn {'active' if not entity_type else ''}">Tous</a>
        <a href="/browse?type=Character" class="filter-btn {'active' if entity_type == 'Character' else ''}">👤 Personnages</a>
        <a href="/browse?type=Location" class="filter-btn {'active' if entity_type == 'Location' else ''}">🗺️ Lieux</a>
        <a href="/browse?type=Work" class="filter-btn {'active' if entity_type == 'Work' else ''}">📖 Œuvres</a>
    </div>
    """
    
    search_value = search_query if search_query else ""
    search_form = f"""
    <form class="search-box" action="/browse" method="get" style="margin-bottom: 20px;">
        <input type="text" name="search" placeholder="Chercher une entité..." value="{search_value}">
        <button type="submit">Rechercher</button>
    </form>
    """
    
    html = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{current_type} - Tolkien Knowledge Graph</title>
        <style>{get_home_css()}</style>
    </head>
    <body>
        {render_header('browse')}
        
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
