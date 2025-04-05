from bottle import route, run, template, static_file, request, redirect, response, default_app, abort
import random
from database import (init_db, add_to_leaderboard, get_leaderboard, 
                     update_regional_stats, get_regional_stats,
                     update_player_achievement, update_player_session_stats,
                     get_player_session_stats)
import json
import os
from datetime import datetime
import logging
import sys
from typing import Dict, Any, Optional, Union, Tuple
from config import DEVELOPMENT_CONFIG
from gevent import pywsgi
from geventwebsocket import WebSocketError
from geventwebsocket.handler import WebSocketHandler

# Game Constants
VICTORY_TYPES = {
    "PERFECT": "Perfect Victory",
    "GLORIOUS": "Glorious Victory",
    "PYRRHIC": "Pyrrhic Victory",
    "STANDARD": "Standard Victory"
}

GAME_THRESHOLDS = {
    "VICTORY_XP": 200,
    "PERFECT_HEALTH": 80,
    "PERFECT_SCORE": 50,
    "GLORIOUS_HEALTH": 50,
    "PYRRHIC_HEALTH": 20
}

EVENT_TYPES = {
    "MONSTER": "monster",
    "TREASURE": "treasure",
    "TREASURE_FOUND": "treasure_found",
    "TRAP": "trap",
    "LOCAL": "local",
    "REST": "rest",
    "WELCOME": "welcome",
    "GAMEOVER": "gameover",
    "JOURNEY_BEGIN": "journey_begin",
    "ADVENTURE_START": "adventure_start",
    "TREASURE_NOT_FOUND": "treasure_not_found",
    "TREASURE_HELP_FAILED": "treasure_help_failed",
    "TREASURE_IGNORED": "treasure_ignored",
    "VICTORY_PERFECT": "victory_perfect",
    "VICTORY_GLORIOUS": "victory_glorious",
    "VICTORY_PYRRHIC": "victory_pyrrhic",
    "VICTORY_STANDARD": "victory_standard",
    "REST_FAILED": "rest_failed",
    "LOCAL_UNAVAILABLE": "local_unavailable"
}

# Environment variables with defaults
HOST = os.environ.get('HOST', '127.0.0.1')
PORT = int(os.environ.get('PORT', 8000))
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Enhanced debugging
logging.basicConfig(
    level=logging.DEBUG if DEBUG else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/game_state.log')
    ]
)
logger = logging.getLogger(__name__)

# Add a dedicated game state logger
game_state_logger = logging.getLogger('game_state')
game_state_logger.setLevel(logging.DEBUG)
game_state_handler = logging.FileHandler('logs/game_state.log')
game_state_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
game_state_logger.addHandler(game_state_handler)

# Default template variables
TEMPLATE_DEFAULTS: Dict[str, Any] = {
    'show_name_input': False,
    'show_choices': False,
    'show_monster_choices': False,
    'show_treasure_choices': False,
    'show_restart': False,
    'message': '',
    'player_stats': None,
    'event_type': None,
    'victory_type': None,
    'previous_stats': None,
    'player_name': None
}

# Initialize player stats
DEFAULT_STATS: Dict[str, int] = {
    'health': 100,
    'score': 0,
    'xp': 0
}

# Event type mapping for victories
VICTORY_EVENT_TYPES = {
    "Perfect Victory": "victory_perfect",
    "Glorious Victory": "victory_glorious", 
    "Pyrrhic Victory": "victory_pyrrhic",
    "Standard Victory": "victory_standard"
}

def test_template_vars(template_vars: Dict[str, Any]) -> bool:
    """Test template variables before rendering"""
    try:
        validate_template_vars(template_vars)
        return True
    except (ValueError, TypeError) as e:
        logger.error(f"Template validation failed: {str(e)}")
        return False

def validate_template_vars(template_vars: Dict[str, Any]) -> None:
    """Ensure all required template variables are present with correct types"""
    required_vars = {
        'show_name_input': bool,
        'show_choices': bool,
        'show_monster_choices': bool,
        'show_treasure_choices': bool,
        'show_restart': bool,
        'message': str,
        'player_stats': (dict, type(None)),
        'event_type': (str, type(None)),
        'victory_type': (str, type(None)),
        'player_name': (str, type(None))
    }
    
    for var, expected_type in required_vars.items():
        if var not in template_vars:
            raise ValueError(f"Missing required template variable: {var}")
        if not isinstance(template_vars[var], expected_type):
            raise TypeError(f"Invalid type for {var}: expected {expected_type}, got {type(template_vars[var])}")

def error_boundary(route_func):
    """Decorator to catch and handle all errors"""
    def wrapper(*args, **kwargs):
        try:
            return route_func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Route error: {str(e)}", exc_info=True)
            return template('game.html', 
                          message="An error occurred. Please try again.",
                          show_name_input=True,
                          **TEMPLATE_DEFAULTS)
    return wrapper

def safe_template(route_func):
    """Decorator to ensure template safety"""
    def wrapper(*args, **kwargs):
        try:
            template_vars = route_func(*args, **kwargs)
            if isinstance(template_vars, dict):
                # Merge with defaults
                full_vars = TEMPLATE_DEFAULTS.copy()
                full_vars.update(template_vars)
                # Test and validate
                if not test_template_vars(full_vars):
                    raise ValueError("Template validation failed")
                return full_vars
            return template_vars
        except Exception as e:
            logger.error(f"Template error: {str(e)}", exc_info=True)
            return template('game.html', **TEMPLATE_DEFAULTS)
    return wrapper

def get_session_id() -> str:
    """Get or create session ID"""
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(random.randint(1000000, 9999999))
        response.set_cookie('session_id', session_id, path='/')
    return session_id

def get_game_state() -> Dict[str, Any]:
    """Get current game state"""
    session_id = get_session_id()
    logger.debug(f"Getting game state for session {session_id}")
    state = game_states.get(session_id, {})
    
    # Initialize previous_stats if not present
    if 'stats' in state and 'previous_stats' not in state:
        state['previous_stats'] = state['stats'].copy()
    
    game_state_logger.debug(f"Current game state for session {session_id}: {json.dumps(state, indent=2)}")
    return state

def save_game_state(state: Dict[str, Any]) -> None:
    """Save current game state"""
    session_id = get_session_id()
    logger.debug(f"Saving game state for session {session_id}")
    
    # Store current stats as previous before updating
    if 'stats' in state:
        current_state = game_states.get(session_id, {})
        if 'stats' in current_state:
            state['previous_stats'] = current_state['stats'].copy()
            game_state_logger.info(f"State transition for session {session_id}:")
            game_state_logger.info(f"Previous stats: {json.dumps(current_state['stats'], indent=2)}")
            game_state_logger.info(f"New stats: {json.dumps(state['stats'], indent=2)}")
        else:
            state['previous_stats'] = state['stats'].copy()
            game_state_logger.info(f"Initial state for session {session_id}: {json.dumps(state['stats'], indent=2)}")
    
    game_states[session_id] = state

def determine_victory_type(stats):
    """Determine the type of victory based on player stats."""
    if stats['health'] > GAME_THRESHOLDS["PERFECT_HEALTH"] and stats['score'] > GAME_THRESHOLDS["PERFECT_SCORE"]:
        return VICTORY_TYPES["PERFECT"]
    elif stats['health'] > GAME_THRESHOLDS["GLORIOUS_HEALTH"]:
        return VICTORY_TYPES["GLORIOUS"]
    elif stats['health'] <= GAME_THRESHOLDS["PYRRHIC_HEALTH"]:
        return VICTORY_TYPES["PYRRHIC"]
    else:
        return VICTORY_TYPES["STANDARD"]

def get_event_type(victory_type):
    """Get the event type for a given victory type."""
    return VICTORY_EVENT_TYPES.get(victory_type, "victory_standard")

def get_victory_message(victory_type, player_name):
    """Get the message for a given victory type."""
    messages = {
        "Perfect Victory": f"Incredible, {player_name}! You've mastered the game with style and grace!\nYour health is outstanding, your score is magnificent, and your experience is unmatched!\nYou are truly a legend!",
        "Glorious Victory": f"Well done, {player_name}! A truly heroic victory!\nYou've maintained your health admirably while gathering the experience needed to triumph!\nThe bards will sing tales of your journey!",
        "Pyrrhic Victory": f"Against all odds, {player_name}, you've achieved victory at great cost!\nThough your health has suffered greatly, your determination never wavered!\nA hard-won victory is still a victory!",
        "Standard Victory": f"Congratulations, {player_name}! You've mastered the game!\nThrough careful balance of risk and reward, you've achieved your goal!\nMay your future adventures be just as successful!"
    }
    return messages.get(victory_type, messages["Standard Victory"])

# Initialize database
init_db()

# Game state storage - separate for each session
game_states = {}

# Add request logging middleware
def log_to_logger(fn):
    """Middleware to log all requests"""
    def _log_to_logger(*args, **kwargs):
        request_time = datetime.now()
        actual_response = fn(*args, **kwargs)
        logger.debug(f'''
            {request_time}
            Request: {request.method} {request.url}
            Headers: {dict(request.headers)}
            Forms: {dict(request.forms)}
            Response: {actual_response}
        ''')
        return actual_response
    return _log_to_logger

@route('/')
@safe_template
def game():
    logger.debug("Handling root route")
    template_vars = TEMPLATE_DEFAULTS.copy()
    game_state = get_game_state()
    
    if game_state.get('player_name'):
        template_vars.update({
            'message': f"Welcome back, {game_state['player_name']}!\nYour epic quest continues! What challenges await you today?",
            'show_choices': True,
            'player_stats': game_state.get('stats'),
            'player_name': game_state['player_name']
        })
    else:
        template_vars.update({
            'message': "Welcome to the Adventure Game! A world of mystery and excitement awaits!\nDare you enter this stupidly cute realm of monsters and treasures?\nPlease enter your name, brave soul, to begin your journey!",
            'show_name_input': True,
            'event_type': 'welcome'
        })
    
    return template('game', **template_vars)

@route('/start', method='POST')
def start_game():
    player_name = request.forms.get('player_name', '').strip()
    template_vars = TEMPLATE_DEFAULTS.copy()
    
    # If no new name provided, check if we have an existing name
    if not player_name:
        game_state = get_game_state()
        player_name = game_state.get('player_name', '').strip()
    
    if player_name:
        logger.debug(f"Starting new game for player: {player_name}")
        game_state = {
            'stats': DEFAULT_STATS.copy(),
            'player_name': player_name
        }
        save_game_state(game_state)
        
        template_vars.update({
            'message': f"Hail, {player_name}! Your journey into the unknown begins...\nWhat treasures will you find? What monsters will you face?\nThe path ahead is yours to choose, brave adventurer!",
            'show_choices': True,
            'player_name': player_name,
            'player_stats': game_state['stats'],
            'event_type': EVENT_TYPES["JOURNEY_BEGIN"]
        })
    else:
        template_vars.update({
            'message': "Please enter a valid name to begin.",
            'show_name_input': True
        })
    
    return template('game', **template_vars)

def validate_choice(choice: str) -> bool:
    """Validate user choice input"""
    valid_choices = {
        'fight', 'run',  # Combat choices
        'search_alone', 'get_help', 'ignore',  # Treasure choices
        'rest',  # Rest choice
        'adventure'  # Adventure choice
    }
    return choice in valid_choices

def validate_stats(stats: dict) -> bool:
    """Validate game stats"""
    required_fields = {'health', 'score', 'xp'}
    if not all(field in stats for field in required_fields):
        return False
    try:
        return (isinstance(stats['health'], (int, float)) and
                isinstance(stats['score'], (int, float)) and
                isinstance(stats['xp'], (int, float)) and
                0 <= stats['health'] <= 100 and
                stats['score'] >= 0 and
                stats['xp'] >= 0)
    except (KeyError, TypeError, ValueError):
        return False

@error_boundary
def handle_choice():
    """Handle user choice with validation"""
    choice = request.form.get('choice')
    if not validate_choice(choice):
        logger.warning(f"Invalid choice attempted: {choice}")
        return {'error': 'Invalid choice'}, 400
        
    stats = get_game_state().get('stats', {})
    if not validate_stats(stats):
        logger.error(f"Invalid stats detected: {stats}")
        return {'error': 'Invalid game state'}, 400

    # Convert stats to proper types
    stats = {
        'health': int(stats.get('health', 0)),
        'score': int(stats.get('score', 0)),
        'xp': int(stats.get('xp', 0))
    }
    
    return process_choice(choice, stats)

@route('/static/<filename:path>')
def serve_static(filename):
    # Basic security: ensure filename doesn't contain path traversal
    if '..' in filename or filename.startswith('/'):
        return 'Access denied', 403
        
    # Try the ./static directory first
    response = static_file(filename, root='./static')
    if response.status_code == 404:
        # If not found, try the views/static directory
        response = static_file(filename, root='./views/static')
    return response

@route('/leaderboard')
def show_leaderboard():
    leaderboard_entries = get_leaderboard(10)  # Get top 10
    return template('leaderboard', entries=leaderboard_entries)

@route('/health')
def health_check():
    return {'status': 'healthy', 'debug': DEBUG}

@route('/favicon.ico')
def get_favicon():
    return static_file('favicon.png', root='./static/favicon')

@route('/debug/die', method='GET')
def debug_die():
    """Debug endpoint to simulate player death (temporary)"""
    if not DEBUG:
        return "Debug endpoints only available in debug mode"
        
    game_state = get_game_state()
    if not game_state or 'stats' not in game_state:
        # Create a test player if none exists
        game_state = {
            'stats': DEFAULT_STATS.copy(),
            'player_name': 'Test Player'
        }
        save_game_state(game_state)
    
    # Set health to 0 and add some score/xp for testing
    game_state['stats']['health'] = 0
    game_state['stats']['score'] = 50
    game_state['stats']['xp'] = 75
    save_game_state(game_state)
    
    template_vars = TEMPLATE_DEFAULTS.copy()
    template_vars.update({
        'message': f"Alas, brave {game_state['player_name']}, your journey has come to an end!\nThough you fell, you achieved a noble score of {game_state['stats']['score']} and gained {game_state['stats']['xp']} XP!\nPerhaps another adventure awaits?",
        'show_restart': True,
        'show_choices': False,
        'show_monster_choices': False,
        'show_treasure_choices': False,
        'event_type': EVENT_TYPES["GAMEOVER"],
        'player_name': game_state['player_name'],
        'player_stats': game_state['stats']
    })
    
    # Record the death in leaderboard
    add_to_leaderboard(
        player_name=game_state['player_name'],
        score=game_state['stats']['score'],
        xp=game_state['stats']['xp'],
        victory_type="DIED",
        health=game_state['stats']['health']
    )
    # Preserve player name and session ID while clearing other state
    preserved_state = {
        'player_name': game_states[get_session_id()]['player_name'],
        'session_id': get_session_id()  # Preserve the session ID
    }
    game_states[get_session_id()] = preserved_state
    
    return template('game', **template_vars)

@route('/api/stats/regional', method='POST')
def update_region():
    """Update regional statistics"""
    try:
        data = request.json
        if not data:
            response.status = 400
            return {'error': 'No data provided'}
            
        required_fields = ['region_key', 'country', 'region', 'player_name']
        if not all(field in data for field in required_fields):
            response.status = 400
            return {'error': 'Missing required fields'}
            
        update_regional_stats(
            region_key=data['region_key'],
            country=data['country'],
            region=data['region'],
            player_name=data['player_name'],
            combat_style=data.get('combat_style'),
            action=data.get('action')
        )
        return {'status': 'success'}
    except Exception as e:
        logger.error(f"Error updating regional stats: {str(e)}")
        response.status = 500
        return {'error': 'Internal server error'}

@route('/api/stats/regional/<region_key>', method='GET')
def get_region(region_key):
    """Get regional statistics"""
    try:
        stats = get_regional_stats(region_key)
        if stats:
            return stats
        response.status = 404
        return {'error': 'Region not found'}
    except Exception as e:
        logger.error(f"Error getting regional stats: {str(e)}")
        response.status = 500
        return {'error': 'Internal server error'}

@route('/api/achievements', method='POST')
def record_achievement():
    """Record a player achievement"""
    try:
        data = request.json
        if not data or 'player_name' not in data or 'achievement' not in data:
            response.status = 400
            return {'error': 'Missing required fields'}
            
        update_player_achievement(
            player_name=data['player_name'],
            achievement=data['achievement']
        )
        return {'status': 'success'}
    except Exception as e:
        logger.error(f"Error recording achievement: {str(e)}")
        response.status = 500
        return {'error': 'Internal server error'}

@route('/api/stats/session', method='POST')
def update_session():
    """Update session statistics"""
    try:
        data = request.json
        if not data:
            response.status = 400
            return {'error': 'No data provided'}
            
        required_fields = ['player_name', 'session_id']
        if not all(field in data for field in required_fields):
            response.status = 400
            return {'error': 'Missing required fields'}
            
        stats_update = {k: v for k, v in data.items() 
                       if k not in ['player_name', 'session_id']}
        
        update_player_session_stats(
            player_name=data['player_name'],
            session_id=data['session_id'],
            stats_update=stats_update
        )
        return {'status': 'success'}
    except Exception as e:
        logger.error(f"Error updating session stats: {str(e)}")
        response.status = 500
        return {'error': 'Internal server error'}

@route('/api/stats/session/<player_name>/<session_id>', method='GET')
def get_session(player_name, session_id):
    """Get session statistics"""
    try:
        stats = get_player_session_stats(player_name, session_id)
        if stats:
            return stats
        response.status = 404
        return {'error': 'Session not found'}
    except Exception as e:
        logger.error(f"Error getting session stats: {str(e)}")
        response.status = 500
        return {'error': 'Internal server error'}

# Debug endpoint for browser tools
@route('/debug/ws')
def handle_websocket():
    wsock = request.environ.get('wsgi.websocket')
    if not wsock:
        abort(400, 'Expected WebSocket request.')
    
    try:
        # Send initial connection success message
        wsock.send(json.dumps({
            'type': 'connection',
            'status': 'connected',
            'debug': True
        }))
        
        while True:
            message = wsock.receive()
            if message:
                try:
                    data = json.loads(message)
                    # Handle different message types
                    if data.get('type') == 'ping':
                        wsock.send(json.dumps({
                            'type': 'pong',
                            'timestamp': datetime.now().isoformat()
                        }))
                    else:
                        # Echo back debug messages
                        response = {
                            'type': 'debug_response',
                            'data': data,
                            'timestamp': datetime.now().isoformat()
                        }
                        wsock.send(json.dumps(response))
                except json.JSONDecodeError:
                    wsock.send(json.dumps({
                        'type': 'error',
                        'message': 'Invalid JSON message'
                    }))
    except WebSocketError as e:
        logger.debug(f"WebSocket closed: {str(e)}")
    finally:
        if not wsock.closed:
            wsock.close()

# Enable CORS for debug endpoints
@route('/debug/<:path>', method=['OPTIONS', 'GET'])
def enable_cors_for_debug(path=None):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Origin, Accept, Content-Type, X-Requested-With, Connection, Upgrade, Sec-WebSocket-Key, Sec-WebSocket-Version'
    response.headers['Access-Control-Max-Age'] = '86400'  # 24 hours
    
    if request.method == 'OPTIONS':
        return ''
    return static_file(path, root='./static') if path else ''

# Initialize app with middleware
app = default_app()
app.install(log_to_logger)

# Error handling
@app.error(500)
def error500(error):
    logger.error(f"Server error: {error}")
    return template('game', 
                   message="An error occurred. Please try again.",
                   show_name_input=True,
                   **TEMPLATE_DEFAULTS)

@app.error(404)
def error404(error):
    logger.error(f"Page not found: {error}")
    return template('game',
                   message="Page not found. Please start over.",
                   show_name_input=True,
                   **TEMPLATE_DEFAULTS)

if __name__ == "__main__":
    try:
        logger.info("Starting server...")
        if DEBUG:
            # Create two servers - one for main app and one for debug
            main_server = pywsgi.WSGIServer((HOST, PORT), app)
            debug_port = int(os.environ.get('DEBUG_PORT', 3025))
            debug_server = pywsgi.WSGIServer((HOST, debug_port), app, handler_class=WebSocketHandler)
            
            # Start both servers
            from gevent import spawn
            spawn(main_server.serve_forever)
            debug_server.serve_forever()
        else:
            run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")