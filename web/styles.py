"""
Shared CSS snippets for the Tolkien KG web UI.
"""

HOME_PAGE_CSS = """
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: #333;
            min-height: 100vh;
        }

        /* Header Navigation */
        .header {
            background: rgba(0, 0, 0, 0.3);
            padding: 15px 0;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
            margin-bottom: 40px;
        }

        .header-content {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .logo {
            font-size: 24px;
            font-weight: bold;
            color: white;
            text-decoration: none;
        }

        .nav-links {
            display: flex;
            gap: 20px;
        }

        .nav-links a {
            color: white;
            text-decoration: none;
            padding: 8px 16px;
            border-radius: 4px;
            transition: background 0.3s;
        }

        .nav-links a:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .nav-links a.active {
            background: rgba(255, 255, 255, 0.3);
        }

        /* Container */
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 0 20px 40px;
        }

        /* Home Page */
        .hero {
            text-align: center;
            color: white;
            margin-bottom: 60px;
        }

        .hero h1 {
            font-size: 48px;
            margin-bottom: 20px;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .hero p {
            font-size: 18px;
            opacity: 0.95;
            text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.3);
        }

        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 60px;
        }

        .stat-card {
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            text-align: center;
        }

        .stat-card .number {
            font-size: 48px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }

        .stat-card .label {
            font-size: 14px;
            color: #666;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        /* Categories Section */
        .categories-section {
            margin-bottom: 60px;
        }

        .section-title {
            color: white;
            font-size: 32px;
            margin-bottom: 30px;
            text-align: center;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }

        .categories-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
            gap: 20px;
        }

        .category-card {
            background: white;
            padding: 25px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            color: inherit;
            border-top: 4px solid #667eea;
        }

        .category-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        }

        .category-icon {
            font-size: 36px;
            margin-bottom: 15px;
        }

        .category-name {
            font-size: 20px;
            font-weight: 600;
            margin-bottom: 10px;
            color: #333;
        }

        .category-count {
            font-size: 14px;
            color: #667eea;
            font-weight: 600;
        }

        .category-desc {
            font-size: 13px;
            color: #666;
            margin-top: 10px;
        }

        /* Characters Browse Page */
        .characters-header {
            background: white;
            padding: 30px;
            border-radius: 8px;
            margin-bottom: 30px;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
        }

        .search-box {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }

        .search-box input {
            flex: 1;
            padding: 12px 15px;
            border: 2px solid #e5e5e5;
            border-radius: 4px;
            font-size: 14px;
            transition: border-color 0.3s;
        }

        .search-box input:focus {
            outline: none;
            border-color: #667eea;
        }

        .search-box button {
            padding: 12px 30px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-weight: 600;
            transition: background 0.3s;
        }

        .search-box button:hover {
            background: #764ba2;
        }

        .filters {
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }

        .filter-btn {
            padding: 8px 16px;
            background: #f0f0f0;
            border: 2px solid #e5e5e5;
            border-radius: 20px;
            cursor: pointer;
            transition: all 0.3s;
            font-size: 13px;
        }

        .filter-btn:hover {
            border-color: #667eea;
            color: #667eea;
        }

        .filter-btn.active {
            background: #667eea;
            color: white;
            border-color: #667eea;
        }

        /* Characters Grid */
        .characters-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }

        .character-card {
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
            transition: transform 0.3s, box-shadow 0.3s;
            text-decoration: none;
            color: inherit;
        }

        .character-card:hover {
            transform: translateY(-3px);
            box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
        }

        .character-card-content {
            padding: 20px;
        }

        .character-name {
            font-size: 18px;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }

        .character-info {
            font-size: 13px;
            color: #666;
            margin-bottom: 5px;
        }

        .character-type {
            display: inline-block;
            font-size: 11px;
            background: #667eea;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            margin-top: 10px;
        }

        /* Pagination */
        .pagination {
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 40px;
        }

        .pagination a, .pagination span {
            padding: 10px 15px;
            border: 2px solid white;
            border-radius: 4px;
            color: white;
            text-decoration: none;
            transition: all 0.3s;
        }

        .pagination a:hover {
            background: rgba(255, 255, 255, 0.2);
        }

        .pagination .active {
            background: white;
            color: #667eea;
            border-color: white;
        }

        .pagination .disabled {
            opacity: 0.5;
            cursor: not-allowed;
            border-color: rgba(255, 255, 255, 0.3);
        }

        /* Footer */
        .footer {
            text-align: center;
            color: white;
            padding: 30px 0;
            margin-top: 40px;
            opacity: 0.9;
        }

        .footer a {
            color: white;
            text-decoration: none;
            margin: 0 10px;
        }

        .footer a:hover {
            text-decoration: underline;
        }

        .empty-state {
            text-align: center;
            padding: 60px 20px;
            background: white;
            border-radius: 8px;
            color: #666;
        }

        .empty-state h2 {
            font-size: 24px;
            margin-bottom: 10px;
            color: #333;
        }
    """

RESOURCE_PAGE_CSS = """
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
                background: #f5f5f5;
                color: #333;
            }
            .container {
                max-width: 1200px;
                margin: 30px auto;
                padding: 0 20px;
                background: white;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
            }

            /* Header section */
            .page-header {
                border-bottom: 1px solid #e5e5e5;
                padding: 30px 0;
                margin-bottom: 30px;
            }
            .page-title {
                font-size: 28px;
                font-weight: bold;
                color: #1a472a;
                margin-bottom: 5px;
            }
            .page-subtitle {
                font-size: 14px;
                color: #666;
                line-height: 1.6;
            }
            .page-subtitle a {
                color: #0066cc;
                text-decoration: none;
            }
            .page-subtitle a:hover {
                text-decoration: underline;
            }

            /* Image section */
            .infobox {
                float: right;
                width: 300px;
                margin-left: 20px;
                margin-bottom: 20px;
                text-align: center;
            }
            .infobox img {
                max-width: 100%;
                height: auto;
                border: 1px solid #ddd;
                border-radius: 4px;
            }

            /* Properties table */
            .properties-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
                clear: both;
            }
            .cards-section {
                margin: 20px 0;
                padding: 12px 15px;
                background: #fbfbfb;
                border: 1px solid #e5e5e5;
                border-radius: 6px;
            }
            .cards-section h2 {
                font-size: 16px;
                color: #1a472a;
                margin-bottom: 10px;
            }
            .cards-list {
                display: flex;
                flex-wrap: wrap;
                gap: 12px;
            }
            .card-item {
                background: #f0f0f0;
                padding: 8px;
                border-radius: 6px;
                font-size: 12px;
                display: flex;
                align-items: center;
                gap: 8px;
            }
            .card-item img {
                width: 60px;
                height: auto;
                border-radius: 4px;
                border: 1px solid #ddd;
                background: white;
            }
            .card-name a {
                color: #0066cc;
                text-decoration: none;
            }
            .card-name a:hover {
                text-decoration: underline;
            }
            .properties-table tr {
                border-bottom: 1px solid #e5e5e5;
            }
            .properties-table tr:hover {
                background: #f9f9f9;
            }
            .incoming-row {
                background: #fff7e8;
            }
            .literal-value {
                display: inline-flex;
                align-items: center;
                gap: 6px;
            }
            .lang-tag {
                background: #e8eef5;
                color: #445;
                border-radius: 4px;
                padding: 1px 6px;
                font-size: 10px;
                text-transform: uppercase;
                letter-spacing: 0.05em;
            }
            .incoming-separator td {
                background: #f6ead1;
                color: #8a5b1f;
                font-weight: 600;
                text-transform: uppercase;
                letter-spacing: 0.08em;
                font-size: 11px;
                border-top: 2px solid #e7d3b2;
            }
            .properties-table th {
                background: #f5f5f5;
                text-align: left;
                font-weight: 600;
                padding: 12px 15px;
                border-bottom: 2px solid #ddd;
            }
            .properties-table td {
                padding: 12px 15px;
                vertical-align: top;
            }
            .property-name {
                font-weight: 600;
                color: #0066cc;
                width: 30%;
                word-break: break-word;
            }
            .property-name a {
                color: #0066cc;
                text-decoration: none;
            }
            .property-name a:hover {
                text-decoration: underline;
            }
            .property-value {
                width: 70%;
            }
            .property-value a {
                color: #0066cc;
                text-decoration: none;
            }
            .property-value a:hover {
                text-decoration: underline;
            }
            .value-list {
                list-style: none;
            }
            .value-list li {
                margin: 3px 0;
            }
            .value-list li:before {
                content: "- ";
                margin-right: 5px;
            }

            /* Timeline section */
            .timeline-section {
                margin-top: 40px;
                padding-top: 30px;
                border-top: 1px solid #e5e5e5;
                clear: both;
            }
            .timeline-section h2 {
                color: #1a472a;
                font-size: 18px;
                margin-bottom: 15px;
                border-bottom: 2px solid #1a472a;
                padding-bottom: 10px;
            }
            .timeline-table {
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }
            .timeline-table th {
                background: #f5f5f5;
                text-align: left;
                font-weight: 600;
                padding: 10px 12px;
                border-bottom: 2px solid #ddd;
            }
            .timeline-table td {
                padding: 8px 12px;
                border-bottom: 1px solid #e5e5e5;
            }
            .timeline-table tr:hover {
                background: #f9f9f9;
            }

            /* Linked data section */
            .linked-data {
                margin-top: 30px;
                padding: 15px;
                background: #f0f8ff;
                border: 1px solid #b3d9ff;
                border-radius: 4px;
                clear: both;
            }
            .linked-data h3 {
                color: #1a472a;
                margin-bottom: 10px;
                font-size: 16px;
            }
            .format-links a {
                display: inline-block;
                margin-right: 15px;
                padding: 6px 12px;
                background: #0066cc;
                color: white;
                text-decoration: none;
                border-radius: 3px;
                font-size: 14px;
            }
            .format-links a:hover {
                background: #0052a3;
            }

            /* Footer */
            .page-footer {
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #e5e5e5;
                text-align: center;
                font-size: 13px;
                color: #666;
            }
            .page-footer a {
                color: #0066cc;
                text-decoration: none;
                margin: 0 10px;
            }
            .page-footer a:hover {
                text-decoration: underline;
            }
    """


def get_home_css() -> str:
    """Expose home/browse CSS."""
    return HOME_PAGE_CSS


def get_resource_css() -> str:
    """Expose resource/detail CSS."""
    return RESOURCE_PAGE_CSS
