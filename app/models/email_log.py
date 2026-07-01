"""
Email Log Model
Track email sending history and delivery status
"""

import uuid
from datetime import datetime
from app.extensions.core import db
from app.models.base import ID_TYPE
from app.models.schema_utils import db_schema, fk_ref

_EMAILS_SCHEMA = db_schema('emails')
_AUTH_SCHEMA = db_schema('auth')


class EmailLog(db.Model):
    """Email sending log for tracking and debugging"""

    __tablename__ = 'email_logs'
    __table_args__ = _EMAILS_SCHEMA

    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    
    # Email details
    to_email = db.Column(db.String(255), nullable=False, index=True)
    from_email = db.Column(db.String(255))
    subject = db.Column(db.String(500), nullable=False)
    template = db.Column(db.String(100))
    
    # Status tracking
    status = db.Column(db.String(20), nullable=False, index=True)  # queued, sent, failed, bounced
    error_message = db.Column(db.Text)
    task_id = db.Column(db.String(100), index=True)  # Celery task ID
    
    # Delivery tracking
    sent_at = db.Column(db.DateTime)
    delivered_at = db.Column(db.DateTime)
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    bounced_at = db.Column(db.DateTime)
    
    # Provider info
    provider = db.Column(db.String(50))  # sendgrid, mailgun, smtp, console
    provider_message_id = db.Column(db.String(255))  # External message ID
    
    # Metadata
    user_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='SET NULL'))
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref='email_logs', foreign_keys=[user_id])
    
    def __repr__(self):
        return f'<EmailLog {self.to_email} - {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'to_email': self.to_email,
            'from_email': self.from_email,
            'subject': self.subject,
            'template': self.template,
            'status': self.status,
            'error_message': self.error_message,
            'task_id': self.task_id,
            'sent_at': self.sent_at.isoformat() if self.sent_at else None,
            'delivered_at': self.delivered_at.isoformat() if self.delivered_at else None,
            'opened_at': self.opened_at.isoformat() if self.opened_at else None,
            'clicked_at': self.clicked_at.isoformat() if self.clicked_at else None,
            'bounced_at': self.bounced_at.isoformat() if self.bounced_at else None,
            'provider': self.provider,
            'provider_message_id': self.provider_message_id,
            'user_id': str(self.user_id) if self.user_id else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_by_task_id(cls, task_id: str):
        """Get email log by Celery task ID"""
        return cls.query.filter_by(task_id=task_id).first()
    
    @classmethod
    def get_user_emails(cls, user_id: str, limit: int = 50):
        """Get email logs for a specific user"""
        return cls.query.filter_by(user_id=user_id).order_by(
            cls.created_at.desc()
        ).limit(limit).all()
    
    @classmethod
    def get_failed_emails(cls, hours: int = 24):
        """Get failed emails within the last N hours"""
        from datetime import timedelta
        cutoff = datetime.utcnow() - timedelta(hours=hours)
        return cls.query.filter(
            cls.status == 'failed',
            cls.created_at >= cutoff
        ).all()
    
    def mark_sent(self, provider_message_id: str = None):
        """Mark email as sent"""
        self.status = 'sent'
        self.sent_at = datetime.utcnow()
        if provider_message_id:
            self.provider_message_id = provider_message_id
        db.session.commit()
    
    def mark_delivered(self):
        """Mark email as delivered"""
        self.status = 'delivered'
        self.delivered_at = datetime.utcnow()
        db.session.commit()
    
    def mark_opened(self):
        """Mark email as opened"""
        self.opened_at = datetime.utcnow()
        db.session.commit()
    
    def mark_clicked(self):
        """Mark email link as clicked"""
        self.clicked_at = datetime.utcnow()
        db.session.commit()
    
    def mark_bounced(self, error_message: str = None):
        """Mark email as bounced"""
        self.status = 'bounced'
        self.bounced_at = datetime.utcnow()
        if error_message:
            self.error_message = error_message
        db.session.commit()
    
    def mark_failed(self, error_message: str):
        """Mark email as failed"""
        self.status = 'failed'
        self.error_message = error_message
        db.session.commit()


class EmailPreference(db.Model):
    """User email preferences and subscription settings"""
    
    __tablename__ = 'email_preferences'
    __table_args__ = _AUTH_SCHEMA

    id = db.Column(ID_TYPE, primary_key=True, default=uuid.uuid4)
    user_id = db.Column(ID_TYPE, db.ForeignKey(fk_ref('auth', 'users'), ondelete='CASCADE'),
                       nullable=False, unique=True, index=True)
    
    # Email categories
    marketing_emails = db.Column(db.Boolean, default=True)
    product_updates = db.Column(db.Boolean, default=True)
    newsletter = db.Column(db.Boolean, default=True)
    order_notifications = db.Column(db.Boolean, default=True)
    account_notifications = db.Column(db.Boolean, default=True)
    security_alerts = db.Column(db.Boolean, default=True)  # Cannot be disabled
    
    # Frequency settings
    email_frequency = db.Column(db.String(20), default='immediate')  # immediate, daily, weekly
    
    # Unsubscribe
    unsubscribed_all = db.Column(db.Boolean, default=False)
    unsubscribed_at = db.Column(db.DateTime)
    unsubscribe_token = db.Column(db.String(100), unique=True, index=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = db.relationship('User', backref=db.backref('email_preference', uselist=False))
    
    def __repr__(self):
        return f'<EmailPreference user_id={self.user_id}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        return {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'marketing_emails': self.marketing_emails,
            'product_updates': self.product_updates,
            'newsletter': self.newsletter,
            'order_notifications': self.order_notifications,
            'account_notifications': self.account_notifications,
            'security_alerts': self.security_alerts,
            'email_frequency': self.email_frequency,
            'unsubscribed_all': self.unsubscribed_all,
            'unsubscribed_at': self.unsubscribed_at.isoformat() if self.unsubscribed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def get_or_create(cls, user_id: str):
        """Get or create email preferences for user"""
        pref = cls.query.filter_by(user_id=user_id).first()
        if not pref:
            pref = cls(user_id=user_id)
            pref.unsubscribe_token = str(uuid.uuid4())
            db.session.add(pref)
            db.session.commit()
        return pref
    
    @classmethod
    def get_by_token(cls, token: str):
        """Get preferences by unsubscribe token"""
        return cls.query.filter_by(unsubscribe_token=token).first()
    
    def can_send_email(self, category: str) -> bool:
        """Check if user can receive emails in this category"""
        if self.unsubscribed_all:
            return category == 'security_alerts'  # Only security alerts
        
        category_map = {
            'marketing': self.marketing_emails,
            'product_updates': self.product_updates,
            'newsletter': self.newsletter,
            'orders': self.order_notifications,
            'account': self.account_notifications,
            'security': self.security_alerts
        }
        
        return category_map.get(category, True)
    
    def unsubscribe_all_emails(self):
        """Unsubscribe from all non-essential emails"""
        self.unsubscribed_all = True
        self.unsubscribed_at = datetime.utcnow()
        self.marketing_emails = False
        self.product_updates = False
        self.newsletter = False
        db.session.commit()
    
    def resubscribe(self):
        """Resubscribe to emails"""
        self.unsubscribed_all = False
        self.unsubscribed_at = None
        self.marketing_emails = True
        self.product_updates = True
        self.newsletter = True
        db.session.commit()
