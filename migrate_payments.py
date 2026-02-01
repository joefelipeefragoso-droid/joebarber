
import sqlite3
import os

# Path to the database
db_path = os.path.join('instance', 'barber.db')

def migrate():
    if os.path.exists(db_path):
        print(f"Connecting to database at {db_path}...")
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Cash Advance Table
        try:
            print("Creating cash_advance table...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS cash_advance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collaborator_id INTEGER NOT NULL,
                amount FLOAT NOT NULL,
                description VARCHAR(200),
                date DATE,
                is_paid BOOLEAN DEFAULT 0,
                FOREIGN KEY(collaborator_id) REFERENCES collaborator(id)
            )
            """)
        except sqlite3.OperationalError as e:
            print(f"Error creating cash_advance: {e}")

        # Payment Record Table
        try:
            print("Creating payment_record table...")
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS payment_record (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                collaborator_id INTEGER NOT NULL,
                date DATETIME,
                start_date DATE,
                end_date DATE,
                total_commission FLOAT DEFAULT 0.0,
                total_advances FLOAT DEFAULT 0.0,
                net_amount FLOAT DEFAULT 0.0,
                admin_name VARCHAR(100) DEFAULT 'Administrador',
                FOREIGN KEY(collaborator_id) REFERENCES collaborator(id)
            )
            """)
        except sqlite3.OperationalError as e:
            print(f"Error creating payment_record: {e}")

        conn.commit()
        conn.close()
        print(f"Migration completed for {db_path}.")
    else:
        print(f"No database file found at {db_path}.")

if __name__ == "__main__":
    migrate()
