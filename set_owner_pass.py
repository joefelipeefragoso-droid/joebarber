from app import create_app
from extensions import db
from models import Collaborator
import sys

app = create_app()

def set_owner_password(password):
    with app.app_context():
        # Find Owner
        owner = Collaborator.query.filter_by(is_owner=True).first()
        
        if not owner:
            print("Nenhum proprietário encontrado. Procurando primeiro colaborador...")
            owner = Collaborator.query.first()
            if owner:
                print(f"Promovendo {owner.name} a Proprietário.")
                owner.is_owner = True
            else:
                print("ERRO: Nenhum colaborador encontrado. Crie um colaborador primeiro.")
                return

        owner.set_password(password)
        db.session.commit()
        print(f"SUCESSO: Senha definida para o proprietário: {owner.name}")
        print(f"Senha: {password}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        pwd = sys.argv[1]
    else:
        pwd = "JoeFelipe@2026" # Default Strong Password
    
    set_owner_password(pwd)
