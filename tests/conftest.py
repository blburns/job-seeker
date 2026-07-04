"""Pytest configuration for job seeker automation tests."""

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import pytest

os.environ.setdefault('FLASK_ENV', 'testing')
os.environ.setdefault('DB_TYPE', 'sqlite')
os.environ.setdefault('DB_NAME', ':memory:')
os.environ.setdefault('TESTING', 'True')
os.environ.setdefault('WTF_CSRF_ENABLED', 'False')


@pytest.fixture
def app():
    from app import create_app
    from app.extensions.core import db

    application = create_app('testing')
    application.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
    })
    with application.app_context():
        db.create_all()
        yield application
        db.session.remove()
        db.drop_all()


@pytest.fixture
def db_session(app):
    from app.extensions.core import db
    with app.app_context():
        yield db.session


@pytest.fixture
def sample_master_profile():
    return {
        'contact': {'name': 'Jane Doe', 'email': 'jane@example.com'},
        'experience': [
            {
                'company': 'Acme',
                'title': 'Engineer',
                'bullets': [
                    {'id': 'b1', 'text': 'Built Python APIs'},
                    {'id': 'b2', 'text': 'Led team of 3'},
                ],
            }
        ],
        'skills': ['Python', 'Flask', 'SQL'],
    }
