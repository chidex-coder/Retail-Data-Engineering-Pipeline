"""Builds the RetailFlow executive dashboard as a single self-contained HTML file.

The Gold fact rows are dictionary-encoded into base64 typed arrays and embedded
in the page; `dashboards/assets/app.js` re-aggregates them in the browser on
every filter change, which is what makes the report cross-filter like Power BI
without needing a server behind it.
"""

import base64
import json
import os
from string import Template

import numpy as np
import plotly.offline as pyo

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "dashboards", "assets")

MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]

# Integer widths the client runtime understands, smallest first.
_INT_TYPES = [("u8", np.uint8, 255), ("u16", np.uint16, 65535), ("u32", np.uint32, 4294967295)]


def _pick_type(max_value):
    """Smallest unsigned type that holds max_value *and* a sentinel above it."""
    for name, dtype, ceiling in _INT_TYPES:
        if max_value < ceiling:
            return name, dtype, ceiling
    raise ValueError(f"value {max_value} does not fit in a uint32 column")


def _b64(arr, dtype):
    little_endian = np.dtype(dtype).newbyteorder("<")
    packed = np.ascontiguousarray(np.asarray(arr).astype(little_endian))
    return base64.b64encode(packed.tobytes()).decode("ascii")


def dim_column(codes, cardinality):
    """Encode dimension codes (-1 meaning 'unknown') as {t, d}.

    The unknown marker is the maximum value of the chosen type, which is what
    the client runtime derives from `t`.
    """
    name, dtype, sentinel = _pick_type(cardinality)
    arr = np.asarray(codes)
    return {"t": name, "d": _b64(np.where(arr < 0, sentinel, arr), dtype)}


def value_column(values):
    """Encode a non-negative measure column (no unknown marker needed)."""
    arr = np.asarray(values)
    largest = int(arr.max()) if arr.size else 0
    name, dtype, _ = _pick_type(largest)
    return {"t": name, "d": _b64(arr, dtype)}


# --------------------------------------------------------------------------- #
# Page markup
# --------------------------------------------------------------------------- #

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

# (card id, default title, default subtitle, extra classes)
CHART_CARDS = [
    ("trend", "Revenue Trend", "By order month · first and last months may be partial", ""),
    ("brands", "Top Products by Brand", "Top brands by revenue", ""),
    ("category", "Revenue by Category", "Product category mix", ""),
    ("city", "Revenue by City", "Top 10 cities by revenue", ""),
    ("gender", "Revenue by Gender", "Customer demographic split", ""),
    ("payment", "Payment Methods", "Revenue by payment method", ""),
    ("status", "Order Status", "Order count by fulfilment state", ""),
    ("customers", "Top Customers", "Top 10 customers by revenue", ""),
    ("orders", "Monthly Orders", "Order volume by month", ""),
]

FILTER_FIELDS = [
    ("f-year", "Year"),
    ("f-month", "Month"),
    ("f-category", "Category"),
    ("f-brand", "Brand"),
    ("f-payment", "Payment"),
    ("f-gender", "Gender"),
    ("f-status", "Status"),
]

PAGE = Template("""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>RetailFlow Executive Business Intelligence Dashboard</title>
<meta name="description" content="Executive view of the RetailFlow Gold layer: revenue, profit and order performance across brands, categories, cities and customers.">
<style>$css</style>
</head>
<body>
<div class="shell">

  <header class="masthead">
    <div>
      <h1>RetailFlow Executive Business Intelligence Dashboard</h1>
      <p class="lede">Enterprise Data Engineering Pipeline &nbsp;·&nbsp; Bronze <span class="chev">→</span> Silver <span class="chev">→</span> Gold &nbsp;|&nbsp; AWS S3 &nbsp;|&nbsp; Spark &nbsp;|&nbsp; Airflow</p>
    </div>
    <div class="masthead-right">
      <div class="refresh">Last refresh<strong id="meta-generated">—</strong></div>
      <button class="icon-btn" id="btn-export" type="button" title="Download the current selection as CSV">⭳ CSV</button>
      <button class="icon-btn" id="btn-theme" type="button" title="Switch colour theme">☾ Dark</button>
    </div>
  </header>

  <section class="kpi-grid" aria-label="Key performance indicators">
$kpi_cards
  </section>

  <section class="controls" aria-label="Filters">
    <div class="field">
      <label for="metric-switch">Metric</label>
      <div class="segmented" id="metric-switch" role="group" aria-label="Metric">
        <button type="button" data-metric="Revenue" aria-pressed="true">Revenue</button>
        <button type="button" data-metric="Profit" aria-pressed="false">Profit</button>
        <button type="button" data-metric="Quantity" aria-pressed="false">Quantity</button>
      </div>
    </div>

    <div class="filters">
$filter_fields
      <div class="field">
        <label for="f-city">City</label>
        <input id="f-city" type="text" list="city-options" placeholder="All cities" autocomplete="off">
        <datalist id="city-options"></datalist>
      </div>
    </div>

    <div class="control-actions">
      <button class="icon-btn" id="btn-reset" type="button">Reset filters</button>
    </div>

    <p class="filter-summary" id="filter-summary">Loading…</p>
  </section>

  <main class="chart-grid">
$chart_cards
  </main>

  <footer class="footer">
    <h2>Data quality</h2>
    <div class="quality"><b id="meta-rows">—</b> order lines in scope</div>
$quality_items
    <div class="spacer"></div>
    <div>Source: Gold star schema (fact_sales × dim_product × dim_customer × dim_date)</div>
  </footer>

</div>

<script>$plotlyjs</script>
<script>window.__RETAILFLOW__ = $payload;</script>
<script>$app</script>
</body>
</html>
""")


def _kpi_markup():
    out = []
    for card_id, label, accent in KPI_CARDS:
        out.append(
            f'    <article class="kpi" id="{card_id}" style="--accent: var({accent})">\n'
            f'      <div class="kpi-label">{label}</div>\n'
            f'      <div class="kpi-value">—</div>\n'
            f'      <div class="kpi-sub"></div>\n'
            f'    </article>'
        )
    return "\n".join(out)


def _chart_markup():
    out = []
    for key, title, subtitle, extra in CHART_CARDS:
        classes = ("card " + extra).strip()
        out.append(
            f'    <section class="{classes}">\n'
            f'      <div class="card-head">\n'
            f'        <h2 class="card-title" id="title-{key}">{title}</h2>\n'
            f'        <p class="card-sub" id="sub-{key}">{subtitle}</p>\n'
            f'      </div>\n'
            f'      <div class="plot" id="plot-{key}"></div>\n'
            f'    </section>'
        )
    return "\n".join(out)


def _filter_markup():
    out = []
    for field_id, label in FILTER_FIELDS:
        out.append(
            f'      <div class="field">\n'
            f'        <label for="{field_id}">{label}</label>\n'
            f'        <select id="{field_id}"></select>\n'
            f'      </div>'
        )
    return "\n".join(out)


def _quality_markup(quality):
    out = []
    for label, value in quality:
        out.append(f'    <div class="quality"><b>{value:,}</b> {label}</div>')
    return "\n".join(out)


def _read_asset(name):
    with open(os.path.join(ASSETS_DIR, name), "r", encoding="utf-8") as handle:
        return handle.read()


def build_html(payload, quality, inline_plotly=True):
    """Render the full dashboard page for an already-encoded payload."""
    plotlyjs = pyo.get_plotlyjs() if inline_plotly else ""
    page = PAGE.substitute(
        css=_read_asset("app.css"),
        app=_read_asset("app.js"),
        plotlyjs=plotlyjs,
        payload=json.dumps(payload, separators=(",", ":")),
        kpi_cards=_kpi_markup(),
        chart_cards=_chart_markup(),
        filter_fields=_filter_markup(),
        quality_items=_quality_markup(quality),
    )
    if not inline_plotly:
        cdn = f"https://cdn.plot.ly/plotly-{pyo.get_plotlyjs_version()}.min.js"
        page = page.replace(
            "<script></script>",
            f'<script src="{cdn}" charset="utf-8"></script>',
            1,
        )
    return page


def write_dashboard(page, paths):
    """Write the page to every destination and report the byte size."""
    written = []
    for path in paths:
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write(page)
        written.append((path, os.path.getsize(path)))
    return written
