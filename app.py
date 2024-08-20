from flask import Flask, request, jsonify
import jwt
from functools import wraps
from model import db, User, Expense, Settlement
from service import (
    add_user, authenticate, add_expense, get_expenses, update_expense, delete_expense,
    get_balances, generate_report, record_settlement, get_user_profile
)

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///expenses.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'zaki'

db.init_app(app)

with app.app_context():
    db.create_all()

SECRET_KEY = app.config['SECRET_KEY']

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'status': 'error', 'message': 'Token is missing!'}), 403
        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
        except:
            return jsonify({'status': 'error', 'message': 'Token is invalid!'}), 403
        return f(*args, **kwargs)
    return decorated

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    result = add_user(data['username'], data['email'], data['password'])
    return jsonify(result)

@app.route('/login', methods=['POST'])
def login():
    data = request.json
    result = authenticate(data['username'], data['password'])
    return jsonify(result)

@app.route('/add_expense', methods=['POST'])
@token_required
def add_expense_route():
    data = request.json
    result = add_expense(data['payer'], data['amount'], data['participants'])
    return jsonify(result)

@app.route('/expenses', methods=['GET'])
@token_required
def expenses_route():
    result = get_expenses()
    return jsonify(result)

@app.route('/expenses/<int:expense_id>', methods=['PUT'])
@token_required
def update_expense_route(expense_id):
    data = request.json
    result = update_expense(expense_id, data['amount'], data['participants'])
    return jsonify(result)

@app.route('/expenses/<int:expense_id>', methods=['DELETE'])
@token_required
def delete_expense_route(expense_id):
    result = delete_expense(expense_id)
    return jsonify(result)

@app.route('/balances', methods=['GET'])
@token_required
def balances_route():
    result = get_balances()
    return jsonify(result)

@app.route('/report', methods=['GET'])
@token_required
def report_route():
    result = generate_report()
    return jsonify(result)

@app.route('/settle', methods=['POST'])
@token_required
def settle():
    data = request.json
    result = record_settlement(data['expense_id'], data['payer'], data['payee'], data['amount'])
    return jsonify(result)

@app.route('/profile/<username>', methods=['GET'])
@token_required
def user_profile(username):
    result = get_user_profile(username)
    return jsonify(result)

if __name__ == '__main__':
    app.run(port=8080, debug=True)
