"""RetailFlow Executive Dashboard — Dash edition.

The live counterpart to the static report in docs/index.html. Same Gold data,
same stylesheet, same chart geometry; the aggregation runs here in pandas
instead of in the browser.

Local:  python -m app.main
Serve:  gunicorn app.main:server
"""

import io
import os

from dash import Dash, Input, Output, State, callback_context, dcc, html, no_update

from app import figures as fig
from app.components import (CHART_KEYS, FILTER_FIELDS, chart_grid, controls,
                            footer, kpi_grid, masthead)
from app.data import Dataset
from app.theme import METRIC_COLOURS, PALETTES

DATA = Dataset()
FILTER_KEYS = [key for key, _, _ in FILTER_FIELDS]
METRICS = ("Revenue", "Profit", "Quantity")

# Counts of rows whose attribute never resolved — the same footer the static
# report prints, recomputed here so the two always agree.
QUALITY = [
    ("without a brand", int(DATA.frame["Brand"].isna().sum())),
    ("without a payment method", int(DATA.frame["PaymentMethod"].isna().sum())),
    ("without a gender", int(DATA.frame["Gender"].isna().sum())),
    ("without an order date", int(DATA.frame["Year"].isna().sum())),
]

app = Dash(
    __name__,
    title="RetailFlow Executive Business Intelligence Dashboard",
    assets_folder=os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "..", "dashboards", "assets"),
    # app.js is the *static* report's runtime; it expects an embedded payload
    # and would throw here. The stylesheet is what we actually want to share.
    assets_ignore=r"^app\.js$",
    update_title=None,
)
server = app.server  # gunicorn entry point

app.layout = html.Div(className="shell", children=[
    dcc.Store(id="metric-store", data="Revenue"),
    dcc.Store(id="theme-store", data="light"),
    html.Div(id="theme-sink", style={"display": "none"}),
    masthead(f"live · {DATA.rows:,} order lines"),
    kpi_grid(),
    controls(DATA.options),
    chart_grid(),
    footer(QUALITY, DATA.rows),
])


# --------------------------------------------------------------------------- #
# Metric switch and theme toggle
# --------------------------------------------------------------------------- #

@app.callback(
    Output("metric-store", "data"),
    [Input(f"metric-{name.lower()}", "n_clicks") for name in METRICS],
    prevent_initial_call=True,
)
def choose_metric(*_clicks):
    triggered = callback_context.triggered_id
    return {f"metric-{n.lower()}": n for n in METRICS}.get(triggered, "Revenue")


@app.callback(
    [Output(f"metric-{name.lower()}", "className") for name in METRICS]
    + [Output("metric-switch", "style")],
    Input("metric-store", "data"),
    Input("theme-store", "data"),
)
def paint_metric_switch(metric, theme):
    """Active state rides on a class here: aria-pressed is a wildcard attribute
    on Dash html components and cannot be a callback Output."""
    accent = PALETTES[theme][METRIC_COLOURS[metric]]
    classes = ["is-active" if name == metric else "" for name in METRICS]
    return classes + [{"--seg-accent": accent}]


@app.callback(
    Output("theme-store", "data"),
    Output("btn-theme", "children"),
    Input("btn-theme", "n_clicks"),
    State("theme-store", "data"),
    prevent_initial_call=True,
)
def toggle_theme(_clicks, current):
    nxt = "dark" if current == "light" else "light"
    return nxt, ("☀ Light" if nxt == "dark" else "☾ Dark")


# Stamp the theme on <html> in the browser so the CSS swaps with no round trip.
# (The figures still re-render server-side, since their colours are baked in.)
app.clientside_callback(
    "function(theme){ document.documentElement.setAttribute('data-theme', theme); return ''; }",
    Output("theme-sink", "children"),
    Input("theme-store", "data"),
)


@app.callback(
    [Output(f"f-{key}", "value") for key in FILTER_KEYS],
    Input("btn-reset", "n_clicks"),
    prevent_initial_call=True,
)
def reset_filters(_clicks):
    return [None] * len(FILTER_KEYS)


# --------------------------------------------------------------------------- #
# The one callback that redraws the report
# --------------------------------------------------------------------------- #

KPI_OUTPUTS = ["revenue", "profit", "orders", "customers", "products", "aov", "margin", "cities"]


@app.callback(
    [Output(f"kpi-{name}-value", "children") for name in KPI_OUTPUTS]
    + [Output(f"kpi-{name}-sub", "children") for name in KPI_OUTPUTS]
    + [Output(f"plot-{key}", "figure") for key in CHART_KEYS]
    + [Output(f"title-{key}", "children") for key in CHART_KEYS]
    + [Output(f"sub-{key}", "children") for key in CHART_KEYS]
    + [Output("filter-summary", "children")],
    [Input(f"f-{key}", "value") for key in FILTER_KEYS]
    + [Input("metric-store", "data"), Input("theme-store", "data")],
)
def redraw(*values):
    filters = dict(zip(FILTER_KEYS, values[:len(FILTER_KEYS)]))
    metric, theme = values[-2], values[-1]

    agg = DATA.aggregate(filters, metric)
    is_money = metric != "Quantity"
    accent = PALETTES[theme][METRIC_COLOURS[metric]]
    orders_colour = PALETTES[theme]["--orders"]
    total = agg["metricTotal"]

    def label(value):
        return fig.metric_label(value, is_money)

    def hover(row):
        share = f"{row['value'] / total * 100:.1f}% of total" if total else ""
        return f"{fig.metric_full(row['value'], is_money)}<br>{fig.count(row['orders'])} orders · {share}"

    def bars(key, colour=accent):
        return fig.h_bar(agg[key], colour, label, theme, hover)

    trend = agg["trend"]
    status_rows = fig.status_colours(list(agg["status"]), theme)
    for row in status_rows:
        pct = row["value"] / agg["rows"] * 100 if agg["rows"] else 0
        row["hover"] = f"{fig.count(row['value'])} orders · {pct:.1f}% of selection"

    charts = {
        "trend": fig.line(trend["dates"], trend["values"], accent, "£" if is_money else "", theme),
        "brands": bars("brand"),
        "category": bars("category"),
        "city": bars("city"),
        "gender": bars("gender"),
        "payment": bars("payment"),
        "status": fig.h_bar(status_rows, orders_colour, fig.count, theme, lambda r: r["hover"]),
        "customers": bars("customer"),
        "orders": fig.column(trend["dates"], trend["orders"], orders_colour,
                             [f"{fig.count(c)} orders" for c in trend["orders"]], theme),
    }

    kpi_values = [
        fig.money(agg["revenue"]), fig.money(agg["profit"]), fig.compact(agg["orders"]),
        fig.compact(agg["customers"]), fig.compact(agg["products"]),
        fig.money_full(agg["aov"]), f"{agg['margin']:.1f}%", fig.compact(agg["cities"]),
    ]
    kpi_subs = [
        fig.money_full(agg["revenue"]),
        f"{agg['margin']:.1f}% margin",
        f"{fig.count(agg['orders'])} order lines",
        f"{fig.count(agg['customers'])} active buyers",
        f"{fig.count(agg['products'])} SKUs sold",
        "per order",
        f"{fig.money(agg['profit'])} on {fig.money(agg['revenue'])}",
        f"{fig.count(agg['cities'])} UK locations",
    ]
    kpi_subs = [[html.Span(className="dot"), text] for text in kpi_subs]

    lower = metric.lower()
    titles = {
        "trend": f"{metric} Trend",
        "brands": "Top Products by Brand",
        "category": f"{metric} by Category",
        "city": f"{metric} by City",
        "gender": f"{metric} by Gender",
        "payment": "Payment Methods",
        "status": "Order Status",
        "customers": "Top Customers",
        "orders": "Monthly Orders",
    }

    def ranked(noun, rows):
        return f"Top {len(rows)} {noun} by {lower}" if rows else f"{noun.capitalize()} by {lower}"

    subs = {
        "trend": "By order month · first and last months may be partial",
        "brands": ranked("brands", agg["brand"]),
        "category": "Product category mix",
        "city": ranked("cities", agg["city"]),
        "gender": "Customer demographic split",
        "payment": f"{metric} by payment method",
        "status": "Order count by fulfilment state",
        "customers": ranked("customers", agg["customer"]),
        "orders": "Order volume by month",
    }

    active = [f"{lbl}: {filters[key]}" for key, lbl, _ in FILTER_FIELDS if filters.get(key)]
    scope = "  ·  ".join(active) if active else "No filters applied — full dataset"
    pct = agg["rows"] / DATA.rows * 100 if DATA.rows else 0
    summary = f"{scope}  →  {agg['rows']:,} of {DATA.rows:,} order lines ({pct:.1f}%)"

    return (kpi_values + kpi_subs
            + [charts[key] for key in CHART_KEYS]
            + [titles[key] for key in CHART_KEYS]
            + [subs[key] for key in CHART_KEYS]
            + [summary])


# --------------------------------------------------------------------------- #
# CSV export of the current selection
# --------------------------------------------------------------------------- #

@app.callback(
    Output("download-csv", "data"),
    Input("btn-export", "n_clicks"),
    [State(f"f-{key}", "value") for key in FILTER_KEYS],
    prevent_initial_call=True,
)
def export_csv(_clicks, *values):
    filters = dict(zip(FILTER_KEYS, values))
    selection = DATA.frame[DATA.mask(filters)]
    if selection.empty:
        return no_update
    buffer = io.StringIO()
    selection.to_csv(buffer, index=False)
    return dcc.send_string(buffer.getvalue(), "retailflow-selection.csv")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
