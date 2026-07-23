#!/usr/bin/env python
"""Create an initial admin user in the database."""
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(
            username='admin',
            email='admin@movie.rec',
            password_hash=generate_password_hash('admin123'),
            is_admin=True
        )
        db.session.add(admin)
        db.session.commit()
        print("Admin user 'admin' (password: admin123) created!")
    else:
        print("Admin user already exists.")
