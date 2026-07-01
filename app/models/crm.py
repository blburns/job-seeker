"""
CRM Schema Models
Customer Relationship Management models (contacts, companies, leads, deals, activities)
"""

import uuid
from datetime import datetime
from enum import Enum as PyEnum
from sqlalchemy import Column, String, Text, Integer, Numeric, Date, DateTime, Boolean, ForeignKey, ARRAY, JSON
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import Enum
from app.extensions.core import db
from app.models.base import BaseModel, TimestampMixin, SoftDeleteMixin


# Enums
class DealStage(PyEnum):
    """Deal pipeline stages"""
    LEAD = 'lead'
    QUALIFIED = 'qualified'
    PROPOSAL = 'proposal'
    NEGOTIATION = 'negotiation'
    CLOSED_WON = 'closed_won'
    CLOSED_LOST = 'closed_lost'


class ActivityType(PyEnum):
    """Activity types"""
    CALL = 'call'
    EMAIL = 'email'
    MEETING = 'meeting'
    NOTE = 'note'
    TASK = 'task'
    SMS = 'sms'


class ContactStatus(PyEnum):
    """Contact status"""
    ACTIVE = 'active'
    INACTIVE = 'inactive'
    DO_NOT_CONTACT = 'do-not-contact'


class LeadStatus(PyEnum):
    """Lead status"""
    NEW = 'new'
    QUALIFIED = 'qualified'
    CONVERTED = 'converted'
    LOST = 'lost'


class TaskStatus(PyEnum):
    """Task status"""
    PENDING = 'pending'
    IN_PROGRESS = 'in_progress'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class CampaignStatus(PyEnum):
    """Campaign status"""
    DRAFT = 'draft'
    SCHEDULED = 'scheduled'
    SENDING = 'sending'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'


class CampaignRecipientStatus(PyEnum):
    """Campaign recipient status"""
    PENDING = 'pending'
    SENT = 'sent'
    DELIVERED = 'delivered'
    OPENED = 'opened'
    CLICKED = 'clicked'
    BOUNCED = 'bounced'
    UNSUBSCRIBED = 'unsubscribed'


# Models
class Company(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Company/Account model"""
    __tablename__ = 'companies'
    __table_args__ = {'schema': 'crm'}
    
    name = Column(String(255), nullable=False, index=True)
    industry = Column(String(100), nullable=True, index=True)
    size = Column(String(50), nullable=True)  # 1-10, 11-50, 51-200, 201-500, 500+
    website = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    address = Column(JSONB, nullable=True)  # {street, city, state, zip, country}
    parent_company_id = Column(UUID(as_uuid=True), ForeignKey('crm.companies.id'), nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True, index=True)
    tags = Column(ARRAY(String), nullable=True)
    custom_fields = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    
    # Relationships
    parent_company = relationship('Company', remote_side='Company.id', backref='subsidiaries')
    owner = relationship('User', foreign_keys=[owner_id], backref='owned_companies')
    contacts = relationship('Contact', back_populates='company')
    deals = relationship('Deal', back_populates='company')
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    @property
    def total_deals_value(self):
        """Calculate total value of all deals for this company"""
        return sum(deal.value for deal in self.deals if deal.stage != DealStage.CLOSED_LOST.value)
    
    @property
    def active_contacts_count(self):
        """Count active contacts for this company"""
        return len([c for c in self.contacts if c.status == ContactStatus.ACTIVE.value and not c.is_deleted])


class Contact(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Contact model"""
    __tablename__ = 'contacts'
    __table_args__ = {'schema': 'crm'}
    
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(100), nullable=True, index=True)
    last_name = Column(String(100), nullable=True, index=True)
    phone = Column(String(50), nullable=True)
    mobile = Column(String(50), nullable=True)
    title = Column(String(100), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('crm.companies.id'), nullable=True, index=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True, index=True)
    status = Column(String(50), default=ContactStatus.ACTIVE.value, nullable=False, index=True)
    source = Column(String(100), nullable=True)  # website, referral, import, etc.
    tags = Column(ARRAY(String), nullable=True)
    address = Column(JSONB, nullable=True)  # {street, city, state, zip, country}
    social_links = Column(JSONB, nullable=True)  # {linkedin, twitter, facebook}
    custom_fields = Column(JSONB, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    last_activity_at = Column(DateTime, nullable=True)
    
    # Relationships
    company = relationship('Company', back_populates='contacts')
    owner = relationship('User', foreign_keys=[owner_id], backref='owned_contacts')
    deals = relationship('Deal', back_populates='contact')
    activities = relationship('Activity', back_populates='contact', order_by='Activity.created_at.desc()')
    tasks = relationship('Task', back_populates='contact')
    notes_rel = relationship('Note', back_populates='contact')
    leads = relationship('Lead', primaryjoin='Contact.id == Lead.contact_id', back_populates='contact')
    
    def __repr__(self):
        return f'<Contact {self.email}>'
    
    @property
    def full_name(self):
        """Get full name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        elif self.first_name:
            return self.first_name
        elif self.last_name:
            return self.last_name
        return self.email.split('@')[0]
    
    @property
    def total_deals_value(self):
        """Calculate total value of all deals for this contact"""
        return sum(deal.value for deal in self.deals if deal.stage != DealStage.CLOSED_LOST.value)


class Lead(BaseModel, TimestampMixin):
    """Lead model"""
    __tablename__ = 'leads'
    __table_args__ = {'schema': 'crm'}
    
    contact_id = Column(UUID(as_uuid=True), ForeignKey('crm.contacts.id'), nullable=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('crm.companies.id'), nullable=True)
    source = Column(String(100), nullable=False)  # website, ad, referral, etc.
    score = Column(Integer, default=0, nullable=False)  # 0-100
    status = Column(String(50), default=LeadStatus.NEW.value, nullable=False, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True, index=True)
    converted_to_contact_id = Column(UUID(as_uuid=True), ForeignKey('crm.contacts.id'), nullable=True)
    converted_to_deal_id = Column(UUID(as_uuid=True), ForeignKey('crm.deals.id'), nullable=True)
    converted_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    
    # Relationships
    contact = relationship('Contact', foreign_keys=[contact_id], back_populates='leads')
    company = relationship('Company', foreign_keys=[company_id])
    assigned_user = relationship('User', foreign_keys=[assigned_to], backref='assigned_leads')
    converted_contact = relationship('Contact', foreign_keys=[converted_to_contact_id], viewonly=True)
    converted_deal = relationship('Deal', foreign_keys=[converted_to_deal_id], viewonly=True)
    
    def __repr__(self):
        return f'<Lead {self.id} - {self.source}>'


class Deal(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Deal/Opportunity model"""
    __tablename__ = 'deals'
    __table_args__ = {'schema': 'crm'}
    
    name = Column(String(255), nullable=False)
    contact_id = Column(UUID(as_uuid=True), ForeignKey('crm.contacts.id'), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('crm.companies.id'), nullable=True, index=True)
    value = Column(Numeric(12, 2), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    stage = Column(String(50), default=DealStage.LEAD.value, nullable=False, index=True)
    probability = Column(Integer, default=0, nullable=False)  # 0-100
    expected_close_date = Column(Date, nullable=True, index=True)
    actual_close_date = Column(Date, nullable=True)
    owner_id = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True, index=True)
    win_reason = Column(Text, nullable=True)
    loss_reason = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    custom_fields = Column(JSONB, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    updated_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    
    # Relationships
    contact = relationship('Contact', back_populates='deals')
    company = relationship('Company', back_populates='deals')
    owner = relationship('User', foreign_keys=[owner_id], backref='owned_deals')
    activities = relationship('Activity', back_populates='deal', order_by='Activity.created_at.desc()')
    tasks = relationship('Task', back_populates='deal')
    notes_rel = relationship('Note', back_populates='deal')
    
    def __repr__(self):
        return f'<Deal {self.name} - {self.value}>'
    
    @property
    def weighted_value(self):
        """Calculate weighted value (value * probability)"""
        return float(self.value) * (self.probability / 100)


class Activity(BaseModel, TimestampMixin):
    """Activity model (calls, emails, meetings, notes)"""
    __tablename__ = 'activities'
    __table_args__ = {'schema': 'crm'}
    
    type = Column(String(50), nullable=False, index=True)
    subject = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey('crm.contacts.id'), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('crm.companies.id'), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey('crm.deals.id'), nullable=True, index=True)
    start_time = Column(DateTime, nullable=True)
    end_time = Column(DateTime, nullable=True)
    duration_minutes = Column(Integer, nullable=True)
    location = Column(String(255), nullable=True)
    participants = Column(ARRAY(String), nullable=True)
    status = Column(String(50), default='completed', nullable=False)
    priority = Column(String(20), default='normal', nullable=False)
    due_date = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=False, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True)
    activity_metadata = Column(JSONB, nullable=True)  # Email ID, call recording URL, etc.
    
    # Relationships
    contact = relationship('Contact', back_populates='activities')
    company = relationship('Company')
    deal = relationship('Deal', back_populates='activities')
    creator = relationship('User', foreign_keys=[created_by], backref='created_activities')
    assignee = relationship('User', foreign_keys=[assigned_to], backref='assigned_activities')
    
    def __repr__(self):
        return f'<Activity {self.type} - {self.subject}>'


class Task(BaseModel, TimestampMixin):
    """Task model"""
    __tablename__ = 'tasks'
    __table_args__ = {'schema': 'crm'}
    
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey('crm.contacts.id'), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('crm.companies.id'), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey('crm.deals.id'), nullable=True, index=True)
    assigned_to = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=True, index=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=False)
    status = Column(String(50), default=TaskStatus.PENDING.value, nullable=False, index=True)
    priority = Column(String(20), default='normal', nullable=False)
    due_date = Column(DateTime, nullable=True, index=True)
    completed_at = Column(DateTime, nullable=True)
    reminder_sent_at = Column(DateTime, nullable=True)
    is_recurring = Column(Boolean, default=False, nullable=False)
    recurrence_rule = Column(String(255), nullable=True)  # RRULE format
    
    # Relationships
    contact = relationship('Contact', back_populates='tasks')
    company = relationship('Company')
    deal = relationship('Deal', back_populates='tasks')
    assignee = relationship('User', foreign_keys=[assigned_to], backref='assigned_tasks')
    creator = relationship('User', foreign_keys=[created_by], backref='created_tasks')
    
    def __repr__(self):
        return f'<Task {self.title}>'
    
    def complete(self):
        """Mark task as completed"""
        self.status = TaskStatus.COMPLETED.value
        self.completed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()


class Note(BaseModel, TimestampMixin, SoftDeleteMixin):
    """Note model"""
    __tablename__ = 'notes'
    __table_args__ = {'schema': 'crm'}
    
    contact_id = Column(UUID(as_uuid=True), ForeignKey('crm.contacts.id'), nullable=True, index=True)
    company_id = Column(UUID(as_uuid=True), ForeignKey('crm.companies.id'), nullable=True)
    deal_id = Column(UUID(as_uuid=True), ForeignKey('crm.deals.id'), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    content = Column(Text, nullable=False)
    is_private = Column(Boolean, default=False, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=False)
    
    # Relationships
    contact = relationship('Contact', back_populates='notes_rel')
    company = relationship('Company')
    deal = relationship('Deal', back_populates='notes_rel')
    creator = relationship('User', foreign_keys=[created_by], backref='created_notes')
    
    def __repr__(self):
        return f'<Note {self.id}>'


class Campaign(BaseModel, TimestampMixin):
    """Campaign model"""
    __tablename__ = 'campaigns'
    __table_args__ = {'schema': 'crm'}
    
    name = Column(String(255), nullable=False)
    type = Column(String(50), nullable=True)  # email, sms, social
    status = Column(String(50), default=CampaignStatus.DRAFT.value, nullable=False, index=True)
    subject = Column(String(255), nullable=True)
    content = Column(Text, nullable=True)
    template_id = Column(UUID(as_uuid=True), nullable=True)  # Reference to email template
    segment_id = Column(UUID(as_uuid=True), ForeignKey('crm.segments.id'), nullable=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    sent_at = Column(DateTime, nullable=True)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=False)
    
    # Relationships
    segment = relationship('Segment', back_populates='campaigns')
    recipients = relationship('CampaignRecipient', back_populates='campaign', cascade='all, delete-orphan')
    creator = relationship('User', foreign_keys=[created_by], backref='created_campaigns')
    
    def __repr__(self):
        return f'<Campaign {self.name}>'


class CampaignRecipient(BaseModel, TimestampMixin):
    """Campaign recipient model"""
    __tablename__ = 'campaign_recipients'
    __table_args__ = {'schema': 'crm'}
    
    campaign_id = Column(UUID(as_uuid=True), ForeignKey('crm.campaigns.id', ondelete='CASCADE'), nullable=False, index=True)
    contact_id = Column(UUID(as_uuid=True), ForeignKey('crm.contacts.id'), nullable=True, index=True)
    email = Column(String(255), nullable=False)
    status = Column(String(50), default=CampaignRecipientStatus.PENDING.value, nullable=False, index=True)
    sent_at = Column(DateTime, nullable=True)
    opened_at = Column(DateTime, nullable=True)
    clicked_at = Column(DateTime, nullable=True)
    bounce_reason = Column(Text, nullable=True)
    
    # Relationships
    campaign = relationship('Campaign', back_populates='recipients')
    contact = relationship('Contact')
    
    def __repr__(self):
        return f'<CampaignRecipient {self.email}>'


class Segment(BaseModel, TimestampMixin):
    """Customer segment model"""
    __tablename__ = 'segments'
    __table_args__ = {'schema': 'crm'}
    
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    criteria = Column(JSONB, nullable=False)  # {field: value, operator: 'equals', etc.}
    is_dynamic = Column(Boolean, default=True, nullable=False)
    contact_count = Column(Integer, default=0, nullable=False)
    created_by = Column(UUID(as_uuid=True), ForeignKey('auth.users.id'), nullable=False)
    
    # Relationships
    campaigns = relationship('Campaign', back_populates='segment')
    creator = relationship('User', foreign_keys=[created_by], backref='created_segments')
    
    def __repr__(self):
        return f'<Segment {self.name}>'


class CustomField(BaseModel, TimestampMixin):
    """Custom field definition model"""
    __tablename__ = 'custom_fields'
    __table_args__ = {'schema': 'crm'}
    
    entity_type = Column(String(50), nullable=False, index=True)  # contact, company, deal
    field_name = Column(String(100), nullable=False)
    field_type = Column(String(50), nullable=False)  # text, number, date, select, multi_select, boolean
    options = Column(JSONB, nullable=True)  # For select/multi_select: ["option1", "option2"]
    is_required = Column(Boolean, default=False, nullable=False)
    display_order = Column(Integer, default=0, nullable=False)
    
    def __repr__(self):
        return f'<CustomField {self.entity_type}.{self.field_name}>'


class CustomFieldValue(BaseModel, TimestampMixin):
    """Custom field value model"""
    __tablename__ = 'custom_field_values'
    __table_args__ = {'schema': 'crm'}
    
    field_id = Column(UUID(as_uuid=True), ForeignKey('crm.custom_fields.id', ondelete='CASCADE'), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False, index=True)
    entity_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    value = Column(Text, nullable=True)
    
    # Relationships
    field = relationship('CustomField', backref='values')
    
    def __repr__(self):
        return f'<CustomFieldValue {self.entity_type}:{self.entity_id}>'


class Tag(BaseModel, TimestampMixin):
    """Tag model"""
    __tablename__ = 'tags'
    __table_args__ = {'schema': 'crm'}
    
    name = Column(String(100), unique=True, nullable=False, index=True)
    color = Column(String(7), nullable=True)  # Hex color code
    category = Column(String(50), nullable=True)
    
    def __repr__(self):
        return f'<Tag {self.name}>'
