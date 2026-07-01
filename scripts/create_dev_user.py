#!/usr/bin/env python3
"""Create a default admin user for local development."""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.extensions.core import db
from app.models.auth import User


def create_dev_user():
    app = create_app()
    with app.app_context():
        email = os.environ.get('DEV_USER_EMAIL', 'admin@example.com')
        password = os.environ.get('DEV_USER_PASSWORD', 'admin123')
        existing = User.query.filter_by(email=email).first()
        if existing:
            print(f'User {email} already exists')
            return True
        user = User(
            username='admin',
            email=email,
            firstname='Admin',
            lastname='User',
            is_active=True,
            is_admin=True,
            is_superadmin=True,
            email_verified=True,
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f'Created dev user: {email} / {password}')
        return True


if __name__ == '__main__':
    create_dev_user()
