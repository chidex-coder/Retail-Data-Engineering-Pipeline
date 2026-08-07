"""Reads the dashboard's design tokens straight out of the stylesheet.

Colours are declared once, in `dashboards/assets/app.css`, as CSS custom
properties. The static report's `app.js` reads them at runtime with
getComputedStyle; Python can't do that, so it parses the same declarations
here. One source of truth, no hex duplicated between CSS and Python.
"""

import json
import os
import re

_HERE = os.path.dirname(os.path.abspath(__file__))
CSS_PATH = os.path.join(_HERE, "..", "dashboards", "assets", "app.css")
CHART_THEME_PATH = os.path.join(_HERE, "..", "shared", "chart_theme.json")

_VAR = re.compile(r"(--[a-z0-9-]+)\s*:\s*([^;]+);", re.IGNORECASE)


def _block_after(css, selector):
    """Return the body of the first `{...}` block following `selector`.

    `selector` must not include the opening brace — the search for it starts
    at the selector, so an included `{` would skip to the *next* block.
    """
    start = css.find(selector)
    if start == -1:
        raise ValueError(f"selector {selector!r} not found in app.css")
    open_brace = css.index("{", start)
    depth, i = 1, open_brace + 1
    while depth and i < len(css):
        if css[i] == "{":
            depth += 1
        elif css[i] == "}":
            depth -= 1
        i += 1
    return css[open_brace + 1:i - 1]


def _vars_in(block):
    return {name: value.strip() for name, value in _VAR.findall(block)}


def load_palettes():
    """Return {"light": {...}, "dark": {...}} of CSS custom properties."""
    with open(CSS_PATH, "r", encoding="utf-8") as handle:
        css = handle.read()

    light = _vars_in(_block_after(css, ":root"))
    # The dark set is an override of the light one, exactly as the cascade does it.
    dark = dict(light)
    dark.update(_vars_in(_block_after(css, ':root[data-theme="dark"]')))
    return {"light": light, "dark": dark}


def load_chart_theme():
    """Geometry shared with the static report (shared/chart_theme.json)."""
    with open(CHART_THEME_PATH, "r", encoding="utf-8") as handle:
        theme = json.load(handle)
    theme.pop("_comment", None)
    return theme


PALETTES = load_palettes()
CHART = load_chart_theme()

# Which palette entry each metric paints with, mirroring METRICS in app.js.
METRIC_COLOURS = {"Revenue": "--revenue", "Profit": "--profit", "Quantity": "--quantity"}

STATUS_COLOURS = {
    "Delivered": "--status-good",
    "Shipped": "--status-neutral",
    "Pending": "--status-warning",
    "Returned": "--status-serious",
    "Cancelled": "--status-critical",
}


def colour(theme, token):
    return PALETTES[theme][token]
