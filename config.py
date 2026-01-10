"""
Configuration file for the PostgreSQL database settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'health_monitor_db'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'port': os.getenv('DB_PORT', '5432')
}

# You can also add other configurations
APP_CONFIG = {
    'debug': os.getenv('DEBUG', 'True').lower() == 'true',
    'secret_key': os.getenv('SECRET_KEY', 'your-secret-key-here'),
    'session_timeout': int(os.getenv('SESSION_TIMEOUT', '3600'))
}