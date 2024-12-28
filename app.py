from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta
import bcrypt

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Enable CORS with full support
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Example in-memory user store (replace with a database in production)
users_db = {}

# Mock data (Replace with actual database models or external integrations)
expenses = []
balances = {}
categories = ["Food", "Transport", "Utilities", "Entertainment"]

# Decorator to require JWT token for protected routes
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token or not token.startswith("Bearer "):
            return jsonify({'status': 'error', 'message': 'Invalid or missing token!'}), 403

        try:
            token = token.split(' ')[1]  # Extract token after 'Bearer'
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            request.user = data['email']  # Attach email to the request context
        except ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token has expired!'}), 403
        except InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Invalid token!'}), 403

        return f(*args, **kwargs)

    return decorated

# Helper functions
def add_user(email, password):
    if email in users_db:
        return {"status": "error", "message": "Email already registered!"}

    # Hash the password before storing (using bcrypt)
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    users_db[email] = hashed_password
    return {"status": "success", "message": f"User with email {email} registered successfully!"}

def authenticate(email, password):
    user = users_db.get(email)
    if not user or not bcrypt.checkpw(password.encode('utf-8'), user):
        return {"status": "error", "message": "Invalid credentials!"}

    # Generate JWT token
    token = jwt.encode(
        {'email': email, 'exp': datetime.utcnow() + timedelta(hours=1)},
        app.config['SECRET_KEY'],
        algorithm='HS256'
    )
    return {"status": "success", "token": token}

def get_categories():
    return categories

def reset_balance():
    global balances
    balances = {}
    return {"status": "success", "message": "Balances reset successfully!"}

def filter_expenses_by_date(start_date, end_date):
    # Mock filtering logic based on dates (format: 'YYYY-MM-DD')
    return [exp for exp in expenses if start_date <= exp["date"] <= end_date]

def add_expense(payer, amount, participants):
    global expenses, balances  # Ensure global modification
    expense = {
        "id": len(expenses) + 1,
        "payer": payer,
        "amount": float(amount),
        "participants": participants,
        "date": datetime.utcnow().strftime('%Y-%m-%d')
    }
    expenses.append(expense)

    # Update balances
    share = expense["amount"] / len(participants)
    for participant in participants:
        if participant == payer:
            continue
        balances[participant] = balances.get(participant, 0) + share
        balances[payer] = balances.get(payer, 0) - share

    return {"status": "success", "message": "Expense added successfully!", "data": expense}

def delete_expense(expense_id):
    global expenses, balances  # Ensure global modification
    expense = next((exp for exp in expenses if exp["id"] == expense_id), None)
    if not expense:
        return {"status": "error", "message": "Expense not found!"}

    # Recalculate balances
    share = expense["amount"] / len(expense["participants"])
    for participant in expense["participants"]:
        if participant == expense["payer"]:
            continue
        balances[participant] -= share
        balances[expense["payer"]] += share

    expenses = [exp for exp in expenses if exp["id"] != expense_id]
    return {"status": "success", "message": "Expense deleted successfully!"}

def get_expenses():
    return {"status": "success", "expenses": expenses}

def get_balances():
    return balances

def generate_report():
    total_expenses = len(expenses)
    total_amount = sum(exp["amount"] for exp in expenses)
    return {"total_expenses": total_expenses, "total_amount": total_amount}

def get_user_profile(email):
    user_expenses = [exp for exp in expenses if exp["payer"] == email]
    return {"status": "success", "profile": {"email": email, "expenses_count": len(user_expenses)}}

# Routes
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required!"}), 400

    result = add_user(email, password)
    return jsonify(result), 201 if result['status'] == 'success' else 400

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"status": "error", "message": "Email and password are required!"}), 400

    result = authenticate(email, password)
    return jsonify(result), 200 if result['status'] == 'success' else 400

@app.route('/categories', methods=['GET'])
@token_required
def get_categories_route():
    categories = get_categories()
    return jsonify({'status': 'success', 'categories': categories})

@app.route('/reset_balance', methods=['POST'])
@token_required
def reset_balance_route():
    result = reset_balance()
    return jsonify(result)

@app.route('/expenses_by_date', methods=['GET'])
@token_required
def filter_expenses_route():
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    result = filter_expenses_by_date(start_date, end_date)
    return jsonify(result)

@app.route('/add_expense', methods=['POST'])
@token_required
def add_expense_route():
    data = request.json
    payer = data.get('payer')
    amount = data.get('amount')
    participants = data.get('participants')

    if not payer or not amount or not participants:
        return jsonify({"status": "error", "message": "Payer, amount, and participants are required!"}), 400

    result = add_expense(payer, amount, participants)
    return jsonify(result), 201 if result['status'] == 'success' else 400

@app.route('/delete_expense/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense_route(expense_id):
    result = delete_expense(expense_id)
    return jsonify(result), 200 if result['status'] == 'success' else 404

@app.route('/expenses', methods=['GET'])
@token_required
def get_expenses_route():
    result = get_expenses()
    return jsonify(result), 200 if result['status'] == 'success' else 400

@app.route('/balances', methods=['GET'])
@token_required
def get_balances_route():
    balances = get_balances()
    return jsonify({'status': 'success', 'balances': balances})

@app.route('/user_profile', methods=['GET'])
@token_required
def get_user_profile_route():
    email = request.user
    result = get_user_profile(email)
    return jsonify(result)

@app.route('/generate_report', methods=['GET'])
@token_required
def generate_report_route():
    result = generate_report()
    return jsonify({'status': 'success', 'report': result})

if __name__ == '__main__':
    app.run(port=5000, debug=True)
