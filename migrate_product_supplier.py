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
                    cursor.execute("ALTER TABLE product ADD COLUMN cost_price FLOAT DEFAULT 0.0")
                    print("Added cost_price.")
                except Exception as e:
                    print(f"cost_price error: {e}")

                try:
                    cursor.execute("ALTER TABLE product ADD COLUMN supplier_id INTEGER REFERENCES supplier(id)")
                    print("Added supplier_id.")
                except Exception as e:
                    print(f"supplier_id error: {e}")
                
                conn.commit()
                conn.close()

if __name__ == "__main__":
    migrate()
