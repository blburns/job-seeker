import os
import sys
from getpass import getpass
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from app.extensions.core import db
from app.main.models import User
from app.utils.security import validate_password_strength


def main():
    """Create a new user with the updated modular structure"""
    app = create_app()
    with app.app_context():
        print("=== User Creation Script ===")
        print("This script will create a new user in the Identity Provider system.\n")
        
        # Get user input
        username = input('Enter username: ').strip()
        email = input('Enter email: ').strip()
        password = getpass('Enter password: ').strip()
        confirm_password = getpass('Confirm password: ').strip()
        
        # Validate required fields
        if not username or not email or not password:
            print('❌ Username, email, and password are required.')
            return
        
        # Validate password confirmation
        if password != confirm_password:
            print('❌ Passwords do not match.')
            return
        
        # Validate password strength
        is_valid, message = validate_password_strength(password)
        if not is_valid:
            print(f'❌ Password validation failed: {message}')
            return
        
        # Check for existing user
        existing = User.query.filter(
            (User.username == username) | (User.email == email)
        ).first()
        
        if existing:
            print('❌ User with that username or email already exists.')
            return
        
        # Get role selection
        print('\nRole Selection:')
        print('1. Regular User (no admin privileges)')
        print('2. Admin (can manage users, view admin dashboard)')
        print('3. Superadmin (full system access, can manage admins)')
        
        role_choice = input('Select role [1-3]: ').strip()
        
        is_admin = False
        is_superadmin = False
        
        if role_choice == '2':
            is_admin = True
        elif role_choice == '3':
            is_admin = True
            is_superadmin = True
        elif role_choice != '1':
            print('❌ Invalid role selection. Defaulting to regular user.')
        
        # Create user
        try:
            user = User(
                username=username, 
                email=email, 
                is_admin=is_admin,
                is_superadmin=is_superadmin
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            print(f'\n✅ User "{username}" created successfully!')
            print(f'   Email: {email}')
            print(f'   Admin: {"Yes" if is_admin else "No"}')
            print(f'   Superadmin: {"Yes" if is_superadmin else "No"}')
            print(f'   User UUID: {user.user_uuid}')
            
            # Show role description
            if is_superadmin:
                print('   Role: Superadmin (full system access)')
            elif is_admin:
                print('   Role: Admin (user management access)')
            else:
                print('   Role: Regular User (standard access)')
            
        except Exception as e:
            db.session.rollback()
            print(f'❌ Error creating user: {e}')
            return


if __name__ == '__main__':
    main()
