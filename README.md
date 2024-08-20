
# expense_splitter

Expense Splitter Application
The Expense Splitter app helps groups of people split expenses and track who owes what. It provides functionality for user authentication, adding expenses, viewing balances, settling payments, and generating reports. The app is built using Python, Flask, and SQLAlchemy.

Features
User Registration and Authentication: Users can register and log in to the system. JSON Web Tokens (JWT) are used for secure API access.
Expense Management: Users can add, update, delete, and retrieve expenses.
Balance Tracking: The app calculates the balance between users based on their shared expenses.
Expense Settlement: Allows users to settle their balances.
Reporting: Generates a detailed report of expenses.
Technologies Used
Python: The core programming language.
Flask: The web framework.
SQLAlchemy: ORM for interacting with the SQLite database.
JWT: For secure authentication.
SQLite: Database for storing expenses and user information.
Setup Instructions
Prerequisites
Python 3.x installed on your machine.
pip to install the dependencies.
Installation
Clone the repository:

bash
Copy code
git clone https://github.com/mohamedHusseinZ/expense-splitter.git
cd expense-splitter
Create and activate a virtual environment:

bash
Copy code
python3 -m venv venv
source venv/bin/activate
Install dependencies:

bash
Copy code
pip install -r requirements.txt
Run the application:

bash
Copy code
python app.py
The application will be available at http://localhost:8080.

Database Initialization
The database will be automatically created when you first run the application. The models are initialized in the model.py file and will be created using SQLAlchemy.

API Endpoints
Authentication
Register:

Endpoint: /register
Method: POST
Body:
json
Copy code
{
  "username": "your_username",
  "email": "your_email",
  "password": "your_password"
}
Login:

Endpoint: /login
Method: POST
Body:
json
Copy code
{
  "username": "your_username",
  "password": "your_password"
}
Expenses
Add Expense:

Endpoint: /add_expense
Method: POST
Body:
json
Copy code
{
  "payer": "payer_username",
  "amount": 100,
  "participants": ["participant1", "participant2"]
}
Requires a valid JWT token in the Authorization header.
View Expenses:

Endpoint: /expenses
Method: GET
Requires a valid JWT token.
Update Expense:

Endpoint: /expenses/<expense_id>
Method: PUT
Body:
json
Copy code
{
  "amount": 150,
  "participants": ["participant1", "participant2"]
}
Requires a valid JWT token.
Delete Expense:

Endpoint: /expenses/<expense_id>
Method: DELETE
Requires a valid JWT token.
Balances and Settlements
View Balances:

Endpoint: /balances
Method: GET
Requires a valid JWT token.
Settle Expenses:

Endpoint: /settle
Method: POST
Body:
json
Copy code
{
  "expense_id": 1,
  "payer": "payer_username",
  "payee": "payee_username",
  "amount": 50
}
Requires a valid JWT token.
Reporting
Generate Report:
Endpoint: /report
Method: GET
Requires a valid JWT token.
User Profile
View User Profile:
Endpoint: /profile/<username>
Method: GET
Requires a valid JWT token.
Token Usage
All endpoints, except for /register and /login, require a valid JWT token in the Authorization header as follows:

makefile
Copy code
Authorization: Bearer <your_token>
License
This project is licensed under the MIT License.
