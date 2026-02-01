
import sqlite3
import os

# Path to the database
db_path = os.path.join('instance', 'barber.db')

def migrate():
    if os.path.exists(db_path):
        print(f"Connecting to database at {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Add password_hash
            print("Adding password_hash column...")
            cursor.execute("ALTER TABLE collaborator ADD COLUMN password_hash VARCHAR(128)")
        except sqlite3.OperationalError as e:
            print(f"Error adding password_hash (might already exist): {e}")

        conn.commit()
        conn.close()
        print(f"Migration completed for {db_path}.")
    else:
        print(f"No database file found at {db_path}.")

if __name__ == "__main__":
    migrate()
