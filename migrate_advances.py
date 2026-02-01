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
                    cursor.execute("ALTER TABLE cash_advance ADD COLUMN payment_record_id INTEGER REFERENCES payment_record(id)")
                    print("Added payment_record_id to cash_advance.")
                except Exception as e:
                    print(f"payment_record_id error (likely exists): {e}")

                conn.commit()
                conn.close()

if __name__ == "__main__":
    migrate()
