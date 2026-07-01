"""
Base Model Classes
Common base classes for all database models with schema support
"""

import os
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from sqlalchemy import Column, DateTime, Boolean, String, TypeDecorator, CHAR
from app.extensions.core import db


class GUID(TypeDecorator):
    """Platform-independent GUID type."""
    impl = CHAR
    cache_ok = True

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            from sqlalchemy.dialects.postgresql import UUID
            return dialect.type_descriptor(UUID(as_uuid=True))
        return dialect.type_descriptor(CHAR(36))

    def process_bind_param(self, value, dialect):
        if value is None:
            return value
        if dialect.name == 'postgresql':
            return value
        if isinstance(value, uuid.UUID):
            return str(value)
        return str(value)

    def process_result_value(self, value, dialect):
        if value is None:
            return value
        if isinstance(value, uuid.UUID):
            return value
        return uuid.UUID(str(value))


ID_TYPE = GUID()


class TimestampMixin:
    """Mixin for created_at and updated_at timestamps"""
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)


class SoftDeleteMixin:
    """Mixin for soft delete functionality"""
    is_deleted = Column(Boolean, default=False, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
    
    def soft_delete(self):
        """Soft delete the record"""
        self.is_deleted = True
        self.deleted_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def restore(self):
        """Restore a soft-deleted record"""
        self.is_deleted = False
        self.deleted_at = None
        self.updated_at = datetime.utcnow()


class BaseModel(db.Model, TimestampMixin):
    """Abstract base model with common fields and functionality"""
    
    __abstract__ = True
    
    # Primary key
    id = Column(ID_TYPE, primary_key=True, default=uuid.uuid4, nullable=False)
    
    def __repr__(self):
        """String representation of the model"""
        return f'<{self.__class__.__name__} {self.id}>'
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        result = {}
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            if isinstance(value, datetime):
                result[column.name] = value.isoformat()
            elif isinstance(value, uuid.UUID):
                result[column.name] = str(value)
            else:
                result[column.name] = value
        return result
    
    @classmethod
    def get_active(cls):
        """Get query for active (non-deleted) records if SoftDeleteMixin is used"""
        if hasattr(cls, 'is_deleted'):
            return cls.query.filter_by(is_deleted=False)
        return cls.query
