import os
import datetime
import config

def ensure_project_directories():
    """Ensure all required project folders exist on start."""
    dirs = [
        os.path.join(config.BASE_DIR, "reports"),
        os.path.join(config.BASE_DIR, "qr_codes"),
        os.path.join(config.BASE_DIR, "visitor_images"),
        os.path.join(config.BASE_DIR, "logs"),
        os.path.join(config.BASE_DIR, "database"),
        os.path.join(config.BASE_DIR, "assets", "icons"),
        os.path.join(config.BASE_DIR, "assets", "fonts"),
        os.path.join(config.BASE_DIR, "assets", "images"),
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        print(f"[Helpers] Ensured directory exists: {d}")

def format_timestamp(timestamp_str, format_out="%Y-%m-%d %H:%M:%S"):
    """Format an ISO timestamp string into custom format."""
    if not timestamp_str:
        return "N/A"
    try:
        dt = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        return dt.strftime(format_out)
    except Exception:
        return timestamp_str
