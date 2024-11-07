from bottle import route, run, template, static_file, request, redirect
import random
from database import GameState, init_db, add_to_leaderboard, get_leaderboard

print("Starting imports...", flush=True)  # Debug print

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

# Store current game state in memory (for prototype)
current_game_state = {}

print("Defining routes...", flush=True)  # Debug print

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

@route('/')
def game():
    print("Handling root route", flush=True)  # Debug print
    template_vars = TEMPLATE_DEFAULTS.copy()
    template_vars.update({
        'message': "Welcome to the Adventure Game! Please enter your name to begin.",
        'show_name_input': True
    })
    return template('game', **template_vars)

@route('/choice', method='POST')
def make_choice():
    choice = request.forms.get('choice')
    template_vars = TEMPLATE_DEFAULTS.copy()
    stats = current_game_state['stats']
    player_name = current_game_state.get('player_name', 'Adventurer')
    
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
                'show_monster_choices': True
            })
        
        elif event == "treasure":
            template_vars.update({
                'message': "You have learned about a treasure chest from a local in town!",
                'show_treasure_choices': True
            })
        
        elif event == "trap":
            stats['health'] -= 10
            stats['xp'] += 2
            template_vars.update({
                'message': "You encountered a trap!\nYou lost 10 health but gained 2 XP, you're tough!",
                'show_choices': True
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
            victory_type=victory_type
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
        current_game_state.clear()  # Reset game state
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
        current_game_state.clear()  # Reset game state
    
    return template('game', **template_vars)

@route('/static/<filename>')
def serve_static(filename):
    # Try the ./static directory first
    response = static_file(filename, root='./static')
    if response.status_code == 404:
        # If not found, try the views/static directory
        response = static_file(filename, root='./views/static')
    return response

@route('/start', method='POST')
def start_game():
    player_name = request.forms.get('player_name')
    template_vars = TEMPLATE_DEFAULTS.copy()
    
    if player_name:
        # Initialize player stats
        current_game_state['stats'] = DEFAULT_STATS.copy()
        current_game_state['player_name'] = player_name
        
        template_vars.update({
            'message': f"Welcome, {player_name}! Your journey begins...",
            'show_choices': True,
            'player_name': player_name,
            'player_stats': current_game_state['stats']
        })
    else:
        template_vars.update({
            'message': "Please enter your name to begin.",
            'show_name_input': True
        })
    
    return template('game', **template_vars)

@route('/leaderboard')
def show_leaderboard():
    leaderboard_entries = get_leaderboard(10)  # Get top 10
    return template('leaderboard', entries=leaderboard_entries)

if __name__ == "__main__":
    try:
        print("Starting server...", flush=True)  # Debug print
        run(host='127.0.0.1', port=8000, debug=True)
    except Exception as e:
        print(f"Error starting server: {str(e)}", flush=True)  # Debug print 