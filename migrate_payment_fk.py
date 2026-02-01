from app import create_app
from extensions import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    print("Migrating Database...")
    try:
        # SQLite doesn't support adding FK constraints easily with ALTER TABLE in old versions,
        # but adding a nullable column works fine.
        with db.engine.connect() as conn:
            conn.execute(text("ALTER TABLE sale ADD COLUMN payment_record_id INTEGER REFERENCES payment_record(id)"))
            conn.commit()
        print("Column 'payment_record_id' added successfully.")
    except Exception as e:
        print(f"Migration failed (might already exist): {e}")
