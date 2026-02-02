from app import create_app
from extensions import db
from models import Collaborator

app = create_app()

def debug_login_security():
    with app.app_context():
        print("--- DEBUGGING LOGIN SECURITY ---")
        
        # 1. List all Owners
        owners = Collaborator.query.filter_by(is_owner=True).all()
        print(f"Found {len(owners)} owner accounts.")
        
        if not owners:
            print("CRITICAL: No owner found! Creating one...")
            # Create a backup owner if none exists
            new_owner = Collaborator(name="Admin Backup", is_owner=True, active=True)
            db.session.add(new_owner)
            db.session.commit()
            owners = [new_owner]
            
        # 2. Reset Password for ALL owners
        new_password = "JoeFelipe@2026"
        print(f"Resetting password for all owners to: {new_password}")
        
        for owner in owners:
            print(f"Updating Owner: {owner.name} (ID: {owner.id})")
            owner.set_password(new_password)
            
            # 3. VERIFY immediately
            if owner.check_password(new_password):
                 print(f"   [OK] Password check PASSED for {owner.name}")
            else:
                 print(f"   [FAIL] Password check FAILED for {owner.name}")
        
        db.session.commit()
        print("--- COMMIT COMPLETE ---")
        
        # 4. Double Check after commit
        print("Double checking from DB...")
        for owner in owners:
             refreshed_owner = Collaborator.query.get(owner.id)
             if refreshed_owner.check_password(new_password):
                 print(f"   [FINAL CHECK] Login should work for: {refreshed_owner.name} with '{new_password}'")
             else:
                 print(f"   [FINAL CHECK] FAILED for {refreshed_owner.name}")

if __name__ == "__main__":
    debug_login_security()
