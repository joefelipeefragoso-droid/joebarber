from app import create_app
from extensions import db
import sqlite3
import os

app = create_app()

db_paths = ['instance/barber.db', 'barber.db']

def migrate():
    with app.app_context():
        for path in db_paths:
            if os.path.exists(path):
                print(f"Migrating {path}...")
                conn = sqlite3.connect(path)
                cursor = conn.cursor()
                
                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN collaborator_id INTEGER REFERENCES collaborator(id)")
                    print("Added collaborator_id.")
                except Exception as e:
                    print(f"collaborator_id error: {e}")

                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN commission_fixed_value FLOAT DEFAULT 0.0")
                    print("Added commission_fixed_value.")
                except Exception as e:
                    print(f"commission_fixed_value error: {e}")

                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN quantity INTEGER DEFAULT 0")
                    print("Added quantity.")
                except Exception as e:
                    print(f"quantity error: {e}")
                
                conn.commit()
                conn.close()

if __name__ == "__main__":
    migrate()
