from bottle import route, run, template, static_file, request, redirect, response, default_app, error, HTTPError
import random
from database import (init_db, add_to_leaderboard, get_leaderboard, 
                     update_regional_stats, get_regional_stats,
                     update_player_achievement, update_player_session_stats,
                     get_player_session_stats, get_game_state_from_db,
                     save_game_state_to_db, cleanup_expired_sessions)
import json
import os
from datetime import datetime
import logging
import sys
from typing import Dict, Any, Optional, Union, Tuple
from config import (DEVELOPMENT_CONFIG, LOG_DIR, DATA_DIR, DB_PATH, 
                   SESSION_COOKIE_NAME, SESSION_COOKIE_HTTPONLY, 
                   SESSION_COOKIE_SECURE, SESSION_COOKIE_PATH,
                   SESSION_EXPIRY_DAYS, TEMPLATE_DEFAULTS, VICTORY_TYPES)
import sqlite3
from logger import get_logger, get_session_logger, game_logger as logger, game_state_logger
import time
import threading

# Game Constants
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
    "LOCAL_UNAVAILABLE": "local_unavailable",
    "JOURNEY_CONTINUE": "journey_continue"
}

# Event type mapping for victories
VICTORY_EVENT_TYPES = {
    "Perfect Victory": "victory_perfect",
    "Glorious Victory": "victory_glorious", 
    "Pyrrhic Victory": "victory_pyrrhic",
    "Standard Victory": "victory_standard"
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

# Initialize with empty game_states for backward compatibility
game_states = {}

# Initialize player stats
DEFAULT_STATS: Dict[str, int] = {
    'health': 100,
    'score': 0,
    'xp': 0
}

# Schedule periodic session cleanup
def cleanup_old_sessions():
    """Cleanup expired sessions periodically"""
    try:
        count = cleanup_expired_sessions(SESSION_EXPIRY_DAYS)
        if count > 0:
            logger.info(f"Cleaned up {count} expired game sessions")
    except Exception as e:
        logger.error(f"Error during session cleanup: {e}")

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
    """Decorator to catch and handle all errors in routes"""
    def wrapper(*args, **kwargs):
        try:
            return route_func(*args, **kwargs)
        except HTTPError as he:
            # Log HTTP errors but let them propagate to be handled by bottle's error handlers
            logger.warning(f"HTTP error in {route_func.__name__}: {str(he)}")
            raise he
        except sqlite3.Error as dbe:
            # Database errors
            logger.error(f"Database error in {route_func.__name__}: {str(dbe)}", exc_info=True)
            response.status = 500
            return template('error', 
                           error_code=500, 
                           title="Database Error", 
                           message="An unexpected database error has occurred. Our wizards have been notified!")
        except Exception as e:
            # All other errors
            logger.error(f"Unhandled exception in {route_func.__name__}: {str(e)}", exc_info=True)
            
            # Get current session info for better diagnostics
            session_id = request.get_cookie(SESSION_COOKIE_NAME, 'unknown')
            logger.error(f"Error context - Session: {session_id}, URL: {request.url}, Method: {request.method}")
            
            response.status = 500
            return template('error', 
                           error_code=500, 
                           title="Server Error", 
                           message="An unexpected error has occurred. The ancient scrolls speak of such anomalies... Our wizards have been notified!")
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
    # Check if we've already generated a session ID for this request
    if hasattr(request, '_cached_session_id'):
        return request._cached_session_id
        
    # Get from cookie or generate new
    session_id = request.cookies.get(SESSION_COOKIE_NAME)
    if not session_id:
        session_id = str(random.randint(1000000, 9999999))
        response.set_cookie(
            SESSION_COOKIE_NAME, 
            session_id, 
            path=SESSION_COOKIE_PATH,
            httponly=SESSION_COOKIE_HTTPONLY,
            secure=SESSION_COOKIE_SECURE
        )
        logger.debug(f"Created new session ID: {session_id}")
    else:
        logger.debug(f"Using existing session ID: {session_id}")
    
    # Cache the session ID for this request
    request._cached_session_id = session_id
    return session_id

def get_game_state() -> Dict[str, Any]:
    """Get current game state from database"""
    session_id = get_session_id()
    session_logger = get_session_logger('game_state', session_id)
    session_logger.debug(f"Getting game state for session {session_id}")
    
    # Get state from database
    state = get_game_state_from_db(session_id)
    
    # Initialize previous_stats if not present
    if 'stats' in state and 'previous_stats' not in state:
        state['previous_stats'] = state['stats'].copy()
    
    session_logger.debug(f"Current game state for session {session_id}: {json.dumps(state, indent=2)}")
    return state

def save_game_state(state: Dict[str, Any]) -> None:
    """Save current game state to database"""
    session_id = get_session_id()
    session_logger = get_session_logger('game_state', session_id)
    player_name = state.get('player_name', 'anonymous')
    
    session_logger.debug(f"Saving game state for session {session_id}")
    
    # Get previous state for logging transition
    current_state = get_game_state_from_db(session_id)
    
    # Store current stats as previous before updating
    if 'stats' in state:
        if 'stats' in current_state:
            state['previous_stats'] = current_state['stats'].copy()
            session_logger.info(f"State transition for session {session_id}:")
            session_logger.info(f"Previous stats: {json.dumps(current_state['stats'], indent=2)}")
            session_logger.info(f"New stats: {json.dumps(state['stats'], indent=2)}")
        else:
            state['previous_stats'] = state['stats'].copy()
            session_logger.info(f"Initial state for session {session_id}: {json.dumps(state['stats'], indent=2)}")
    
    # Save to database
    success = save_game_state_to_db(session_id, player_name, state, SESSION_EXPIRY_DAYS)
    
    if not success:
        session_logger.error(f"Failed to save game state for session {session_id}")

def determine_victory_type(stats):
    """Determine the type of victory based on player stats."""
    # First check if player has enough XP for victory
    if stats['xp'] < GAME_THRESHOLDS["VICTORY_XP"]:
        return None
        
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

# Start a background thread to periodically clean up expired sessions
def start_session_cleanup_scheduler():
    """Start a background thread to periodically clean up expired sessions"""
    def cleanup_thread():
        while True:
            try:
                cleanup_old_sessions()
                # Run cleanup every 6 hours
                time.sleep(6 * 60 * 60)  # 6 hours in seconds
            except Exception as e:
                logger.error(f"Error in cleanup thread: {e}")
                # If there's an error, wait a bit and try again
                time.sleep(60)
    
    # Create and start the thread
    cleanup_thread = threading.Thread(target=cleanup_thread, daemon=True)
    cleanup_thread.start()
    logger.info("Session cleanup scheduler started")

# Initialize database and start schedulers
init_db()
start_session_cleanup_scheduler()

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

def summarize_message(msg: str, max_chars: int = 120) -> str:
    """Summarize the message to fit within max_chars, preserving meaning."""
    if len(msg) <= max_chars:
        return msg
    # Try to keep sentences whole if possible
    sentences = msg.split('. ')
    summary = ''
    for sentence in sentences:
        if len(summary) + len(sentence) + 2 > max_chars:
            break
        if summary:
            summary += '. '
        summary += sentence
    if not summary:
        # Fallback: just truncate and add ellipsis
        return msg[:max_chars-3] + '...'
    if len(summary) < len(msg):
        summary = summary.rstrip('. ') + '...'
    return summary

@route('/')
@safe_template
def game():
    """Show the main game page"""
    session_id = get_session_id()
    session_logger = get_session_logger('game', session_id)
    
    # Get the current game state
    state = get_game_state()
    
    template_vars = TEMPLATE_DEFAULTS.copy()
    
    # If this is a new game or no state exists, prompt for name
    if not state or 'player_name' not in state or not state.get('player_name'):
        session_logger.debug("No active game found, showing name input")
        template_vars['show_name_input'] = True
        return template('views/game', **template_vars)
    
    player_name = state.get('player_name', 'Adventurer')
    stats = state.get('stats', DEFAULT_STATS.copy())
    
    session_logger.debug(f"Showing game for player {player_name} with stats: {stats}")
    
    # Set up template variables
    template_vars.update({
        'message': summarize_message(f"Hail, {player_name}! Your journey into the unknown continues...\nWhat path will you choose?"),
        'show_choices': True,
        'show_name_input': False,  # Explicitly set to False to hide the name input
        'player_name': player_name,
        'player_stats': stats,
        'previous_stats': state.get('previous_stats', stats.copy()),
        'event_type': EVENT_TYPES["JOURNEY_CONTINUE"]
    })
    
    return template('views/game', **template_vars)

@route('/victory/<victory_type>')
def victory_page(victory_type):
    """Display victory page with appropriate type"""
    session_id = get_session_id()
    session_logger = get_session_logger('game', session_id)
    
    # Get current game state
    state = get_game_state()
    
    # Default template variables
    template_vars = TEMPLATE_DEFAULTS.copy()
    
    # If no game state found, redirect to start
    if not state or 'stats' not in state:
        session_logger.warning(f"No game state found for victory page, session {session_id}")
        template_vars['show_name_input'] = True
        return template('views/game', **template_vars)
    
    # Get player info
    player_name = state.get('player_name', 'Adventurer')
    stats = state.get('stats', DEFAULT_STATS.copy())
    
    # Validate victory type
    if victory_type not in VICTORY_TYPES.values():
        session_logger.warning(f"Invalid victory type requested: {victory_type}")
        victory_type = VICTORY_TYPES["STANDARD"]
    
    session_logger.info(f"Player {player_name} achieved {victory_type}")
    
    # Get current stats and event type for this victory
    template_vars.update({
        'message': summarize_message(f"{victory_type}!\n{get_victory_message(victory_type, player_name)}\nFinal Stats - Health: {stats['health']} | Score: {stats['score']} | XP: {stats['xp']}\n\nYou can continue playing to improve your score or restart the adventure!"),
        'show_restart': True,
        'show_choices': True,  # Allow the player to continue the adventure
        'show_name_input': False,
        'player_name': player_name,
        'player_stats': stats,
        'previous_stats': state.get('previous_stats', stats.copy()),
        'victory_type': victory_type,
        'event_type': VICTORY_EVENT_TYPES.get(victory_type, "victory_standard")
    })
    
    # Update leaderboard
    try:
        add_to_leaderboard(player_name, stats['score'], stats['xp'], victory_type, stats['health'])
        update_player_session_stats(player_name, session_id, {"games_played": 1, "victory": 1})
    except Exception as e:
        session_logger.error(f"Error updating leaderboard or session stats: {e}")
    
    # Don't clear the game state so the player can continue
    state['victory_achieved'] = True
    save_game_state(state)
    
    return template('views/game', **template_vars)

@route('/game_over')
def game_over():
    """Display game over page"""
    session_id = get_session_id()
    session_logger = get_session_logger('game', session_id)
    
    # Get current game state
    state = get_game_state()
    
    # Default template variables
    template_vars = TEMPLATE_DEFAULTS.copy()
    
    # If no game state found, redirect to start
    if not state or 'stats' not in state:
        session_logger.warning(f"No game state found for game over page, session {session_id}")
        template_vars['show_name_input'] = True
        return template('views/game', **template_vars)
    
    # Get player info
    player_name = state.get('player_name', 'Adventurer')
    stats = state.get('stats', DEFAULT_STATS.copy())
    
    session_logger.info(f"Game over for player {player_name} with score {stats['score']}")
    
    template_vars.update({
        'message': summarize_message(f"Game Over, {player_name}! Your adventure has come to an end."),
        'show_restart': True,
        'player_name': player_name,
        'player_stats': stats,
        'previous_stats': state.get('previous_stats', stats.copy()),
        'event_type': EVENT_TYPES["GAMEOVER"]
    })
    
    # Update session stats
    try:
        update_player_session_stats(player_name, session_id, {"games_played": 1, "game_over": 1})
    except Exception as e:
        session_logger.error(f"Error updating session stats: {e}")
    
    # Clear game state for this session
    state['game_over'] = True
    save_game_state(state)
    
    return template('views/game', **template_vars)

@route('/start', method=['GET', 'POST'])
def start_game():
    """Start or restart a game"""
    session_id = get_session_id()
    session_logger = get_session_logger('game', session_id)
    
    if request.method == 'POST':
        player_name = request.forms.get('player_name', '').strip()
        session_logger.info(f"Starting new game for player: {player_name}")
        
        # Clear previous game state and start fresh
        state = {
            'player_name': player_name,
            'stats': DEFAULT_STATS.copy(),
            'previous_stats': DEFAULT_STATS.copy(),
            'events': []
        }
        
        # Save the new game state
        save_game_state(state)
        
        # Update session stats
        try:
            update_player_session_stats(player_name, session_id, {"games_played": 1})
        except Exception as e:
            session_logger.error(f"Error updating session stats: {e}")
        
        # Create template vars dictionary
        template_vars = TEMPLATE_DEFAULTS.copy()
        template_vars.update({
            'message': summarize_message(f"Hail, {player_name}! Your journey into the unknown begins...\nWhat path will you choose?"),
            'show_choices': True,
            'show_name_input': False,  # Explicitly set to False to hide the name input
            'player_name': player_name,
            'player_stats': DEFAULT_STATS.copy(),
            'previous_stats': DEFAULT_STATS.copy(),
            'event_type': EVENT_TYPES["JOURNEY_BEGIN"]
        })
        
        # Redirect directly to the game page with choices
        return template('views/game', **template_vars)
    else:
        # Show the name input form
        template_vars = TEMPLATE_DEFAULTS.copy()
        template_vars['show_name_input'] = True
        return template('views/game', **template_vars)

@route('/choice', method='POST')
def make_choice():
    """Process player choice and update game state"""
    session_id = get_session_id()
    session_logger = get_session_logger('game', session_id)
    
    # Get the current state
    state = get_game_state()
    
    # If no game state is found, redirect to start page
    if not state or 'stats' not in state:
        session_logger.warning(f"No game state found for session {session_id}")
        template_vars = TEMPLATE_DEFAULTS.copy()
        template_vars['show_name_input'] = True
        template_vars['message'] = summarize_message("Your adventure was lost in the mists of time. Please enter your name to start a new journey.")
        response.set_cookie(SESSION_COOKIE_NAME, str(random.randint(1000000, 9999999)), 
                            path=SESSION_COOKIE_PATH, httponly=SESSION_COOKIE_HTTPONLY, 
                            secure=SESSION_COOKIE_SECURE)
        return template('views/game', **template_vars)
    
    choice = request.forms.get('choice')
    
    if not choice:
        session_logger.warning("No choice provided")
        redirect('/')

    player_name = state.get('player_name', 'anonymous')
    session_logger.info(f"Player {player_name} chose: {choice}")
    
    # Get current stats
    stats = state['stats']
    
    # Base template variables
    template_vars = TEMPLATE_DEFAULTS.copy()
    template_vars['player_stats'] = stats
    template_vars['previous_stats'] = state.get('previous_stats', stats.copy())
    template_vars['player_name'] = player_name
    template_vars['show_name_input'] = False  # Explicitly set to False to hide the name input

    # Process the choice
    try:
        if choice == 'rest':
            if stats['score'] >= 10:
                health_gain = min(20, 100 - stats['health'])
                score_cost = min(10, health_gain)
                stats['health'] += health_gain
                stats['score'] -= score_cost
                template_vars.update({
                    'message': summarize_message(f"You find a cozy spot to rest and recover...\nThe peaceful moment restores {health_gain} health at the cost of {score_cost} score points.\nSometimes the wisest action is to take care of yourself buddy!"),
                    'show_choices': True,
                    'event_type': EVENT_TYPES["REST"]
                })
            else:
                template_vars.update({
                    'message': summarize_message("You search for a place to rest, but alas!\nYou need at least 10 score points to afford a safe resting spot.\nPerhaps some adventure will fill your score points jar?"),
                    'show_choices': True,
                    'event_type': EVENT_TYPES["REST_FAILED"]
                })
        
        elif choice == 'adventure':
            event = random.choice(["treasure", "monster", "trap"])
            
            if event == "monster":
                template_vars.update({
                    'message': summarize_message("A wild ugly Monster appears!\nWhat will you do now, brave adventurer? It's fight or flight!"),
                    'show_monster_choices': True,
                    'event_type': EVENT_TYPES["MONSTER"]
                })
            
            elif event == "treasure":
                template_vars.update({
                    'message': summarize_message("A local shares the location of a treasure...You can maximize XP & search alone.\nAsk local for more info  (costs 10 scorepoints)? Or just ignore the treasure and move on."),
                    'show_treasure_choices': True,
                    'event_type': EVENT_TYPES["TREASURE"]
                })
            
            elif event == "trap":
                stats['health'] -= 10
                stats['xp'] += 2
                template_vars.update({
                    'message': summarize_message("Oh no! You've stumbled into a cleverly hidden trap!\nYou lost 10 health but gained 2 XP - you're getting tougher with every mishap!"),
                    'show_choices': True,
                    'event_type': EVENT_TYPES["TRAP"]
                })

        elif choice == 'fight':
            if random.random() > 0.5:
                stats['score'] += 20
                stats['xp'] += 20
                template_vars.update({
                    'message': summarize_message("With courage in your heart and steel in your hand, you face the monster head-on...\nVICTORY! The monster falls before your might!\nYou gained 20 score points and a whopping 20 XP for your bravery!"),
                    'show_choices': True,
                    'event_type': 'combat_victory'
                })
            else:
                stats['health'] -= 20
                stats['xp'] += 5
                template_vars.update({
                    'message': summarize_message("Despite your bravery, the monster proves too strong!\nYou lost 20 health, but gained 5 XP - every battle makes you stronger!\nPerhaps next time victory will be yours!"),
                    'show_choices': True,
                    'event_type': 'combat_defeat'
                })

        elif choice == 'run':
            template_vars.update({
                'message': summarize_message("Using your quick wit and quicker feet, you make a strategic retreat!\nSometimes living to fight another day is the wisest choice.\nNothing ventured and nothing gained, but nothing lost either! As Dr honeysnow used to say."),
                'show_choices': True,
                'event_type': 'combat_escape'
            })

        elif choice == 'search_alone':
            if random.random() > 0.4:  # 60% chance of success
                stats['score'] += 25
                stats['xp'] += 25
                template_vars.update({
                    'message': summarize_message("You found the treasure by yourself! You're amazing bucko!\nYou gained 25 score points and a whopping 25 XP!"),
                    'show_choices': True,
                    'event_type': EVENT_TYPES["TREASURE_FOUND"]
                })
            else:
                stats['xp'] += 3
                template_vars.update({
                    'message': summarize_message("Despite your valiant efforts, you couldn't find the treasure...\nBut at least you gained 3 XP for trying! Never give up!"),
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
                        'message': summarize_message("With the local's help, your willingness to pay, and a little luck, you found the treasure!\nYou gained 25 score points and 10 XP!"),
                        'show_choices': True,
                        'event_type': EVENT_TYPES["TREASURE_FOUND"]
                    })
                else:
                    template_vars.update({
                        'message': summarize_message("Despite the local's help, you couldn't find the treasure...\nDon't you feel silly after paying 10 score points? At least you learned a valuable lesson!"),
                        'show_choices': True,
                        'event_type': EVENT_TYPES["TREASURE_HELP_FAILED"]
                    })
            else:
                template_vars.update({
                    'message': summarize_message("You don't have enough points to get help (need 10 points).\nPerhaps try searching alone or come back when you're score pointsricher!"),
                    'show_choices': True,
                    'event_type': EVENT_TYPES["LOCAL_UNAVAILABLE"]
                })

        elif choice == 'ignore':
            template_vars.update({
                'message': summarize_message("You decided to ignore the treasure and move on.\nSometimes the real treasure is the adventures we choose not to undertake!"),
                'show_choices': True,
                'event_type': EVENT_TYPES["TREASURE_IGNORED"]
            })

        # Save the updated game state
        state['stats'] = stats
        save_game_state(state)
        
        # Check for win condition before checking for game over
        victory_type = determine_victory_type(stats)
        if victory_type and not state.get('victory_achieved'):
            # Add to leaderboard when victory is achieved for the first time
            add_to_leaderboard(
                player_name=player_name,
                score=stats['score'],
                xp=stats['xp'],
                victory_type=victory_type,
                health=stats['health']
            )
            template_vars.update({
                'victory_type': victory_type,
                'event_type': get_event_type(victory_type),
                'message': summarize_message(f"\n{victory_type}!\n{get_victory_message(victory_type, player_name)}\n"
                          f"Final Stats - Health: {stats['health']} | Score: {stats['score']} | XP: {stats['xp']}\n\n"
                          f"You can continue playing to improve your score or restart the adventure!"),
                'show_restart': True,
                'show_choices': True,  # Allow player to continue playing
                'player_name': player_name
            })
            # Mark that victory has been achieved but don't clear the state
            state['victory_achieved'] = True
            save_game_state(state)
            return template('game', **template_vars)
        # If victory was already achieved, just continue normally
        elif victory_type and state.get('victory_achieved'):
            # Just continue with the normal game flow
            pass
        
        # Check for game over
        if stats['health'] <= 0:
            template_vars.update({
                'message': summarize_message(f"Alas, brave {player_name}, your journey has come to an end!\nThough you fell, you achieved a noble score of {stats['score']} and gained {stats['xp']} XP!\nWould you like to embark on another adventure?"),
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
            # Mark the state as game over but preserve player name
            state['game_over'] = True
            save_game_state(state)
        
        return template('game', **template_vars)

    except Exception as e:
        logger.error(f"Error processing choice: {str(e)}")
        template_vars = TEMPLATE_DEFAULTS.copy()
        template_vars.update({
            'message': summarize_message("Alas! A mysterious force disrupts your adventure!\nThe ancient scrolls speak of such anomalies...\nPlease try again, brave or perhaps recalcitrant adventurer!"),
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
    # Perform basic health checks
    health_status = {
        "status": "ok",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0",
        "db_connection": "ok"
    }
    
    # Check database connection
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        conn.close()
    except Exception as e:
        health_status["status"] = "error"
        health_status["db_connection"] = str(e)
    
    # Set appropriate status code
    response.status = 200 if health_status["status"] == "ok" else 503
    
    return health_status

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
        'message': summarize_message(f"Alas, brave {game_state['player_name']}, your journey has come to an end!\nThough you fell, you achieved a noble score of {game_state['stats']['score']} and gained {game_state['stats']['xp']} XP!\nPerhaps another adventure awaits?"),
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
    # Mark the state as game over but preserve player name
    game_state['game_over'] = True
    save_game_state(game_state)
    
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
        
        update_player_session_stats(player_name=data['player_name'], session_id=data['session_id'], stats_update=stats_update)
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

# Initialize app with middleware
app = default_app()
app.install(log_to_logger)

# Add proper error handler for 404 errors
@error(404)
def error404(error):
    """Handle 404 errors"""
    logger.warning(f"404 error: {request.url}")
    response.status = 404
    return template('error', 
                   error_code=404, 
                   title="Page Not Found", 
                   message="Sorry, the page you're looking for doesn't exist. Perhaps it was just a mirage in your adventure?")

@error(500)
def error500(error):
    """Handle 500 errors"""
    logger.error(f"500 error: {error}")
    logger.error(f"Request: {request.url}")
    
    response.status = 500
    return template('error', 
                   error_code=500, 
                   title="Server Error", 
                   message="An unexpected error has occurred. The ancient scrolls speak of such anomalies... Our wizards have been notified!")

if __name__ == "__main__":
    try:
        logger.info("Starting server...")
        run(host=HOST, port=PORT, debug=DEBUG, reloader=DEBUG)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")