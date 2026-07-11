"""
Initialize database for job seeker app.
Creates auth + full jobs schema tables (SQLite or PostgreSQL).

This script is the single entry point for first-time setup. It creates
all tables previously split across init_database.py and create_jobs_schema.py.
Running create_jobs_schema.py afterward remains safe (idempotent).
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

COLUMN_MIGRATIONS = [
    ('applications', 'submission_status', 'VARCHAR(50)', 'VARCHAR(50)'),
    ('applications', 'submission_proof', 'VARCHAR(1024)', 'VARCHAR(1024)'),
    ('applications', 'submission_error', 'TEXT', 'TEXT'),
    ('applications', 'apply_batch_id', 'CHAR(36)', 'UUID'),
    ('applications', 'follow_up_at', 'DATETIME', 'TIMESTAMP'),
    ('apply_drafts', 'cover_letter', 'TEXT', 'TEXT'),
    ('job_search_profiles', 'indeed_max_age_days', 'INTEGER', 'INTEGER'),
    ('job_search_profiles', 'indeed_radius_miles', 'INTEGER', 'INTEGER'),
    ('job_search_profiles', 'ashby_boards', 'JSON', 'JSONB'),
]


def _auth_tables():
    from app.models.auth import Role, Group, User, FailedLogin, user_groups, user_roles, group_roles
    from app.models.rbac import Permission, UserRoleAssignment, RoleHierarchy, role_permissions
    from app.models.session import UserSession
    return [
        user_groups, user_roles, group_roles, role_permissions,
        Role.__table__, Group.__table__, Permission.__table__,
        User.__table__, FailedLogin.__table__,
        UserRoleAssignment.__table__, RoleHierarchy.__table__,
        UserSession.__table__,
    ]


def _jobs_tables():
    from app.models.jobs import (
        MasterProfile, JobPosting, ResumeVersion, Application,
        ApplicationActivity, KeywordAnalysis, ApplyDraft,
        JobSearchProfile, CompanyBlocklist, DiscoveryRun, DiscoveredJob,
        ApplyBatch, ApplyBatchItem, PortalCredential,
    )
    return [
        MasterProfile.__table__,
        JobPosting.__table__,
        ResumeVersion.__table__,
        Application.__table__,
        ApplicationActivity.__table__,
        KeywordAnalysis.__table__,
        ApplyDraft.__table__,
        JobSearchProfile.__table__,
        CompanyBlocklist.__table__,
        DiscoveryRun.__table__,
        DiscoveredJob.__table__,
        ApplyBatch.__table__,
        ApplyBatchItem.__table__,
        PortalCredential.__table__,
    ]


def _migrate_automation_columns(engine, db_type: str):
    from sqlalchemy import inspect
    schema = 'jobs' if db_type == 'postgresql' else None
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names(schema=schema))
    if not schema:
        existing_tables |= set(inspector.get_table_names())

    for table, column, sqlite_type, pg_type in COLUMN_MIGRATIONS:
        if table not in existing_tables:
            continue
        columns = {c['name'] for c in inspector.get_columns(table, schema=schema)}
        if column in columns:
            continue
        col_type = pg_type if db_type == 'postgresql' else sqlite_type
        qualified = f'"{schema}"."{table}"' if schema else f'"{table}"'
        db.session.execute(text(f'ALTER TABLE {qualified} ADD COLUMN {column} {col_type}'))
        print(f'Added column {table}.{column}')
    db.session.commit()


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

            print('Creating auth tables...')
            engine = db.engine
            for table in _auth_tables():
                table.create(engine, checkfirst=True)

            print('Creating jobs tables (full automation schema)...')
            for table in _jobs_tables():
                table.create(engine, checkfirst=True)

            if db_type == 'postgresql':
                print('Creating indexes...')
                db.session.execute(text("""
                    CREATE INDEX IF NOT EXISTS idx_master_profiles_user ON jobs.master_profiles(user_id);
                    CREATE INDEX IF NOT EXISTS idx_job_postings_user ON jobs.job_postings(user_id);
                    CREATE INDEX IF NOT EXISTS idx_applications_user ON jobs.applications(user_id);
                    CREATE INDEX IF NOT EXISTS idx_applications_stage ON jobs.applications(stage);
                    CREATE INDEX IF NOT EXISTS idx_resume_versions_job ON jobs.resume_versions(job_posting_id);
                """))
                db.session.commit()

            _migrate_automation_columns(engine, db_type)
            print('Database initialized successfully (auth + jobs)')
            print('Note: create_jobs_schema.py is still safe to run (idempotent).')
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
