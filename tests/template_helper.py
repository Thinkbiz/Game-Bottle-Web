def test_template_vars(template_name, vars_dict):
    """Test if template variables are complete"""
    # Import TEMPLATE_DEFAULTS from web_game.py
    from web_game import TEMPLATE_DEFAULTS
    
    missing_vars = set(TEMPLATE_DEFAULTS.keys()) - set(vars_dict.keys())
    if missing_vars:
        raise ValueError(f"Missing template variables for {template_name}: {missing_vars}") 