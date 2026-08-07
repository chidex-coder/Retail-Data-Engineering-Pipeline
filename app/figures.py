"""Plotly figures for the Dash app.

A direct port of the chart builders in dashboards/assets/app.js. Geometry
comes from shared/chart_theme.json and colours from app.css, so the two
front-ends stay visually identical without sharing runtime code.
"""

from app.theme import CHART, PALETTES, STATUS_COLOURS

GRAPH_CONFIG = {
    "displaylogo": False,
    "responsive": True,
    "displayModeBar": "hover",
    "modeBarButtonsToRemove": ["lasso2d", "select2d", "autoScale2d", "zoomIn2d", "zoomOut2d"],
    "toImageButtonOptions": {"format": "png", "scale": 2, "filename": "retailflow-chart"},
}

PLOT_HEIGHT = 300


# --------------------------------------------------------------------------- #
# Number formatting — mirrors the helpers in app.js
# --------------------------------------------------------------------------- #

def compact(value):
    magnitude = abs(value)
    if magnitude >= 1e9:
        return f"{value / 1e9:.2f}".rstrip("0").rstrip(".") + "B"
    if magnitude >= 1e6:
        return f"{value / 1e6:.{0 if magnitude >= 1e8 else 1}f}M"
    if magnitude >= 1e3:
        return f"{value / 1e3:.{0 if magnitude >= 1e5 else 1}f}K"
    return f"{value:.2f}" if magnitude < 10 and value % 1 else f"{value:.0f}"


def money(value):
    return "£" + compact(value)


def money_full(value):
    return f"£{value:,.2f}"


def count(value):
    return f"{int(value):,}"


def metric_label(value, is_money):
    return money(value) if is_money else compact(value)


def metric_full(value, is_money):
    return money_full(value) if is_money else f"{count(value)} units"


def _rgba(hex_colour, alpha):
    raw = hex_colour.lstrip("#")
    if len(raw) == 3:
        raw = "".join(c * 2 for c in raw)
    r, g, b = (int(raw[i:i + 2], 16) for i in (0, 2, 4))
    return f"rgba({r},{g},{b},{alpha})"


# --------------------------------------------------------------------------- #
# Layout scaffolding
# --------------------------------------------------------------------------- #

def _base_layout(theme, **extra):
    p = PALETTES[theme]
    layout = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor": "rgba(0,0,0,0)",
        "font": {
            "family": CHART["font"]["family"],
            "size": CHART["font"]["size"],
            "color": p["--text-secondary"],
        },
        "margin": {"l": 8, "r": 16, "t": 10, "b": 28},
        "showlegend": False,
        "hoverlabel": {
            "bgcolor": p["--surface"],
            "bordercolor": p["--border-strong"],
            "font": {"color": p["--text-primary"], "size": 12},
        },
        "dragmode": False,
    }
    layout.update(extra)
    return layout


def empty_figure(theme, message="No records match the current filters."):
    return {
        "data": [],
        "layout": _base_layout(
            theme,
            xaxis={"visible": False},
            yaxis={"visible": False},
            annotations=[{
                "text": message,
                "showarrow": False,
                "xref": "paper", "yref": "paper", "x": 0.5, "y": 0.5,
                "font": {"color": PALETTES[theme]["--text-muted"], "size": 12.5},
            }],
        ),
    }


# --------------------------------------------------------------------------- #
# Chart builders
# --------------------------------------------------------------------------- #

def h_bar(rows, colour, formatter, theme, hover_formatter=None):
    """Horizontal bars: labels left, values on the mark, no x-axis."""
    if not rows:
        return empty_figure(theme)

    p = PALETTES[theme]
    bar = CHART["bar"]

    # Plotly draws horizontal bars bottom-up, so reverse for largest-at-top.
    ordered = list(reversed(rows))
    values = [r["value"] for r in ordered]
    largest = max(values + [0]) or 1

    # Width is in category units, so cap it when the chart has few rows.
    width = min(0.65, (bar["maxThicknessPx"] * len(ordered)) / PLOT_HEIGHT)

    return {
        "data": [{
            "type": "bar",
            "orientation": "h",
            "x": values,
            "y": [r["label"] for r in ordered],
            "width": width,
            "marker": {
                "color": [r.get("colour", colour) for r in ordered],
                "cornerradius": bar["cornerRadius"],
                "line": {"width": 0},
            },
            "text": [formatter(v) for v in values],
            "textposition": "outside",
            "cliponaxis": False,
            "textfont": {"color": p["--text-secondary"], "size": CHART["font"]["labelSize"]},
            "customdata": [(hover_formatter or (lambda r: formatter(r["value"])))(r) for r in ordered],
            "hovertemplate": "<b>%{y}</b><br>%{customdata}<extra></extra>",
        }],
        "layout": _base_layout(
            theme,
            bargap=bar["gap"],
            margin=bar["margin"],
            xaxis={"visible": False, "range": [0, largest * bar["headroom"]], "fixedrange": True},
            yaxis={
                "automargin": True,
                "ticklabelposition": "outside",
                "tickfont": {"color": p["--text-secondary"], "size": CHART["font"]["size"]},
                "showgrid": False, "zeroline": False, "showline": False,
                "ticks": "", "fixedrange": True,
            },
        ),
    }


def line(dates, values, colour, prefix, theme):
    if not dates:
        return empty_figure(theme)

    p = PALETTES[theme]
    ln, axis = CHART["line"], CHART["axis"]

    return {
        "data": [{
            "type": "scatter",
            "mode": "lines+markers",
            "x": dates,
            "y": values,
            "line": {"color": colour, "width": ln["width"]},
            "marker": {
                "size": ln["markerSize"], "color": colour,
                "line": {"width": ln["markerRing"], "color": p["--surface"]},
            },
            "fill": "tozeroy",
            "fillcolor": _rgba(colour, ln["fillOpacity"]),
            "hovertemplate": "%{y:,.0f}<extra></extra>",
        }],
        "layout": _base_layout(
            theme,
            margin=ln["margin"],
            hovermode="x unified",
            xaxis={
                "type": "date", "tickformat": axis["dateTickFormat"],
                "showgrid": False, "zeroline": False, "linecolor": p["--axis"],
                "tickfont": {"color": p["--text-muted"], "size": CHART["font"]["tickSize"]},
                "fixedrange": True, "nticks": axis["maxTicks"], "showspikes": True,
                "spikemode": "across", "spikethickness": 1, "spikedash": "dot",
                "spikecolor": p["--axis"],
            },
            yaxis={
                "showgrid": True, "gridcolor": p["--grid"], "gridwidth": 1, "zeroline": False,
                "tickprefix": prefix, "tickformat": axis["valueTickFormat"], "rangemode": "tozero",
                "tickfont": {"color": p["--text-muted"], "size": CHART["font"]["tickSize"]},
                "fixedrange": True,
            },
        ),
    }


def column(dates, values, colour, hover, theme):
    if not dates:
        return empty_figure(theme)

    p = PALETTES[theme]
    col, axis = CHART["column"], CHART["axis"]

    return {
        "data": [{
            "type": "bar",
            "x": dates,
            "y": values,
            "marker": {"color": colour, "cornerradius": col["cornerRadius"], "line": {"width": 0}},
            "customdata": hover,
            "hovertemplate": "<b>%{x|%b %Y}</b><br>%{customdata}<extra></extra>",
        }],
        "layout": _base_layout(
            theme,
            bargap=col["gap"],
            margin=col["margin"],
            hovermode="x unified",
            xaxis={
                "type": "date", "tickformat": axis["dateTickFormat"],
                "showgrid": False, "zeroline": False, "linecolor": p["--axis"],
                "tickfont": {"color": p["--text-muted"], "size": CHART["font"]["tickSize"]},
                "fixedrange": True, "nticks": axis["maxTicks"],
            },
            yaxis={
                "showgrid": True, "gridcolor": p["--grid"], "gridwidth": 1, "zeroline": False,
                "tickfont": {"color": p["--text-muted"], "size": CHART["font"]["tickSize"]},
                "tickformat": axis["valueTickFormat"], "fixedrange": True, "rangemode": "tozero",
            },
        ),
    }


def status_colours(rows, theme):
    """Attach the reserved status palette; labels stay visible on every bar."""
    p = PALETTES[theme]
    for row in rows:
        row["colour"] = p[STATUS_COLOURS.get(row["label"], "--status-neutral")]
    return rows
