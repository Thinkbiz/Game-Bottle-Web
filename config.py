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
        'csrf_enabled': True,
        'secure_cookies': True,
        'strict_transport_security': True
    }
} 