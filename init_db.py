"""
Database initialization script for Scan2Eat
Run this script to create all database tables and add default admin user
"""

from app import app, db, hash_password
from models import User

def init_database():
    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")

        # Check if admin user exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            # Create default admin user
            admin_user = User(
                username='admin',
                password_hash=hash_password('admin123'),
                name='Administrator',
                role='admin'
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Default admin user created!")
            print("Username: admin")
            print("Password: admin123")
            print("\n*** Please change the admin password after first login! ***")
        else:
            print("Admin user already exists.")

        print("\nDatabase initialization complete!")

if __name__ == '__main__':
    init_database()
