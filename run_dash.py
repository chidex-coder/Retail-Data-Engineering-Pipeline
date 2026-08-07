"""Entry point for the Dash dashboard.

Runs from any working directory:  python /path/to/run_dash.py
In production gunicorn imports the app directly: gunicorn app.main:server
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app  # noqa: E402

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8050)), debug=False)
