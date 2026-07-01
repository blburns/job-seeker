"""
Accounts Schema Models
Business account management models
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions.core import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


class AccountType(db.Model):
    """Account type classifications"""
    __tablename__ = 'account_types'
    __table_args__ = {'schema': 'accounts'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(32), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    sort_order = db.Column(db.Integer, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = db.relationship('Account', back_populates='account_type')
    
    def __repr__(self):
        return f'<AccountType {self.name}>'


class AccountCategory(db.Model):
    """Account category classifications"""
    __tablename__ = 'account_categories'
    __table_args__ = {'schema': 'accounts'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), nullable=False)
    description = db.Column(db.Text, nullable=True)
    color = db.Column(db.String(32), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    accounts = db.relationship('Account', back_populates='category')
    
    def __repr__(self):
        return f'<AccountCategory {self.name}>'


class Account(BaseModel, SoftDeleteMixin):
    """Account model for managing business accounts"""
    __tablename__ = 'accounts'
    __table_args__ = {'schema': 'accounts'}
    
    account_uuid = db.Column(UUID(as_uuid=True), unique=True, default=uuid.uuid4, index=True)
    
    # Basic information
    account_name = db.Column(db.String(128), nullable=False, index=True)
    account_number = db.Column(db.String(64), nullable=True, unique=True, index=True)
    legal_name = db.Column(db.String(128), nullable=True)
    
    # Account classification
    account_type_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.account_types.id'), nullable=True)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.account_categories.id'), nullable=True)
    status = db.Column(db.String(32), default='active')
    
    # Contact information
    primary_email = db.Column(db.String(120), nullable=True, index=True)
    primary_phone = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    
    # Address information
    billing_address_line1 = db.Column(db.String(128), nullable=True)
    billing_address_line2 = db.Column(db.String(128), nullable=True)
    billing_city = db.Column(db.String(64), nullable=True)
    billing_state_province = db.Column(db.String(64), nullable=True)
    billing_postal_code = db.Column(db.String(20), nullable=True)
    billing_country = db.Column(db.String(64), nullable=True)
    
    shipping_address_line1 = db.Column(db.String(128), nullable=True)
    shipping_address_line2 = db.Column(db.String(128), nullable=True)
    shipping_city = db.Column(db.String(64), nullable=True)
    shipping_state_province = db.Column(db.String(64), nullable=True)
    shipping_postal_code = db.Column(db.String(20), nullable=True)
    shipping_country = db.Column(db.String(64), nullable=True)
    
    # Business information
    industry = db.Column(db.String(64), nullable=True)
    company_size = db.Column(db.String(64), nullable=True)
    annual_revenue = db.Column(db.String(64), nullable=True)
    tax_id = db.Column(db.String(64), nullable=True)
    registration_number = db.Column(db.String(64), nullable=True)
    
    # Financial information
    credit_limit = db.Column(db.Numeric, nullable=True)
    payment_terms = db.Column(db.String(64), nullable=True)
    currency = db.Column(db.String(10), nullable=True)
    
    # Relationships
    parent_account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.accounts.id'), nullable=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.users.id'), nullable=True)
    
    # Additional fields
    notes = db.Column(db.Text, nullable=True)
    tags = db.Column(db.JSON, nullable=True)
    custom_fields = db.Column(db.JSON, nullable=True)
    last_activity_date = db.Column(db.DateTime, nullable=True)
    last_contacted = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    account_type = db.relationship('AccountType', back_populates='accounts')
    category = db.relationship('AccountCategory', back_populates='accounts')
    parent_account = db.relationship('Account', remote_side='Account.id', backref='child_accounts')
    activities = db.relationship('AccountActivity', back_populates='account')
    
    def __repr__(self):
        return f'<Account {self.account_name}>'


class AccountActivity(db.Model):
    """Account activity tracking"""
    __tablename__ = 'account_activities'
    __table_args__ = {'schema': 'accounts'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_id = db.Column(UUID(as_uuid=True), db.ForeignKey('accounts.accounts.id'), nullable=False)
    activity_type = db.Column(db.String(64), nullable=False)
    subject = db.Column(db.String(255), nullable=True)
    description = db.Column(db.Text, nullable=True)
    activity_date = db.Column(db.DateTime, nullable=True)
    outcome = db.Column(db.String(64), nullable=True)
    duration = db.Column(db.Integer, nullable=True)
    priority = db.Column(db.String(32), nullable=True)
    related_entity_type = db.Column(db.String(64), nullable=True)
    related_entity_id = db.Column(UUID(as_uuid=True), nullable=True)
    created_by = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    account = db.relationship('Account', back_populates='activities')
    
    def __repr__(self):
        return f'<AccountActivity {self.activity_type}>'


class AccountSetting(db.Model):
    """Account-specific settings"""
    __tablename__ = 'account_settings'
    __table_args__ = {'schema': 'accounts'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_key = db.Column(db.String(128), nullable=False)
    json_data = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<AccountSetting {self.setting_key}>'
