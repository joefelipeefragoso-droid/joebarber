from app import create_app
from extensions import db, admin

app = create_app()

with app.test_client() as client:
    # Login as admin mock
    with client.session_transaction() as sess:
        sess['admin_logged_in'] = True
        
    print("Attempting to access SupplierPayment Create View...")
    try:
        # We need the endpoint. 'supplierpayment.create_view'
        # The URL usually defaults to /admin/supplierpayment/new/
        resp = client.get('/admin/supplierpayment/new/')
        print(f"Status Code: {resp.status_code}")
        if resp.status_code != 200:
            print("Error content:")
            print(resp.data.decode('utf-8')[:500])
        else:
            print("Success! Page loaded.")
            
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()
