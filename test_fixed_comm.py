from app import create_app
from extensions import db
from models import Product, Collaborator, Sale, SaleItem, Supplier
import datetime

app = create_app()

with app.app_context():
    # Setup Data
    print("Setting up test data...")
    
    # 1. Create Supplier
    supp = Supplier.query.filter_by(name="TestSupplier").first()
    if not supp:
        supp = Supplier(name="TestSupplier")
        db.session.add(supp)
        db.session.commit()
        
    # 2. Create Collaborator
    collab = Collaborator.query.filter_by(name="BarberFixed").first()
    if not collab:
        collab = Collaborator(name="BarberFixed")
        collab.set_password("123")
        collab.active = True
        collab.is_owner = False
        import uuid
        collab.token = str(uuid.uuid4())
        db.session.add(collab)
    db.session.commit()
    
    # 3. Create Product with Fixed Commission
    prod = Product.query.filter_by(name="FixedComb").first()
    if prod:
        db.session.delete(prod)
        db.session.commit()
        
    prod = Product(
        name="FixedComb",
        price=50.0,
        cost_price=20.0,
        commission_fixed_value=5.0, # 5 Reais fixed
        quantity=10,
        supplier_id=supp.id,
        collaborator_id=collab.id # Linked to BarberFixed
    )
    db.session.add(prod)
    db.session.commit()
    print(f"Created Product: {prod.name}, Stock: {prod.quantity}, Fixed Comm: {prod.commission_fixed_value}")

    # 4. Simulate Sale by BarberFixed (Logged in)
    with app.test_request_context():
        # Mock Session logic manually or call logic function?
        # Let's hit the route logic directly or replicate it to verify the Core Logic.
        # Actually I can't easily mock session in a script without test_client.
        # I'll use test_client.
        
        pass

with app.test_client() as client:
    with client.session_transaction() as sess:
        # Get ID back
        with app.app_context():
            c = Collaborator.query.filter_by(name="BarberFixed").first()
            p = Product.query.filter_by(name="FixedComb").first()
            pid = p.id
            cid = c.id
        
        sess['collab_id'] = cid
        sess['collab_name'] = "BarberFixed"
    
    # Send Post Request
    payload = {
        'client_name': 'Test Client',
        'payment_method': 'Dinheiro',
        'items': [
            {'type': 'product', 'id': pid}
        ]
    }
    
    print("Sending Sale Request...")
    resp = client.post('/sale/new', json=payload)
    print(f"Response: {resp.status_code}, {resp.json}")
    
    # Verify
    with app.app_context():
        # Check Stock
        p_refresh = Product.query.get(pid)
        print(f"New Stock: {p_refresh.quantity} (Expected 9)")
        
        # Check Sale
        last_sale = Sale.query.filter_by(collaborator_id=cid).order_by(Sale.id.desc()).first()
        print(f"Sale Total Comm: {last_sale.total_commission} (Expected 5.0)")
        
        item = SaleItem.query.filter_by(sale_id=last_sale.id).first()
        print(f"Item Comm: {item.commission} (Expected 5.0)")
        
        if p_refresh.quantity == 9 and item.commission == 5.0:
            print("TEST PASSED!")
        else:
            print("TEST FAILED!")
