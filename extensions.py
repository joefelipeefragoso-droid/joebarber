from flask_sqlalchemy import SQLAlchemy
from flask_admin import Admin

# Initialize extensions here to avoid circular imports and dual-instance issues
db = SQLAlchemy()
admin = Admin(name='Barbearia JoeFelipe')
