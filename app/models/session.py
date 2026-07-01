"""
Session Management Model
Tracks active user sessions for security and management
"""

import uuid
from datetime import datetime, timedelta
from app.extensions.core import db
from app.models.base import ID_TYPE
from app.models.schema_utils import db_schema, fk_ref

_AUTH_SCHEMA = db_schema('auth')


def _json_type():
    import os
    if os.environ.get('DB_TYPE', 'sqlite') == 'postgresql':
        from sqlalchemy.dialects.postgresql import JSONB
        return JSONB
    from sqlalchemy import JSON
    return JSON


class UserSession(db.Model):
    """User session model for tracking active sessions"""
    __tablename__ = 'user_sessions'
    __table_args__ = _AUTH_SCHEMA

    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='CASCADE'), nullable=False, index=True)
    session_token = db.Column(db.String(255), unique=True, nullable=False, index=True)

    device_info = db.Column(_json_type(), nullable=True)
    ip_address = db.Column(db.String(45), nullable=True)
    user_agent = db.Column(db.Text, nullable=True)

    last_activity = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    remember_me = db.Column(db.Boolean, default=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    revoked_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('sessions', lazy='dynamic', cascade='all, delete-orphan'))

    def __repr__(self):
        return f'<UserSession {self.id} for user {self.user_id}>'

    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    def is_valid(self):
        return self.is_active and not self.is_expired()

    def revoke(self):
        self.is_active = False
        self.revoked_at = datetime.utcnow()

    def update_activity(self):
        self.last_activity = datetime.utcnow()

    def extend_expiration(self, days=30):
        self.expires_at = datetime.utcnow() + timedelta(days=days)
        self.remember_me = True

    @property
    def device_name(self):
        if not self.device_info:
            return 'Unknown Device'
        browser = self.device_info.get('browser', 'Unknown Browser')
        os_name = self.device_info.get('os', 'Unknown OS')
        device = self.device_info.get('device', '')
        if device:
            return f"{browser} on {device}"
        return f"{browser} on {os_name}"

    @property
    def location(self):
        return self.ip_address or 'Unknown'

    def to_dict(self):
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'device_name': self.device_name,
            'device_info': self.device_info,
            'ip_address': self.ip_address,
            'location': self.location,
            'last_activity': self.last_activity.isoformat() if self.last_activity else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'is_active': self.is_active,
            'is_expired': self.is_expired(),
            'remember_me': self.remember_me,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'revoked_at': self.revoked_at.isoformat() if self.revoked_at else None,
        }

    @classmethod
    def create_session(cls, user_id, session_token, request, remember_me=False):
        from app.utils.device_parser import parse_user_agent
        device_info = parse_user_agent(request.user_agent.string if request.user_agent else None)
        expires_at = datetime.utcnow() + timedelta(days=30 if remember_me else 1)
        return cls(
            user_id=user_id,
            session_token=session_token,
            device_info=device_info,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string if request.user_agent else None,
            expires_at=expires_at,
            remember_me=remember_me,
        )
