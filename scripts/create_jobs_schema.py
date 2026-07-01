"""
Create Jobs Schema and Tables
Creates the jobs schema and all required tables for the job seeker module
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

JOBS_TABLES = None


def _get_jobs_tables():
    global JOBS_TABLES
    if JOBS_TABLES is None:
        from app.models.jobs import (
            MasterProfile, JobPosting, ResumeVersion, Application,
            ApplicationActivity, KeywordAnalysis, ApplyDraft,
        )
        JOBS_TABLES = [
            MasterProfile.__table__,
            JobPosting.__table__,
            ResumeVersion.__table__,
            Application.__table__,
            ApplicationActivity.__table__,
            KeywordAnalysis.__table__,
            ApplyDraft.__table__,
        ]
    return JOBS_TABLES


def create_jobs_schema():
    app = create_app()
    db_type = os.environ.get('DB_TYPE', 'sqlite')

    with app.app_context():
        try:
            if db_type == 'postgresql':
                print('Creating jobs schema...')
                db.session.execute(text('CREATE SCHEMA IF NOT EXISTS jobs'))
                db.session.commit()
                print('Jobs schema created')

            print('Creating jobs tables...')
            engine = db.engine
            for table in _get_jobs_tables():
                table.create(engine, checkfirst=True)
            print('Jobs tables created')

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
                print('Indexes created')

            print('\nJob seeker schema ready.')
            return True
        except Exception as exc:
            db.session.rollback()
            print(f'Error creating jobs schema: {exc}')
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    success = create_jobs_schema()
    sys.exit(0 if success else 1)
