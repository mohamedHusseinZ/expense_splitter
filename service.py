import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from model import User, Expense, Settlement, db

SECRET_KEY = 'your_secret_key_here'

def add_user(username, email, password):
    if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
        return {'status': 'error', 'message': 'User already exists'}
    
    hashed_password = generate_password_hash(password)
    user = User(username=username, email=email, hashed_password=hashed_password)
    db.session.add(user)
    db.session.commit()
    return {'status': 'success'}

def authenticate(username, password):
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.hashed_password, password):
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')
        return {'status': 'success', 'token': token}
    return {'status': 'error', 'message': 'Invalid credentials'}

def add_expense(payer, amount, participants):
    payer_user = User.query.filter_by(username=payer).first()
    if not payer_user:
        return {'status': 'error', 'message': 'Payer not found'}
    
    expense = Expense(payer_id=payer_user.id, amount=amount, participants=participants)
    db.session.add(expense)
    db.session.commit()
    return {'status': 'success', 'expense': expense}

def get_expenses():
    expenses = Expense.query.all()
    return [{'id': exp.id, 'payer': User.query.get(exp.payer_id).username, 'amount': exp.amount, 'participants': exp.participants} for exp in expenses]

def update_expense(expense_id, amount, participants):
    expense = Expense.query.get(expense_id)
    if not expense:
        return {'status': 'error', 'message': 'Expense not found'}
    
    expense.amount = amount
    expense.participants = participants
    db.session.commit()
    return {'status': 'success'}

def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return {'status': 'error', 'message': 'Expense not found'}
    
    db.session.delete(expense)
    db.session.commit()
    return {'status': 'success'}

def get_user_profile(username):
    user = User.query.filter_by(username=username).first()
    if not user:
        return {'status': 'error', 'message': 'User not found'}

    expenses = Expense.query.filter_by(payer_id=user.id).all()
    settlements = Settlement.query.filter((Settlement.payer_id == user.id) | (Settlement.payee_id == user.id)).all()

    profile = {
        'username': user.username,
        'email': user.email,
        'expenses': [{'id': exp.id, 'amount': exp.amount, 'participants': exp.participants} for exp in expenses],
        'settlements': [{'id': settle.id, 'amount': settle.amount, 'payee': User.query.get(settle.payee_id).username} for settle in settlements]
    }

    return profile

def record_settlement(expense_id, payer, payee, amount):
    expense = Expense.query.get(expense_id)
    payer_user = User.query.filter_by(username=payer).first()
    payee_user = User.query.filter_by(username=payee).first()

    if not expense or not payer_user or not payee_user:
        return {'status': 'error', 'message': 'Invalid expense or user'}

    settlement = Settlement(expense_id=expense_id, payer_id=payer_user.id, payee_id=payee_user.id, amount=amount)
    db.session.add(settlement)
    db.session.commit()
    return {'status': 'success'}

def get_balances():
    expenses = Expense.query.all()
    balances = {user.username: 0 for user in User.query.all()}

    for expense in expenses:
        split_amount = expense.amount / len(expense.participants)
        for participant in expense.participants:
            if participant != User.query.get(expense.payer_id).username:
                balances[participant] -= split_amount
                balances[User.query.get(expense.payer_id).username] += split_amount
    return balances

def generate_report():
    balances = get_balances()
    report = []
    for person, balance in balances.items():
        if balance > 0:
            report.append(f"{person} is owed ${balance:.2f}")
        elif balance < 0:
            report.append(f"{person} owes ${-balance:.2f}")
    return report
