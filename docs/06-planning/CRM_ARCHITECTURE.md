# CRM (Customer Relationship Management) Architecture
## Complete Architecture and Implementation Guide

## Table of Contents
1. [Overview](#overview)
2. [Core Architecture](#core-architecture)
3. [Core Features](#core-features)
4. [Database Design](#database-design)
5. [API Design](#api-design)
6. [Routes & UI](#routes--ui)
7. [Integration Patterns](#integration-patterns)
8. [Workflows & Automation](#workflows--automation)
9. [Reporting & Analytics](#reporting--analytics)
10. [Security & Permissions](#security--permissions)
11. [Scalability Considerations](#scalability-considerations)
12. [Implementation Roadmap](#implementation-roadmap)

---

## Overview

A comprehensive CRM system for managing customer relationships, sales pipelines, and business interactions. This document provides a complete architecture for building a scalable, feature-rich CRM module that integrates seamlessly with your existing authentication and user management system.

### Key Principles
- **360° Customer View**: Centralized view of all customer interactions, orders, and activities
- **Pipeline Management**: Visual deal pipeline with stage tracking and forecasting
- **Activity Tracking**: Complete history of calls, emails, meetings, and notes
- **Automation**: Workflow automation for lead assignment, follow-ups, and notifications
- **Flexibility**: Custom fields and tags for extensibility
- **Integration-Ready**: Built to integrate with email, calendar, phone, and other systems

### Business Value
- **Sales Efficiency**: Track deals, forecast revenue, manage pipeline
- **Customer Insights**: Understand customer behavior and engagement
- **Team Collaboration**: Shared contacts, activities, and notes
- **Data-Driven Decisions**: Reporting and analytics for sales performance

---

## Core Architecture

### High-Level Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     Frontend Layer                          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   Web    │  │  Mobile  │  │   Admin  │  │  Reports │  │
│  │   Portal │  │   App    │  │ Dashboard│  │ Dashboard│  │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      API Gateway                            │
│              (Authentication, Rate Limiting)                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                      CRM Service                            │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │  Contacts  │  │   Leads    │  │   Deals    │             │
│  │  Service   │  │  Service   │  │  Service   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
│                                                             │
│  ┌────────────┐  ┌────────────┐  ┌────────────┐             │
│  │ Activities │  │  Campaigns │  │  Reporting │             │
│  │  Service   │  │  Service   │  │  Service   │             │
│  └────────────┘  └────────────┘  └────────────┘             │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Data Layer (PostgreSQL)                   │
│  ┌────────┐  ┌────────┐  ┌──────-──┐  ┌────────┐            │
│  │  auth  │  │  crm   │  │  sales  │  │  ref   │            │
│  │ schema │  │ schema │  │ schema  │  │ schema │            │
│  └────────┘  └────────┘  └───────-─┘  └────────┘            │
└─────────────────────────────────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        ▼                   ▼                   ▼
┌──────────────┐   ┌─────────────--─┐   ┌──────────────┐
│   Redis      │   │  Elasticsearch │   │   Celery     │
│   Cache      │   │   Search       │   │   Queue      │
└──────────────┘   └──────────────--┘   └──────────────┘
```

### Technology Stack

**Backend:**
- **Framework**: Flask (current boilerplate)
- **Database**: PostgreSQL with `crm` schema
- **Cache**: Redis (contact lists, search results)
- **Search**: PostgreSQL full-text search or Elasticsearch
- **Queue**: Celery (email sync, report generation)

**Frontend:**
- **Admin Portal**: Server-rendered templates (Jinja2) + Alpine.js/HTMX
- **API**: RESTful API for mobile/SPA clients
- **Charts**: Chart.js or D3.js for visualizations

**Integrations:**
- **Email**: Gmail API, Outlook API
- **Calendar**: Google Calendar API, Outlook Calendar
- **Phone**: Twilio for call tracking
- **Documents**: S3/GCS for file attachments

---

## Core Features

### 1. Contact Management

**Features:**
- Individual contact records with full profile
- Contact search and filtering
- Custom fields support
- Tags and categories
- Contact import/export (CSV)
- Duplicate detection and merging
- Contact history timeline

**Data Model:**
- Basic info: name, email, phone, address
- Company association
- Owner/assigned user
- Status (active, inactive, do-not-contact)
- Source (website, referral, import, etc.)
- Custom fields (flexible schema)

### 2. Company/Account Management

**Features:**
- Company records with hierarchy support
- Multiple contacts per company
- Company insights (total deals, revenue)
- Industry and size tracking
- Website and social links
- Parent-child company relationships

**Data Model:**
- Company name, industry, size
- Address and contact info
- Website, LinkedIn, etc.
- Owner/assigned user
- Parent company (for subsidiaries)

### 3. Lead Management

**Features:**
- Lead capture and tracking
- Lead scoring (automatic or manual)
- Lead qualification workflow
- Lead source tracking
- Lead conversion to contact/deal
- Lead assignment rules

**Data Model:**
- Lead source (website, ad, referral)
- Score (0-100)
- Status (new, qualified, converted, lost)
- Assigned user
- Conversion date and outcome

### 4. Deal/Opportunity Pipeline

**Features:**
- Visual pipeline board (Kanban)
- Customizable stages
- Deal value and probability
- Expected close date
- Win/loss tracking
- Revenue forecasting
- Deal history and stage changes

**Pipeline Stages (Default):**
1. **Lead** - Initial contact
2. **Qualified** - Needs identified
3. **Proposal** - Proposal sent
4. **Negotiation** - Terms discussion
5. **Closed Won** - Deal won
6. **Closed Lost** - Deal lost

**Data Model:**
- Deal name, value, currency
- Stage and probability
- Close date (expected and actual)
- Contact and company association
- Owner/assigned user
- Win/loss reason

### 5. Activity Tracking

**Features:**
- Log calls, emails, meetings, notes
- Activity timeline per contact/deal
- Email integration (sync from Gmail/Outlook)
- Calendar integration (sync meetings)
- Task management with reminders
- Activity templates

**Activity Types:**
- **Call**: Phone call with notes
- **Email**: Email sent/received
- **Meeting**: In-person or video meeting
- **Note**: General note
- **Task**: Follow-up task
- **SMS**: Text message

### 6. Task Management

**Features:**
- Task creation and assignment
- Due dates and reminders
- Task status (pending, in-progress, completed)
- Task priorities
- Recurring tasks
- Task templates

### 7. Email Campaigns

**Features:**
- Email campaign creation
- Contact segmentation
- Email templates
- Send tracking (opens, clicks)
- Unsubscribe management
- Campaign performance metrics

### 8. Customer Segmentation

**Features:**
- Create segments based on criteria
- Dynamic segments (auto-update)
- Segment-based campaigns
- Segment analytics

**Segment Criteria:**
- Contact attributes (industry, location, etc.)
- Deal value ranges
- Activity frequency
- Last contact date
- Custom field values

### 9. Reporting & Analytics

**Features:**
- Sales pipeline reports
- Revenue forecasting
- Activity reports
- Lead source analysis
- Team performance metrics
- Custom report builder
- Scheduled reports (email)

---

## Database Design

### Schema: `crm`

#### Core Tables

**1. `crm.contacts`**
```sql
CREATE TABLE crm.contacts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    phone VARCHAR(50),
    mobile VARCHAR(50),
    title VARCHAR(100),
    company_id UUID REFERENCES crm.companies(id),
    owner_id UUID REFERENCES auth.users(id),
    status VARCHAR(50) DEFAULT 'active', -- active, inactive, do-not-contact
    source VARCHAR(100), -- website, referral, import, etc.
    tags TEXT[], -- Array of tags
    address JSONB, -- {street, city, state, zip, country}
    social_links JSONB, -- {linkedin, twitter, facebook}
    custom_fields JSONB, -- Flexible custom data
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_contacts_email ON crm.contacts(email);
CREATE INDEX idx_contacts_company ON crm.contacts(company_id);
CREATE INDEX idx_contacts_owner ON crm.contacts(owner_id);
CREATE INDEX idx_contacts_status ON crm.contacts(status);
CREATE INDEX idx_contacts_tags ON crm.contacts USING gin(tags);
```

**2. `crm.companies`**
```sql
CREATE TABLE crm.companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    industry VARCHAR(100),
    size VARCHAR(50), -- 1-10, 11-50, 51-200, 201-500, 500+
    website VARCHAR(255),
    phone VARCHAR(50),
    email VARCHAR(255),
    address JSONB,
    parent_company_id UUID REFERENCES crm.companies(id),
    owner_id UUID REFERENCES auth.users(id),
    tags TEXT[],
    custom_fields JSONB,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_companies_name ON crm.companies(name);
CREATE INDEX idx_companies_owner ON crm.companies(owner_id);
CREATE INDEX idx_companies_industry ON crm.companies(industry);
```

**3. `crm.leads`**
```sql
CREATE TABLE crm.leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES crm.contacts(id),
    company_id UUID REFERENCES crm.companies(id),
    source VARCHAR(100) NOT NULL, -- website, ad, referral, etc.
    score INTEGER DEFAULT 0, -- 0-100
    status VARCHAR(50) DEFAULT 'new', -- new, qualified, converted, lost
    assigned_to UUID REFERENCES auth.users(id),
    converted_to_contact_id UUID REFERENCES crm.contacts(id),
    converted_to_deal_id UUID REFERENCES crm.deals(id),
    converted_at TIMESTAMP NULL,
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id)
);

CREATE INDEX idx_leads_status ON crm.leads(status);
CREATE INDEX idx_leads_assigned ON crm.leads(assigned_to);
CREATE INDEX idx_leads_score ON crm.leads(score DESC);
```

**4. `crm.deals`**
```sql
CREATE TYPE deal_stage AS ENUM (
    'lead', 'qualified', 'proposal', 
    'negotiation', 'closed_won', 'closed_lost'
);

CREATE TABLE crm.deals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    contact_id UUID REFERENCES crm.contacts(id),
    company_id UUID REFERENCES crm.companies(id),
    value DECIMAL(12, 2) NOT NULL,
    currency VARCHAR(3) DEFAULT 'USD',
    stage deal_stage DEFAULT 'lead',
    probability INTEGER DEFAULT 0, -- 0-100
    expected_close_date DATE,
    actual_close_date DATE NULL,
    owner_id UUID REFERENCES auth.users(id),
    win_reason TEXT,
    loss_reason TEXT,
    notes TEXT,
    custom_fields JSONB,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    created_by UUID REFERENCES auth.users(id),
    updated_by UUID REFERENCES auth.users(id),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_deals_contact ON crm.deals(contact_id);
CREATE INDEX idx_deals_company ON crm.deals(company_id);
CREATE INDEX idx_deals_owner ON crm.deals(owner_id);
CREATE INDEX idx_deals_stage ON crm.deals(stage);
CREATE INDEX idx_deals_close_date ON crm.deals(expected_close_date);
```

**5. `crm.activities`**
```sql
CREATE TYPE activity_type AS ENUM (
    'call', 'email', 'meeting', 'note', 'task', 'sms'
);

CREATE TABLE crm.activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type activity_type NOT NULL,
    subject VARCHAR(255),
    description TEXT,
    contact_id UUID REFERENCES crm.contacts(id),
    company_id UUID REFERENCES crm.companies(id),
    deal_id UUID REFERENCES crm.deals(id),
    start_time TIMESTAMP,
    end_time TIMESTAMP,
    duration_minutes INTEGER,
    location VARCHAR(255),
    participants TEXT[], -- Array of participant emails/names
    status VARCHAR(50) DEFAULT 'completed', -- scheduled, completed, cancelled
    priority VARCHAR(20) DEFAULT 'normal', -- low, normal, high
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    created_by UUID REFERENCES auth.users(id),
    assigned_to UUID REFERENCES auth.users(id),
    metadata JSONB, -- Email ID, call recording URL, etc.
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_activities_contact ON crm.activities(contact_id, created_at DESC);
CREATE INDEX idx_activities_company ON crm.activities(company_id);
CREATE INDEX idx_activities_deal ON crm.activities(deal_id);
CREATE INDEX idx_activities_type ON crm.activities(type);
CREATE INDEX idx_activities_created_by ON crm.activities(created_by);
CREATE INDEX idx_activities_due_date ON crm.activities(due_date) WHERE due_date IS NOT NULL;
```

**6. `crm.tasks`**
```sql
CREATE TABLE crm.tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    description TEXT,
    contact_id UUID REFERENCES crm.contacts(id),
    company_id UUID REFERENCES crm.companies(id),
    deal_id UUID REFERENCES crm.deals(id),
    assigned_to UUID REFERENCES auth.users(id),
    created_by UUID REFERENCES auth.users(id),
    status VARCHAR(50) DEFAULT 'pending', -- pending, in_progress, completed, cancelled
    priority VARCHAR(20) DEFAULT 'normal',
    due_date TIMESTAMP,
    completed_at TIMESTAMP,
    reminder_sent_at TIMESTAMP,
    is_recurring BOOLEAN DEFAULT FALSE,
    recurrence_rule VARCHAR(255), -- RRULE format
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tasks_assigned ON crm.tasks(assigned_to, status);
CREATE INDEX idx_tasks_due_date ON crm.tasks(due_date) WHERE status != 'completed';
CREATE INDEX idx_tasks_contact ON crm.tasks(contact_id);
```

**7. `crm.notes`**
```sql
CREATE TABLE crm.notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    contact_id UUID REFERENCES crm.contacts(id),
    company_id UUID REFERENCES crm.companies(id),
    deal_id UUID REFERENCES crm.deals(id),
    title VARCHAR(255),
    content TEXT NOT NULL,
    is_private BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    deleted_at TIMESTAMP NULL
);

CREATE INDEX idx_notes_contact ON crm.notes(contact_id, created_at DESC);
CREATE INDEX idx_notes_company ON crm.notes(company_id);
CREATE INDEX idx_notes_deal ON crm.notes(deal_id);
```

**8. `crm.campaigns`**
```sql
CREATE TABLE crm.campaigns (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    type VARCHAR(50), -- email, sms, social
    status VARCHAR(50) DEFAULT 'draft', -- draft, scheduled, sending, completed, cancelled
    subject VARCHAR(255),
    content TEXT,
    template_id UUID, -- Reference to email template
    segment_id UUID REFERENCES crm.segments(id),
    scheduled_at TIMESTAMP,
    sent_at TIMESTAMP,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_campaigns_status ON crm.campaigns(status);
CREATE INDEX idx_campaigns_scheduled ON crm.campaigns(scheduled_at) WHERE status = 'scheduled';
```

**9. `crm.campaign_recipients`**
```sql
CREATE TABLE crm.campaign_recipients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID REFERENCES crm.campaigns(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES crm.contacts(id),
    email VARCHAR(255) NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, sent, delivered, opened, clicked, bounced, unsubscribed
    sent_at TIMESTAMP,
    opened_at TIMESTAMP,
    clicked_at TIMESTAMP,
    bounce_reason TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_campaign_recipients_campaign ON crm.campaign_recipients(campaign_id);
CREATE INDEX idx_campaign_recipients_contact ON crm.campaign_recipients(contact_id);
CREATE INDEX idx_campaign_recipients_status ON crm.campaign_recipients(status);
```

**10. `crm.segments`**
```sql
CREATE TABLE crm.segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    description TEXT,
    criteria JSONB NOT NULL, -- {field: value, operator: 'equals', etc.}
    is_dynamic BOOLEAN DEFAULT TRUE, -- Auto-update based on criteria
    contact_count INTEGER DEFAULT 0,
    created_by UUID REFERENCES auth.users(id),
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_segments_name ON crm.segments(name);
```

**11. `crm.custom_fields`**
```sql
CREATE TABLE crm.custom_fields (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type VARCHAR(50) NOT NULL, -- contact, company, deal
    field_name VARCHAR(100) NOT NULL,
    field_type VARCHAR(50) NOT NULL, -- text, number, date, select, multi_select, boolean
    options JSONB, -- For select/multi_select: ["option1", "option2"]
    is_required BOOLEAN DEFAULT FALSE,
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_custom_fields_unique ON crm.custom_fields(entity_type, field_name);
```

**12. `crm.custom_field_values`**
```sql
CREATE TABLE crm.custom_field_values (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    field_id UUID REFERENCES crm.custom_fields(id) ON DELETE CASCADE,
    entity_type VARCHAR(50) NOT NULL,
    entity_id UUID NOT NULL, -- Contact, company, or deal ID
    value TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE UNIQUE INDEX idx_custom_field_values_unique ON crm.custom_field_values(field_id, entity_type, entity_id);
CREATE INDEX idx_custom_field_values_entity ON crm.custom_field_values(entity_type, entity_id);
```

**13. `crm.tags`**
```sql
CREATE TABLE crm.tags (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(100) NOT NULL UNIQUE,
    color VARCHAR(7), -- Hex color code
    category VARCHAR(50), -- Optional grouping
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_tags_name ON crm.tags(name);
```

### Relationships Summary

```
contacts ──┬──> companies (many-to-one)
           ├──> users (owner, many-to-one)
           ├──> deals (one-to-many)
           ├──> activities (one-to-many)
           ├──> tasks (one-to-many)
           └──> notes (one-to-many)

companies ──┬──> companies (parent-child, self-referential)
            └──> users (owner, many-to-one)

deals ──┬──> contacts (many-to-one)
        ├──> companies (many-to-one)
        ├──> users (owner, many-to-one)
        └──> activities (one-to-many)

leads ──┬──> contacts (one-to-one, when converted)
        ├──> companies (many-to-one)
        └──> users (assigned_to, many-to-one)
```

---

## API Design

### RESTful Endpoints

#### Contacts

```
GET    /api/v1/crm/contacts              # List contacts (with filters)
POST   /api/v1/crm/contacts              # Create contact
GET    /api/v1/crm/contacts/:id          # Get contact details
PATCH  /api/v1/crm/contacts/:id          # Update contact
DELETE /api/v1/crm/contacts/:id          # Delete contact (soft delete)
POST   /api/v1/crm/contacts/:id/merge     # Merge duplicate contacts
GET    /api/v1/crm/contacts/:id/timeline # Get activity timeline
POST   /api/v1/crm/contacts/import       # Bulk import (CSV)
GET    /api/v1/crm/contacts/export       # Export contacts (CSV)
```

#### Companies

```
GET    /api/v1/crm/companies             # List companies
POST   /api/v1/crm/companies             # Create company
GET    /api/v1/crm/companies/:id         # Get company details
PATCH  /api/v1/crm/companies/:id         # Update company
DELETE /api/v1/crm/companies/:id         # Delete company
GET    /api/v1/crm/companies/:id/contacts # Get company contacts
GET    /api/v1/crm/companies/:id/deals   # Get company deals
```

#### Leads

```
GET    /api/v1/crm/leads                 # List leads
POST   /api/v1/crm/leads                 # Create lead
GET    /api/v1/crm/leads/:id             # Get lead details
PATCH  /api/v1/crm/leads/:id             # Update lead
POST   /api/v1/crm/leads/:id/convert     # Convert lead to contact/deal
POST   /api/v1/crm/leads/:id/qualify     # Mark as qualified
DELETE /api/v1/crm/leads/:id             # Delete lead
```

#### Deals

```
GET    /api/v1/crm/deals                 # List deals (with filters)
POST   /api/v1/crm/deals                 # Create deal
GET    /api/v1/crm/deals/:id             # Get deal details
PATCH  /api/v1/crm/deals/:id             # Update deal
DELETE /api/v1/crm/deals/:id             # Delete deal
PATCH  /api/v1/crm/deals/:id/stage       # Update deal stage
POST   /api/v1/crm/deals/:id/win         # Mark as won
POST   /api/v1/crm/deals/:id/lose        # Mark as lost
GET    /api/v1/crm/deals/pipeline        # Get pipeline view
GET    /api/v1/crm/deals/forecast        # Get revenue forecast
```

#### Activities

```
GET    /api/v1/crm/activities            # List activities
POST   /api/v1/crm/activities            # Create activity
GET    /api/v1/crm/activities/:id       # Get activity details
PATCH  /api/v1/crm/activities/:id       # Update activity
DELETE /api/v1/crm/activities/:id       # Delete activity
GET    /api/v1/crm/activities/upcoming   # Get upcoming activities
```

#### Tasks

```
GET    /api/v1/crm/tasks                 # List tasks
POST   /api/v1/crm/tasks                 # Create task
GET    /api/v1/crm/tasks/:id             # Get task details
PATCH  /api/v1/crm/tasks/:id             # Update task
DELETE /api/v1/crm/tasks/:id             # Delete task
POST   /api/v1/crm/tasks/:id/complete    # Mark task as completed
GET    /api/v1/crm/tasks/overdue         # Get overdue tasks
GET    /api/v1/crm/tasks/upcoming        # Get upcoming tasks
```

#### Campaigns

```
GET    /api/v1/crm/campaigns             # List campaigns
POST   /api/v1/crm/campaigns             # Create campaign
GET    /api/v1/crm/campaigns/:id         # Get campaign details
PATCH  /api/v1/crm/campaigns/:id         # Update campaign
DELETE /api/v1/crm/campaigns/:id         # Delete campaign
POST   /api/v1/crm/campaigns/:id/send    # Send campaign
GET    /api/v1/crm/campaigns/:id/stats   # Get campaign statistics
```

#### Reports

```
GET    /api/v1/crm/reports/pipeline      # Pipeline report
GET    /api/v1/crm/reports/forecast     # Revenue forecast
GET    /api/v1/crm/reports/activities    # Activity report
GET    /api/v1/crm/reports/leads         # Lead source report
GET    /api/v1/crm/reports/team         # Team performance report
```

### Request/Response Examples

**Create Contact:**
```json
POST /api/v1/crm/contacts
{
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1-555-123-4567",
  "title": "VP of Sales",
  "company_id": "uuid-here",
  "tags": ["vip", "enterprise"],
  "custom_fields": {
    "annual_revenue": "5000000",
    "industry": "Technology"
  }
}

Response: 201 Created
{
  "id": "contact-uuid",
  "email": "john.doe@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

**List Deals with Filters:**
```json
GET /api/v1/crm/deals?stage=negotiation&owner_id=user-uuid&min_value=10000

Response: 200 OK
{
  "data": [
    {
      "id": "deal-uuid",
      "name": "Enterprise License",
      "value": 50000.00,
      "currency": "USD",
      "stage": "negotiation",
      "probability": 75,
      "expected_close_date": "2024-02-15",
      "contact": {
        "id": "contact-uuid",
        "name": "John Doe"
      }
    }
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 5
  }
}
```

**Pipeline View:**
```json
GET /api/v1/crm/deals/pipeline

Response: 200 OK
{
  "stages": [
    {
      "stage": "lead",
      "deals": [...],
      "total_value": 100000.00,
      "count": 5
    },
    {
      "stage": "qualified",
      "deals": [...],
      "total_value": 250000.00,
      "count": 8
    }
  ],
  "summary": {
    "total_value": 1500000.00,
    "weighted_value": 1125000.00,
    "total_deals": 25
  }
}
```

---

## Routes & UI

### Web Routes

```
/crm/dashboard                    # CRM dashboard (overview, metrics)
/crm/contacts                     # Contact list
/crm/contacts/new                 # Create contact
/crm/contacts/:id                 # Contact detail view
/crm/contacts/:id/edit           # Edit contact
/crm/companies                    # Company list
/crm/companies/new                # Create company
/crm/companies/:id                # Company detail view
/crm/leads                        # Lead list
/crm/leads/new                    # Create lead
/crm/leads/:id                    # Lead detail view
/crm/deals                        # Deal list (table view)
/crm/deals/pipeline               # Deal pipeline (Kanban board)
/crm/deals/new                    # Create deal
/crm/deals/:id                    # Deal detail view
/crm/activities                   # Activity list
/crm/activities/new               # Create activity
/crm/tasks                        # Task list
/crm/tasks/new                    # Create task
/crm/campaigns                    # Campaign list
/crm/campaigns/new                # Create campaign
/crm/campaigns/:id                # Campaign detail and stats
/crm/reports                       # Reports dashboard
/crm/reports/pipeline              # Pipeline report
/crm/reports/forecast              # Revenue forecast
/crm/reports/activities            # Activity report
/crm/settings                      # CRM settings (custom fields, stages, etc.)
```

### Key UI Components

**1. Contact Detail Page**
- Contact information card
- Activity timeline (chronological)
- Related deals
- Related tasks
- Notes section
- Custom fields panel
- Quick actions (call, email, create task)

**2. Pipeline Board (Kanban)**
- Columns for each stage
- Deal cards with key info (name, value, contact)
- Drag-and-drop to change stages
- Filters (owner, date range, value range)
- Summary totals per stage

**3. Activity Timeline**
- Chronological list of all activities
- Grouped by date
- Activity type icons
- Quick add activity button
- Filter by type

**4. Dashboard Widgets**
- Pipeline summary (total value, weighted value)
- Upcoming activities
- Overdue tasks
- Recent deals
- Lead conversion rate
- Activity chart (last 30 days)

---

## Integration Patterns

### Email Integration

**Gmail API Integration:**
```python
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

def sync_gmail_emails(user_id):
    """Sync emails from Gmail to CRM activities"""
    credentials = get_user_oauth_credentials(user_id, 'gmail')
    service = build('gmail', 'v1', credentials=credentials)
    
    # Get messages
    messages = service.users().messages().list(
        userId='me',
        q='is:unread',
        maxResults=50
    ).execute()
    
    for msg in messages.get('messages', []):
        message = service.users().messages().get(
            userId='me',
            id=msg['id']
        ).execute()
        
        # Extract contact email
        from_email = extract_from_email(message)
        contact = find_or_create_contact(from_email)
        
        # Create activity
        create_email_activity(
            contact_id=contact.id,
            subject=message['subject'],
            body=extract_body(message),
            email_id=msg['id'],
            created_by=user_id
        )
```

**Email Tracking:**
- Track email opens (pixel tracking)
- Track link clicks
- Auto-create activities for replies

### Calendar Integration

**Google Calendar Sync:**
```python
def sync_calendar_events(user_id, start_date, end_date):
    """Sync calendar events to CRM activities"""
    credentials = get_user_oauth_credentials(user_id, 'calendar')
    service = build('calendar', 'v3', credentials=credentials)
    
    events = service.events().list(
        calendarId='primary',
        timeMin=start_date.isoformat(),
        timeMax=end_date.isoformat()
    ).execute()
    
    for event in events.get('items', []):
        # Extract contact from attendees
        attendees = event.get('attendees', [])
        contact = find_contact_by_email(attendees)
        
        if contact:
            create_meeting_activity(
                contact_id=contact.id,
                subject=event['summary'],
                start_time=event['start']['dateTime'],
                end_time=event['end']['dateTime'],
                location=event.get('location'),
                created_by=user_id
            )
```

### Phone Integration (Twilio)

**Call Tracking:**
```python
from twilio.rest import Client

@app.route('/webhooks/twilio/call', methods=['POST'])
def twilio_call_webhook():
    """Handle incoming call webhook"""
    call_sid = request.form['CallSid']
    from_number = request.form['From']
    to_number = request.form['To']
    
    # Find contact by phone number
    contact = Contact.query.filter_by(phone=from_number).first()
    
    if contact:
        create_call_activity(
            contact_id=contact.id,
            phone_number=from_number,
            direction='inbound',
            call_sid=call_sid,
            duration=0  # Will be updated when call ends
        )
    
    return 'OK'

@app.route('/webhooks/twilio/call-complete', methods=['POST'])
def twilio_call_complete():
    """Update call activity with duration"""
    call_sid = request.form['CallSid']
    duration = int(request.form['Duration'])
    
    activity = Activity.query.filter_by(
        metadata['call_sid'].astext == call_sid
    ).first()
    
    if activity:
        activity.duration_minutes = duration
        activity.completed_at = datetime.utcnow()
        db.session.commit()
    
    return 'OK'
```

### Document Storage

**File Attachments:**
- Store files in S3/GCS
- Reference in activity metadata
- Support images, PDFs, documents
- Virus scanning for uploads

---

## Workflows & Automation

### Lead Assignment Rules

```python
def auto_assign_lead(lead):
    """Automatically assign lead based on rules"""
    rules = LeadAssignmentRule.query.filter_by(active=True).all()
    
    for rule in rules:
        if matches_criteria(lead, rule.criteria):
            lead.assigned_to = rule.assigned_user_id
            lead.save()
            
            # Send notification
            send_notification(
                user_id=rule.assigned_user_id,
                message=f"New lead assigned: {lead.contact.email}"
            )
            break
```

### Automated Follow-ups

```python
@celery.task
def check_follow_ups():
    """Check for contacts needing follow-up"""
    # Find contacts with no activity in last 7 days
    contacts = Contact.query.filter(
        Contact.last_activity_at < datetime.utcnow() - timedelta(days=7),
        Contact.status == 'active'
    ).all()
    
    for contact in contacts:
        # Create follow-up task
        create_task(
            title=f"Follow up with {contact.first_name}",
            contact_id=contact.id,
            assigned_to=contact.owner_id,
            due_date=datetime.utcnow() + timedelta(days=1),
            priority='normal'
        )
```

### Deal Stage Automation

```python
def update_deal_stage(deal, new_stage):
    """Update deal stage and trigger automations"""
    old_stage = deal.stage
    deal.stage = new_stage
    deal.save()
    
    # Log stage change
    create_note(
        deal_id=deal.id,
        content=f"Deal moved from {old_stage} to {new_stage}",
        created_by=current_user.id
    )
    
    # Trigger stage-specific actions
    if new_stage == 'proposal':
        # Send proposal email
        send_proposal_email(deal)
    elif new_stage == 'closed_won':
        # Create invoice, update contact status
        create_invoice_from_deal(deal)
        update_contact_status(deal.contact_id, 'customer')
```

### Email Campaign Automation

```python
@celery.task
def send_campaign(campaign_id):
    """Send email campaign to all recipients"""
    campaign = Campaign.query.get(campaign_id)
    recipients = get_campaign_recipients(campaign)
    
    for recipient in recipients:
        # Send email
        email_result = send_email(
            to=recipient.email,
            subject=campaign.subject,
            body=render_template(campaign.content, contact=recipient.contact)
        )
        
        # Update recipient status
        recipient.status = 'sent' if email_result.success else 'bounced'
        recipient.sent_at = datetime.utcnow()
        recipient.save()
        
        # Create activity
        create_email_activity(
            contact_id=recipient.contact_id,
            subject=campaign.subject,
            type='campaign',
            campaign_id=campaign_id
        )
```

---

## Reporting & Analytics

### Key Metrics

**Sales Metrics:**
- Total pipeline value
- Weighted pipeline value (value × probability)
- Average deal size
- Average sales cycle length
- Win rate (%)
- Conversion rate (lead → deal)

**Activity Metrics:**
- Activities per contact
- Calls per day/week
- Emails sent/received
- Meetings scheduled
- Task completion rate

**Team Performance:**
- Deals per rep
- Revenue per rep
- Activity volume per rep
- Response time to leads

### Report Types

**1. Pipeline Report**
```python
def generate_pipeline_report(start_date, end_date):
    """Generate pipeline report with stage breakdown"""
    deals = Deal.query.filter(
        Deal.created_at >= start_date,
        Deal.created_at <= end_date
    ).all()
    
    report = {
        'stages': {},
        'total_value': 0,
        'weighted_value': 0,
        'total_deals': len(deals)
    }
    
    for deal in deals:
        stage = deal.stage
        if stage not in report['stages']:
            report['stages'][stage] = {
                'count': 0,
                'total_value': 0,
                'weighted_value': 0
            }
        
        report['stages'][stage]['count'] += 1
        report['stages'][stage]['total_value'] += deal.value
        report['stages'][stage]['weighted_value'] += deal.value * (deal.probability / 100)
        report['total_value'] += deal.value
        report['weighted_value'] += deal.value * (deal.probability / 100)
    
    return report
```

**2. Revenue Forecast**
```python
def generate_forecast(end_date):
    """Generate revenue forecast based on deals"""
    deals = Deal.query.filter(
        Deal.stage.in_(['qualified', 'proposal', 'negotiation']),
        Deal.expected_close_date <= end_date
    ).all()
    
    forecast = {
        'months': {},
        'total_forecast': 0,
        'weighted_forecast': 0
    }
    
    for deal in deals:
        month = deal.expected_close_date.strftime('%Y-%m')
        if month not in forecast['months']:
            forecast['months'][month] = {
                'value': 0,
                'weighted_value': 0,
                'deal_count': 0
            }
        
        forecast['months'][month]['value'] += deal.value
        forecast['months'][month]['weighted_value'] += deal.value * (deal.probability / 100)
        forecast['months'][month]['deal_count'] += 1
        forecast['total_forecast'] += deal.value
        forecast['weighted_forecast'] += deal.value * (deal.probability / 100)
    
    return forecast
```

**3. Activity Report**
```python
def generate_activity_report(start_date, end_date, user_id=None):
    """Generate activity report by type and user"""
    query = Activity.query.filter(
        Activity.created_at >= start_date,
        Activity.created_at <= end_date
    )
    
    if user_id:
        query = query.filter(Activity.created_by == user_id)
    
    activities = query.all()
    
    report = {
        'by_type': {},
        'by_user': {},
        'total': len(activities)
    }
    
    for activity in activities:
        # By type
        if activity.type not in report['by_type']:
            report['by_type'][activity.type] = 0
        report['by_type'][activity.type] += 1
        
        # By user
        user_name = activity.created_by_user.full_name
        if user_name not in report['by_user']:
            report['by_user'][user_name] = 0
        report['by_user'][user_name] += 1
    
    return report
```

---

## Security & Permissions

### CRM-Specific Permissions

```python
# Permission structure
CRM_PERMISSIONS = {
    'contacts': ['view', 'create', 'update', 'delete', 'export'],
    'companies': ['view', 'create', 'update', 'delete'],
    'leads': ['view', 'create', 'update', 'delete', 'convert'],
    'deals': ['view', 'create', 'update', 'delete', 'close'],
    'activities': ['view', 'create', 'update', 'delete'],
    'campaigns': ['view', 'create', 'update', 'delete', 'send'],
    'reports': ['view', 'export']
}
```

### Data Access Control

**Owner-Based Access:**
- Users can view/edit contacts/deals they own
- Managers can view team members' records
- Admins have full access

**Field-Level Security:**
- Hide sensitive fields (e.g., custom revenue fields)
- Restrict access to private notes

**Implementation:**
```python
@permission_required('contacts.view')
def get_contact(contact_id):
    contact = Contact.query.get_or_404(contact_id)
    
    # Check ownership or admin
    if contact.owner_id != current_user.id and not current_user.has_permission('contacts.view_all'):
        abort(403)
    
    return jsonify(contact.to_dict())
```

---

## Scalability Considerations

### Database Optimization

**Indexing:**
```sql
-- Full-text search on contacts
CREATE INDEX idx_contacts_search ON crm.contacts 
USING gin(to_tsvector('english', first_name || ' ' || last_name || ' ' || email));

-- Activity timeline queries
CREATE INDEX idx_activities_timeline ON crm.activities(contact_id, created_at DESC, type);

-- Deal pipeline queries
CREATE INDEX idx_deals_pipeline ON crm.deals(owner_id, stage, expected_close_date);
```

**Partitioning:**
For large activity tables, partition by date:
```sql
CREATE TABLE crm.activities_2024 PARTITION OF crm.activities
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');
```

### Caching Strategy

**Redis Cache:**
- Contact lists (TTL: 5 minutes)
- Pipeline data (TTL: 2 minutes)
- Report results (TTL: 15 minutes)
- Segment membership (TTL: 1 hour)

**Cache Invalidation:**
- On contact update: Clear contact cache
- On deal stage change: Clear pipeline cache
- On activity create: Clear timeline cache

### Search Optimization

**PostgreSQL Full-Text Search:**
```sql
-- Search contacts
SELECT * FROM crm.contacts
WHERE to_tsvector('english', first_name || ' ' || last_name || ' ' || email)
@@ plainto_tsquery('english', 'john doe');
```

**Elasticsearch (for large datasets):**
- Index contacts, companies, deals
- Fast faceted search
- Autocomplete support

---

## Implementation Roadmap

### Phase 1: Core CRM (Weeks 1-4)
- [ ] Database schema creation (contacts, companies, deals, activities)
- [ ] Contact CRUD operations
- [ ] Company CRUD operations
- [ ] Basic deal management
- [ ] Activity logging
- [ ] Contact detail page with timeline
- [ ] Basic search and filtering

### Phase 2: Pipeline & Leads (Weeks 5-6)
- [ ] Deal pipeline board (Kanban)
- [ ] Lead management
- [ ] Lead scoring
- [ ] Lead conversion workflow
- [ ] Pipeline reporting
- [ ] Revenue forecasting

### Phase 3: Advanced Features (Weeks 7-8)
- [ ] Task management
- [ ] Email campaigns
- [ ] Customer segmentation
- [ ] Custom fields
- [ ] Tags system
- [ ] Advanced reporting

### Phase 4: Integrations (Weeks 9-10)
- [ ] Gmail integration (email sync)
- [ ] Google Calendar integration
- [ ] Twilio phone integration
- [ ] Email tracking (opens, clicks)
- [ ] Document attachments

### Phase 5: Automation (Weeks 11-12)
- [ ] Lead assignment rules
- [ ] Automated follow-ups
- [ ] Workflow automation
- [ ] Email templates
- [ ] Scheduled reports

### Phase 6: Polish & Optimization (Weeks 13-14)
- [ ] Performance optimization
- [ ] Caching implementation
- [ ] Search optimization
- [ ] Mobile responsiveness
- [ ] User documentation

---

## Code Organization

```
app/
├── modules/
│   └── crm/
│       ├── __init__.py
│       ├── routes.py              # Web routes
│       ├── forms.py               # WTForms
│       └── views.py               # View functions
├── models/
│   └── crm.py                     # CRM models (Contact, Deal, etc.)
├── api/
│   └── v1/
│       └── crm.py                 # CRM API endpoints
├── services/
│   ├── crm_service.py             # Business logic
│   ├── lead_scoring_service.py   # Lead scoring
│   ├── pipeline_service.py        # Pipeline calculations
│   └── reporting_service.py        # Report generation
└── tasks/
    └── crm_tasks.py               # Celery tasks (follow-ups, etc.)
```

---

## Additional Resources

- [Salesforce Architecture Patterns](https://developer.salesforce.com/docs)
- [HubSpot CRM Best Practices](https://www.hubspot.com/crm)
- [PostgreSQL Full-Text Search](https://www.postgresql.org/docs/current/textsearch.html)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Twilio API Documentation](https://www.twilio.com/docs)
