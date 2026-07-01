"""
Settings Schema Models
Application settings and configuration models
"""

import uuid
from datetime import datetime
from sqlalchemy.dialects.postgresql import UUID
from app.extensions.core import db
from app.models.base import BaseModel, TimestampMixin


class SettingCategory(db.Model):
    """Settings category classifications"""
    __tablename__ = 'setting_categories'
    __table_args__ = {'schema': 'settings'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = db.Column(db.String(64), nullable=False)
    display_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    sort_order = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    settings = db.relationship('Setting', back_populates='category')
    
    def __repr__(self):
        return f'<SettingCategory {self.name}>'


class Setting(db.Model):
    """Core settings table"""
    __tablename__ = 'settings'
    __table_args__ = {'schema': 'settings'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = db.Column(db.String(128), nullable=False, unique=True)
    name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    category_id = db.Column(UUID(as_uuid=True), db.ForeignKey('settings.setting_categories.id'), nullable=True)
    setting_type = db.Column(db.String(32), nullable=False)
    data_type = db.Column(db.String(32), nullable=False)
    default_value = db.Column(db.Text, nullable=True)
    current_value = db.Column(db.Text, nullable=True)
    is_required = db.Column(db.Boolean, default=False)
    is_encrypted = db.Column(db.Boolean, default=False)
    is_readonly = db.Column(db.Boolean, default=False)
    validation_rules = db.Column(db.JSON, nullable=True)
    sort_order = db.Column(db.Integer, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    user_id = db.Column(UUID(as_uuid=True), db.ForeignKey('auth.users.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    category = db.relationship('SettingCategory', back_populates='settings')
    values = db.relationship('SettingValue', back_populates='setting')
    overrides = db.relationship('SettingOverride', back_populates='setting')
    
    def __repr__(self):
        return f'<Setting {self.key}>'


class SettingValue(db.Model):
    """Historical setting values (audit trail)"""
    __tablename__ = 'setting_values'
    __table_args__ = {'schema': 'settings'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_id = db.Column(UUID(as_uuid=True), db.ForeignKey('settings.settings.id'), nullable=False)
    value = db.Column(db.Text, nullable=True)
    previous_value = db.Column(db.Text, nullable=True)
    changed_by = db.Column(db.String(64), nullable=True)
    change_reason = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    setting = db.relationship('Setting', back_populates='values')
    
    def __repr__(self):
        return f'<SettingValue {self.setting_id}>'


class SettingOverride(db.Model):
    """Environment-specific setting overrides"""
    __tablename__ = 'setting_overrides'
    __table_args__ = {'schema': 'settings'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    setting_id = db.Column(UUID(as_uuid=True), db.ForeignKey('settings.settings.id'), nullable=False)
    environment = db.Column(db.String(32), nullable=False)
    value = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    setting = db.relationship('Setting', back_populates='overrides')
    
    def __repr__(self):
        return f'<SettingOverride {self.environment}>'


class ModuleSetting(db.Model):
    """Module-specific JSON configurations"""
    __tablename__ = 'module_settings'
    __table_args__ = {'schema': 'settings'}
    
    id = db.Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    module_name = db.Column(db.String(64), nullable=False, index=True)
    setting_key = db.Column(db.String(128), nullable=False)
    setting_name = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    json_data = db.Column(db.JSON, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(64), nullable=True)
    updated_by = db.Column(db.String(64), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<ModuleSetting {self.module_name}.{self.setting_key}>'
