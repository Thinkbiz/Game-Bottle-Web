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
        'player_stats': None
    }
} 