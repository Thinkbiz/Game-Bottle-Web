import os
from typing import Dict, Any

# Base paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Environment settings
DEVELOPMENT = os.environ.get('DEVELOPMENT', 'False').lower() in ('true', '1', 't')
DEBUG = os.environ.get('DEBUG', str(DEVELOPMENT)).lower() in ('true', '1', 't')

# Database settings
DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
DB_PATH = os.environ.get('DB_PATH', os.path.join(DATA_DIR, 'game.db'))
DB_BACKUP_DIR = os.environ.get('DB_BACKUP_DIR', os.path.join(DATA_DIR, 'backups'))

# Logging settings
LOG_DIR = os.environ.get('LOG_DIR', os.path.join(BASE_DIR, 'logs'))
LOG_LEVEL = os.environ.get('LOG_LEVEL', 'DEBUG' if DEVELOPMENT else 'INFO')
LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'True').lower() in ('true', '1', 't')
LOG_FORMAT = os.environ.get('LOG_FORMAT', 'json' if not DEVELOPMENT else 'text')
LOG_MAX_SIZE = int(os.environ.get('LOG_MAX_SIZE', '10485760'))  # 10MB
LOG_BACKUP_COUNT = int(os.environ.get('LOG_BACKUP_COUNT', '5'))

# Session settings
SESSION_COOKIE_NAME = os.environ.get('SESSION_COOKIE_NAME', 'session_id')
SESSION_COOKIE_HTTPONLY = os.environ.get('SESSION_COOKIE_HTTPONLY', 'True').lower() in ('true', '1', 't')
SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'False').lower() in ('true', '1', 't')
SESSION_COOKIE_PATH = os.environ.get('SESSION_COOKIE_PATH', '/')
SESSION_EXPIRY_DAYS = int(os.environ.get('SESSION_EXPIRY_DAYS', '30'))

# Web server settings
HOST = os.environ.get('HOST', '127.0.0.1' if DEVELOPMENT else '0.0.0.0')
PORT = int(os.environ.get('PORT', '8000'))
SERVER_WORKERS = int(os.environ.get('SERVER_WORKERS', '1' if DEVELOPMENT else '4'))

# Game settings
VICTORY_TYPES = {
    "PERFECT": "Perfect Victory",
    "GLORIOUS": "Glorious Victory",
    "PYRRHIC": "Pyrrhic Victory",
    "STANDARD": "Standard Victory"
}

# Default template variables
TEMPLATE_DEFAULTS: Dict[str, Any] = {
    'title': 'Monsters and Treasure',
    'show_name_input': True,
    'show_restart': False,
    'show_choices': False,
    'show_treasure_choices': False,
    'show_monster_choices': False,
    'player_name': '',
    'message': 'Welcome, brave adventurer! What is your name?',
    'event_type': 'welcome',
    'victory_type': None,
    'player_stats': None,
    'previous_stats': None
}

# Development configuration for backward compatibility
DEVELOPMENT_CONFIG = {
    'debug': DEBUG,
    'host': HOST,
    'port': PORT,
    'reloader': DEVELOPMENT
}

# Ensure required directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(DB_BACKUP_DIR, exist_ok=True)

# Development configuration settings
DEVELOPMENT_CONFIG = {
    'TEMPLATE_STRICT_VARS': True,  # Enable strict template variable checking
    'DEBUG': True,
    'TEMPLATE_PATH': './views',
    'TEMPLATE_DEFAULTS': {
        'show_name_input': False,
        'show_choices': False,
        'show_monster_choices': False,
        'show_treasure_choices': False,
        'message': '',
        'player_stats': None,
        'ga_measurement_id': 'G-69G95PRCQQ'  # Your GA4 ID
    },
    'RATE_LIMIT': {
        'requests_per_second': 10,
        'burst': 20
    },
    'SECURITY': {
        'allowed_hosts': ['localhost', '127.0.0.1'],
        'cors_origins': ['http://localhost:8000'],
        'max_request_size': 10 * 1024,  # 10KB
        'request_timeout': 5,  # seconds
        'session_lifetime': 24 * 60 * 60  # 24 hours
    }
}

# Production configuration (to be loaded from environment variables)
PRODUCTION_CONFIG = {
    'TEMPLATE_STRICT_VARS': True,
    'DEBUG': False,
    'TEMPLATE_PATH': './views',
    'TEMPLATE_DEFAULTS': {
        'show_name_input': False,
        'show_choices': False,
        'show_monster_choices': False,
        'show_treasure_choices': False,
        'message': '',
        'player_stats': None,
        'ga_measurement_id': 'G-69G95PRCQQ'  # Your GA4 ID
    },
    'RATE_LIMIT': {
        'requests_per_second': 5,
        'burst': 10
    },
    'SECURITY': {
        'allowed_hosts': ['${ALLOWED_HOSTS}'],  # To be replaced with actual domain
        'cors_origins': ['${CORS_ORIGINS}'],    # To be replaced with actual origins
        'max_request_size': 10 * 1024,  # 10KB
        'request_timeout': 5,  # seconds
        'session_lifetime': 24 * 60 * 60,  # 24 hours
        'csrf_enabled': False,
        'secure_cookies': True,
        'strict_transport_security': True
    }
} 