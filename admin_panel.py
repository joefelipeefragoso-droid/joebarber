from flask_admin.contrib.sqla import ModelView
from flask_admin import BaseView, expose
from flask import redirect, url_for, request, flash, session, render_template
from extensions import db, admin
from models import User, Collaborator, Service, Product, Sale, Expense, SaleItem
from sqlalchemy import func
from datetime import datetime, timedelta


class SecureModelView(ModelView):
    def is_accessible(self):
        return True # SECURITY REMOVED

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.admin_login'))

class SecureBaseView(BaseView):
    def is_accessible(self):
        return True # SECURITY REMOVED

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('main.admin_login'))

from flask_admin.form import rules
from wtforms import PasswordField
from markupsafe import Markup

class CollaboratorView(SecureModelView):
    column_list = ('name', 'phone', 'commission_percent', 'active', 'is_owner', 'total_earnings', 'qr_link')
    form_columns = ('name', 'phone', 'password', 'commission_percent', 'active', 'is_owner')
    column_labels = dict(name='Nome', phone='Telefone', commission_percent='Comissão (%)', active='Ativo', is_owner='Dono do Aplicativo', qr_link='Link de Acesso', password='Senha', total_earnings='Total Acumulado')
    # ... (Rest of existing CollaboratorView methods) ...
    form_extra_fields = {
        'password': PasswordField('Senha')
    }

    def _format_qr_link(view, context, model, name):
        if model.token:
            url = url_for('main.magic_login', token=model.token, _external=True)
            return Markup(f'<a href="{url}" target="_blank" class="btn btn-sm btn-info"><i class="fa fa-qrcode"></i> Acessar/QR</a>')
        return ''
    
    def _format_total_earnings(view, context, model, name):
        total = sum(s.total_commission for s in model.sales)
        return Markup(f'R$ {total:.2f}')

    column_formatters = {
        'qr_link': _format_qr_link,
        'total_earnings': _format_total_earnings
    }

    def on_model_change(self, form, model, is_created):
        if is_created and not model.token:
            import uuid
            model.token = str(uuid.uuid4())
        
        # Capture password before hashing for notification
        raw_password = form.password.data
        
        if form.password.data:
            # Security Check for Owner/Admin
            # Security Check for Owner/Admin VALIDATION REMOVED
            # if model.is_owner:
            #      import re
            #      pwd = form.password.data
            #      if len(pwd) < 8:
            #          raise ValueError('Senha muito curta. Mínimo 8 caracteres para administradores.')
            #      if not re.search(r"[A-Z]", pwd):
            #          raise ValueError('Senha deve conter letra Maiúscula.')
            #      if not re.search(r"\d", pwd):
            #          raise ValueError('Senha deve conter número.')
            #      if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", pwd):
            #          raise ValueError('Senha deve conter caractere especial.')

            model.set_password(form.password.data)
            
        if is_created and raw_password:
            # Send WhatsApp Notification
            try:
                from services.whatsapp import send_welcome_message
                # We need to commit the session first to ensure the ID/Token is ready? 
                # Actually token is set above.
                # But to get the correct URL we might need context. 
                # url_for works if request context is active (which it is here).
                send_welcome_message(model, raw_password)
                flash(f'Mensagem de boas-vindas enviada para {model.name} (Simulação/Log).', 'success')
            except Exception as e:
                flash(f'Erro ao enviar WhatsApp: {str(e)}', 'warning')


class VipRoomView(SecureBaseView):
    @expose('/', methods=['GET', 'POST'])
    def index(self):
        # Identify Owner (First one found or specific logic)
        owner = Collaborator.query.filter_by(is_owner=True).first()
        
        if not owner:
            flash('Nenhum perfil de "Proprietário" encontrado. Cadastre um colaborador e marque como Proprietário.', 'warning')
            return redirect(url_for('collaborator.index_view'))

        services = Service.query.all()
        products = Product.query.all()

        if request.method == 'POST':
            # Handle Sale Registration
            sale_type = request.form.get('type') # service or product
            item_id = request.form.get('item_id')
            price = float(request.form.get('price'))
            payment_method = request.form.get('payment_method')
            client_name = request.form.get('client_name')
            
            # Create Sale
            # Owner commission is 0 (cost to business), but we track revenue
            # Or should total_commission be 0? Yes, as per plan.
            
            sale = Sale(
                collaborator_id=owner.id,
                date=datetime.now(),
                total_amount=price,
                total_commission=0.0, # NO COMMISSION for Owner
                client_name=client_name,
                payment_method=payment_method,
                commission_paid=True # Automatically "paid" since it's owner
            )
            db.session.add(sale)
            
            # Sale Item
            if sale_type == 'service':
                svc = Service.query.get(item_id)
                item = SaleItem(sale=sale, service_id=svc.id, item_name=svc.name, price=price, commission=0.0)
                db.session.add(item)
            else:
                prod = Product.query.get(item_id)
                item = SaleItem(sale=sale, product_id=prod.id, item_name=prod.name, price=price, commission=0.0)
                db.session.add(item)
            
            db.session.commit()
            flash('Atendimento VIP registrado com sucesso!', 'success')
            return redirect(url_for('vip.index'))

        # Recent VIP Activity
        recent_vip_sales = Sale.query.filter_by(collaborator_id=owner.id).order_by(Sale.date.desc()).limit(10).all()
        
        # VIP Stats (Today)
        now = datetime.now()
        today = now.replace(hour=0, minute=0, second=0, microsecond=0)
        todays_vip_sales = Sale.query.filter(Sale.collaborator_id==owner.id, Sale.date >= today).all()
        today_total = sum(s.total_amount for s in todays_vip_sales)

        return self.render('admin/vip_room.html', 
                         owner=owner, 
                         services=services, 
                         products=products, 
                         recent=recent_vip_sales,
                         today_total=today_total)

class DashboardView(SecureBaseView):
    @expose('/')
    def index(self):
        # Filter Logic
        period = request.args.get('period', 'month')
        now = datetime.now()
        start_date = None
        
        if period == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif period == 'week':
             start_date = now - timedelta(days=7)
        elif period == 'month':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Base Queries
        sales_query = Sale.query
        expenses_query = Expense.query
        
        if start_date:
            sales_query = sales_query.filter(Sale.date >= start_date)
            expenses_query = expenses_query.filter(Expense.date >= start_date.date())

        sales = sales_query.all()
        expenses = expenses_query.all()
        
        # Split Sales into VIP and Team
        # We need to check is_owner for each sale's collaborator
        # Ideally we join, but python loop is fine for MVP size
        vip_sales = [s for s in sales if s.collaborator.is_owner]
        team_sales = [s for s in sales if not s.collaborator.is_owner]

        # 1. KPIs
        vip_revenue = sum(s.total_amount for s in vip_sales)
        team_revenue = sum(s.total_amount for s in team_sales)
        total_revenue = vip_revenue + team_revenue
        
        total_expenses = sum(e.amount for e in expenses)
        
        # Commissions (Only from Team)
        total_commissions = sum(s.total_commission for s in team_sales)
        
        total_services = len(sales)

        # Net Profit = (Team Rev - Team Comm) + VIP Rev - Expenses
        # Or simply Total Rev - Total Comm - Expenses
        net_profit = total_revenue - total_expenses - total_commissions
        
        # 2. Detailed Commission Stats (Team Only)
        collab_stats = []
        collabs = Collaborator.query.filter_by(is_owner=False).all() # Only regular staff
        
        for c in collabs:
            c_sales = [s for s in team_sales if s.collaborator_id == c.id]
            gross_revenue = sum(s.total_amount for s in c_sales)
            comm_generated = sum(s.total_commission for s in c_sales)
            
            if gross_revenue > 0:
                collab_stats.append({
                    'name': c.name,
                    'gross_revenue': gross_revenue,
                    'commission_percent': c.commission_percent,
                    'commission_generated': comm_generated
                })

        # Recent appointments
        recent_sales = Sale.query.order_by(Sale.date.desc()).limit(10).all()

        # Chart Data (Last 7 Days)
        dates = [datetime.now().date() - timedelta(days=i) for i in range(6, -1, -1)]
        daily_labels = [d.strftime('%d/%m') for d in dates]
        daily_values = []
        
        for d in dates:
             # Sum sales for this specific day
             day_total = db.session.query(func.sum(Sale.total_amount))\
                .filter(func.date(Sale.date) == d).scalar() or 0.0
             daily_values.append(day_total)

        # Suppliers Debt
        from models import Supplier
        suppliers = Supplier.query.all()
        total_supplier_debt = sum(s.current_balance for s in suppliers)

        # 3. Monthly Financial Report (Full History)
        all_sales = Sale.query.all()
        all_expenses = Expense.query.all()
        monthly_report = self._calculate_monthly_finance(all_sales, all_expenses)
        report_7_days = self._calculate_last_7_days(all_sales, all_expenses)

        return self.render('admin/dashboard.html', 
                         period=period,
                         total_revenue=total_revenue,
                         vip_revenue=vip_revenue,
                         team_revenue=team_revenue,
                         total_expenses=total_expenses, 
                         total_commissions=total_commissions,
                         total_services=total_services,
                         net_profit=net_profit,
                         collab_stats=collab_stats,
                         recent_sales=recent_sales,
                         daily_labels=daily_labels,
                         daily_values=daily_values,
                         monthly_report=monthly_report,
                         report_7_days=report_7_days,
                         total_supplier_debt=total_supplier_debt)

    def _calculate_last_7_days(self, sales, expenses):
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        
        # Helper to ensure datetime comparison
        def to_dt(d):
            return datetime.combine(d, datetime.min.time()) if isinstance(d, type(datetime.now().date())) else d

        receita = sum(s.total_amount for s in sales if s.date >= seven_days_ago)
        despesa = sum(e.amount for e in expenses if to_dt(e.date) >= seven_days_ago)
        
        return {"receita": receita, "despesa": despesa, "lucro": receita - despesa}

    def _calculate_monthly_finance(self, sales, expenses):
        from collections import defaultdict
        
        financeiro = defaultdict(lambda: {"receita": 0.0, "despesa": 0.0, "lucro": 0.0})

        # Process Sales (Receita)
        for sale in sales:
            chave_mes = sale.date.strftime("%Y-%m")
            financeiro[chave_mes]["receita"] += sale.total_amount

        # Process Expenses (Despesa)
        for expense in expenses:
            chave_mes = expense.date.strftime("%Y-%m")
            financeiro[chave_mes]["despesa"] += expense.amount

        # Calculate Profit
        for mes in financeiro:
            financeiro[mes]["lucro"] = financeiro[mes]["receita"] - financeiro[mes]["despesa"]

        # Sort by date descending (newest first)
        return dict(sorted(financeiro.items(), reverse=True))

    @expose('/delete_sale/<int:id>', methods=['POST'])
    def delete_sale(self, id):
        sale = Sale.query.get_or_404(id)
        
        try:
            # Delete items first (manual cascade safety)
            SaleItem.query.filter_by(sale_id=sale.id).delete()
            
            db.session.delete(sale)
            db.session.commit()
            
            flash('Atendimento excluído com sucesso!', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erro ao excluir: {str(e)}', 'danger')
            
        return redirect(url_for('.index'))

# Function to register views explicitly
def init_admin(admin):
    from models import CashAdvance, PaymentRecord
    
    # Add Views
    admin.add_view(DashboardView(name='Painel de Gestão', endpoint='dashboard'))
    admin.add_view(VipRoomView(name='Sala VIP (Proprietário)', endpoint='vip'))
    admin.add_view(FinancialControlView(name='Controle Financeiro', endpoint='financial'))



class ServiceView(SecureModelView):
    column_labels = dict(name='Nome', price='Preço (R$)')
    form_columns = ('name', 'price')

class ProductView(SecureModelView):
    column_labels = dict(
        name='Nome', 
        price='Preço Venda', 
        cost_price='Custo', 
        commission_fixed_value='Comissão Fixa (R$)', 
        supplier='Fornecedor',
        collaborator='Colaborador (Comissão)',
        quantity='Estoque',
        gross_profit='Lucro Bruto',
        net_profit='Lucro Líquido (Real)'
    )
    list_columns = ('name', 'quantity', 'cost_price', 'price', 'gross_profit', 'commission_fixed_value', 'collaborator', 'net_profit', 'supplier')
    form_columns = ('name', 'quantity', 'price', 'cost_price', 'commission_fixed_value', 'collaborator', 'supplier')
    
    def _format_gross_profit(view, context, model, name):
        cost = model.cost_price or 0.0
        price = model.price or 0.0
        return Markup(f'R$ {price - cost:.2f}')

    def _format_net_profit(view, context, model, name):
        cost = model.cost_price or 0.0
        price = model.price or 0.0
        comm_fixed = model.commission_fixed_value or 0.0
        
        gross = price - cost
        net = gross - comm_fixed
        color = "text-success" if net >= 0 else "text-danger"
        return Markup(f'<b class="{color}">R$ {net:.2f}</b>')

    column_formatters = {
        'gross_profit': _format_gross_profit,
        'net_profit': _format_net_profit
    }
    
    def on_model_change(self, form, model, is_created):
        # Logic: Fixed Value Commission
        # We NO LONGER use 10% of profit.
        # We must keep commission_percent updated though, because current logic in Routes uses it.
        # Wait, if we change Routes logic, we don't need commission_percent.
        # But to be safe, set commission_percent to 0 or calculate equivalent for legacy support?
        # Let's set commission_percent to the equivalent % just in case.
        
        cost = model.cost_price or 0.0
        price = model.price or 0.0
        comm_fixed = model.commission_fixed_value or 0.0
        
        if price > 0:
             # Equiv percent = (Fixed / Price) * 100
             model.commission_percent = (comm_fixed / price) * 100
        
        # 2. Update Supplier Debt (Only on creation to avoid double counting edits)
        if is_created and model.supplier:
            # Increase debt based on COST * QUANTITY?
            # User said: "Quantidade Comprada".
            # The Supplier Debt logic previously assumed Cost was total? No, cost_price is Unit Cost.
            # Usually strict accounting: Debt += Cost * Qty.
            # Previous logic: `supplier.current_balance += cost`.
            # If user adds "10 Minoxidils" at "60 each", Debt should be 600.
            # Let's check `quantity` field.
            
            qty = model.quantity or 0
            # If QTY is 0, maybe user means 1 unit? Let's assume previously it was 1 unit.
            # If new field Quantity is used, we multiply.
            total_cost = cost * (qty if qty > 0 else 1) # Fallback if user leaves 0 but implies 1
            
            supplier = model.supplier
            supplier.current_balance += total_cost
            db.session.add(supplier)
            flash(f'Dívida com {supplier.name} aumentada em R$ {total_cost:.2f} ({qty} itens).', 'info')
            
            # 3. Register Expense
            try:
                from models import Expense
                expense = Expense(
                    description=f'Compra Estoque: {model.name} (x{qty})',
                    amount=total_cost,
                    category='Fornecedor',
                    date=datetime.now().date()
                )
                db.session.add(expense)
                flash(f'Despesa de R$ {total_cost:.2f} lançada automaticamente.', 'info')
            except Exception as e:
                flash(f'Erro ao lançar despesa: {e}', 'warning')

class ExpenseView(SecureModelView):
    column_labels = dict(description='Descrição', amount='Valor (R$)', category='Categoria', date='Data')
    form_columns = ('description', 'amount', 'category', 'date')

class CashAdvanceView(SecureModelView):
    column_labels = dict(collaborator='Colaborador', amount='Valor (R$)', description='Descrição', date='Data', is_paid='Pago?')
    form_columns = ('collaborator', 'amount', 'description', 'date')
    column_filters = ('collaborator.name', 'is_paid')

class PaymentRecordView(SecureModelView):
    can_create = False
    can_edit = False
    can_delete = False
    column_labels = dict(collaborator='Colaborador', date='Data Pgto', total_commission='Comissões', total_advances='Vales', net_amount='Líquido Pago', admin_name='Por')
    
    def _format_receipt(view, context, model, name):
         url_admin = url_for('payments.receipt_view', id=model.id)
         url_collab = url_for('payments.collab_report_view', id=model.id)
         return Markup(f'''
            <a href="{url_admin}" target="_blank" class="btn btn-xs btn-primary" title="Via Administrativa"><i class="fa fa-file-invoice"></i> Admin</a>
            <a href="{url_collab}" target="_blank" class="btn btn-xs btn-success" title="Relatório para Colaborador"><i class="fa fa-print"></i> Colab.</a>
         ''')

    column_formatters = {
        'receipt': _format_receipt
    }
    column_list = ('date', 'collaborator', 'total_commission', 'total_advances', 'net_amount', 'admin_name', 'receipt')

class WeeklyPaymentView(SecureBaseView):
    @expose('/')
    def index(self):
        # Only show staff that are NOT owners for payment processing
        from models import PaymentRecord
        collabs = Collaborator.query.filter_by(active=True, is_owner=False).all()
        recent_payments = PaymentRecord.query.order_by(PaymentRecord.date.desc()).limit(20).all()
        return self.render('admin/weekly_payment.html', collabs=collabs, recent_payments=recent_payments)

    @expose('/confirm/<int:id>', methods=['POST'])
    def confirm_payment(self, id):
        from models import CashAdvance, PaymentRecord # Local import to avoid circular issues if any
        collab = Collaborator.query.get_or_404(id)
        
        # Get pending items
        pending_sales = Sale.query.filter_by(collaborator_id=id, commission_paid=False).all()
        pending_advances = CashAdvance.query.filter_by(collaborator_id=id, is_paid=False).all()
        
        total_comm = sum(s.total_commission for s in pending_sales)
        total_adv = sum(a.amount for a in pending_advances)
        net = total_comm - total_adv
        
        if net < 0:
            flash(f'Saldo negativo (R$ {net:.2f}). Não é possível fechar pagamento.', 'error')
            return redirect(url_for('.index'))
            
        if total_comm == 0 and total_adv == 0:
             flash('Nada a pagar.', 'warning')
             return redirect(url_for('.index'))

        # Determine period dates from sales
        start_date = min([s.date for s in pending_sales]).date() if pending_sales else datetime.utcnow().date()
        end_date = max([s.date for s in pending_sales]).date() if pending_sales else datetime.utcnow().date()

        # Create Record
        payment = PaymentRecord(
            collaborator_id=id,
            total_commission=total_comm,
            total_advances=total_adv,
            net_amount=net,
            admin_name='Administrador',
            start_date=start_date,
            end_date=end_date
        )
        db.session.add(payment)
        db.session.flush() # Get ID
        
        # Update items
        for s in pending_sales:
            s.commission_paid = True
            s.payment_record_id = payment.id # Link sale to this receipt
            
        for a in pending_advances:
            a.is_paid = True
            a.payment_record_id = payment.id # Link advance to this receipt
            
        db.session.commit()
        
        flash(f'Pagamento de R$ {net:.2f} realizado com sucesso!', 'success')
        return redirect(url_for('payments.receipt_view', id=payment.id))

    @expose('/receipt/<int:id>')
    def receipt_view(self, id):
        from models import PaymentRecord
        payment = PaymentRecord.query.get_or_404(id)
        # ADMIN MODE: Shows Revenue, Profit, Gross
        return render_template('receipt_unified.html', payment=payment, mode='admin')

    @expose('/collab_report/<int:id>')
    def collab_report_view(self, id):
        from models import PaymentRecord
        payment = PaymentRecord.query.get_or_404(id)
        # COLLAB MODE: Hides Revenue, Profit. Shows only Commission & Discounts.
        return render_template('receipt_unified.html', payment=payment, mode='collab')


class FinancialControlView(SecureBaseView):
    @expose('/')
    def index(self):
        # Time ranges
        now = datetime.now()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        week_start = now - timedelta(days=7) # Or week start: now - timedelta(days=now.weekday())

        # 1. Daily Control by Payment Method
        # Aggregate manually for flexibility
        todays_sales = Sale.query.filter(Sale.date >= today_start).all()
        
        methods = ['Dinheiro', 'Pix', 'Débito', 'Crédito']
        daily_control = {m: {'total': 0.0, 'breakdown': []} for m in methods}
        
        # Populate Daily Data
        for sale in todays_sales:
            method = sale.payment_method
            if method in daily_control:
                daily_control[method]['total'] += sale.total_amount
                # Add to breakdown (we will group by collab later or just list them)
                daily_control[method]['breakdown'].append({
                    'collab': sale.collaborator.name,
                    'amount': sale.total_amount
                })
        
        # Group breakdown by collaborator
        for m in methods:
            raw_list = daily_control[m]['breakdown']
            grouped = {}
            for item in raw_list:
                name = item['collab']
                grouped[name] = grouped.get(name, 0.0) + item['amount']
            
            # Convert back to list of dicts
            daily_control[m]['breakdown'] = [{'name': k, 'amount': v} for k, v in grouped.items()]


        # 2. Weekly Money Control
        weekly_sales = Sale.query.filter(Sale.date >= week_start, Sale.payment_method == 'Dinheiro').all()
        weekly_money_total = sum(s.total_amount for s in weekly_sales)
        
        weekly_money_breakdown = {}
        for s in weekly_sales:
            name = s.collaborator.name
            weekly_money_breakdown[name] = weekly_money_breakdown.get(name, 0.0) + s.total_amount
            
        weekly_money_breakdown_list = [{'name': k, 'amount': v} for k, v in weekly_money_breakdown.items()]

        return self.render('admin/financial_control.html',
                           daily_control=daily_control,
                           weekly_money_total=weekly_money_total,
                           weekly_money_breakdown=weekly_money_breakdown_list)

class SupplierView(SecureModelView):
    column_list = ('name', 'initial_debt', 'current_balance')
    column_labels = dict(name='Fornecedor (Ações)', initial_debt='Dívida Conhecida', current_balance='Saldo Devedor Atual')
    
    def _format_name(view, context, model, name):
        url_stmt = url_for('.statement_view', id=model.id)
        # Use explicit endpoint 'supplierpayment'
        url_pay = url_for('supplierpayment.create_view') 
        
        # Display Name + Buttons
        return Markup(f'''
            {model.name} 
            <span class="float-right" style="margin-left: 10px;">
                <a href="{url_stmt}" class="btn btn-xs btn-info" title="Ver Nota"><i class="fa fa-list-alt"></i> Nota</a>
                <a href="{url_pay}" class="btn btn-xs btn-success" title="Pagar"><i class="fa fa-dollar-sign"></i> Pagar</a>
            </span>
        ''')
    
    column_formatters = {
        'name': _format_name
    }
    
    @expose('/statement/<int:id>')
    def statement_view(self, id):
        from models import Supplier
        supplier = Supplier.query.get_or_404(id)
        return self.render('admin/supplier_statement.html', supplier=supplier)

    def on_model_change(self, form, model, is_created):
        if is_created:
            # On create, if no explicit balance set (usually user sets initial debt), sync them
            if model.initial_debt and not model.current_balance:
                model.current_balance = model.initial_debt

class SupplierPaymentView(SecureModelView):
    column_list = ('supplier', 'amount', 'date', 'description')
    column_labels = dict(supplier='Fornecedor', amount='Valor Pago', date='Data', description='Descrição')
    
    def on_model_change(self, form, model, is_created):
        if is_created:
            # Deduct from Supplier Balance immediately
            if model.supplier:
                supplier = model.supplier
                try:
                    current_balance = float(supplier.current_balance or 0.0)
                    payment_amount = float(model.amount or 0.0)
                except ValueError:
                    current_balance = 0.0
                    payment_amount = 0.0
                
                supplier.current_balance = current_balance - payment_amount
                
                if supplier.current_balance < 0:
                    supplier.current_balance = 0.0
                
                db.session.add(supplier)
                flash(f'Pagamento de R$ {payment_amount:.2f} registrado. Novo saldo de {supplier.name}: R$ {supplier.current_balance:.2f}', 'success')

# Function to register views explicitly
def init_admin(admin):
    from models import CashAdvance, PaymentRecord, Supplier, SupplierPayment
    
    # Add Views
    admin.add_view(DashboardView(name='Painel de Gestão', endpoint='dashboard'))
    admin.add_view(VipRoomView(name='Sala VIP (Dono do Aplicativo)', endpoint='vip'))
    admin.add_view(FinancialControlView(name='Controle Financeiro', endpoint='financial'))
    
    # Notas e Pagamentos Category
    admin.add_view(WeeklyPaymentView(name='Fechar Pagamentos', endpoint='payments', category='Notas e Pagamentos'))
    admin.add_view(PaymentRecordView(PaymentRecord, db.session, name='Histórico de Notas', category='Notas e Pagamentos'))
    
    admin.add_view(CollaboratorView(Collaborator, db.session, name='Colaboradores'))
    admin.add_view(CashAdvanceView(CashAdvance, db.session, name='Vales/Adiantamentos', category='Notas e Pagamentos'))
    admin.add_view(ServiceView(Service, db.session, name='Serviços'))
    admin.add_view(ProductView(Product, db.session, name='Produtos'))
    admin.add_view(ExpenseView(Expense, db.session, name='Despesas'))
    
    admin.add_view(SupplierView(Supplier, db.session, name='Fornecedores'))
    admin.add_view(SupplierPaymentView(SupplierPayment, db.session, name='Pagamentos Fornec.', endpoint='supplierpayment'))

