import sqlite3
import os

def check_database():
    print("\nChecking database setup...")
    
    # Check if database file exists
    if os.path.exists('game.db'):
        print("✓ game.db file exists")
    else:
        print("✗ game.db file not found")
        return
    
    try:
        # Connect to the database
        conn = sqlite3.connect('game.db')
        print("✓ Successfully connected to database")
        
        c = conn.cursor()
        
        # Get list of tables
        c.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = c.fetchall()
        
        if tables:
            print("\nTables found:")
            for table in tables:
                print(f"\n- {table[0]}:")
                # Get schema for this table
                c.execute(f"PRAGMA table_info({table[0]});")
                columns = c.fetchall()
                for col in columns:
                    print(f"  • {col[1]} ({col[2]})")
                
                # Get row count
                c.execute(f"SELECT COUNT(*) FROM {table[0]}")
                count = c.fetchone()[0]
                print(f"  → Contains {count} records")
        else:
            print("✗ No tables found in database")
        
        conn.close()
        print("\nDatabase check completed!")
        
    except sqlite3.Error as e:
        print(f"\n✗ SQLite error occurred: {e}")
    except Exception as e:
        print(f"\n✗ An error occurred: {e}")

if __name__ == "__main__":
    check_database() 