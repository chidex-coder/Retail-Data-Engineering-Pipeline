"""Loads the Gold analytics table and aggregates it per request.

This is the server-side twin of `aggregate()` in dashboards/assets/app.js.
Both consume the same cleaned fact rows and must agree on every number; the
difference is only where the loop runs.
"""

import os

import pandas as pd

_HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_PATH = os.path.join(_HERE, "..", "data", "gold", "analytics_facts.parquet")

# Filter key -> column in the frame. Order matches the filter bar.
FILTER_COLUMNS = {
    "year": "Year",
    "month": "Month",
    "category": "Category",
    "brand": "Brand",
    "payment": "PaymentMethod",
    "gender": "Gender",
    "status": "Status",
    "city": "City",
}

METRIC_COLUMNS = {"Revenue": "Revenue", "Profit": "Profit", "Quantity": "Quantity"}

MONTH_NAMES = ["January", "February", "March", "April", "May", "June",
               "July", "August", "September", "October", "November", "December"]


class Dataset:
    """The fact table, held in memory, plus the dimension members for the filters."""

    def __init__(self, path=None):
        self.frame = pd.read_parquet(path or os.environ.get("ANALYTICS_PARQUET", DEFAULT_PATH))
        self.rows = len(self.frame)
        self.options = {
            key: self._members(column) for key, column in FILTER_COLUMNS.items()
            if key not in ("year", "month")
        }
        years = sorted(int(y) for y in self.frame["Year"].dropna().unique())
        self.options["year"] = [str(y) for y in years]
        self.options["month"] = MONTH_NAMES

    def _members(self, column):
        values = self.frame[column].dropna().unique().tolist()
        return sorted(str(v) for v in values)

    def mask(self, filters):
        """Boolean mask for the active filter set (empty/None means 'all')."""
        mask = pd.Series(True, index=self.frame.index)
        for key, value in filters.items():
            if value in (None, "", []):
                continue
            column = FILTER_COLUMNS[key]
            if key == "year":
                mask &= self.frame[column] == float(value)
            elif key == "month":
                mask &= self.frame[column] == float(MONTH_NAMES.index(value) + 1)
            else:
                mask &= self.frame[column].astype("object") == value
        return mask

    def aggregate(self, filters, metric):
        """One pass producing every KPI and every chart's rows."""
        selection = self.frame[self.mask(filters)]
        column = METRIC_COLUMNS[metric]

        revenue = float(selection["Revenue"].sum())
        profit = float(selection["Profit"].sum())
        orders = int(len(selection))

        result = {
            "rows": orders,
            "revenue": revenue,
            "profit": profit,
            "quantity": int(selection["Quantity"].sum()),
            "orders": orders,
            "customers": int(selection["CustomerKey"].nunique()),
            "products": int(selection["ProductKey"].nunique()),
            "cities": int(selection["City"].nunique()),
            "aov": revenue / orders if orders else 0.0,
            "margin": (profit / revenue * 100) if revenue else 0.0,
            "metricTotal": float(selection[column].sum()),
        }

        result["brand"] = self._breakdown(selection, "Brand", column, 10)
        result["category"] = self._breakdown(selection, "Category", column)
        result["city"] = self._breakdown(selection, "City", column, 10)
        result["gender"] = self._breakdown(selection, "Gender", column)
        result["payment"] = self._breakdown(selection, "PaymentMethod", column)
        result["customer"] = self._breakdown(selection, "CustomerName", column, 10)
        result["status"] = self._breakdown(selection, "Status", "__count__")
        result["trend"] = self._monthly(selection, column)
        return result

    @staticmethod
    def _breakdown(selection, dimension, column, limit=None):
        """Rows of {label, value, orders} for one dimension, largest first.

        Rows whose attribute is unresolved drop out of the breakdown but stay
        in the totals — the same rule the static report applies.
        """
        if selection.empty:
            return []
        grouped = selection.groupby(dimension, observed=True)
        counts = grouped.size()
        values = counts if column == "__count__" else grouped[column].sum()
        table = pd.DataFrame({"value": values, "orders": counts}).dropna()
        table = table[table["orders"] > 0].sort_values("value", ascending=False)
        if limit:
            table = table.head(limit)
        return [
            {"label": str(label), "value": float(row.value), "orders": int(row.orders)}
            for label, row in table.iterrows()
        ]

    @staticmethod
    def _monthly(selection, column):
        """Monthly points on a real date axis; undated rows are excluded."""
        dated = selection.dropna(subset=["Year", "Month"])
        if dated.empty:
            return {"dates": [], "values": [], "orders": []}
        grouped = dated.groupby(["Year", "Month"], observed=True)
        table = pd.DataFrame({"value": grouped[column].sum(), "orders": grouped.size()})
        table = table.sort_index()
        dates = [f"{int(y)}-{int(m):02d}-01" for y, m in table.index]
        return {
            "dates": dates,
            "values": [float(v) for v in table["value"]],
            "orders": [int(c) for c in table["orders"]],
        }
