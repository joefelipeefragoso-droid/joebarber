
import sqlite3
import os

# Path to the database
db_paths = ['instance/barber.db', 'barber.db']

def migrate_expenses():
    connected = False
    for path in db_paths:
        if os.path.exists(path):
            print(f"Connecting to database at {path}...")
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            try:
                # Create Expense table
                print("Creating Expense table...")
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS expense (
                        id INTEGER PRIMARY KEY,
                        description VARCHAR(200) NOT NULL,
                        amount FLOAT NOT NULL,
                        category VARCHAR(50),
                        date DATE
                    )
                ''')
            except sqlite3.OperationalError as e:
                print(f"Error creating Expense table: {e}")
            
            conn.commit()
            conn.close()
            print(f"Migration completed for {path}.")
            connected = True
            
    if not connected:
        print("No database file found to migrate.")

if __name__ == "__main__":
    migrate_expenses()
