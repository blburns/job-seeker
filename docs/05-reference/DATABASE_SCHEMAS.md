# Database Schema Structure

## Overview
This document describes the database structure organized by PostgreSQL schemas. Tables are logically grouped into schemas based on their functional domain.

## Schema Organization

The database uses PostgreSQL schemas to logically separate tables by module/domain:

1. **`auth`** - Authentication and authorization
2. **`jobs`** - Job seeker automation (master profiles, postings, applications, discovery, auto-apply)
3. **`accounts`** - Business account management (legacy boilerplate)
4. **`contacts`** - Contact management (legacy boilerplate)
5. **`documents`** - Document/file management (legacy boilerplate)
6. **`organizations`** - Organization management (legacy boilerplate)
7. **`tenants`** - Multi-tenancy support (legacy boilerplate)
8. **`settings`** - Application settings and configuration (legacy boilerplate)
9. **`public`** - System tables (alembic_version)

> **Job seeker tables** are the primary active schema. See [JOB_SEEKER_DATA_MODEL.md](JOB_SEEKER_DATA_MODEL.md) for complete jobs schema documentation with field descriptions and relationships.

---

## Schema: `jobs`

**Purpose**: Job seeker automation — master profiles, job postings, applications, discovery, tailoring, and auto-apply.

**Source**: [`app/models/jobs.py`](../../app/models/jobs.py)

### Tables

| Table | Purpose |
|-------|---------|
| `master_profiles` | Canonical structured resume per user |
| `job_postings` | Saved job listings (manual, URL, or discovery) |
| `job_search_profiles` | Automated discovery criteria |
| `discovered_jobs` | Staging records in discovery inbox |
| `discovery_runs` | Audit log for connector executions |
| `company_blocklists` | Companies/URLs to skip during discovery |
| `applications` | Job application tracking with pipeline stage |
| `resume_versions` | Per-job tailored resume with diff log |
| `keyword_analyses` | JD keyword coverage snapshots |
| `apply_drafts` | Pre-filled application forms |
| `apply_batches` | Groups of applications for auto-submission |
| `apply_batch_items` | Per-application batch progress |
| `portal_credentials` | Encrypted portal session data |
| `application_activities` | Application timeline events |

### Key enums

- **ApplicationStage**: `saved`, `tailoring`, `ready_to_apply`, `applied`, `phone_screen`, `interview`, `offer`, `rejected`, `withdrawn`
- **JobSource**: `manual`, `url`, `rss`, `adzuna`, `remotive`, `greenhouse`, `lever`, `linkedin`, `indeed`
- **PortalType**: `greenhouse`, `lever`, `ashby`, `linkedin`, `indeed`, `generic`

### Initialization

```bash
python scripts/init_database.py      # auth + core tables
python scripts/create_jobs_schema.py # all jobs tables above
```

Full field-level documentation: [JOB_SEEKER_DATA_MODEL.md](JOB_SEEKER_DATA_MODEL.md)

---

## Schema: `auth`

**Purpose**: User authentication, authorization, and RBAC (Role-Based Access Control)

### Tables

#### `users`
User accounts and authentication

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `username` | VARCHAR(64) | Unique username, indexed |
| `email` | VARCHAR(120) | Unique email, indexed |
| `password_hash` | VARCHAR(256) | Bcrypt hashed password |
| `is_active` | BOOLEAN | Account active status |
| `is_admin` | BOOLEAN | Admin privileges |
| `is_superadmin` | BOOLEAN | Super admin privileges |
| `email_verified` | BOOLEAN | Email verification status |
| `email_verification_token` | VARCHAR(255) | Email verification token |
| `email_verification_expires` | TIMESTAMP | Token expiration |
| `password_reset_token` | VARCHAR(255) | Password reset token |
| `password_reset_expires` | TIMESTAMP | Reset token expiration |
| `last_login` | TIMESTAMP | Last login timestamp |
| `last_activity` | TIMESTAMP | Last activity timestamp |
| `failed_login_attempts` | INTEGER | Failed login counter (default: 0) |
| `last_failed_login` | TIMESTAMP | Last failed login attempt |
| `lockout_until` | TIMESTAMP | Account lockout expiration |
| `firstname` | VARCHAR(64) | First name |
| `lastname` | VARCHAR(64) | Last name |
| `display_name` | VARCHAR(64) | Display name |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Indexes**: `username`, `email`

**Security Features**:
- Account lockout after 5 failed attempts (30 minutes)
- Password reset tokens with expiration
- Email verification tokens with expiration

---

#### `roles`
RBAC roles with permissions

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(64) | Unique role name |
| `display_name` | VARCHAR(64) | Display name |
| `description` | TEXT | Role description |
| `permissions` | JSON | Permission structure: `{"module": ["action1", "action2"]}` |
| `priority` | INTEGER | Role priority (default: 0) |
| `is_system_role` | BOOLEAN | System role flag (default: false) |
| `is_active` | BOOLEAN | Active status (default: true) |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Indexes**: `name` (unique)

**Relationships**:
- Many-to-Many with `users` (via `user_roles`)
- Many-to-Many with `groups` (via `group_roles`)

---

#### `groups`
User groups for organizing users

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(64) | Unique group name |
| `display_name` | VARCHAR(64) | Display name |
| `description` | TEXT | Group description |
| `is_active` | BOOLEAN | Active status (default: true) |
| `is_system_group` | BOOLEAN | System group flag (default: false) |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Indexes**: `name` (unique)

**Relationships**:
- Many-to-Many with `users` (via `user_groups`)
- Many-to-Many with `roles` (via `group_roles`)

---

#### `user_roles`
Association table: Users ↔ Roles (Many-to-Many)

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | UUID (FK) | Foreign key to `users.id` |
| `role_id` | UUID (FK) | Foreign key to `roles.id` |
| `created_at` | TIMESTAMP | Creation timestamp |

**Primary Key**: (`user_id`, `role_id`)

---

#### `user_groups`
Association table: Users ↔ Groups (Many-to-Many)

| Column | Type | Description |
|--------|------|-------------|
| `user_id` | UUID (FK) | Foreign key to `users.id` |
| `group_id` | UUID (FK) | Foreign key to `groups.id` |
| `created_at` | TIMESTAMP | Creation timestamp |

**Primary Key**: (`user_id`, `group_id`)

---

#### `group_roles`
Association table: Groups ↔ Roles (Many-to-Many)

| Column | Type | Description |
|--------|------|-------------|
| `group_id` | UUID (FK) | Foreign key to `groups.id` |
| `role_id` | UUID (FK) | Foreign key to `roles.id` |
| `created_at` | TIMESTAMP | Creation timestamp |

**Primary Key**: (`group_id`, `role_id`)

---

## Schema: `accounts`

**Purpose**: Business account management (customers, vendors, partners)

### Tables

#### `accounts`
Main account records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `account_uuid` | UUID | Unique account identifier, indexed |
| `account_name` | VARCHAR(128) | Account name, indexed |
| `account_number` | VARCHAR(64) | Account number (unique, indexed) |
| `legal_name` | VARCHAR(128) | Legal name |
| `account_type_id` | UUID (FK) | Foreign key to `account_types.id` |
| `category_id` | UUID (FK) | Foreign key to `account_categories.id` |
| `status` | VARCHAR(32) | Status (active, inactive, prospect, customer, vendor) |
| `primary_email` | VARCHAR(120) | Primary email, indexed |
| `primary_phone` | VARCHAR(20) | Primary phone |
| `website` | VARCHAR(255) | Website URL |
| `billing_address_line1` | VARCHAR(128) | Billing address line 1 |
| `billing_address_line2` | VARCHAR(128) | Billing address line 2 |
| `billing_city` | VARCHAR(64) | Billing city |
| `billing_state_province` | VARCHAR(64) | Billing state/province |
| `billing_postal_code` | VARCHAR(20) | Billing postal code |
| `billing_country` | VARCHAR(64) | Billing country |
| `shipping_address_line1` | VARCHAR(128) | Shipping address line 1 |
| `shipping_address_line2` | VARCHAR(128) | Shipping address line 2 |
| `shipping_city` | VARCHAR(64) | Shipping city |
| `shipping_state_province` | VARCHAR(64) | Shipping state/province |
| `shipping_postal_code` | VARCHAR(20) | Shipping postal code |
| `shipping_country` | VARCHAR(64) | Shipping country |
| `industry` | VARCHAR(64) | Industry |
| `company_size` | VARCHAR(64) | Company size |
| `annual_revenue` | VARCHAR(64) | Annual revenue |
| `tax_id` | VARCHAR(64) | Tax ID |
| `registration_number` | VARCHAR(64) | Registration number |
| `credit_limit` | NUMERIC | Credit limit |
| `payment_terms` | VARCHAR(64) | Payment terms (e.g., Net 30) |
| `currency` | VARCHAR(10) | Currency code |
| `parent_account_id` | UUID (FK) | Parent account (self-referential) |
| `notes` | TEXT | Notes |
| `tags` | JSON | Tags array |
| `custom_fields` | JSON | Custom fields object |
| `last_activity_date` | TIMESTAMP | Last activity date |
| `last_contacted` | TIMESTAMP | Last contacted date |
| `created_by` | UUID (FK) | Creator user ID |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Indexes**: `account_uuid`, `account_name`, `account_number`, `primary_email`

**Relationships**:
- Foreign key to `account_types`
- Foreign key to `account_categories`
- Self-referential to `parent_account_id`

---

#### `account_types`
Account type classifications

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(64) | Type name |
| `description` | TEXT | Description |
| `color` | VARCHAR(32) | Display color |
| `is_active` | BOOLEAN | Active status |
| `sort_order` | INTEGER | Sort order |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

#### `account_categories`
Account category classifications

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(64) | Category name |
| `description` | TEXT | Description |
| `color` | VARCHAR(32) | Display color |
| `is_active` | BOOLEAN | Active status |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

#### `account_activities`
Account activity tracking

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `account_id` | UUID (FK) | Foreign key to `accounts.id` |
| `activity_type` | VARCHAR(64) | Activity type |
| `subject` | VARCHAR(255) | Activity subject |
| `description` | TEXT | Activity description |
| `activity_date` | TIMESTAMP | Activity date |
| `outcome` | VARCHAR(64) | Outcome |
| `duration` | INTEGER | Duration (minutes) |
| `priority` | VARCHAR(32) | Priority level |
| `related_entity_type` | VARCHAR(64) | Related entity type |
| `related_entity_id` | UUID | Related entity ID |
| `created_by` | UUID (FK) | Creator user ID |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Relationships**:
- Foreign key to `accounts`

---

#### `account_settings`
Account-specific settings

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `setting_key` | VARCHAR(128) | Setting key |
| `json_data` | JSON | Setting data |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

## Schema: `contacts`

**Purpose**: Contact management and communication tracking

### Tables

#### `contacts`
Contact records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `first_name` | VARCHAR(64) | First name |
| `last_name` | VARCHAR(64) | Last name |
| `company` | VARCHAR(128) | Company name |
| `job_title` | VARCHAR(128) | Job title |
| `email` | VARCHAR(120) | Email address |
| `phone` | VARCHAR(20) | Phone number |
| `mobile` | VARCHAR(20) | Mobile number |
| `website` | VARCHAR(255) | Website URL |
| `address_line1` | VARCHAR(128) | Address line 1 |
| `address_line2` | VARCHAR(128) | Address line 2 |
| `city` | VARCHAR(64) | City |
| `state_province` | VARCHAR(64) | State/province |
| `postal_code` | VARCHAR(20) | Postal code |
| `country` | VARCHAR(64) | Country |
| `notes` | TEXT | Notes |
| `tags` | JSON | Tags array |
| `source` | VARCHAR(64) | Contact source |
| `status` | VARCHAR(32) | Contact status |
| `linkedin` | VARCHAR(255) | LinkedIn URL |
| `twitter` | VARCHAR(255) | Twitter handle |
| `facebook` | VARCHAR(255) | Facebook URL |
| `industry` | VARCHAR(64) | Industry |
| `company_size` | VARCHAR(64) | Company size |
| `annual_revenue` | VARCHAR(64) | Annual revenue |
| `last_contacted` | TIMESTAMP | Last contacted date |
| `category_id` | UUID (FK) | Foreign key to `contact_categories.id` |
| `created_by` | UUID (FK) | Creator user ID |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `contact_categories`

---

#### `contact_categories`
Contact category classifications

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(64) | Category name |
| `description` | TEXT | Description |
| `color` | VARCHAR(32) | Display color |
| `is_active` | BOOLEAN | Active status |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

#### `contact_communications`
Communication history tracking

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `contact_id` | UUID (FK) | Foreign key to `contacts.id` |
| `communication_type` | VARCHAR(64) | Type (email, phone, meeting, etc.) |
| `subject` | VARCHAR(255) | Communication subject |
| `content` | TEXT | Communication content |
| `direction` | VARCHAR(32) | Direction (inbound, outbound) |
| `communication_date` | TIMESTAMP | Communication date |
| `duration` | INTEGER | Duration (minutes) |
| `outcome` | VARCHAR(64) | Outcome |
| `created_by` | UUID (FK) | Creator user ID |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Relationships**:
- Foreign key to `contacts`

---

#### `contact_settings`
Contact module settings

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `setting_key` | VARCHAR(128) | Setting key |
| `json_data` | JSON | Setting data |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

## Schema: `documents`

**Purpose**: Document and file management

### Tables

#### `documents`
Document records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `title` | VARCHAR(255) | Document title |
| `description` | TEXT | Description |
| `filename` | VARCHAR(255) | Stored filename |
| `original_filename` | VARCHAR(255) | Original filename |
| `file_path` | VARCHAR(512) | File storage path |
| `file_size` | BIGINT | File size in bytes |
| `mime_type` | VARCHAR(128) | MIME type |
| `file_extension` | VARCHAR(16) | File extension |
| `version` | INTEGER | Version number |
| `is_latest_version` | BOOLEAN | Latest version flag |
| `parent_document_id` | UUID (FK) | Parent document (versioning) |
| `is_public` | BOOLEAN | Public access flag |
| `access_level` | VARCHAR(32) | Access level (private, internal, public) |
| `password_protected` | BOOLEAN | Password protection flag |
| `password_hash` | VARCHAR(256) | Password hash |
| `tags` | JSON | Tags array |
| `document_metadata` | JSON | Metadata object |
| `status` | VARCHAR(32) | Document status |
| `workflow_stage` | VARCHAR(64) | Workflow stage |
| `last_accessed` | TIMESTAMP | Last accessed date |
| `category_id` | UUID (FK) | Foreign key to `document_categories.id` |
| `created_by` | UUID (FK) | Creator user ID |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `document_categories`
- Self-referential to `parent_document_id` (versioning)

---

#### `document_categories`
Document category classifications

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(64) | Category name |
| `description` | TEXT | Description |
| `color` | VARCHAR(32) | Display color |
| `is_active` | BOOLEAN | Active status |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

#### `document_access_logs`
Document access tracking

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `document_id` | UUID (FK) | Foreign key to `documents.id` |
| `access_type` | VARCHAR(64) | Access type (view, download, etc.) |
| `ip_address` | VARCHAR(45) | IP address |
| `user_agent` | TEXT | User agent string |
| `accessed_by` | UUID (FK) | User who accessed |
| `accessed_at` | TIMESTAMP | Access timestamp |

**Relationships**:
- Foreign key to `documents`

---

#### `document_shares`
Document sharing permissions

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `document_id` | UUID (FK) | Foreign key to `documents.id` |
| `shared_with_user` | UUID (FK) | Shared with user |
| `shared_with_group` | UUID (FK) | Shared with group |
| `permission_level` | VARCHAR(32) | Permission level (read, write, etc.) |
| `expires_at` | TIMESTAMP | Expiration date |
| `password_protected` | BOOLEAN | Password protection flag |
| `password_hash` | VARCHAR(256) | Password hash |
| `created_at` | TIMESTAMP | Creation timestamp |
| `created_by` | UUID (FK) | Creator user ID |

**Relationships**:
- Foreign key to `documents`

---

#### `document_workflows`
Document workflow definitions

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(128) | Workflow name |
| `description` | TEXT | Description |
| `stages` | JSON | Workflow stages array |
| `is_active` | BOOLEAN | Active status |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

## Schema: `organizations`

**Purpose**: Organization and brand management

### Tables

#### `organizations`
Organization records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(128) | Organization name |
| `legal_name` | VARCHAR(128) | Legal name |
| `slug` | VARCHAR(128) | URL slug (unique) |
| `code` | VARCHAR(64) | Organization code |
| `org_type` | VARCHAR(32) | Organization type |
| `status` | VARCHAR(32) | Status (active, inactive, etc.) |
| `parent_id` | UUID (FK) | Parent organization (self-referential) |
| `tenant_id` | UUID (FK) | Foreign key to `tenants.id` |
| `root_organization_id` | UUID (FK) | Root organization ID |
| `description` | TEXT | Description |
| `industry` | VARCHAR(64) | Industry |
| `business_type` | VARCHAR(64) | Business type |
| `registration_number` | VARCHAR(64) | Registration number |
| `tax_id` | VARCHAR(64) | Tax ID |
| `vat_number` | VARCHAR(64) | VAT number |
| `email` | VARCHAR(120) | Email address |
| `phone` | VARCHAR(20) | Phone number |
| `website` | VARCHAR(255) | Website URL |
| `address_line1` | VARCHAR(128) | Address line 1 |
| `address_line2` | VARCHAR(128) | Address line 2 |
| `city` | VARCHAR(64) | City |
| `state` | VARCHAR(64) | State |
| `postal_code` | VARCHAR(20) | Postal code |
| `country` | VARCHAR(64) | Country |
| `currency` | VARCHAR(10) | Currency code |
| `fiscal_year_start` | VARCHAR(10) | Fiscal year start |
| `logo_url` | VARCHAR(512) | Logo URL |
| `brand_colors` | JSON | Brand colors object |
| `brand_guidelines` | TEXT | Brand guidelines |
| `settings` | JSON | Settings object |
| `permissions` | JSON | Permissions object |
| `notes` | TEXT | Notes |
| `tags` | JSON | Tags array |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `tenants`
- Self-referential to `parent_id` and `root_organization_id`

---

#### `organization_members`
Organization membership records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `organization_id` | UUID (FK) | Foreign key to `organizations.id` |
| `user_id` | UUID (FK) | Foreign key to `users.id` |
| `role` | VARCHAR(64) | Member role |
| `is_active` | BOOLEAN | Active status |
| `joined_at` | TIMESTAMP | Join date |
| `left_at` | TIMESTAMP | Leave date |
| `permissions` | JSON | Permissions object |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `organizations`
- Foreign key to `users` (in `auth` schema)

---

#### `brands`
Brand records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(128) | Brand name |
| `slug` | VARCHAR(128) | URL slug (unique) |
| `description` | TEXT | Description |
| `organization_id` | UUID (FK) | Foreign key to `organizations.id` |
| `parent_brand_id` | UUID (FK) | Parent brand (self-referential) |
| `logo_url` | VARCHAR(512) | Logo URL |
| `brand_colors` | JSON | Brand colors object |
| `typography` | JSON | Typography settings |
| `brand_guidelines` | TEXT | Brand guidelines |
| `is_active` | BOOLEAN | Active status |
| `is_public` | BOOLEAN | Public visibility |
| `tags` | JSON | Tags array |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `organizations`
- Self-referential to `parent_brand_id`

---

## Schema: `tenants`

**Purpose**: Multi-tenancy support

### Tables

#### `tenants`
Tenant records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(128) | Tenant name |
| `slug` | VARCHAR(128) | URL slug (unique) |
| `domain` | VARCHAR(255) | Custom domain |
| `is_active` | BOOLEAN | Active status |
| `is_trial` | BOOLEAN | Trial account flag |
| `trial_ends_at` | TIMESTAMP | Trial end date |
| `subscription_plan` | VARCHAR(64) | Subscription plan |
| `subscription_status` | VARCHAR(32) | Subscription status |
| `subscription_ends_at` | TIMESTAMP | Subscription end date |
| `settings` | JSON | Settings object |
| `custom_domain` | VARCHAR(255) | Custom domain |
| `max_users` | INTEGER | Maximum users |
| `max_storage_gb` | INTEGER | Maximum storage (GB) |
| `max_api_calls_per_month` | INTEGER | Maximum API calls per month |
| `contact_email` | VARCHAR(120) | Contact email |
| `contact_phone` | VARCHAR(20) | Contact phone |
| `billing_email` | VARCHAR(120) | Billing email |
| `address_line1` | VARCHAR(128) | Address line 1 |
| `address_line2` | VARCHAR(128) | Address line 2 |
| `city` | VARCHAR(64) | City |
| `state` | VARCHAR(64) | State |
| `postal_code` | VARCHAR(20) | Postal code |
| `country` | VARCHAR(64) | Country |
| `notes` | TEXT | Notes |
| `tags` | JSON | Tags array |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Indexes**: `slug` (unique)

---

#### `tenant_invitations`
Tenant invitation records

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `tenant_id` | UUID (FK) | Foreign key to `tenants.id` |
| `email` | VARCHAR(120) | Invitee email |
| `role` | VARCHAR(64) | Assigned role |
| `invited_by` | UUID (FK) | Inviter user ID |
| `token` | VARCHAR(255) | Invitation token |
| `expires_at` | TIMESTAMP | Expiration date |
| `is_accepted` | BOOLEAN | Acceptance status |
| `accepted_at` | TIMESTAMP | Acceptance date |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `tenants`

---

#### `tenant_settings`
Tenant-specific settings

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `tenant_id` | UUID (FK) | Foreign key to `tenants.id` |
| `key` | VARCHAR(128) | Setting key |
| `value` | JSON | Setting value |
| `description` | TEXT | Description |
| `is_public` | BOOLEAN | Public visibility |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `tenants`

---

#### `tenant_usage`
Tenant usage metrics

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `tenant_id` | UUID (FK) | Foreign key to `tenants.id` |
| `metric_name` | VARCHAR(64) | Metric name |
| `metric_value` | INTEGER | Metric value |
| `recorded_at` | TIMESTAMP | Recording timestamp |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |
| `is_deleted` | BOOLEAN | Soft delete flag |
| `deleted_at` | TIMESTAMP | Deletion timestamp |

**Relationships**:
- Foreign key to `tenants`

---

## Schema: `settings`

**Purpose**: Application settings and configuration

### Tables

#### `settings`
Core settings table

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `key` | VARCHAR(128) | Setting key (unique) |
| `name` | VARCHAR(128) | Setting name |
| `description` | TEXT | Description |
| `category_id` | UUID (FK) | Foreign key to `setting_categories.id` |
| `setting_type` | VARCHAR(32) | Setting type |
| `data_type` | VARCHAR(32) | Data type (string, integer, boolean, json) |
| `default_value` | TEXT | Default value |
| `current_value` | TEXT | Current value |
| `is_required` | BOOLEAN | Required flag |
| `is_encrypted` | BOOLEAN | Encrypted flag |
| `is_readonly` | BOOLEAN | Read-only flag |
| `validation_rules` | JSON | Validation rules |
| `sort_order` | INTEGER | Sort order |
| `is_active` | BOOLEAN | Active status |
| `user_id` | UUID (FK) | User-specific setting (nullable) |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Relationships**:
- Foreign key to `setting_categories`
- Foreign key to `users` (in `auth` schema) for user-specific settings

---

#### `setting_categories`
Settings category classifications

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `name` | VARCHAR(64) | Category name |
| `display_name` | VARCHAR(128) | Display name |
| `description` | TEXT | Description |
| `sort_order` | INTEGER | Sort order |
| `is_active` | BOOLEAN | Active status |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

---

#### `setting_values`
Historical setting values (audit trail)

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `setting_id` | UUID (FK) | Foreign key to `settings.id` |
| `value` | TEXT | Setting value |
| `previous_value` | TEXT | Previous value |
| `changed_by` | VARCHAR(64) | User who changed |
| `change_reason` | VARCHAR(255) | Change reason |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Relationships**:
- Foreign key to `settings`

---

#### `setting_overrides`
Environment-specific setting overrides

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `setting_id` | UUID (FK) | Foreign key to `settings.id` |
| `environment` | VARCHAR(32) | Environment (development, staging, production) |
| `value` | TEXT | Override value |
| `is_active` | BOOLEAN | Active status |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Relationships**:
- Foreign key to `settings`

---

#### `module_settings`
Module-specific JSON configurations

| Column | Type | Description |
|--------|------|-------------|
| `id` | UUID (PK) | Primary key |
| `module_name` | VARCHAR(64) | Module name |
| `setting_key` | VARCHAR(128) | Setting key |
| `setting_name` | VARCHAR(128) | Setting name |
| `description` | TEXT | Description |
| `json_data` | JSON | JSON configuration data |
| `is_active` | BOOLEAN | Active status |
| `created_by` | VARCHAR(64) | Creator |
| `updated_by` | VARCHAR(64) | Updater |
| `created_at` | TIMESTAMP | Creation timestamp |
| `updated_at` | TIMESTAMP | Last update timestamp |

**Indexes**: `module_name`, (`module_name`, `setting_key`) unique

---

## Schema: `public`

**Purpose**: System tables

### Tables

#### `alembic_version`
Alembic migration version tracking

| Column | Type | Description |
|--------|------|-------------|
| `version_num` | VARCHAR(32) | Migration version number |

---

## Cross-Schema Relationships

### Foreign Key Relationships

1. **`auth.users`** referenced by:
   - `accounts.accounts.created_by`
   - `accounts.account_activities.created_by`
   - `contacts.contacts.created_by`
   - `contacts.contact_communications.created_by`
   - `documents.documents.created_by`
   - `documents.document_access_logs.accessed_by`
   - `documents.document_shares.created_by`
   - `organizations.organization_members.user_id`
   - `tenants.tenant_invitations.invited_by`
   - `settings.settings.user_id`

2. **`tenants.tenants`** referenced by:
   - `organizations.organizations.tenant_id`

3. **`organizations.organizations`** referenced by:
   - `organizations.brands.organization_id`
   - `organizations.organization_members.organization_id`

---

## Schema Summary

| Schema | Tables | Purpose |
|--------|--------|---------|
| `auth` | 6 | Authentication and authorization |
| `accounts` | 5 | Business account management |
| `contacts` | 4 | Contact management |
| `documents` | 5 | Document/file management |
| `organizations` | 3 | Organization and brand management |
| `tenants` | 4 | Multi-tenancy support |
| `settings` | 5 | Application settings |
| `public` | 1 | System tables |
| **Total** | **33** | |

---

## Schema Migration Strategy

To move tables from `public` schema to their respective schemas:

1. **Create schemas**:
   ```sql
   CREATE SCHEMA IF NOT EXISTS auth;
   CREATE SCHEMA IF NOT EXISTS accounts;
   CREATE SCHEMA IF NOT EXISTS contacts;
   CREATE SCHEMA IF NOT EXISTS documents;
   CREATE SCHEMA IF NOT EXISTS organizations;
   CREATE SCHEMA IF NOT EXISTS tenants;
   CREATE SCHEMA IF NOT EXISTS settings;
   ```

2. **Move tables** (example for auth schema):
   ```sql
   ALTER TABLE users SET SCHEMA auth;
   ALTER TABLE roles SET SCHEMA auth;
   ALTER TABLE groups SET SCHEMA auth;
   ALTER TABLE user_roles SET SCHEMA auth;
   ALTER TABLE user_groups SET SCHEMA auth;
   ALTER TABLE group_roles SET SCHEMA auth;
   ```

3. **Update foreign key references** to use schema-qualified names:
   ```sql
   -- Example: Update foreign keys to reference auth.users
   ALTER TABLE accounts.accounts 
   DROP CONSTRAINT IF EXISTS accounts_created_by_fkey;
   
   ALTER TABLE accounts.accounts 
   ADD CONSTRAINT accounts_created_by_fkey 
   FOREIGN KEY (created_by) REFERENCES auth.users(id);
   ```

4. **Update SQLAlchemy models** to specify schema:
   ```python
   class User(db.Model):
       __tablename__ = 'users'
       __table_args__ = {'schema': 'auth'}
       # ...
   ```

---

## Benefits of Schema Organization

1. **Logical Separation**: Tables grouped by functional domain
2. **Security**: Schema-level permissions for access control
3. **Maintainability**: Easier to understand and maintain
4. **Scalability**: Easy to add new modules with their own schemas
5. **Multi-tenancy**: Can support tenant-specific schemas if needed
6. **Backup/Restore**: Can backup/restore individual schemas

---

## Notes

- All tables use **UUID primary keys** (PostgreSQL UUID type)
- Most tables include **soft delete** support (`is_deleted`, `deleted_at`)
- All tables have **timestamps** (`created_at`, `updated_at`)
- **Cross-schema foreign keys** require schema qualification in PostgreSQL
- **Indexes** are created on frequently queried columns
- **JSON columns** are used for flexible data storage (tags, metadata, settings)
