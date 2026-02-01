from flask import Flask
from extensions import db, admin
import os

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = 'dev-secret-key-change-in-production'
    # Use SQLite for now, easy to switch to MySQL
    basedir = os.path.abspath(os.path.dirname(__file__))
    db_path = os.path.join(basedir, 'instance', 'barber.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize extensions with app
    # Initialize extensions with app
    db.init_app(app)
    
    # Initialize Babel for translations
    from flask_babel import Babel
    
    def get_locale():
        return 'pt_BR'
        
    babel = Babel(app, locale_selector=get_locale)

    # We will initialize admin views in admin_panel.py to avoid circular imports, 
    # but for now let's just init the object.
    admin.init_app(app)

    with app.app_context():
        # Import models to ensure they are registered
        from models import User, Collaborator, Service, Product, Sale, SaleItem
        
        # Import routes
        from routes import main_bp
        app.register_blueprint(main_bp)

        # Initialize Admin Views
        from admin_panel import init_admin
        init_admin(admin)

        # Create DB tables
        db.create_all()

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
