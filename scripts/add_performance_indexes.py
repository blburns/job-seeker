#!/usr/bin/env python3
"""
Add performance indexes for critical queries (Phase 1.5).
PostgreSQL only. Idempotent (uses IF NOT EXISTS where supported).
Run: python scripts/add_performance_indexes.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import create_app
from app.extensions.core import db
from sqlalchemy import text


INDEXES = [
    # auth.user_sessions: cleanup and list-by-user
    ("auth.user_sessions (expires_at)", "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_auth_user_sessions_expires_at ON auth.user_sessions (expires_at)"),
    ("auth.user_sessions (user_id, is_active)", "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_auth_user_sessions_user_id_is_active ON auth.user_sessions (user_id, is_active)"),
    # auth.failed_logins: recent attempts reports
    ("auth.failed_logins (attempted_at)", "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_auth_failed_logins_attempted_at ON auth.failed_logins (attempted_at)"),
    # emails.email_logs: admin reports by template and time
    ("emails.email_logs (template)", "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_emails_email_logs_template ON emails.email_logs (template)"),
    ("emails.email_logs (created_at)", "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_emails_email_logs_created_at ON emails.email_logs (created_at)"),
    # auth.user_role_assignments: active assignments lookup
    ("auth.user_role_assignments (user_id, is_active)", "CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_auth_user_role_assignments_user_active ON auth.user_role_assignments (user_id, is_active)"),
]


def main():
    app = create_app()
    with app.app_context():
        url = str(db.engine.url)
        if "postgresql" not in url and "postgres" not in url:
            print("Skipping: this script is for PostgreSQL. Current DB:", url.split("?")[0])
            return 0

        print("Adding performance indexes (PostgreSQL)...")
        for name, sql in INDEXES:
            try:
                # CONCURRENTLY must run outside a transaction (autocommit)
                with db.engine.connect().execution_options(isolation_level="AUTOCOMMIT") as conn:
                    conn.execute(text(sql))
                print("  OK:", name)
            except Exception as e:
                # If CONCURRENTLY fails (e.g. inside transaction), try without it
                if "CONCURRENTLY" in sql:
                    simple_sql = sql.replace("CREATE INDEX CONCURRENTLY IF NOT EXISTS", "CREATE INDEX IF NOT EXISTS")
                    try:
                        db.session.execute(text(simple_sql))
                        db.session.commit()
                        print("  OK (non-concurrent):", name)
                    except Exception as e2:
                        print("  SKIP:", name, "-", e2)
                else:
                    print("  SKIP:", name, "-", e)
        print("Done.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
