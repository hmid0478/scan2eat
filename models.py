from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)  # roll_number for students, username for admin
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='student')  # 'admin' or 'student'
    room_number = db.Column(db.String(50), nullable=True)  # Only for students
    wallet_balance = db.Column(db.Float, default=0.0)  # Only for students
    qr_code_path = db.Column(db.String(255), nullable=True)  # Only for students
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_active = db.Column(db.Boolean, default=True)

    # Relationships
    wallet_transactions = db.relationship('WalletTransaction', backref='user', lazy=True)
    attendances = db.relationship('Attendance', backref='user', lazy=True)

    def __repr__(self):
        return f'<User {self.username}>'

class WalletTransaction(db.Model):
    __tablename__ = 'wallet_transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)  # Positive for credit, negative for debit
    transaction_type = db.Column(db.String(50), nullable=False)  # 'credit', 'debit'
    description = db.Column(db.String(255), nullable=True)
    balance_after = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<WalletTransaction {self.id} - {self.transaction_type} - {self.amount}>'

class Meal(db.Model):
    __tablename__ = 'meals'

    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    meal_type = db.Column(db.String(50), nullable=False)  # 'breakfast', 'lunch', 'dinner'
    price = db.Column(db.Float, nullable=False)
    menu_items = db.Column(db.Text, nullable=True)  # Food items available (comma-separated or newline-separated)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationships
    attendances = db.relationship('Attendance', backref='meal', lazy=True)

    def __repr__(self):
        return f'<Meal {self.meal_type} on {self.date}>'

class Attendance(db.Model):
    __tablename__ = 'attendance'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    meal_id = db.Column(db.Integer, db.ForeignKey('meals.id'), nullable=False)
    amount_paid = db.Column(db.Float, nullable=False)
    scanned_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f'<Attendance {self.user_id} - Meal {self.meal_id}>'

class RefundRequest(db.Model):
    __tablename__ = 'refund_requests'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    attendance_id = db.Column(db.Integer, db.ForeignKey('attendance.id'), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    reason = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='pending')  # 'pending', 'approved', 'rejected'
    admin_remarks = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    processed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref='refund_requests')
    attendance = db.relationship('Attendance', backref='refund_request')

    def __repr__(self):
        return f'<RefundRequest {self.id} - {self.status}>'
