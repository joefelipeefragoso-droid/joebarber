
import sqlite3
import os

# Path to the database
# Depending on where the app runs, it might be in 'instance/barber.db' or just 'barber.db'
# We check both to be safe
db_paths = ['instance/barber.db', 'barber.db']

def migrate():
    connected = False
    for path in db_paths:
        if os.path.exists(path):
            print(f"Connecting to database at {path}...")
            conn = sqlite3.connect(path)
            cursor = conn.cursor()
            
            try:
                # Add client_name
                print("Adding client_name column...")
                cursor.execute("ALTER TABLE sale ADD COLUMN client_name VARCHAR(100)")
            except sqlite3.OperationalError as e:
                print(f"Error adding client_name (might already exist): {e}")

            try:
                # Add payment_method
                print("Adding payment_method column...")
                cursor.execute("ALTER TABLE sale ADD COLUMN payment_method VARCHAR(50) DEFAULT 'Dinheiro'")
            except sqlite3.OperationalError as e:
                print(f"Error adding payment_method (might already exist): {e}")
            
            conn.commit()
            conn.close()
            print(f"Migration completed for {path}.")
            connected = True
            
    if not connected:
        print("No database file found to migrate.")

if __name__ == "__main__":
    migrate()
