from flask import Blueprint, render_template, redirect, url_for, session, request, jsonify, flash
from extensions import db
from models import Collaborator, Service, Product, Sale, SaleItem
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        password = request.form.get('password')
        # Check against any Collaborator marked as Owner
        owners = Collaborator.query.filter_by(is_owner=True).all()
        
        authorized = False
        for owner in owners:
            if owner.check_password(password):
                session['admin_logged_in'] = True
                session['admin_name'] = owner.name
                flash(f'Bem-vindo, {owner.name}!', 'success')
                authorized = True
                break
        
        if authorized:
            return redirect(url_for('dashboard.index'))
        else:
            flash('Acesso negado. Senha incorreta ou nenhum proprietário configurado.', 'danger')

    return render_template('admin/login.html')


@main_bp.route('/login/<token>', methods=['GET', 'POST'])
def magic_login(token):
    collab = Collaborator.query.filter_by(token=token).first()
    
    if not collab or not collab.active:
        flash('Token inválido ou colaborador inativo.', 'danger')
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        password = request.form.get('password')
        if collab.check_password(password):
            session['collab_id'] = collab.id
            session['collab_name'] = collab.name
            return redirect(url_for('main.dashboard'))
        else:
            flash('Senha incorreta.', 'danger')

    return render_template('collab_login.html', collaborator=collab)

@main_bp.route('/dashboard')
def dashboard():
    if 'collab_id' not in session:
        return redirect(url_for('main.index'))
    
    collab = Collaborator.query.get(session['collab_id'])
    
    # Calculate total accumulated commission (History)
    total_history = db.session.query(db.func.sum(Sale.total_commission)).filter(Sale.collaborator_id == collab.id).scalar() or 0.0

    # Calculate current unpaid commission (Balance)
    current_balance = db.session.query(db.func.sum(Sale.total_commission)).filter(Sale.collaborator_id == collab.id, Sale.commission_paid == False).scalar() or 0.0

    # Calculate total paid
    total_paid = total_history - current_balance

    # Simple stats for the logged in user
    sales = Sale.query.filter_by(collaborator_id=collab.id).order_by(Sale.date.desc()).limit(10).all()
    
    return render_template('collab_dashboard.html', 
                           collaborator=collab, 
                           recent_sales=sales, 
                           total_commission=total_history, 
                           current_balance=current_balance,
                           total_paid=total_paid)

@main_bp.route('/reset-commissions', methods=['POST'])
def reset_commissions():
    if 'collab_id' not in session:
        return jsonify({'success': False, 'message': 'Unauthorized'}), 401
    
    collab_id = session['collab_id']
    
    # Update all unpaid sales to paid
    try:
        sales = Sale.query.filter_by(collaborator_id=collab_id, commission_paid=False).all()
        count = 0
        for sale in sales:
            sale.commission_paid = True
            count += 1
        
        db.session.commit()
        return jsonify({'success': True, 'message': f'{count} vendas marcadas como pagas.'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@main_bp.route('/sale/new', methods=['GET', 'POST'])
def new_sale():
    if 'collab_id' not in session:
        return redirect(url_for('main.index'))

    if request.method == 'POST':
        # Logic to process sale
        data = request.json # Expecting JSON from the frontend JS
        if not data:
             return jsonify({'error': 'No data'}), 400
        
        collab_id = session['collab_id']
        total = 0
        total_comm = 0
        
        client_name = data.get('client_name', '')
        payment_method = data.get('payment_method', 'Dinheiro')
        
        new_sale = Sale(collaborator_id=collab_id, client_name=client_name, payment_method=payment_method)
        db.session.add(new_sale)
        db.session.flush() # Get ID
        
        # Process items
        for item in data.get('items', []):
            cost = 0
            comm_val = 0
            
            if item['type'] == 'service':
                svc = Service.query.get(item['id'])
                if svc:
                    cost = svc.price
                    # Service commission uses collaborator's percent
                    collab = Collaborator.query.get(collab_id)
                    comm_val = cost * (collab.commission_percent / 100.0)
                    
                    sale_item = SaleItem(sale_id=new_sale.id, service_id=svc.id, 
                                         item_name=svc.name, price=cost, commission=comm_val)
                    db.session.add(sale_item)
            
            elif item['type'] == 'product':
                prod = Product.query.get(item['id'])
                if prod:
                    cost = prod.price
                    # Product commission uses fixed value now
                    comm_val = prod.commission_fixed_value or 0.0
                    
                    # Deduct Stock
                    if prod.quantity and prod.quantity > 0:
                        prod.quantity -= 1
                        db.session.add(prod)
                    
                    sale_item = SaleItem(sale_id=new_sale.id, product_id=prod.id, 
                                         item_name=prod.name, price=cost, commission=comm_val)
                    db.session.add(sale_item)

            total += cost
            total_comm += comm_val
            
        new_sale.total_amount = total
        new_sale.total_commission = total_comm
        new_sale.date = datetime.utcnow()
        
        db.session.commit()
        return jsonify({'success': True, 'redirect': url_for('main.dashboard')})

    # GET request
    services = Service.query.all()
    products = Product.query.all()
    return render_template('new_sale.html', services=services, products=products)

@main_bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('main.index'))

@main_bp.route('/my-receipts')
def my_receipts():
    if 'collab_id' not in session:
        return redirect(url_for('main.index'))
    
    from models import PaymentRecord
    collab_id = session['collab_id']
    payments = PaymentRecord.query.filter_by(collaborator_id=collab_id).order_by(PaymentRecord.date.desc()).all()
    
    return render_template('collab_receipts_list.html', payments=payments)

@main_bp.route('/my-receipts/<int:id>')
def receipt_detail(id):
    if 'collab_id' not in session:
        return redirect(url_for('main.index'))
        
    from models import PaymentRecord
    payment = PaymentRecord.query.get_or_404(id)
    
    # Security Check
    if payment.collaborator_id != session['collab_id']:
        flash('Acesso negado a este comprovante.', 'danger')
        return redirect(url_for('main.my_receipts'))
        
    # Unified Template with Collab Mode
    return render_template('receipt_unified.html', payment=payment, mode='collab')
