Description: Rules for Python game logic files in a lightweight webapp game
Globs: *.py, !app.py, !test_*.py
Content:
- Write procedural code using functions and dictionaries (e.g., get_game_state), avoiding classes unless required for game objects.
- Use type hints for all functions with Dict[str, Any] for state (e.g., def update_stats(stats: Dict[str, int]) -> None).
- Limit functions to 15 lines and one responsibility (e.g., calculate scores, not update and log).
- Use verbose names (e.g., 'get_player_health' not 'get_hp') with lowercase_underscore convention.
- Add triple-quoted docstrings for logic functions (e.g., """Return victory type from stats""").
- Wrap file I/O and SQLite calls in try/except, logging errors (e.g., logger.error(f"DB failed: {e}")).
- Define game constants in ALL_CAPS at module level (e.g., VICTORY_TYPES = {...}).
- Log state changes as structured JSON (e.g., logger.debug(json.dumps({"event": "victory", "stats": stats}))).
- Optimize for 4GB RAM: avoid large loops/lists (>1000 items); use generators for iteration if needed.
- Import only used modules (e.g., from datetime import datetime, not import datetime).