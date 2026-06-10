import os
import sys
import configparser

# Determine base directory depending on if we are running as a PyInstaller bundle or standard python
if getattr(sys, 'frozen', False):
    # Running in a PyInstaller bundle
    EXECUTABLE_DIR = os.path.dirname(sys.executable)
    BUNDLE_DIR = sys._MEIPASS
else:
    # Running in normal python
    EXECUTABLE_DIR = os.path.abspath(os.path.dirname(__file__))
    BUNDLE_DIR = EXECUTABLE_DIR

BASE_DIR = BUNDLE_DIR

# ---------------------------------------------------------
# Dynamic Database Configuration (For Network Sharing)
# ---------------------------------------------------------
config_file_path = os.path.join(EXECUTABLE_DIR, 'app_config.ini')
ini_config = configparser.ConfigParser()

if not os.path.exists(config_file_path):
    # Create default config file if it doesn't exist
    ini_config['DATABASE'] = {
        'SharedDBPath': os.path.join(EXECUTABLE_DIR, 'database', 'vms.db')
    }
    with open(config_file_path, 'w') as configfile:
        ini_config.write(configfile)

ini_config.read(config_file_path)
DB_PATH = ini_config.get('DATABASE', 'SharedDBPath', fallback=os.path.join(EXECUTABLE_DIR, 'database', 'vms.db'))
# Ensure the directory for the database exists
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)


# Security Configurations
SECRET_KEY = "vms_secure_session_key_production_2026"

# Email Notification Configurations (SMTP Settings)
EMAIL_CONFIG = {
    "SMTP_ENABLED": False,  # Set to True to enable actual email notifications
    "SMTP_HOST": "smtp.gmail.com",
    "SMTP_PORT": 587,
    "SMTP_USER": "your-smtp-username@gmail.com",
    "SMTP_PASS": "your-smtp-app-password",
    "SMTP_SENDER": "SmartVMS Alert <alerts@smartvms.com>"
}

# General App Properties
APP_NAME = "Smart VMS - Enterprise Visitor Management System"
VERSION = "1.0.0"

# Styling & UI Theme Defaults
THEME = {
    "DEFAULT_MODE": "dark",  # Option: "dark" or "light"
    "ACCENT_COLOR": "#2ecc71",
    "PRIMARY_BG_DARK": "#121214",
    "PRIMARY_BG_LIGHT": "#f4f6f9",
    "CARD_BG_DARK": "rgba(32, 32, 46, 0.7)",
    "CARD_BG_LIGHT": "#ffffff",
    "FONT_FAMILY": "Segoe UI"
}

# Logging configurations
LOG_LEVEL = "INFO"  # Option: DEBUG, INFO, WARNING, ERROR, CRITICAL
LOG_FILE = os.path.join(BASE_DIR, "logs", "app.log")
