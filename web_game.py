from bottle import route, run, template, static_file, request, redirect, response, default_app
import random
from database import init_db, add_to_leaderboard, get_leaderboard
import json
import os
from datetime import datetime
import logging
import sys
from typing import Dict, Any, Optional, Union, Tuple
from config import DEVELOPMENT_CONFIG

# Game Constants
VICTORY_TYPES = {
    "PERFECT": "Perfect Victory",
    "GLORIOUS": "Glorious Victory",
    "PYRRHIC": "Pyrrhic Victory",
    "STANDARD": "Standard Victory",
    "DIED": "Died"
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
        logging.FileHandler('game.log')
    ]
)
logger = logging.getLogger(__name__)

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
        else:
            state['previous_stats'] = state['stats'].copy()
    
    game_states[session_id] = state

def check_victory_type(stats: Dict[str, int]) -> Optional[str]:
    """Check if player has achieved victory and determine type"""
    if stats['xp'] >= GAME_THRESHOLDS["VICTORY_XP"]:
        if stats['health'] > GAME_THRESHOLDS["PERFECT_HEALTH"] and stats['score'] > GAME_THRESHOLDS["PERFECT_SCORE"]:
            return VICTORY_TYPES["PERFECT"]
        elif stats['health'] > GAME_THRESHOLDS["GLORIOUS_HEALTH"]:
            return VICTORY_TYPES["GLORIOUS"]
        elif stats['health'] <= GAME_THRESHOLDS["PYRRHIC_HEALTH"]:
            return VICTORY_TYPES["PYRRHIC"]
        else:
            return VICTORY_TYPES["STANDARD"]
    return None

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
            'player_stats': game_state.get('stats')
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

@route('/choice', method='POST')
def make_choice():
    try:
        choice = request.forms.get('choice', '').strip()
        game_state = get_game_state()
        
        logger.debug(f"Processing choice: {choice}")
        logger.debug(f"Current game state: {game_state}")
        
        if not choice:
            logger.warning("No choice provided")
            return redirect('/')
            
        if 'stats' not in game_state:
            logger.warning("No game state found")
            return redirect('/')
            
        template_vars = TEMPLATE_DEFAULTS.copy()
        stats = game_state['stats']
        previous_stats = game_state.get('previous_stats', stats.copy())
        player_name = game_state.get('player_name', 'Adventurer')
        
        logger.debug(f"Player {player_name} made choice: {choice}")
        
        if choice == 'rest':
            if stats['score'] >= 10:
                health_gain = min(20, 100 - stats['health'])
                score_cost = min(10, health_gain)
                stats['health'] += health_gain
                stats['score'] -= score_cost
                template_vars.update({
                    'message': f"You find a cozy spot to rest and recover...\nThe peaceful moment restores {health_gain} health at the cost of {score_cost} score points.\nSometimes the wisest action is to take care of yourself buddy!",
                    'show_choices': True,
                    'event_type': EVENT_TYPES["REST"]
                })
            else:
                template_vars.update({
                    'message': "You search for a place to rest, but alas!\nYou need at least 10 score points to afford a safe resting spot.\nPerhaps some adventure will fill your score points jar?",
                    'show_choices': True,
                    'event_type': EVENT_TYPES["REST_FAILED"]
                })
        
        elif choice == 'adventure':
            event = random.choice(["treasure", "monster", "trap"])
            
            if event == "monster":
                template_vars.update({
                    'message': "A wild ugly Monster appears!\nWhat will you do now, brave adventurer? It's fight or flight!",
                    'show_monster_choices': True,
                    'event_type': EVENT_TYPES["MONSTER"]
                })
            
            elif event == "treasure":
                template_vars.update({
                    'message': "You have learned about a treasure chest from a local in town!\n\nDo you want to maximize your XP and search alone?\nOr get help from a local and earn all the points but less XP (costs 10 scorepoints)?\nOr perhaps play it silly and completely ignore the treasure?",
                    'show_treasure_choices': True,
                    'event_type': EVENT_TYPES["TREASURE"]
                })
            
            elif event == "trap":
                stats['health'] -= 10
                stats['xp'] += 2
                template_vars.update({
                    'message': "Oh no! You've stumbled into a cleverly hidden trap!\nYou lost 10 health but gained 2 XP - you're getting tougher with every mishap!",
                    'show_choices': True,
                    'event_type': EVENT_TYPES["TRAP"]
                })

        elif choice == 'fight':
            if random.random() > 0.5:
                stats['score'] += 20
                stats['xp'] += 20
                template_vars.update({
                    'message': "With courage in your heart and steel in your hand, you face the monster head-on...\nVICTORY! The monster falls before your might!\nYou gained 20 score points and a whopping 20 XP for your bravery!",
                    'show_choices': True,
                    'event_type': 'combat_victory'
                })
            else:
                stats['health'] -= 20
                stats['xp'] += 5
                template_vars.update({
                    'message': "Despite your bravery, the monster proves too strong!\nYou lost 20 health, but gained 5 XP - every battle makes you stronger!\nPerhaps next time victory will be yours!",
                    'show_choices': True,
                    'event_type': 'combat_defeat'
                })

        elif choice == 'run':
            template_vars.update({
                'message': "Using your quick wit and quicker feet, you make a strategic retreat!\nSometimes living to fight another day is the wisest choice.\nNothing ventured and nothing gained, but nothing lost either! As Dr honeysnow used to say.",
                'show_choices': True,
                'event_type': 'combat_escape'
            })

        elif choice == 'search_alone':
            if random.random() > 0.4:  # 60% chance of success
                stats['score'] += 25
                stats['xp'] += 25
                template_vars.update({
                    'message': "You found the treasure by yourself! You're amazing bucko!\nYou gained 25 score points and a whopping 25 XP!",
                    'show_choices': True,
                    'event_type': EVENT_TYPES["TREASURE_FOUND"]
                })
            else:
                stats['xp'] += 3
                template_vars.update({
                    'message': "Despite your valiant efforts, you couldn't find the treasure...\nBut at least you gained 3 XP for trying! Never give up!",
                    'show_choices': True,
                    'event_type': EVENT_TYPES["TREASURE_NOT_FOUND"]
                })

        elif choice == 'get_help':
            template_vars.update({
                'event_type': EVENT_TYPES["LOCAL"]
            })
            if stats['score'] >= 10:
                stats['score'] -= 10
                if random.random() > 0.2:
                    stats['score'] += 25
                    stats['xp'] += 10
                    template_vars.update({
                        'message': "With the local's help, your willingness to pay, and a little luck, you found the treasure!\nYou gained 25 score points and 10 XP!",
                        'show_choices': True,
                        'event_type': EVENT_TYPES["TREASURE_FOUND"]
                    })
                else:
                    template_vars.update({
                        'message': "Despite the local's help, you couldn't find the treasure...\nDon't you feel silly after paying 10 score points? At least you learned a valuable lesson!",
                        'show_choices': True,
                        'event_type': EVENT_TYPES["TREASURE_HELP_FAILED"]
                    })
            else:
                template_vars.update({
                    'message': "You don't have enough points to get help (need 10 points).\nPerhaps try searching alone or come back when you're score pointsricher!",
                    'show_choices': True,
                    'event_type': EVENT_TYPES["LOCAL_UNAVAILABLE"]
                })

        elif choice == 'ignore':
            template_vars.update({
                'message': "You decided to ignore the treasure and move on.\nSometimes the real treasure is the adventures we choose not to undertake!",
                'show_choices': True,
                'event_type': EVENT_TYPES["TREASURE_IGNORED"]
            })

        # Save the updated game state
        game_state['stats'] = stats
        save_game_state(game_state)
        
        # Add stats to template variables
        template_vars['player_stats'] = stats
        template_vars['previous_stats'] = previous_stats
        
        # Check for win condition before checking for game over
        victory_type = check_victory_type(stats)
        if victory_type:
            # Map victory types to event types
            victory_event_types = {
                "Perfect Victory": EVENT_TYPES["VICTORY_PERFECT"],
                "Glorious Victory": EVENT_TYPES["VICTORY_GLORIOUS"],
                "Pyrrhic Victory": EVENT_TYPES["VICTORY_PYRRHIC"],
                "Standard Victory": EVENT_TYPES["VICTORY_STANDARD"]
            }
            # Add to leaderboard when victory is achieved
            add_to_leaderboard(
                player_name=player_name,
                score=stats['score'],
                xp=stats['xp'],
                victory_type=victory_type,
                health=stats['health']
            )
            victory_messages = {
                "PERFECT VICTORY": f"Incredible, {player_name}! You've mastered the game with style and grace!\nYour health is outstanding, your score is magnificent, and your experience is unmatched!\nYou are truly a legendary adventurer!",
                "GLORIOUS VICTORY": f"Well done, {player_name}! A truly heroic victory!\nYou've maintained your health admirably while gathering the experience needed to triumph!\nThe bards will sing tales of your journey!",
                "PYRRHIC VICTORY": f"Against all odds, {player_name}, you've achieved victory at great cost!\nThough your health has suffered greatly, your determination never wavered!\nA hard-won victory is still a victory!",
                "STANDARD VICTORY": f"Congratulations, {player_name}! You've mastered the game!\nThrough careful balance of risk and reward, you've achieved your goal!\nMay your future adventures be just as successful!"
            }
            template_vars.update({
                'victory_type': victory_type,
                'event_type': victory_event_types.get(victory_type),
                'message': f"\n{victory_type}!\n{victory_messages[victory_type]}\n"
                          f"Final Stats - Health: {stats['health']} | Score: {stats['score']} | XP: {stats['xp']}",
                'show_name_input': True  # Allow restart
            })
            game_states.pop(get_session_id(), None)  # Clear game state
            return template('game', **template_vars)
        
        # Check for game over
        if stats['health'] <= 0:
            template_vars.update({
                'message': f"Alas, brave {player_name}, your journey has come to an end!\nThough you fell, you achieved a noble score of {stats['score']} and gained {stats['xp']} XP!\nPerhaps another adventure awaits?",
                'show_restart': True,
                'show_choices': False,
                'show_monster_choices': False,
                'show_treasure_choices': False,
                'event_type': EVENT_TYPES["GAMEOVER"],
                'player_name': player_name,
                'player_stats': stats
            })
            # Record the death in leaderboard
            add_to_leaderboard(
                player_name=player_name,
                score=stats['score'],
                xp=stats['xp'],
                victory_type="DIED",
                health=stats['health']
            )
            game_states.pop(get_session_id(), None)  # Clear game state
        
        return template('game', **template_vars)

    except Exception as e:
        logger.error(f"Error processing choice: {str(e)}")
        template_vars = TEMPLATE_DEFAULTS.copy()
        template_vars.update({
            'message': "Alas! A mysterious force disrupts your adventure!\nThe ancient scrolls speak of such anomalies...\nPlease try again, brave or perhaps recalcitrant adventurer!",
            'show_name_input': True
        })
    
    return template('game', **template_vars)

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
        run(host=HOST, port=PORT, debug=DEBUG, reloader=DEBUG)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")