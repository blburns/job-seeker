#!/usr/bin/env python3
"""
Rebuild migrations directory logically
"""
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask
from flask_migrate import Migrate
from app.extensions.core import db
from config.app_config import AppConfig

# Import all models to ensure they're registered
from app.main.models import User, Role, Group, user_groups, user_roles, group_roles
from app.models.contact import Contact, ContactCategory, ContactCommunication
from app.models.document import Document, DocumentCategory, DocumentAccessLog
from app.models.organization import Organization, Brand, OrganizationMember
from app.models.tenant import Tenant, TenantInvitation, TenantSettings, TenantUsage
from app.modules.settings.models import (
    Setting, SettingCategory, SettingValue, SettingOverride, ModuleSetting
)

app = Flask(__name__)
app.config.from_object(AppConfig)
db.init_app(app)

migrate = Migrate(app, db)

def rebuild_migrations():
    """Generate fresh migrations from models"""
    with app.app_context():
        # Create migration for initial schema
        print("Creating initial schema migration...")
        
        # Try to create the initial migration
        # This will be done via command line, so we'll just prepare the environment
        
        print("\nTo complete the migration rebuild, run:")
        print("  flask db init")
        print("  flask db migrate -m 'Initial schema'")
        print("  flask db upgrade")
        
        # For now, let's just show what we're going to do
        print("\nMigrations will be organized as:")
        print("  1. Initial schema migration (all tables)")
        print("  2. Data migrations (seed data)")
        print("  3. Feature migrations (as features are added)")

if __name__ == '__main__':
    rebuild_migrations()

