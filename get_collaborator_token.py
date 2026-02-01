from app import create_app
from models import Collaborator
from extensions import db
import secrets

app = create_app()

with app.app_context():
    collab = Collaborator.query.first()
    if not collab:
        print("No collaborator found. Creating one...")
        token = secrets.token_urlsafe(16)
        collab = Collaborator(name="Barbeiro Exemplo", token=token)
        db.session.add(collab)
        db.session.commit()
    
    print(f"Collaborator: {collab.name}")
    print(f"Token: {collab.token}")
    print(f"Link: http://localhost:5000/login/{collab.token}")
