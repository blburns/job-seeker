"""
Migrate existing jobs tables for full automation expansion.

Adds columns introduced after initial jobs schema (submission tracking,
apply batches, cover letters). Safe to run multiple times.

Usage:
    python scripts/migrate_jobs_automation.py
"""

import os
import sys
from typing import Optional

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import inspect, text

from app import create_app
from app.extensions.core import db

# (table_name, column_name, column_ddl_for_sqlite, column_ddl_for_postgresql)
COLUMN_MIGRATIONS = [
    (
        'applications',
        'submission_status',
        'VARCHAR(50)',
        'VARCHAR(50)',
    ),
    (
        'applications',
        'submission_proof',
        'VARCHAR(1024)',
        'VARCHAR(1024)',
    ),
    (
        'applications',
        'submission_error',
        'TEXT',
        'TEXT',
    ),
    (
        'applications',
        'apply_batch_id',
        'CHAR(36)',
        'UUID',
    ),
    (
        'applications',
        'follow_up_at',
        'DATETIME',
        'TIMESTAMP',
    ),
    (
        'apply_drafts',
        'cover_letter',
        'TEXT',
        'TEXT',
    ),
    (
        'job_search_profiles',
        'indeed_max_age_days',
        'INTEGER',
        'INTEGER',
    ),
    (
        'job_search_profiles',
        'indeed_radius_miles',
        'INTEGER',
        'INTEGER',
    ),
]


def _qualified_table(table: str, schema: Optional[str]) -> str:
    if schema:
        return f'"{schema}"."{table}"'
    return f'"{table}"'


def migrate_columns():
    app = create_app()
    db_type = os.environ.get('DB_TYPE', 'sqlite')
    schema = 'jobs' if db_type == 'postgresql' else None

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names(schema=schema))
        if not schema:
            existing_tables |= set(inspector.get_table_names())

        added = 0
        skipped = 0

        for table, column, sqlite_type, pg_type in COLUMN_MIGRATIONS:
            if table not in existing_tables:
                print(f'⚠️  Table {table} not found — run scripts/create_jobs_schema.py first')
                continue

            columns = {c['name'] for c in inspector.get_columns(table, schema=schema)}
            if column in columns:
                print(f'  skip {table}.{column} (exists)')
                skipped += 1
                continue

            col_type = pg_type if db_type == 'postgresql' else sqlite_type
            qualified = _qualified_table(table, schema)
            ddl = f'ALTER TABLE {qualified} ADD COLUMN {column} {col_type}'

            try:
                db.session.execute(text(ddl))
                db.session.commit()
                print(f'✅ Added {table}.{column}')
                added += 1
            except Exception as exc:
                db.session.rollback()
                print(f'❌ Failed to add {table}.{column}: {exc}')

        # Ensure any new tables exist
        from app.models.jobs import (
            ApplyBatch, ApplyBatchItem, CompanyBlocklist, DiscoveredJob,
            DiscoveryRun, JobSearchProfile, PortalCredential,
        )
        engine = db.engine
        for table in (
            JobSearchProfile.__table__,
            CompanyBlocklist.__table__,
            DiscoveryRun.__table__,
            DiscoveredJob.__table__,
            ApplyBatch.__table__,
            ApplyBatchItem.__table__,
            PortalCredential.__table__,
        ):
            table.create(engine, checkfirst=True)

        print(f'\nMigration complete: {added} added, {skipped} already present.')
        return True


if __name__ == '__main__':
    success = migrate_columns()
    sys.exit(0 if success else 1)
