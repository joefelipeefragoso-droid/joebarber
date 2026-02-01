
import sqlite3
import os

db_path = os.path.join('instance', 'barber.db')

def migrate_owner():
    if os.path.exists(db_path):
        print(f"Connecting to {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            print("Adding is_owner column to collaborator...")
            cursor.execute("ALTER TABLE collaborator ADD COLUMN is_owner BOOLEAN DEFAULT 0")
            print("Column added.")
        except sqlite3.OperationalError as e:
            print(f"Error (column likely exists): {e}")
            
        conn.commit()
        conn.close()
        print("Migration finished.")
    else:
        print("DB not found.")

if __name__ == "__main__":
    migrate_owner()
