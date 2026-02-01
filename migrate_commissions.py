
import sqlite3
import os

# Path to the database
db_paths = ['instance/barber.db', 'barber.db']

def migrate():
    connected = False
    for path in db_paths:
        if os.path.exists(path):
            print(f"Connecting to database at {path}...")
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            try:
                # Add commission_paid
                print("Adding commission_paid column...")
                cursor.execute("ALTER TABLE sale ADD COLUMN commission_paid BOOLEAN DEFAULT 0")
            except sqlite3.OperationalError as e:
                print(f"Error adding commission_paid (might already exist): {e}")

            conn.commit()
            conn.close()
            print(f"Migration completed for {path}.")
            connected = True
            
    if not connected:
        print("No database file found to migrate.")

if __name__ == "__main__":
    migrate()
