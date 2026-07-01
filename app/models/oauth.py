"""
OAuth Account Model
Links external OAuth providers (Google, Microsoft, GitHub) to user accounts
"""

import uuid
from datetime import datetime
from app.extensions.core import db
from app.models.base import ID_TYPE
from app.models.schema_utils import auth_table_args, fk_ref


class OAuthAccount(db.Model):
    """OAuth account linking model"""
    __tablename__ = 'oauth_accounts'

    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='CASCADE'), nullable=False, index=True)
    provider = db.Column(db.String(50), nullable=False, index=True)
    provider_user_id = db.Column(db.String(255), nullable=False)
    access_token = db.Column(db.Text, nullable=True)
    refresh_token = db.Column(db.Text, nullable=True)
    token_expires_at = db.Column(db.DateTime, nullable=True)
    provider_email = db.Column(db.String(255), nullable=True)
    provider_name = db.Column(db.String(255), nullable=True)
    provider_picture = db.Column(db.String(500), nullable=True)
    provider_data = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('oauth_accounts', lazy='dynamic', cascade='all, delete-orphan'))

    __table_args__ = auth_table_args(
        db.UniqueConstraint('provider', 'provider_user_id', name='uq_oauth_provider_user'),
    )

    def __repr__(self):
        return f'<OAuthAccount {self.provider}:{self.provider_user_id}>'

    @classmethod
    def find_by_provider(cls, provider, provider_user_id):
        return cls.query.filter_by(provider=provider, provider_user_id=provider_user_id).first()

    @classmethod
    def find_by_user_and_provider(cls, user_id, provider):
        return cls.query.filter_by(user_id=user_id, provider=provider).first()

    def update_tokens(self, access_token, refresh_token=None, expires_at=None):
        self.access_token = access_token
        if refresh_token:
            self.refresh_token = refresh_token
        if expires_at:
            self.token_expires_at = expires_at
        self.updated_at = datetime.utcnow()

    def update_profile(self, email=None, name=None, picture=None, data=None):
        if email:
            self.provider_email = email
        if name:
            self.provider_name = name
        if picture:
            self.provider_picture = picture
        if data:
            self.provider_data = data
        self.updated_at = datetime.utcnow()

    def mark_used(self):
        self.last_used_at = datetime.utcnow()

    @property
    def is_token_expired(self):
        if not self.token_expires_at:
            return False
        return datetime.utcnow() >= self.token_expires_at
