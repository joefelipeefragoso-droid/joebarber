from app import create_app
from extensions import db
from models import Supplier, SupplierPayment

app = create_app()

with app.app_context():
    print("Creating Supplier tables...")
    try:
        db.create_all() # This only creates tables that don't exist
        print("Tables 'supplier' and 'supplier_payment' created successfully.")
    except Exception as e:
        print(f"Error creating tables: {e}")
