"""Page furniture for the Dash app.

Deliberately reuses the class names from dashboards/assets/app.css so the
stylesheet drives both front-ends — no second design system.
"""

from dash import dcc, html

from app.figures import GRAPH_CONFIG

KPI_CARDS = [
    ("kpi-revenue", "Total Revenue", "--revenue"),
    ("kpi-profit", "Gross Profit", "--profit"),
    ("kpi-orders", "Orders", "--orders"),
    ("kpi-customers", "Customers", "--profit"),
    ("kpi-products", "Products Sold", "--quantity"),
    ("kpi-aov", "Avg Order Value", "--revenue"),
    ("kpi-margin", "Avg Profit Margin", "--profit"),
    ("kpi-cities", "Cities Served", "--orders"),
]

# (key, default title, default subtitle)
CHART_CARDS = [
    ("trend", "Revenue Trend", "By order month · first and last months may be partial"),
    ("brands", "Top Products by Brand", "Top brands by revenue"),
    ("category", "Revenue by Category", "Product category mix"),
    ("city", "Revenue by City", "Top cities by revenue"),
    ("gender", "Revenue by Gender", "Customer demographic split"),
    ("payment", "Payment Methods", "Revenue by payment method"),
    ("status", "Order Status", "Order count by fulfilment state"),
    ("customers", "Top Customers", "Top customers by revenue"),
    ("orders", "Monthly Orders", "Order volume by month"),
]

CHART_KEYS = [key for key, _, _ in CHART_CARDS]

FILTER_FIELDS = [
    ("year", "Year", "All years"),
    ("month", "Month", "All months"),
    ("category", "Category", "All categories"),
    ("brand", "Brand", "All brands"),
    ("payment", "Payment", "All methods"),
    ("gender", "Gender", "All genders"),
    ("status", "Status", "All statuses"),
    ("city", "City", "All cities"),
]


def masthead(generated):
    return html.Header(className="masthead", children=[
        html.Div([
            html.H1("RetailFlow Executive Business Intelligence Dashboard"),
            html.P(className="lede", children=[
                "Enterprise Data Engineering Pipeline  ·  Bronze ",
                html.Span("→", className="chev"), " Silver ",
                html.Span("→", className="chev"), " Gold  |  AWS S3  |  Spark  |  Airflow",
            ]),
        ]),
        html.Div(className="masthead-right", children=[
            html.Div(className="refresh", children=["Last refresh", html.Strong(generated)]),
            html.Button("⭳ CSV", id="btn-export", className="icon-btn", n_clicks=0,
                        title="Download the current selection as CSV"),
            html.Button("☾ Dark", id="btn-theme", className="icon-btn", n_clicks=0,
                        title="Switch colour theme"),
            dcc.Download(id="download-csv"),
        ]),
    ])


def kpi_grid():
    cards = []
    for card_id, label, accent in KPI_CARDS:
        cards.append(html.Article(
            className="kpi", style={"--accent": f"var({accent})"}, children=[
                html.Div(label, className="kpi-label"),
                html.Div("—", className="kpi-value", id=f"{card_id}-value"),
                html.Div(className="kpi-sub", id=f"{card_id}-sub"),
            ],
        ))
    return html.Section(cards, className="kpi-grid", id="kpi-grid",
                        **{"aria-label": "Key performance indicators"})


def controls(options):
    fields = []
    for key, label, placeholder in FILTER_FIELDS:
        fields.append(html.Div(className="field", children=[
            html.Label(label, htmlFor=f"f-{key}"),
            dcc.Dropdown(
                id=f"f-{key}",
                options=[{"label": v, "value": v} for v in options[key]],
                value=None,
                placeholder=placeholder,
                clearable=True,
                searchable=True,
                className="rf-dropdown",
            ),
        ]))

    return html.Section(className="controls", **{"aria-label": "Filters"}, children=[
        html.Div(className="field", children=[
            html.Label("Metric"),
            html.Div(className="segmented", id="metric-switch", role="group", children=[
                html.Button(name, id=f"metric-{name.lower()}", n_clicks=0,
                            **{"aria-pressed": "true" if name == "Revenue" else "false"})
                for name in ("Revenue", "Profit", "Quantity")
            ]),
        ]),
        html.Div(className="control-actions", children=[
            html.Button("Reset filters", id="btn-reset", className="icon-btn", n_clicks=0),
        ]),
        html.Div(fields, className="filters"),
        html.P("Loading…", className="filter-summary", id="filter-summary"),
    ])


def chart_grid():
    cards = []
    for key, title, subtitle in CHART_CARDS:
        cards.append(html.Section(className="card", children=[
            html.Div(className="card-head", children=[
                html.H2(title, className="card-title", id=f"title-{key}"),
                html.P(subtitle, className="card-sub", id=f"sub-{key}"),
            ]),
            dcc.Graph(
                id=f"plot-{key}",
                className="plot",
                config=GRAPH_CONFIG,
                style={"height": "300px"},
            ),
        ]))
    return html.Main(cards, className="chart-grid")


def footer(quality, row_count):
    items = [html.Div(className="quality", children=[
        html.B(f"{row_count:,}"), " order lines in scope",
    ])]
    for label, value in quality:
        items.append(html.Div(className="quality", children=[html.B(f"{value:,}"), f" {label}"]))
    return html.Footer(className="footer", children=[
        html.H2("Data quality"), *items, html.Div(className="spacer"),
        html.Div("Source: Gold star schema (fact_sales × dim_product × dim_customer × dim_date)"),
    ])
