Description: Rules for Bottle web server, SQLite, and static assets in the adventure game webapp
Globs: web_game.py, templates/*.html, static/css/*.css, static/js/*.js
Content:
- Use Bottle for routing with @route (e.g., @route('/play')) and REST-like paths (e.g., /api/score/<id:int>).
- Keep route handlers under 20 lines; delegate game logic to separate files (e.g., game_logic.py, database.py).
- Use SQLite with parameterized queries (e.g., conn.execute('SELECT * FROM scores WHERE id = ?', (id,))) and context managers (with sqlite3.connect('game.db')).
- Return JSON for API routes (e.g., {'status': 'ok'}) and render templates for HTML (e.g., template('game.html', vars)).
- Include a /health route returning {'status': 'healthy'} for Docker HEALTHCHECK compatibility.
- Apply decorators like error_boundary and safe_template for error handling and template safety.
- Use structured logging for requests and errors (e.g., logger.debug(json.dumps({'route': '/play', 'method': request.method}))).
- Store SQLite DB as 'game.db' in /app; load path via os.environ.get('DB_PATH', 'game.db').
- Manage game state with Dict[str, Any] in session cookies or game_states, tied to Bottle’s request/response cycle.
- For HTML templates (templates/*.html):
  - Use Jinja2-style syntax (e.g., {{ variable }}) consistent with Bottle’s template engine.
  - Include all vars from TEMPLATE_DEFAULTS (e.g., show_name_input, message, player_stats) with fallback defaults.
  - Keep templates under 200 lines for readability; split into partials (e.g., _header.html, _footer.html) if larger.
  - Add comments for complex logic (e.g., {% if show_restart %}) or template-specific behavior.
  - Use Tailwind classes (e.g., bg-accent-orange, text-slate-gray) matching tailwind.config.js colors, fonts (Inter, Outfit), and utilities (shadow-soft, shadow-strong).
- For CSS (static/css/*.css):
  - Use Tailwind CSS (via tailwind.config.js) for utility-first styling, leveraging custom colors (slate-gray, off-white, accent-orange, light-orange), fonts (Inter, Outfit), and shadows (soft, strong).
  - Minimize custom CSS; use Tailwind’s @apply directive sparingly for shared styles (e.g., @apply bg-accent-orange text-white).
  - Optimize file size with PostCSS (via postcss.config.js) using autoprefixer for production builds, ensuring compatibility with modern browsers (e.g., last 2 versions).
  - Keep CSS files under 500 lines; split into modules (e.g., base.css, components.css) if larger.
  - Add comments for non-obvious styles or custom overrides (e.g., /* Custom shadow for game buttons */).
  - Purge unused styles in production using Tailwind’s content configuration (./views/**/*.{html,tpl}).
- For JavaScript (static/js/*.js):
  - Use vanilla JS or minimal libraries (e.g., no jQuery) to keep lightweight for 4GB RAM VPS.
  - Keep scripts under 100 lines; split into modules (e.g., game.js, ui.js) if larger.
  - Use ES6+ syntax (e.g., const, let) and add JSDoc comments for functions (e.g., /** @function startGame - Initiates game fetch */).
  - Log errors to console.error for debugging, avoiding heavy logging frameworks.
  - Use Tailwind-inspired class manipulation dynamically if needed (e.g., element.classList.add('bg-accent-orange')).

  