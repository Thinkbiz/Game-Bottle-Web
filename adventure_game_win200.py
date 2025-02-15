import random
import sys
import sqlite3
from datetime import datetime

print("Script is starting...", flush=True)

VERSION = "Alpha 1.0"

# Victory type constants
VICTORY_TYPES = {
    "PERFECT": "Perfect Victory",
    "GLORIOUS": "Glorious Victory",
    "PYRRHIC": "Pyrrhic Victory",
    "STANDARD": "Standard Victory"
}

def init_leaderboard():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('DROP TABLE IF EXISTS leaderboard')
    c.execute('''
        CREATE TABLE IF NOT EXISTS leaderboard
        (id INTEGER PRIMARY KEY AUTOINCREMENT,
         player_name TEXT,
         score INTEGER,
         xp INTEGER,
         victory_type TEXT,
         health INTEGER,
         date TIMESTAMP DEFAULT CURRENT_TIMESTAMP)
    ''')
    conn.commit()
    conn.close()

def add_to_leaderboard(player_name: str, score: int, xp: int, victory_type: str, health: int):
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''
        INSERT INTO leaderboard (player_name, score, xp, victory_type, health)
        VALUES (?, ?, ?, ?, ?)
    ''', (player_name, score, xp, victory_type, health))
    conn.commit()
    conn.close()

def show_leaderboard():
    conn = sqlite3.connect('game.db')
    c = conn.cursor()
    c.execute('''
        SELECT player_name, score, xp, victory_type, health, date
        FROM leaderboard
        ORDER BY score DESC, xp DESC
        LIMIT 10
    ''')
    entries = c.fetchall()
    conn.close()

    # Add Victory Types Legend first
    print("\n=== VICTORY TYPES EXPLANATION ===")
    print_victory_conditions()
    
    # Add a separator
    print("\n" + "=" * 60)

    # Then show the leaderboard
    print("=== ADVENTURE GAME LEADERBOARD ===")
    print("Rank  Player          Score  XP    Victory Type      Health  Date")
    print("-" * 60)
    for i, (name, score, xp, victory_type, health, date) in enumerate(entries, 1):
        date_str = datetime.fromisoformat(date).strftime('%Y-%m-%d %H:%M')
        print(f"{i:<5} {name:<15} {score:<6} {xp:<5} {victory_type:<15} {health:<6} {date_str}")

def print_victory_conditions():
    """Print the conditions for each victory type"""
    print("\nVictory Conditions:")
    print(f"{VICTORY_TYPES['PERFECT']}  : Health > 80, Score > 50, XP ≥ 200")
    print(f"{VICTORY_TYPES['GLORIOUS']}: Health > 50, XP ≥ 200")
    print(f"{VICTORY_TYPES['PYRRHIC']} : Health ≤ 20, XP ≥ 200")
    print(f"{VICTORY_TYPES['STANDARD']}: XP ≥ 200")

def determine_victory_type(stats):
    """Determine victory type based on final stats"""
    if stats['xp'] >= 200:
        if stats['health'] > 80 and stats['score'] > 50:
            return VICTORY_TYPES["PERFECT"]
        elif stats['health'] > 50:
            return VICTORY_TYPES["GLORIOUS"]
        elif stats['health'] <= 20:
            return VICTORY_TYPES["PYRRHIC"]
        else:
            return VICTORY_TYPES["STANDARD"]
    return None

def get_victory_color(victory_type):
    """Get the color code for each victory type"""
    if victory_type == VICTORY_TYPES["PERFECT"]:
        return "\033[1;36m"  # Cyan
    elif victory_type == VICTORY_TYPES["GLORIOUS"]:
        return "\033[1;32m"  # Green
    elif victory_type == VICTORY_TYPES["PYRRHIC"]:
        return "\033[1;31m"  # Red
    return "\033[1;33m"  # Yellow for Standard

def main():
    init_leaderboard()  # Initialize leaderboard table
    print(f"Adventure Game v{VERSION} starting...", flush=True)
    print("Welcome to Danny's Python Text Adventure!")
    
    while True:
        print("\n1. Start New Game")
        print("2. View Leaderboard")
        print("3. Quit")
        choice = input("Choose an option (1-3): ")
        
        if choice == '1':
            play_game()
        elif choice == '2':
            show_leaderboard()
        elif choice == '3':
            print("Thanks for playing!")
            break
        else:
            print("Invalid choice. Please choose 1-3.")

def play_game():
    player_name = input("What's your name, adventurer? ")
    print(f"Welcome, {player_name}! Your journey begins...")

    health = 100
    score = 0
    xp = 0

    while health > 0:
        print(f"\n--- New Turn for {player_name} ---")
        print(f"{player_name}'s Health: {health} | Score: {score} | XP: {xp}")
        
        # Check for win condition
        victory_type = determine_victory_type({'health': health, 'score': score, 'xp': xp})
        if victory_type:
            print(f"\n{get_victory_color(victory_type)}{victory_type}!")
            if victory_type == VICTORY_TYPES["PERFECT"]:
                print(f"Incredible, {player_name}! You've mastered the game with style and grace!")
            elif victory_type == VICTORY_TYPES["GLORIOUS"]:
                print(f"Well done, {player_name}! A truly heroic victory!")
            elif victory_type == VICTORY_TYPES["PYRRHIC"]:
                print(f"Against all odds, {player_name}, you've achieved victory at great cost!")
            else:
                print(f"Congratulations, {player_name}! You've mastered the game!")
            
            print(f"Final Stats - Health: {health} | Score: {score} | XP: {xp}")
            
            # Add to leaderboard
            add_to_leaderboard(player_name, score, xp, victory_type, health)
            
            # Show the leaderboard after victory
            show_leaderboard()
            return
        
        # Add rest option
        action = input("Do you want to (a)dventure or (r)est? ").lower()
        
        if action == 'r':
            if score >= 10:
                health_gain = min(20, 100 - health)  # Cap health at 100
                score_cost = health_gain  # 1 health point per 1 score point
                health += health_gain
                score -= score_cost
                print(f"You rested and gained {health_gain} health at the cost of {score_cost} score points.")
            else:
                print("You don't have enough score points to rest.")
            continue
        
        # Random event
        event = random.choice(["treasure", "monster", "trap"])
        
        if event == "treasure":
            print(f"{player_name}, you have learned about a treasure chest from a local in town!")
            while True:  # Keep asking until valid input is received
                if score >= 10:
                    treasure_choice = input("Do you want to maximize your XP and (s)earch alone, OR get (h)elp from a local and earn all the points but less XP (costs 10 points), or play it silly and completely ignore the treasure (i)gnore? ").lower()
                else:
                    treasure_choice = input("Do you want to (s)earch alone or (i)gnore? ").lower()
                
                if treasure_choice == 's':
                    if random.random() > 0.4:  # 60% chance of success alone
                        print("You found the treasure by yourself! You're amazing bucko!")
                        score += 25
                        xp += 25
                        print("You gained 25 points and a whopping 25 XP!")
                    else:
                        print("Despite searching, you couldn't find the treasure...")
                        xp += 3  # Award 3 XP for the attempt
                        print("But at least You gained 3 XP for your efforts! Never give up!")
                    break
                
                elif treasure_choice == 'h' and score >= 10:
                    score -= 10  # Pay the local
                    if random.random() > 0.2:  # 80% chance with help
                        print("With the local's help, your willingness to pay, and a little luck, you found the treasure!")
                        score += 25
                        xp += 10
                        print("You gained 25 points and 10 XP!")
                    else:
                        print("Despite the local's help, you couldn't find the treasure... dont you feel silly after paying 10 points?")
                    break
                
                elif treasure_choice == 'i':
                    print("You decided to ignore the treasure clue and move on.")
                    break
                
                else:
                    if score >= 10:
                        print("Invalid choice! Please enter 's' to search alone, 'h' for help, or 'i' to ignore.")
                    else:
                        print("Invalid choice! Please enter 's' to search alone or 'i' to ignore.")
        
        elif event == "monster":
            print("A wild ugly Monster appears!")
            fight_choice = input("Do you want to fight (f) or run (r)? ").lower()
            if fight_choice == 'f':
                if random.random() > 0.5:
                    print("You defeated the monster!")
                    score += 20
                    xp += 20  # Gain XP for defeating monster
                    print("You gained 20 points and a whopping 20 XP!")
                else:
                    print("The monster hurt you!")
                    health -= 20
                    xp += 5  # Moderate gain XP gain for surviving monster damage
                    print("You lost 20 health but gained 5 XP, you're tough!")
            else:
                print("You ran away safely nothing ventured and nothing gained!")
        
        elif event == "trap":
            print("You encountered a trap!")
            health -= 10
            xp += 2  # Small XP gain for surviving trap
            print("You lost 10 health but gained 2 XP, you're tough!")
        
        # Ask to continue
        if health > 0:
            while True:
                continue_choice = input("Do you want to continue your adventure? (y/n/yes/no) ").lower().strip()
                if continue_choice in ['y', 'yes']:
                    break  # Continue the game
                elif continue_choice in ['n', 'no']:
                    return  # End the game
                else:
                    print("Invalid input. Please enter 'y', 'n', 'yes', or 'no'.")

        # Give player chance to rest if they have score points
        while health <= 0 and score > 0:
            print(f"\n{player_name}, you're critically wounded! But you might be able to rest...")
            print(f"Current Stats - Health: {health} | Score: {score} | XP: {xp}")
            rest_choice = input("Would you like to rest and recover health using your score points? (y/n) ").lower()
            
            if rest_choice == 'y':
                health_gain = min(20, 100 - health)  # Cap health at 100
                score_cost = health_gain  # 1 health point per 1 score point
                
                if score >= score_cost:
                    health += health_gain
                    score -= score_cost
                    print(f"You rested and gained {health_gain} health at the cost of {score_cost} score points.")
                    if health > 0:
                        break  # Exit this recovery loop
                else:
                    print("You don't have enough score points to rest effectively.")
                    break
            else:
                break

    # Only show game over if health is still 0 or negative
    if health <= 0:
        print(f"\nGame Over, {player_name}! You died with {xp} XP and {score} points!")
        add_to_leaderboard(player_name, score, xp, "DIED", health)
        show_leaderboard()
        return

if __name__ == "__main__":
    main()

print("Script has finished.", flush=True)
