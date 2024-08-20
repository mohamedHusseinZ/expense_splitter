from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    hashed_password = db.Column(db.String(128), nullable=False)

    expenses = db.relationship('Expense', backref='payer_user', lazy=True)
    
    # Specify foreign_keys for settlements
    settlements = db.relationship(
        'Settlement', 
        foreign_keys='Settlement.payer_id', 
        backref='payer_user', 
        lazy=True
    )
    
    settlements_as_payee = db.relationship(
        'Settlement', 
        foreign_keys='Settlement.payee_id', 
        backref='payee_user', 
        lazy=True
    )

class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    participants = db.Column(db.PickleType, nullable=False)  # List of participant usernames
    
    settlements = db.relationship('Settlement', backref='expense', lazy=True)

class Settlement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expense_id = db.Column(db.Integer, db.ForeignKey('expense.id'), nullable=False)
    
    payer_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    
    payee_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
