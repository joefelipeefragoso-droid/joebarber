from extensions import db
from datetime import datetime

class User(db.Model):
    """Admin user for the owner"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False) # In prod, use hashed password

    def __repr__(self):
        return f'<User {self.username}>'

class Collaborator(db.Model):
    """Barbers/Staff"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    phone = db.Column(db.String(20))
    start_date = db.Column(db.Date, default=datetime.utcnow)
    commission_percent = db.Column(db.Float, default=50.0) # e.g., 50.0 for 50%
    active = db.Column(db.Boolean, default=True)
    is_owner = db.Column(db.Boolean, default=False) # True for Owner/VIP
    token = db.Column(db.String(100), unique=True) # For Magic Link/QR Code
    password_hash = db.Column(db.String(128))

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        if not self.password_hash:
            return False
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    @property
    def balance(self):
        # Commissions
        total_comm = sum(s.total_commission for s in self.sales if not s.commission_paid)
        # Advances
        total_adv = sum(a.amount for a in self.advances if not a.is_paid)
        return total_comm - total_adv

    def __repr__(self):
        return f'<Collaborator {self.name}>'

class Service(db.Model):
    """Services offered (Cut, Beard, etc.)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Service {self.name}>'

class Product(db.Model):
    """Products for sale (Pomade, Shampoo)"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False) # Selling price
    cost_price = db.Column(db.Float, default=0.0) # Cost price
    commission_percent = db.Column(db.Float, default=10.0) # Logic replaced by fixed value, kept for legacy?
    commission_fixed_value = db.Column(db.Float, default=0.0) # Fixed commission value
    quantity = db.Column(db.Integer, default=0) # Stock quantity
    
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=True)
    supplier = db.relationship('Supplier', backref=db.backref('products', lazy=True))
    
    collaborator_id = db.Column(db.Integer, db.ForeignKey('collaborator.id'), nullable=True)
    collaborator = db.relationship('Collaborator', backref=db.backref('assigned_products', lazy=True))

    def __repr__(self):
        return f'<Product {self.name}>'

class Sale(db.Model):
    """Record of a service/product sale"""
    id = db.Column(db.Integer, primary_key=True)
    collaborator_id = db.Column(db.Integer, db.ForeignKey('collaborator.id'), nullable=False)
    collaborator = db.relationship('Collaborator', backref=db.backref('sales', cascade='all, delete-orphan'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    total_amount = db.Column(db.Float, default=0.0)
    total_commission = db.Column(db.Float, default=0.0)
    client_name = db.Column(db.String(100), nullable=True)
    payment_method = db.Column(db.String(50), default='Dinheiro')
    commission_paid = db.Column(db.Boolean, default=False)
    
    # Link to the specific payment batch
    payment_record_id = db.Column(db.Integer, db.ForeignKey('payment_record.id'), nullable=True)
    payment_record = db.relationship('PaymentRecord', backref=db.backref('sales', lazy=True))
    
    items = db.relationship('SaleItem', backref='sale', lazy=True, cascade='all, delete-orphan')

class SaleItem(db.Model):
    """Individual items in a sale"""
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('sale.id'), nullable=False)
    
    # Polymorphic-like behavior or just simple optional FKs
    service_id = db.Column(db.Integer, db.ForeignKey('service.id'), nullable=True)
    service = db.relationship('Service')
    
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=True)
    product = db.relationship('Product')
    
    item_name = db.Column(db.String(100)) # Snapshot of name
    price = db.Column(db.Float) # Snapshot of price at time of sale
    commission = db.Column(db.Float) # Calculated commission for this item

class Expense(db.Model):
    """Operational Expenses"""
    id = db.Column(db.Integer, primary_key=True)
    description = db.Column(db.String(200), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(50), default='Geral') # e.g. Aluguel, Luz, Água, Produtos
    date = db.Column(db.Date, default=datetime.utcnow)

    def __repr__(self):
        return f'<Expense {self.description}>'

class CashAdvance(db.Model):
    """Vales/Adiantamentos"""
    id = db.Column(db.Integer, primary_key=True)
    collaborator_id = db.Column(db.Integer, db.ForeignKey('collaborator.id'), nullable=False)
    collaborator = db.relationship('Collaborator', backref=db.backref('advances', cascade='all, delete-orphan'))
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(200))
    date = db.Column(db.Date, default=datetime.utcnow)
    is_paid = db.Column(db.Boolean, default=False) # True if deducted from a payment
    
    payment_record_id = db.Column(db.Integer, db.ForeignKey('payment_record.id'), nullable=True)
    payment_record = db.relationship('PaymentRecord', backref=db.backref('advances', lazy=True))

class PaymentRecord(db.Model):
    """Comprovante de Pagamento Semanal"""
    id = db.Column(db.Integer, primary_key=True)
    collaborator_id = db.Column(db.Integer, db.ForeignKey('collaborator.id'), nullable=False)
    collaborator = db.relationship('Collaborator', backref=db.backref('payments', cascade='all, delete-orphan'))
    date = db.Column(db.DateTime, default=datetime.utcnow)
    start_date = db.Column(db.Date) # Period start
    end_date = db.Column(db.Date)   # Period end
    
    total_commission = db.Column(db.Float, default=0.0)
    total_advances = db.Column(db.Float, default=0.0)
    net_amount = db.Column(db.Float, default=0.0)
    
    admin_name = db.Column(db.String(100)) # Who generated it
    
    admin_name = db.Column(db.String(100), default='Administrador')

class Supplier(db.Model):
    """Fornecedores e Dívidas"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    initial_debt = db.Column(db.Float, default=0.0)
    current_balance = db.Column(db.Float, default=0.0) # Debito atual
    
    payments = db.relationship('SupplierPayment', backref='supplier', lazy=True, cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Supplier {self.name}>'

class SupplierPayment(db.Model):
    """Pagamentos a Fornecedores"""
    id = db.Column(db.Integer, primary_key=True)
    supplier_id = db.Column(db.Integer, db.ForeignKey('supplier.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    description = db.Column(db.String(200)) # Opcional


