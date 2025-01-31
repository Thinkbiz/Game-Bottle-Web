from bottle import route, run, template, static_file, request, redirect, response, default_app
import random
from database import init_db, add_to_leaderboard, get_leaderboard
import json
import os
from google.oauth2 import id_token
from google.auth.transport import requests
from datetime import datetime
import logging
import sys

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

# Add request logging middleware
def log_to_logger(fn):
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

# Session handling
def get_session_id():
    session_id = request.cookies.get('session_id')
    if not session_id:
        session_id = str(random.randint(1000000, 9999999))
        response.set_cookie('session_id', session_id, path='/')
    return session_id

# Game state storage - separate for each session
game_states = {}

def get_game_state():
    session_id = get_session_id()
    logger.debug(f"Getting game state for session {session_id}")
    return game_states.get(session_id, {})

def save_game_state(state):
    session_id = get_session_id()
    logger.debug(f"Saving game state for session {session_id}")
    game_states[session_id] = state

# Initialize database
init_db()

# Default template variables
TEMPLATE_DEFAULTS = {
    'show_name_input': False,
    'show_choices': False,
    'show_monster_choices': False,
    'show_treasure_choices': False,
    'message': '',
    'player_stats': None
}

# Initialize player stats
DEFAULT_STATS = {
    'health': 100,
    'score': 0,
    'xp': 0
}

@route('/')
def game():
    logger.debug("Handling root route")
    template_vars = TEMPLATE_DEFAULTS.copy()
    game_state = get_game_state()
    
    if game_state.get('player_name'):
        template_vars.update({
            'message': f"Welcome back, {game_state['player_name']}!",
            'show_choices': True,
            'player_stats': game_state.get('stats')
        })
    else:
        template_vars.update({
            'message': "Welcome to the Adventure Game! Please enter your name to begin.",
            'show_name_input': True
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
            'message': f"Welcome, {player_name}! Your journey begins...",
            'show_choices': True,
            'player_name': player_name,
            'player_stats': game_state['stats']
        })
    else:
        template_vars.update({
            'message': "Please enter a valid name to begin.",
            'show_name_input': True
        })
    
    return template('game', **template_vars)

def check_victory_type(stats):
    if stats['xp'] >= 200:
        if stats['health'] > 80 and stats['score'] > 50:
            return "PERFECT VICTORY"
        elif stats['health'] > 50:
            return "GLORIOUS VICTORY"
        elif stats['health'] <= 20:
            return "PYRRHIC VICTORY"
        else:
            return "STANDARD VICTORY"
    return None

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
        player_name = game_state.get('player_name', 'Adventurer')
        
        logger.debug(f"Player {player_name} made choice: {choice}")
        
        if choice == 'rest':
            if stats['score'] >= 10:
                health_gain = min(20, 100 - stats['health'])  # Cap health at 100
                score_cost = min(10, health_gain)  # Only deduct what was actually healed
                stats['health'] += health_gain
                stats['score'] -= score_cost
                template_vars.update({
                    'message': f"You rested and gained {health_gain} health at the cost of {score_cost} score points.",
                    'show_choices': True
                })
            else:
                template_vars.update({
                    'message': "You don't have enough score points to rest (need 10 points).",
                    'show_choices': True
                })
        
        elif choice == 'adventure':
            event = random.choice(["treasure", "monster", "trap"])
            
            if event == "monster":
                template_vars.update({
                    'message': "A wild ugly Monster appears!",
                    'show_monster_choices': True,
                    'event_type': 'monster'
                })
            
            elif event == "treasure":
                template_vars.update({
                    'message': "You have learned about a treasure chest from a local in town!",
                    'show_treasure_choices': True,
                    'event_type': 'treasure'
                })
            
            elif event == "trap":
                stats['health'] -= 10
                stats['xp'] += 2
                template_vars.update({
                    'message': "You encountered a trap!\nYou lost 10 health but gained 2 XP, you're tough!",
                    'show_choices': True,
                    'event_type': 'trap'
                })

        elif choice == 'fight':
            if random.random() > 0.5:
                stats['score'] += 20
                stats['xp'] += 20
                template_vars.update({
                    'message': "You defeated the monster!\nYou gained 20 points and a whopping 20 XP!",
                    'show_choices': True
                })
            else:
                stats['health'] -= 20
                stats['xp'] += 5
                template_vars.update({
                    'message': "The monster hurt you!\nYou lost 20 health but gained 5 XP, you're tough!",
                    'show_choices': True
                })

        elif choice == 'run':
            template_vars.update({
                'message': "You ran away safely! Nothing ventured and nothing gained!",
                'show_choices': True
            })

        elif choice == 'search_alone':
            if random.random() > 0.4:  # 60% chance of success
                stats['score'] += 25
                stats['xp'] += 25
                template_vars.update({
                    'message': "You found the treasure by yourself! You gained 25 points and 25 XP!",
                    'show_choices': True
                })
            else:
                stats['xp'] += 3
                template_vars.update({
                    'message': "Despite searching, you couldn't find the treasure... But you gained 3 XP for trying!",
                    'show_choices': True
                })

        elif choice == 'get_help':
            template_vars.update({
                'event_type': 'local'
            })
            if stats['score'] >= 10:
                stats['score'] -= 10
                if random.random() > 0.2:
                    stats['score'] += 25
                    stats['xp'] += 10
                    template_vars.update({
                        'message': "With the local's help, you found the treasure! You gained 25 points and 10 XP!",
                        'show_choices': True
                    })
                else:
                    template_vars.update({
                        'message': "Despite the local's help, you couldn't find the treasure... And you lost 10 points!",
                        'show_choices': True
                    })
            else:
                template_vars.update({
                    'message': "You don't have enough points to get help (need 10 points).",
                    'show_choices': True
                })

        elif choice == 'ignore':
            template_vars.update({
                'message': "You decided to ignore the treasure and move on.",
                'show_choices': True
            })

        # Save the updated game state
        game_state['stats'] = stats
        save_game_state(game_state)
        
        # Add stats to template variables
        template_vars['player_stats'] = stats
        
        # Check for win condition before checking for game over
        victory_type = check_victory_type(stats)
        if victory_type:
            # Add to leaderboard when victory is achieved
            add_to_leaderboard(
                player_name=player_name,
                score=stats['score'],
                xp=stats['xp'],
                victory_type=victory_type,
                health=stats['health']
            )
            victory_messages = {
                "PERFECT VICTORY": f"Incredible, {player_name}! You've mastered the game with style and grace!",
                "GLORIOUS VICTORY": f"Well done, {player_name}! A truly heroic victory!",
                "PYRRHIC VICTORY": f"Against all odds, {player_name}, you've achieved victory at great cost!",
                "STANDARD VICTORY": f"Congratulations, {player_name}! You've mastered the game!"
            }
            template_vars.update({
                'victory_type': victory_type,
                'message': f"\n{victory_type}!\n{victory_messages[victory_type]}\n"
                          f"Final Stats - Health: {stats['health']} | Score: {stats['score']} | XP: {stats['xp']}",
                'show_name_input': True  # Allow restart
            })
            game_states.pop(get_session_id(), None)  # Clear game state
            return template('game', **template_vars)
        
        # Check for game over
        if stats['health'] <= 0:
            template_vars.update({
                'message': f"Game Over! Your final score: {stats['score']}, XP: {stats['xp']}",
                'show_name_input': True  # Allow restart
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
            'message': "An error occurred. Please try again.",
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

# Create the application
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
        run(host=HOST, port=PORT, debug=DEBUG)
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")