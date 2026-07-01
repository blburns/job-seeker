from app import create_app
from app.extensions.core import db
from app.models.auth import User

app = create_app()

with app.app_context():
    print("--- Admin Users ---")
    admins = User.query.filter((User.is_admin == True) | (User.is_superadmin == True)).all()
    for u in admins:
        print(f"User: {u.username} (ID: {u.id})")
        print(f"  - is_admin: {u.is_admin}")
        print(f"  - is_superadmin: {u.is_superadmin}")
        print(f"  - Active: {u.is_active}")
        print("-" * 20)
    
    if not admins:
        print("No admin users found!")
