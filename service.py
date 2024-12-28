# service.py
import jwt
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from model import User, Expense, Settlement, db
from sqlalchemy.exc import SQLAlchemyError

SECRET_KEY = 'your_secret_key_here'  # Replace with your actual secret key

# Helper function to fetch user by username
def get_user_by_username(username):
    return User.query.filter_by(username=username).first()

# Helper function to fetch user by ID
def get_user_by_id(user_id):
    return User.query.get(user_id)

# Helper function to fetch all users
def get_all_users():
    return User.query.all()

# User registration logic
def add_user(username, email, password):
    try:
        # Check if username or email already exists
        if get_user_by_username(username) or User.query.filter_by(email=email).first():
            return {'status': 'error', 'message': 'User already exists'}

        # Hash password
        hashed_password = generate_password_hash(password)
        user = User(username=username, email=email, hashed_password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return {'status': 'success'}
    except SQLAlchemyError as e:
        db.session.rollback()  # Rollback transaction in case of an error
        return {'status': 'error', 'message': str(e)}

# User authentication with JWT token generation
def authenticate(username, password):
    user = get_user_by_username(username)
    if user and check_password_hash(user.hashed_password, password):
        # Generate JWT token
        token = jwt.encode({
            'user_id': user.id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
        }, SECRET_KEY, algorithm='HS256')
        return {'status': 'success', 'token': token}
    return {'status': 'error', 'message': 'Invalid credentials'}

# Adding an expense to the database
def add_expense(payer, amount, participants):
    payer_user = get_user_by_username(payer)
    if not payer_user:
        return {'status': 'error', 'message': 'Payer not found'}

    try:
        # Create expense with participants as a many-to-many relationship
        expense = Expense(
            payer_id=payer_user.id,
            amount=amount
        )
        db.session.add(expense)
        db.session.commit()

        # Associate participants with the expense
        for participant in participants:
            user = get_user_by_username(participant)
            if user:
                expense.participants.append(user)
        db.session.commit()

        return {'status': 'success', 'expense': {
            'id': expense.id,
            'amount': expense.amount,
            'participants': [p.username for p in expense.participants]
        }}
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

# Fetch all expenses from the database
def get_expenses():
    try:
        expenses = Expense.query.all()
        return [{
            'id': exp.id,
            'payer': get_user_by_id(exp.payer_id).username,
            'amount': exp.amount,
            'participants': [p.username for p in exp.participants]  # Convert participants list to usernames
        } for exp in expenses]
    except SQLAlchemyError as e:
        return {'status': 'error', 'message': str(e)}

# Update an existing expense
def update_expense(expense_id, amount, participants):
    expense = Expense.query.get(expense_id)
    if not expense:
        return {'status': 'error', 'message': 'Expense not found'}

    try:
        expense.amount = amount
        expense.participants.clear()  # Clear existing participants
        for participant in participants:
            user = get_user_by_username(participant)
            if user:
                expense.participants.append(user)
        db.session.commit()
        return {'status': 'success'}
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

# Delete an expense from the database
def delete_expense(expense_id):
    expense = Expense.query.get(expense_id)
    if not expense:
        return {'status': 'error', 'message': 'Expense not found'}

    try:
        db.session.delete(expense)
        db.session.commit()
        return {'status': 'success'}
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

# Fetch user profile with expenses and settlements
def get_user_profile(username):
    user = get_user_by_username(username)
    if not user:
        return {'status': 'error', 'message': 'User not found'}

    try:
        expenses = Expense.query.filter_by(payer_id=user.id).all()
        settlements = Settlement.query.filter(
            (Settlement.payer_id == user.id) | (Settlement.payee_id == user.id)
        ).all()

        profile = {
            'username': user.username,
            'email': user.email,
            'expenses': [{'id': exp.id, 'amount': exp.amount, 'participants': [p.username for p in exp.participants]} for exp in expenses],
            'settlements': [{'id': settle.id, 'amount': settle.amount, 'payee': get_user_by_id(settle.payee_id).username} for settle in settlements]
        }
        return {'status': 'success', 'profile': profile}
    except SQLAlchemyError as e:
        return {'status': 'error', 'message': str(e)}

# Record a settlement between payer and payee
def record_settlement(expense_id, payer, payee, amount):
    expense = Expense.query.get(expense_id)
    payer_user = get_user_by_username(payer)
    payee_user = get_user_by_username(payee)

    if not expense or not payer_user or not payee_user:
        return {'status': 'error', 'message': 'Invalid expense or user'}

    try:
        settlement = Settlement(
            expense_id=expense_id,
            payer_id=payer_user.id,
            payee_id=payee_user.id,
            amount=amount
        )
        db.session.add(settlement)
        db.session.commit()
        return {'status': 'success'}
    except SQLAlchemyError as e:
        db.session.rollback()
        return {'status': 'error', 'message': str(e)}

# Get the balances for all users based on their expenses and settlements
def get_balances():
    expenses = Expense.query.all()
    balances = {user.username: 0 for user in get_all_users()}

    # Update balances based on expenses
    for expense in expenses:
        participants = [p.username for p in expense.participants]  # Get participants as list of usernames
        split_amount = expense.amount / len(participants)
        payer_username = get_user_by_id(expense.payer_id).username
        for participant in participants:
            if participant != payer_username:
                balances[participant] -= split_amount
                balances[payer_username] += split_amount

    # Adjust balances based on recorded settlements
    settlements = Settlement.query.all()
    for settle in settlements:
        payer_username = get_user_by_id(settle.payer_id).username
        payee_username = get_user_by_id(settle.payee_id).username
        balances[payer_username] -= settle.amount
        balances[payee_username] += settle.amount

    return balances

# Generate a report based on balances
def generate_report():
    balances = get_balances()
    report = []
    for person, balance in balances.items():
        if balance > 0:
            report.append(f"{person} is owed ${balance:.2f}")
        elif balance < 0:
            report.append(f"{person} owes ${-balance:.2f}")
    return report
