from airflow.www.app import cached_app

# Run Airflow using the lightweight Flask development server
# This bypasses Gunicorn and prevents the macOS Segmentation Fault crash
app = cached_app()
app.run(host="0.0.0.0", port=8082)