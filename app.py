from flask import Flask, jsonify, request
from flask_cors import CORS
from functools import wraps
import jwt
from jwt.exceptions import ExpiredSignatureError, InvalidTokenError
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'

# Enable CORS with explicit support for all methods
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

# Mock data and users (Replace with actual database models or external integrations)
users = {"user1": "password123"}
expenses = []
balances = {}

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
            request.user = data['username']  # Attach username to the request context
        except ExpiredSignatureError:
            return jsonify({'status': 'error', 'message': 'Token has expired!'}), 403
        except InvalidTokenError:
            return jsonify({'status': 'error', 'message': 'Invalid token!'}), 403

        return f(*args, **kwargs)

    return decorated

# Route to simulate login and issue JWT token
@app.route('/login', methods=['POST'])
def login():
    auth = request.json
    username = auth.get('username')
    password = auth.get('password')

    if username in users and users[username] == password:
        # Create JWT token
        token = jwt.encode(
            {'username': username, 'exp': datetime.utcnow() + timedelta(hours=1)},
            app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        return jsonify({'token': token})

    return jsonify({'status': 'error', 'message': 'Invalid credentials!'}), 401

# Route to register a new user
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if username in users:
        return jsonify({'status': 'error', 'message': 'User already exists!'}), 400

    users[username] = password
    return jsonify({'status': 'success', 'message': f'User {username} registered successfully!'})

# Route to add an expense
@app.route('/add_expense', methods=['POST'])
@token_required
def add_expense():
    data = request.json
    payer = data.get('payer')
    amount = data.get('amount')
    participants = data.get('participants')

    if not payer or not amount or not participants:
        return jsonify({'status': 'error', 'message': 'Missing required fields!'}), 400

    try:
        # Ensure amount is a number (convert it to float)
        amount = float(amount)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Amount must be a valid number!'}), 400

    expense = {
        "id": len(expenses) + 1,
        "payer": payer,
        "amount": amount,
        "participants": participants
    }
    expenses.append(expense)

    # Update balances (simplified logic)
    share = amount / len(participants)
    for participant in participants:
        if participant == payer:
            continue
        balances[participant] = balances.get(participant, 0) + share
        balances[payer] = balances.get(payer, 0) - share

    return jsonify({"status": "success", "message": "Expense added successfully!", "data": expense})

# Route to get all expenses
@app.route('/expenses', methods=['GET'])
@token_required
def get_expenses():
    return jsonify({"status": "success", "expenses": expenses})

# Route to get balances
@app.route('/balances', methods=['GET'])
@token_required
def get_balances():
    return jsonify({"status": "success", "balances": balances})

# Route to update an expense
@app.route('/expenses/<int:expense_id>', methods=['PUT'])
@token_required
def update_expense(expense_id):
    data = request.json
    expense = next((exp for exp in expenses if exp["id"] == expense_id), None)

    if not expense:
        return jsonify({'status': 'error', 'message': 'Expense not found!'}), 404

    expense.update({
        "payer": data.get('payer', expense["payer"]),
        "amount": data.get('amount', expense["amount"]),
        "participants": data.get('participants', expense["participants"])
    })

    return jsonify({"status": "success", "message": "Expense updated successfully!", "data": expense})

# Route to delete an expense
@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense(expense_id):
    global expenses
    expense = next((exp for exp in expenses if exp["id"] == expense_id), None)

    if not expense:
        return jsonify({'status': 'error', 'message': 'Expense not found!'}), 404

    expenses = [exp for exp in expenses if exp["id"] != expense_id]
    return jsonify({"status": "success", "message": "Expense deleted successfully!"})

# Route to generate a report (mock data)
@app.route('/report', methods=['GET'])
@token_required
def generate_report():
    report = {"total_expenses": len(expenses), "total_amount": sum(exp["amount"] for exp in expenses)}
    return jsonify({"status": "success", "report": report})

# Route to get user profile (mock data)
@app.route('/profile/<username>', methods=['GET'])
@token_required
def user_profile(username):
    if username not in users:
        return jsonify({'status': 'error', 'message': 'User not found!'}), 404

    return jsonify({
        "status": "success",
        "profile": {"username": username, "expenses_count": len([exp for exp in expenses if exp["payer"] == username])}
    })

if __name__ == '__main__':
    app.run(port=5000, debug=True)
