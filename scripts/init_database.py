"""
Initialize database for job seeker app.
Creates auth and jobs tables (SQLite or PostgreSQL).
"""

import os
import sys

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app import create_app
from app.extensions.core import db


def _essential_tables():
    from app.models.auth import Role, Group, User, FailedLogin, user_groups, user_roles, group_roles
    from app.models.rbac import Permission, UserRoleAssignment, RoleHierarchy, role_permissions
    from app.models.session import UserSession
    from app.models.jobs import (
        MasterProfile, JobPosting, ResumeVersion, Application,
        ApplicationActivity, KeywordAnalysis, ApplyDraft,
    )
    return [
        user_groups, user_roles, group_roles, role_permissions,
        Role.__table__, Group.__table__, Permission.__table__,
        User.__table__, FailedLogin.__table__,
        UserRoleAssignment.__table__, RoleHierarchy.__table__,
        UserSession.__table__,
        MasterProfile.__table__, JobPosting.__table__, ResumeVersion.__table__,
        Application.__table__, ApplicationActivity.__table__,
        KeywordAnalysis.__table__, ApplyDraft.__table__,
    ]


def init_database():
    app = create_app()
    db_type = os.environ.get('DB_TYPE', 'sqlite')

    with app.app_context():
        try:
            if db_type == 'postgresql':
                for schema in ('auth', 'jobs'):
                    db.session.execute(text(f'CREATE SCHEMA IF NOT EXISTS {schema}'))
                db.session.commit()
                print('PostgreSQL schemas created')

            print('Creating essential tables...')
            engine = db.engine
            for table in _essential_tables():
                table.create(engine, checkfirst=True)
            print('Database initialized successfully')
            return True
        except Exception as exc:
            db.session.rollback()
            print(f'Error initializing database: {exc}')
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
