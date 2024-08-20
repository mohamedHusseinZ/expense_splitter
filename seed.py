from model import db, User, Expense, Settlement
from service import add_user, add_expense, record_settlement
from app import app  # Import the app object

# Initialize the database
with app.app_context():
    db.drop_all()
    db.create_all()

    # Add some users
    users = [
        {'username': 'Alice', 'email': 'alice@example.com', 'password': 'password123'},
        {'username': 'Bob', 'email': 'bob@example.com', 'password': 'password123'},
        {'username': 'Charlie', 'email': 'charlie@example.com', 'password': 'password123'},
    ]

    for user in users:
        add_user(user['username'], user['email'], user['password'])

    # Add some expenses
    response_expense1 = add_expense('Alice', 100.0, ['Alice', 'Bob'])
    response_expense2 = add_expense('Bob', 150.0, ['Bob', 'Charlie'])
    response_expense3 = add_expense('Charlie', 200.0, ['Alice', 'Bob', 'Charlie'])

    # Use the 'id' from the response dictionary
    expense1_id = response_expense1.get('expense', {}).get('id')
    expense2_id = response_expense2.get('expense', {}).get('id')
    expense3_id = response_expense3.get('expense', {}).get('id')

    if expense1_id:
        record_settlement(expense1_id, 'Alice', 'Bob', 50.0)
    if expense2_id:
        record_settlement(expense2_id, 'Bob', 'Charlie', 75.0)
    if expense3_id:
        record_settlement(expense3_id, 'Charlie', 'Alice', 66.67)
        record_settlement(expense3_id, 'Charlie', 'Bob', 66.67)

    print("Database seeded successfully!")
