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
    from app.extensions.core import db, login_manager

    application = create_app('testing')
    application.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': 'sqlite:///:memory:',
        'WTF_CSRF_ENABLED': False,
        'LOGIN_DISABLED': False,
    })
    # Strong session protection clears manually seeded test sessions
    login_manager.session_protection = None
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
def client(app):
    return app.test_client()


@pytest.fixture
def test_user(app, db_session):
    from app.models.auth import User

    user = User(
        username='testuser',
        email='test@example.com',
        is_active=True,
        email_verified=True,
    )
    user.set_password('testpass123')
    db_session.add(user)
    db_session.commit()
    return user


@pytest.fixture
def auth_client(client, test_user):
    """Flask test client with an authenticated session."""
    with client.session_transaction() as sess:
        sess['_user_id'] = str(test_user.id)
        sess['_fresh'] = True
    return client


@pytest.fixture
def sample_master_profile():
    return {
        'contact': {
            'name': 'Jane Doe',
            'email': 'jane@example.com',
            'phone': '555-0100',
            'location': 'Remote',
        },
        'headline': 'Software Engineer',
        'summary': 'Experienced Python engineer.',
        'summary_variants': [{'text': 'Experienced Python engineer.'}],
        'experience': [
            {
                'company': 'Acme',
                'title': 'Engineer',
                'start': '2020-01',
                'end': 'Present',
                'bullets': [
                    {'id': 'b1', 'text': 'Built Python APIs with Flask'},
                    {'id': 'b2', 'text': 'Led team of 3 engineers'},
                    {'id': 'b3', 'text': 'Deployed services on AWS'},
                ],
            }
        ],
        'education': [
            {'institution': 'State University', 'degree': 'BS Computer Science', 'end': '2019'}
        ],
        'skills': {
            'technical': ['Python', 'Flask', 'SQL', 'AWS'],
            'certifications': [],
        },
    }
