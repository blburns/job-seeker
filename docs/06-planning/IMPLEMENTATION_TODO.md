# Implementation TODO List
## Ecommerce/Billing/CRM/ERP Platform

> **Reference**: See [ECOMMERCE_CRM_ERP_ARCHITECTURE.md](./ECOMMERCE_CRM_ERP_ARCHITECTURE.md) for detailed specifications.

---

## Legend
- [ ] Not Started
- [x] Completed
- [🚧] In Progress
- [⏸️] Blocked/On Hold
- [🔄] Needs Review/Testing

---

## Phase 1: Foundation & Infrastructure (Weeks 1-4)

### 1.1 Authentication & User Management
- [x] Basic user registration and login
- [x] Password reset functionality
- [x] User profile management (firstname, lastname, email)
- [x] Extended profile fields (organization, phone, address, etc.)
- [x] Profile photo upload
- [x] User view pages (admin view of user accounts)
- [x] Email verification on registration
- [x] Email verification endpoint with token validation
- [x] Resend verification email functionality
- [x] Account activation/deactivation workflow
- [x] Two-factor authentication (2FA) setup
  - [x] TOTP implementation (Google Authenticator)
  - [x] Backup codes generation
  - [x] 2FA setup flow with QR code
  - [x] 2FA verification on login
  - [x] Backup code verification
  - [x] 2FA management UI (enable/disable/regenerate)
  - [ ] 2FA enforcement for admin roles (optional)
- [x] OAuth integration
  - [x] Google OAuth
  - [x] Microsoft OAuth
  - [x] GitHub OAuth
  - [x] OAuth account linking model
  - [x] OAuth service with Authlib
  - [x] OAuth login/callback routes
  - [x] OAuth UI buttons
- [x] Session management improvements
  - [x] Active sessions list
  - [x] Remote session revocation
  - [x] "Remember me" functionality
  - [x] Session timeout configuration
  - [x] Session tracking database table
  - [x] Device and browser detection
  - [x] IP address tracking
  - [x] Session expiration handling

### 1.2 RBAC Enhancement
- [x] Basic roles and permissions system
- [x] Permission checking decorators
- [x] Enhanced RBAC models (Permission, UserRoleAssignment, RoleHierarchy)
- [x] RBAC service for centralized management
- [x] Admin module with comprehensive routes
- [x] Role management UI
  - [x] Create/edit/delete roles
  - [x] Assign permissions to roles
  - [x] Role hierarchy (inheritance) - model ready
  - [x] View role details and assignments
- [x] Permission management UI
  - [x] List all permissions
  - [x] Group permissions by module
  - [x] Permission descriptions
  - [x] Create/edit permissions
- [x] User role assignment UI
  - [x] Assign multiple roles to users
  - [x] Role expiration dates
  - [x] Role audit log (assignment tracking)
  - [x] Revoke roles with reason
- [x] Advanced permission features
  - [x] Resource-level permissions (via permission naming)
  - [x] Dynamic permission checking (via decorators)
  - [x] Permission inheritance (via role hierarchy model)
  - [ ] Permission caching (future optimization)

### 1.3 Email Service Integration
- [x] Email service setup (SendGrid/Mailgun/SMTP/Console)
  - [x] Multi-provider support (SendGrid, Mailgun, SMTP, Console)
  - [x] API key configuration
  - [ ] Domain verification (manual setup required)
  - [ ] SPF/DKIM/DMARC setup (manual setup required)
- [x] Email templates
  - [x] Base email template
  - [x] Welcome email
  - [x] Email verification
  - [x] Password reset
  - [x] Order confirmation
  - [x] Shipping notification
  - [x] Invoice email
  - [x] Account suspension notice
- [x] Email queue system (Celery)
  - [x] Async email sending with Celery and Redis
  - [x] Retry logic for failed emails (exponential backoff)
  - [x] Email delivery tracking (EmailLog model)
  - [x] Bulk email support
  - [x] Periodic maintenance tasks
- [x] Email preferences
  - [x] User opt-in/opt-out by category
  - [x] Email frequency settings (immediate, daily, weekly)
  - [x] Unsubscribe functionality with unique tokens
  - [x] Resubscribe support
  - [x] Email preferences UI

### 1.4 Admin Dashboard
- [x] Admin dashboard layout
  - [x] Key metrics widgets (users, sessions, signups, emails)
  - [x] Recent activity feed (logins and actions)
  - [x] Quick actions panel
  - [x] System health status overview
- [x] System metrics
  - [x] Total users count with breakdowns
  - [x] Active sessions with device breakdown
  - [x] Daily/weekly/monthly signups with averages
  - [x] User growth data for charts
  - [x] Email metrics (sent, failed, delivered, bounced)
- [x] Activity monitoring
  - [x] Recent logins with device/browser info
  - [x] Failed login attempts (requires failed_logins table)
  - [x] User actions log (role assignments)
- [x] System health
  - [x] Database connection status and size
  - [x] Redis connection status, version, and memory
  - [x] Queue status (Celery workers and tasks)
  - [x] Disk space monitoring with status levels
- [x] Dedicated monitoring page
  - [x] Detailed system health cards
  - [x] Comprehensive metrics breakdown
  - [x] Extended activity tables
  - [x] Auto-refresh functionality

### 1.5 Infrastructure Setup

**References:** [INFRASTRUCTURE.md](../04-operations/INFRASTRUCTURE.md) · [DEPLOYMENT.md](../04-operations/DEPLOYMENT.md) · [CONFIGURATION.md](../04-operations/CONFIGURATION.md) · [EMAIL_QUEUE_CELERY.md](../03-development/email/EMAIL_QUEUE_CELERY.md)

- [ ] Production environment setup
  - [ ] Server provisioning (AWS/GCP/Azure)
  - [ ] Load balancer configuration
  - [ ] SSL certificate setup (see [DEPLOYMENT](../04-operations/DEPLOYMENT.md))
  - [ ] Domain configuration
- [ ] Database optimization
  - [x] Index creation for critical queries (`scripts/add_performance_indexes.py` — see [INFRASTRUCTURE](../04-operations/INFRASTRUCTURE.md))
  - [x] Connection pooling (config: `DB_POOL_SIZE`, `DB_MAX_OVERFLOW` — see [CONFIGURATION](../04-operations/CONFIGURATION.md))
  - [ ] Read replica setup
  - [x] Backup automation (`scripts/backup_database.py`; cron/systemd examples in [INFRASTRUCTURE](../04-operations/INFRASTRUCTURE.md))
- [ ] Redis setup
  - [ ] Session storage configuration (optional; app supports Redis for cache when configured; see [INFRASTRUCTURE](../04-operations/INFRASTRUCTURE.md))
  - [x] Cache configuration (`REDIS_URL`, `CACHE_TYPE=redis` in [CONFIGURATION](../04-operations/CONFIGURATION.md))
  - [x] Queue broker setup (Celery broker: `CELERY_BROKER_URL` — see [EMAIL_QUEUE_CELERY](../03-development/email/EMAIL_QUEUE_CELERY.md))
- [ ] Celery setup
  - [x] Worker configuration (`celery -A celery_app.celery worker` — see [EMAIL_QUEUE_CELERY](../03-development/email/EMAIL_QUEUE_CELERY.md))
  - [x] Beat scheduler setup (schedule in `app/extensions/celery_config.py`; run `celery -A celery_app.celery beat` — see [INFRASTRUCTURE](../04-operations/INFRASTRUCTURE.md))
  - [ ] Monitoring (Flower; optional — see [INFRASTRUCTURE](../04-operations/INFRASTRUCTURE.md))
- [ ] Logging infrastructure
  - [x] Structured logging setup (app uses `app/data/logs/`; admin log viewer at `/admin/logs`)
  - [ ] Log aggregation (ELK/CloudWatch; see [INFRASTRUCTURE](../04-operations/INFRASTRUCTURE.md))
  - [x] Error tracking (Sentry; optional: set `SENTRY_DSN` in .env; see [INFRASTRUCTURE](../04-operations/INFRASTRUCTURE.md))
  - [ ] APM setup (DataDog/New Relic)

---

## Phase 2: Ecommerce Core (Weeks 5-10)

### 2.1 Product Management

#### Database Schema
- [ ] Create `sales` schema
- [ ] Create `products` table
  - [ ] id (UUID, primary key)
  - [ ] sku (unique)
  - [ ] name
  - [ ] slug (unique, for URLs)
  - [ ] description (text)
  - [ ] short_description
  - [ ] price (decimal)
  - [ ] compare_at_price (for showing discounts)
  - [ ] cost (for profit calculations)
  - [ ] stock_quantity
  - [ ] low_stock_threshold
  - [ ] weight, dimensions
  - [ ] is_active (boolean)
  - [ ] is_featured (boolean)
  - [ ] category_id (foreign key)
  - [ ] created_at, updated_at
  - [ ] created_by, updated_by
- [ ] Create `categories` table
  - [ ] id, name, slug, description
  - [ ] parent_id (for nested categories)
  - [ ] sort_order, is_active
  - [ ] image_url
- [ ] Create `product_images` table
  - [ ] id, product_id, url, alt_text
  - [ ] sort_order, is_primary
- [ ] Create `product_variants` table
  - [ ] id, product_id, sku
  - [ ] attributes (JSONB: {size: "L", color: "Red"})
  - [ ] price, stock_quantity
  - [ ] is_active
- [ ] Create `product_tags` table
  - [ ] id, name, slug
- [ ] Create `product_tag_associations` table
  - [ ] product_id, tag_id

#### Backend Implementation
- [ ] Product model (SQLAlchemy)
- [ ] Product service layer
  - [ ] Create product
  - [ ] Update product
  - [ ] Delete product (soft delete)
  - [ ] Get product by ID/slug
  - [ ] List products (with pagination)
  - [ ] Search products
  - [ ] Filter products (category, price range, tags)
- [ ] Product API endpoints
  - [ ] `GET /api/products` (list with filters)
  - [ ] `POST /api/products` (admin only)
  - [ ] `GET /api/products/:id`
  - [ ] `PATCH /api/products/:id` (admin only)
  - [ ] `DELETE /api/products/:id` (admin only)
  - [ ] `POST /api/products/:id/images` (upload)
  - [ ] `GET /api/products/:id/variants`

#### Frontend Implementation
- [ ] Product listing page (`/shop`)
  - [ ] Grid/list view toggle
  - [ ] Pagination
  - [ ] Filters sidebar (category, price, tags)
  - [ ] Sort options (price, name, newest)
  - [ ] Search bar
- [ ] Product detail page (`/shop/products/:slug`)
  - [ ] Image gallery with zoom
  - [ ] Variant selector (size, color)
  - [ ] Quantity selector
  - [ ] Add to cart button
  - [ ] Product description tabs
  - [ ] Related products
  - [ ] Reviews section
- [ ] Admin product management
  - [ ] Product list table
  - [ ] Create product form
  - [ ] Edit product form
  - [ ] Bulk actions (activate, deactivate, delete)
  - [ ] Image upload (drag & drop)
  - [ ] Variant management UI
  - [ ] Inventory management

#### Additional Features
- [ ] Product search (Elasticsearch or PostgreSQL full-text)
  - [ ] Index products
  - [ ] Autocomplete suggestions
  - [ ] Search result ranking
- [ ] Category management
  - [ ] Nested category tree
  - [ ] Category page with products
  - [ ] Breadcrumb navigation
- [ ] Product reviews & ratings
  - [ ] Submit review
  - [ ] Moderate reviews (admin)
  - [ ] Display average rating
  - [ ] Filter by rating

### 2.2 Shopping Cart

#### Database Schema
- [ ] Create `carts` table
  - [ ] id, user_id (nullable for guest carts)
  - [ ] session_id (for guest carts)
  - [ ] expires_at
  - [ ] created_at, updated_at
- [ ] Create `cart_items` table
  - [ ] id, cart_id, product_id, variant_id
  - [ ] quantity, price (snapshot at add time)
  - [ ] created_at, updated_at

#### Backend Implementation
- [ ] Cart model
- [ ] Cart service layer
  - [ ] Get or create cart (user or session-based)
  - [ ] Add item to cart
  - [ ] Update item quantity
  - [ ] Remove item from cart
  - [ ] Clear cart
  - [ ] Calculate cart totals
  - [ ] Merge guest cart with user cart on login
- [ ] Cart API endpoints
  - [ ] `GET /api/cart`
  - [ ] `POST /api/cart/add`
  - [ ] `PATCH /api/cart/items/:id`
  - [ ] `DELETE /api/cart/items/:id`
  - [ ] `DELETE /api/cart/clear`

#### Frontend Implementation
- [ ] Cart icon with item count (header)
- [ ] Cart dropdown (mini cart)
- [ ] Cart page (`/cart`)
  - [ ] Cart items table
  - [ ] Quantity adjustment
  - [ ] Remove item button
  - [ ] Subtotal calculation
  - [ ] Proceed to checkout button
  - [ ] Continue shopping link
  - [ ] Empty cart state
- [ ] Add to cart animations
- [ ] Cart persistence (localStorage for guests)

### 2.3 Checkout Flow

#### Database Schema
- [ ] Create `orders` table
  - [ ] id, order_number (human-readable)
  - [ ] user_id
  - [ ] status (pending, processing, shipped, delivered, cancelled)
  - [ ] subtotal, tax, shipping, discount, total
  - [ ] currency
  - [ ] shipping_address (JSONB)
  - [ ] billing_address (JSONB)
  - [ ] notes
  - [ ] created_at, updated_at
- [ ] Create `order_items` table
  - [ ] id, order_id, product_id, variant_id
  - [ ] quantity, price, subtotal
  - [ ] product_snapshot (JSONB: name, sku, etc.)
- [ ] Create `payments` table
  - [ ] id, order_id
  - [ ] amount, currency
  - [ ] method (card, paypal, etc.)
  - [ ] status (pending, completed, failed, refunded)
  - [ ] transaction_id (from payment processor)
  - [ ] metadata (JSONB)
  - [ ] created_at, updated_at
- [ ] Create `shipments` table
  - [ ] id, order_id
  - [ ] carrier, tracking_number
  - [ ] status (pending, shipped, in_transit, delivered)
  - [ ] shipped_at, delivered_at
  - [ ] address (JSONB)

#### Backend Implementation
- [ ] Order model
- [ ] Order service layer
  - [ ] Create order from cart
  - [ ] Calculate order totals (tax, shipping)
  - [ ] Update order status
  - [ ] Cancel order
  - [ ] Process refund
- [ ] Checkout API endpoints
  - [ ] `POST /api/checkout/init` (create order draft)
  - [ ] `POST /api/checkout/shipping` (calculate shipping)
  - [ ] `POST /api/checkout/payment` (process payment)
  - [ ] `POST /api/checkout/complete` (finalize order)
- [ ] Payment integration (Stripe)
  - [ ] Create payment intent
  - [ ] Confirm payment
  - [ ] Handle webhooks (payment success/failure)
  - [ ] Refund processing
- [ ] Inventory management
  - [ ] Reserve stock on order creation
  - [ ] Deduct stock on payment success
  - [ ] Restore stock on order cancellation

#### Frontend Implementation
- [ ] Checkout page (`/checkout`)
  - [ ] Multi-step wizard (shipping, payment, review)
  - [ ] Progress indicator
  - [ ] Order summary sidebar
- [ ] Step 1: Shipping information
  - [ ] Shipping address form
  - [ ] Saved addresses dropdown
  - [ ] Address validation
- [ ] Step 2: Shipping method
  - [ ] List available shipping options
  - [ ] Calculate shipping cost
  - [ ] Estimated delivery date
- [ ] Step 3: Payment
  - [ ] Stripe Elements integration
  - [ ] Card input form
  - [ ] Saved payment methods
  - [ ] PayPal button (optional)
- [ ] Step 4: Review & confirm
  - [ ] Order summary
  - [ ] Edit links for each section
  - [ ] Terms & conditions checkbox
  - [ ] Place order button
- [ ] Order confirmation page
  - [ ] Order number
  - [ ] Thank you message
  - [ ] Order details
  - [ ] Email confirmation notice
- [ ] Guest checkout support
  - [ ] Email input for order updates
  - [ ] Option to create account

### 2.4 Order Management

#### Backend Implementation
- [ ] Order management API
  - [ ] `GET /api/orders` (user's orders)
  - [ ] `GET /api/orders/:id`
  - [ ] `POST /api/orders/:id/cancel`
  - [ ] `POST /api/orders/:id/return` (initiate return)
  - [ ] Admin endpoints for order management
- [ ] Order status workflow
  - [ ] Pending → Processing → Shipped → Delivered
  - [ ] Cancellation logic
  - [ ] Return/refund logic
- [ ] Email notifications
  - [ ] Order confirmation
  - [ ] Order shipped
  - [ ] Order delivered
  - [ ] Order cancelled

#### Frontend Implementation
- [ ] Customer order history (`/orders`)
  - [ ] Order list with status
  - [ ] Filter by status, date range
  - [ ] Search by order number
- [ ] Order detail page (`/orders/:id`)
  - [ ] Order information
  - [ ] Items list
  - [ ] Shipping status
  - [ ] Tracking link
  - [ ] Cancel order button (if applicable)
  - [ ] Reorder button
  - [ ] Invoice download
- [ ] Admin order management
  - [ ] Order list table (all orders)
  - [ ] Advanced filters
  - [ ] Bulk status updates
  - [ ] Order detail view
  - [ ] Update order status
  - [ ] Add tracking information
  - [ ] Process refunds
  - [ ] Print packing slips

### 2.5 Shipping Integration

- [ ] Shipping service setup
  - [ ] EasyPost/Shippo account
  - [ ] API key configuration
  - [ ] Carrier accounts (USPS, FedEx, UPS)
- [ ] Shipping features
  - [ ] Real-time rate calculation
  - [ ] Label generation
  - [ ] Address validation
  - [ ] Tracking integration
  - [ ] Shipping zones configuration
  - [ ] Free shipping rules

### 2.6 Inventory Management

#### Database Schema
- [ ] Add inventory tracking fields to `products`
  - [ ] track_inventory (boolean)
  - [ ] allow_backorder (boolean)
  - [ ] low_stock_threshold
- [ ] Create `inventory_transactions` table
  - [ ] id, product_id, variant_id
  - [ ] type (sale, return, adjustment, restock)
  - [ ] quantity (positive or negative)
  - [ ] reference_type, reference_id (order_id, etc.)
  - [ ] notes
  - [ ] created_by, created_at

#### Backend Implementation
- [ ] Inventory service layer
  - [ ] Check stock availability
  - [ ] Reserve stock
  - [ ] Deduct stock
  - [ ] Restore stock
  - [ ] Adjust stock (manual)
  - [ ] Get stock history
- [ ] Low stock alerts
  - [ ] Email notification to admin
  - [ ] Dashboard widget
- [ ] Stock reports
  - [ ] Current stock levels
  - [ ] Low stock items
  - [ ] Out of stock items
  - [ ] Stock movement history

#### Frontend Implementation
- [ ] Inventory dashboard
  - [ ] Stock overview
  - [ ] Low stock alerts
  - [ ] Recent transactions
- [ ] Stock adjustment form
  - [ ] Adjust quantity
  - [ ] Add adjustment reason
  - [ ] Bulk adjustments
- [ ] Stock history view
  - [ ] Transaction log
  - [ ] Filter by product, date, type

---

## Phase 3: CRM Basics (Weeks 11-14)

### 3.1 Contact Management

#### Database Schema
- [ ] Create `crm` schema
- [ ] Create `contacts` table
  - [ ] id, email (unique), phone
  - [ ] first_name, last_name, full_name (generated)
  - [ ] company_id (foreign key)
  - [ ] title, department
  - [ ] address, city, state, zip, country
  - [ ] source (website, referral, import, etc.)
  - [ ] status (lead, prospect, customer, inactive)
  - [ ] owner_id (assigned user)
  - [ ] tags (array or JSONB)
  - [ ] custom_fields (JSONB)
  - [ ] created_at, updated_at
  - [ ] created_by, updated_by
- [ ] Create `companies` table
  - [ ] id, name, website
  - [ ] industry, size (employees)
  - [ ] address, city, state, zip, country
  - [ ] owner_id
  - [ ] status, tags
  - [ ] custom_fields (JSONB)
  - [ ] created_at, updated_at
- [ ] Create `contact_companies` table (many-to-many)
  - [ ] contact_id, company_id
  - [ ] is_primary (boolean)
  - [ ] title, department

#### Backend Implementation
- [ ] Contact model
- [ ] Company model
- [ ] Contact service layer
  - [ ] Create contact
  - [ ] Update contact
  - [ ] Delete contact (soft delete)
  - [ ] Search contacts
  - [ ] Merge duplicate contacts
  - [ ] Import contacts (CSV)
  - [ ] Export contacts (CSV)
- [ ] Contact API endpoints
  - [ ] `GET /api/crm/contacts`
  - [ ] `POST /api/crm/contacts`
  - [ ] `GET /api/crm/contacts/:id`
  - [ ] `PATCH /api/crm/contacts/:id`
  - [ ] `DELETE /api/crm/contacts/:id`
  - [ ] `POST /api/crm/contacts/import`
  - [ ] `GET /api/crm/contacts/export`

#### Frontend Implementation
- [ ] CRM dashboard
  - [ ] Contact count by status
  - [ ] Recent contacts
  - [ ] Upcoming tasks
  - [ ] Activity feed
- [ ] Contact list page (`/crm/contacts`)
  - [ ] Table view with sorting
  - [ ] Filter by status, owner, tags
  - [ ] Search by name, email, phone
  - [ ] Bulk actions (tag, assign, delete)
  - [ ] Import/export buttons
- [ ] Contact detail page (`/crm/contacts/:id`)
  - [ ] Contact information card
  - [ ] Company association
  - [ ] Activity timeline
  - [ ] Notes section
  - [ ] Tasks section
  - [ ] Deals section
  - [ ] Edit button
- [ ] Contact create/edit form
  - [ ] Basic information
  - [ ] Company selection
  - [ ] Tags input
  - [ ] Custom fields
  - [ ] Owner assignment
- [ ] Company management
  - [ ] Company list
  - [ ] Company detail page
  - [ ] Associated contacts
  - [ ] Create/edit company

### 3.2 Lead Tracking

#### Database Schema
- [ ] Create `leads` table
  - [ ] id, contact_id (foreign key)
  - [ ] source (website, referral, cold call, etc.)
  - [ ] status (new, contacted, qualified, unqualified)
  - [ ] score (0-100)
  - [ ] assigned_to (user_id)
  - [ ] notes
  - [ ] created_at, updated_at
  - [ ] qualified_at, converted_at

#### Backend Implementation
- [ ] Lead model
- [ ] Lead service layer
  - [ ] Create lead
  - [ ] Update lead status
  - [ ] Assign lead
  - [ ] Score lead (manual or automated)
  - [ ] Convert lead to customer
  - [ ] Lead distribution (round-robin, etc.)
- [ ] Lead API endpoints
  - [ ] `GET /api/crm/leads`
  - [ ] `POST /api/crm/leads`
  - [ ] `GET /api/crm/leads/:id`
  - [ ] `PATCH /api/crm/leads/:id`
  - [ ] `POST /api/crm/leads/:id/convert`

#### Frontend Implementation
- [ ] Lead list page (`/crm/leads`)
  - [ ] Kanban board view (by status)
  - [ ] Table view
  - [ ] Filter by source, status, assigned user
  - [ ] Lead scoring indicator
- [ ] Lead detail page
  - [ ] Lead information
  - [ ] Contact details
  - [ ] Activity timeline
  - [ ] Convert to customer button
  - [ ] Disqualify button
- [ ] Lead capture form (public)
  - [ ] Embed on website
  - [ ] Form builder
  - [ ] Thank you page
  - [ ] Auto-assign rules

### 3.3 Deal Pipeline

#### Database Schema
- [ ] Create `deals` table
  - [ ] id, name, contact_id, company_id
  - [ ] value (amount), currency
  - [ ] stage (lead, qualified, proposal, negotiation, won, lost)
  - [ ] probability (0-100%)
  - [ ] expected_close_date
  - [ ] actual_close_date
  - [ ] owner_id
  - [ ] lost_reason (if lost)
  - [ ] notes
  - [ ] created_at, updated_at
- [ ] Create `deal_stages` table (configurable pipeline)
  - [ ] id, name, sort_order
  - [ ] probability (default for stage)
  - [ ] is_active

#### Backend Implementation
- [ ] Deal model
- [ ] Deal service layer
  - [ ] Create deal
  - [ ] Update deal stage
  - [ ] Calculate deal probability
  - [ ] Mark deal as won/lost
  - [ ] Deal forecasting
- [ ] Deal API endpoints
  - [ ] `GET /api/crm/deals`
  - [ ] `POST /api/crm/deals`
  - [ ] `GET /api/crm/deals/:id`
  - [ ] `PATCH /api/crm/deals/:id`
  - [ ] `PATCH /api/crm/deals/:id/stage`

#### Frontend Implementation
- [ ] Deal pipeline page (`/crm/deals`)
  - [ ] Kanban board (by stage)
  - [ ] Drag & drop to change stage
  - [ ] Deal cards with key info
  - [ ] Filter by owner, date range
  - [ ] Pipeline value summary
- [ ] Deal detail page
  - [ ] Deal information
  - [ ] Associated contact/company
  - [ ] Activity timeline
  - [ ] Notes
  - [ ] Stage progression history
  - [ ] Mark as won/lost
- [ ] Deal create/edit form
  - [ ] Deal name, value
  - [ ] Contact/company selection
  - [ ] Stage, probability
  - [ ] Expected close date
  - [ ] Owner assignment
- [ ] Sales forecasting dashboard
  - [ ] Pipeline value by stage
  - [ ] Expected revenue (by close date)
  - [ ] Win rate statistics
  - [ ] Top deals

### 3.4 Activity Tracking

#### Database Schema
- [ ] Create `activities` table
  - [ ] id, type (call, email, meeting, note, task)
  - [ ] subject, description
  - [ ] contact_id, company_id, deal_id
  - [ ] scheduled_at, completed_at
  - [ ] duration (minutes)
  - [ ] outcome (for calls/meetings)
  - [ ] created_by, created_at
  - [ ] updated_at

#### Backend Implementation
- [ ] Activity model
- [ ] Activity service layer
  - [ ] Log activity
  - [ ] Update activity
  - [ ] Get activity timeline
  - [ ] Get upcoming activities
- [ ] Activity API endpoints
  - [ ] `GET /api/crm/activities`
  - [ ] `POST /api/crm/activities`
  - [ ] `GET /api/crm/activities/:id`
  - [ ] `PATCH /api/crm/activities/:id`
  - [ ] `DELETE /api/crm/activities/:id`

#### Frontend Implementation
- [ ] Activity timeline (on contact/company/deal pages)
  - [ ] Chronological list
  - [ ] Filter by type
  - [ ] Quick add activity
- [ ] Activity create/edit modal
  - [ ] Type selector
  - [ ] Subject, description
  - [ ] Date/time picker
  - [ ] Link to contact/company/deal
- [ ] Activity calendar view
  - [ ] Month/week/day views
  - [ ] Drag & drop to reschedule
  - [ ] Color coding by type
- [ ] Upcoming activities widget (dashboard)

### 3.5 Task Management

#### Database Schema
- [ ] Create `tasks` table
  - [ ] id, title, description
  - [ ] contact_id, company_id, deal_id
  - [ ] assigned_to, created_by
  - [ ] due_date, priority (low, medium, high)
  - [ ] status (pending, in_progress, completed, cancelled)
  - [ ] completed_at
  - [ ] created_at, updated_at

#### Backend Implementation
- [ ] Task model
- [ ] Task service layer
  - [ ] Create task
  - [ ] Update task
  - [ ] Complete task
  - [ ] Get user's tasks
  - [ ] Get overdue tasks
- [ ] Task API endpoints
  - [ ] `GET /api/crm/tasks`
  - [ ] `POST /api/crm/tasks`
  - [ ] `GET /api/crm/tasks/:id`
  - [ ] `PATCH /api/crm/tasks/:id`
  - [ ] `DELETE /api/crm/tasks/:id`

#### Frontend Implementation
- [ ] Task list page (`/crm/tasks`)
  - [ ] Filter by status, priority, due date
  - [ ] Sort by due date, priority
  - [ ] Mark as complete checkbox
  - [ ] Overdue indicator
- [ ] Task create/edit modal
  - [ ] Title, description
  - [ ] Due date picker
  - [ ] Priority selector
  - [ ] Assign to user
  - [ ] Link to contact/company/deal
- [ ] My tasks widget (dashboard)
  - [ ] Today's tasks
  - [ ] Overdue tasks
  - [ ] Quick complete

### 3.6 CRM Reports

- [ ] Contact reports
  - [ ] Contacts by source
  - [ ] Contacts by status
  - [ ] Contact growth over time
- [ ] Lead reports
  - [ ] Lead conversion rate
  - [ ] Lead response time
  - [ ] Leads by source
- [ ] Deal reports
  - [ ] Pipeline value by stage
  - [ ] Win/loss analysis
  - [ ] Average deal size
  - [ ] Sales cycle length
- [ ] Activity reports
  - [ ] Activities by type
  - [ ] Activities by user
  - [ ] Activity completion rate

---

## Phase 4: Billing & Subscriptions (Weeks 15-18)

### 4.1 Subscription Plans

#### Database Schema
- [ ] Create `billing` schema
- [ ] Create `plans` table
  - [ ] id, name, description
  - [ ] price, currency
  - [ ] interval (month, year)
  - [ ] interval_count (e.g., 3 for quarterly)
  - [ ] trial_days
  - [ ] features (JSONB array)
  - [ ] limits (JSONB: {api_calls: 1000, storage_gb: 10})
  - [ ] is_active, is_featured
  - [ ] stripe_price_id
  - [ ] sort_order
  - [ ] created_at, updated_at

#### Backend Implementation
- [ ] Plan model
- [ ] Plan service layer
  - [ ] Create plan
  - [ ] Update plan
  - [ ] Deactivate plan
  - [ ] Get active plans
  - [ ] Sync with Stripe
- [ ] Plan API endpoints
  - [ ] `GET /api/billing/plans`
  - [ ] `POST /api/billing/plans` (admin)
  - [ ] `GET /api/billing/plans/:id`
  - [ ] `PATCH /api/billing/plans/:id` (admin)

#### Frontend Implementation
- [ ] Pricing page (`/pricing`)
  - [ ] Plan cards (3-4 tiers)
  - [ ] Monthly/yearly toggle
  - [ ] Feature comparison table
  - [ ] Subscribe buttons
  - [ ] FAQ section
- [ ] Plan management (admin)
  - [ ] Plan list
  - [ ] Create/edit plan form
  - [ ] Feature management
  - [ ] Stripe sync button

### 4.2 Subscription Management

#### Database Schema
- [ ] Create `subscriptions` table
  - [ ] id, user_id, plan_id
  - [ ] status (trialing, active, past_due, cancelled, expired)
  - [ ] current_period_start, current_period_end
  - [ ] trial_start, trial_end
  - [ ] cancelled_at, cancel_at_period_end
  - [ ] stripe_subscription_id
  - [ ] created_at, updated_at

#### Backend Implementation
- [ ] Subscription model
- [ ] Subscription service layer
  - [ ] Create subscription (via Stripe)
  - [ ] Update subscription (change plan)
  - [ ] Cancel subscription
  - [ ] Reactivate subscription
  - [ ] Handle trial expiration
  - [ ] Handle payment failures
  - [ ] Proration calculation
- [ ] Stripe webhook handlers
  - [ ] `customer.subscription.created`
  - [ ] `customer.subscription.updated`
  - [ ] `customer.subscription.deleted`
  - [ ] `customer.subscription.trial_will_end`
  - [ ] `invoice.payment_succeeded`
  - [ ] `invoice.payment_failed`
- [ ] Subscription API endpoints
  - [ ] `GET /api/billing/subscription`
  - [ ] `POST /api/billing/subscribe`
  - [ ] `PATCH /api/billing/subscription`
  - [ ] `POST /api/billing/subscription/cancel`
  - [ ] `POST /api/billing/subscription/reactivate`

#### Frontend Implementation
- [ ] Subscription page (`/billing/subscription`)
  - [ ] Current plan details
  - [ ] Billing cycle info
  - [ ] Next billing date
  - [ ] Usage statistics (if metered)
  - [ ] Change plan button
  - [ ] Cancel subscription button
- [ ] Plan change modal
  - [ ] Select new plan
  - [ ] Proration preview
  - [ ] Confirm change
- [ ] Cancellation flow
  - [ ] Cancellation reason survey
  - [ ] Retention offer (discount, pause)
  - [ ] Confirm cancellation
  - [ ] Feedback collection

### 4.3 Payment Methods

#### Database Schema
- [ ] Create `payment_methods` table
  - [ ] id, user_id
  - [ ] type (card, paypal, bank_account)
  - [ ] is_default (boolean)
  - [ ] card_brand, card_last4
  - [ ] card_exp_month, card_exp_year
  - [ ] billing_address (JSONB)
  - [ ] stripe_payment_method_id
  - [ ] created_at, updated_at

#### Backend Implementation
- [ ] PaymentMethod model
- [ ] Payment method service layer
  - [ ] Add payment method (via Stripe)
  - [ ] Set default payment method
  - [ ] Remove payment method
  - [ ] Update billing address
- [ ] Payment method API endpoints
  - [ ] `GET /api/billing/payment-methods`
  - [ ] `POST /api/billing/payment-methods`
  - [ ] `PATCH /api/billing/payment-methods/:id`
  - [ ] `DELETE /api/billing/payment-methods/:id`
  - [ ] `POST /api/billing/payment-methods/:id/default`

#### Frontend Implementation
- [x] Payment methods page (`/billing/payment-methods`)
  - [x] List saved payment methods
  - [x] Add payment method form (Stripe Elements)
  - [x] Set default button
  - [x] Remove button
  - [ ] Make functional (currently static UI)
- [ ] Add payment method modal
  - [ ] Stripe Elements card input
  - [ ] Billing address form
  - [ ] Save as default checkbox
- [ ] Payment method card component
  - [ ] Card brand icon
  - [ ] Last 4 digits
  - [ ] Expiration date
  - [ ] Default badge
  - [ ] Edit/delete actions

### 4.4 Invoicing

#### Database Schema
- [ ] Create `invoices` table
  - [ ] id, invoice_number (human-readable)
  - [ ] user_id, subscription_id
  - [ ] status (draft, open, paid, void, uncollectible)
  - [ ] subtotal, tax, total, currency
  - [ ] due_date, paid_at
  - [ ] stripe_invoice_id
  - [ ] pdf_url
  - [ ] created_at, updated_at
- [ ] Create `invoice_items` table
  - [ ] id, invoice_id
  - [ ] description, quantity, unit_price, amount
  - [ ] period_start, period_end (for subscriptions)

#### Backend Implementation
- [ ] Invoice model
- [ ] Invoice service layer
  - [ ] Create invoice
  - [ ] Generate invoice PDF
  - [ ] Send invoice email
  - [ ] Mark invoice as paid
  - [ ] Void invoice
- [ ] Invoice API endpoints
  - [ ] `GET /api/billing/invoices`
  - [ ] `GET /api/billing/invoices/:id`
  - [ ] `GET /api/billing/invoices/:id/pdf`
  - [ ] `POST /api/billing/invoices/:id/pay`

#### Frontend Implementation
- [ ] Invoice list page (`/billing/invoices`)
  - [ ] Table with invoice number, date, amount, status
  - [ ] Filter by status, date range
  - [ ] Download PDF button
  - [ ] Pay now button (for unpaid)
- [ ] Invoice detail page (`/billing/invoices/:id`)
  - [ ] Invoice header (number, date, due date)
  - [ ] Company info
  - [ ] Customer info
  - [ ] Line items table
  - [ ] Subtotal, tax, total
  - [ ] Payment status
  - [ ] Download PDF button
  - [ ] Pay now button
- [ ] Invoice PDF template
  - [ ] Professional layout
  - [ ] Company logo
  - [ ] Invoice details
  - [ ] Line items
  - [ ] Payment instructions

### 4.5 Usage-Based Billing (Optional)

#### Database Schema
- [ ] Create `usage_records` table
  - [ ] id, subscription_id, user_id
  - [ ] metric (api_calls, storage_gb, etc.)
  - [ ] quantity
  - [ ] timestamp
  - [ ] created_at

#### Backend Implementation
- [ ] Usage tracking service
  - [ ] Record usage event
  - [ ] Aggregate usage by period
  - [ ] Calculate overage charges
  - [ ] Report usage to Stripe
- [ ] Usage API endpoints
  - [ ] `POST /api/billing/usage` (internal)
  - [ ] `GET /api/billing/usage` (user's usage)
  - [ ] `GET /api/billing/usage/current-period`

#### Frontend Implementation
- [ ] Usage dashboard
  - [ ] Current period usage
  - [ ] Usage by metric (charts)
  - [ ] Limit indicators
  - [ ] Overage warnings
  - [ ] Historical usage

### 4.6 Dunning Management

- [ ] Failed payment handling
  - [ ] Automatic retry schedule (3, 5, 7 days)
  - [ ] Update subscription status to past_due
  - [ ] Send dunning emails
  - [ ] Suspend account after X failures
- [ ] Dunning email templates
  - [ ] Payment failed notification
  - [ ] Retry reminder (3 days)
  - [ ] Final notice (7 days)
  - [ ] Account suspended notice
- [ ] Payment recovery page
  - [ ] Update payment method
  - [ ] Retry payment button
  - [ ] Contact support link

---

## Phase 5: ERP Core (Weeks 19-24)

### 5.1 Advanced Inventory Management

#### Database Schema
- [ ] Create `erp` schema
- [ ] Create `warehouses` table
  - [ ] id, name, code
  - [ ] address, city, state, zip, country
  - [ ] manager_id (user)
  - [ ] is_active
  - [ ] created_at, updated_at
- [ ] Create `inventory` table (multi-warehouse)
  - [ ] id, product_id, variant_id, warehouse_id
  - [ ] quantity, reserved_quantity
  - [ ] reorder_point, reorder_quantity
  - [ ] cost (weighted average)
  - [ ] updated_at
- [ ] Create `stock_movements` table
  - [ ] id, product_id, variant_id, warehouse_id
  - [ ] type (sale, return, adjustment, transfer, restock)
  - [ ] quantity (positive or negative)
  - [ ] reference_type, reference_id (order_id, po_id, etc.)
  - [ ] from_warehouse_id, to_warehouse_id (for transfers)
  - [ ] cost_per_unit
  - [ ] notes
  - [ ] created_by, created_at

#### Backend Implementation
- [ ] Warehouse model
- [ ] Inventory model
- [ ] Stock movement model
- [ ] Inventory service layer
  - [ ] Get stock by warehouse
  - [ ] Transfer stock between warehouses
  - [ ] Adjust stock (with reason)
  - [ ] Calculate available stock (quantity - reserved)
  - [ ] Calculate inventory value
  - [ ] Low stock alerts by warehouse
- [ ] Inventory API endpoints
  - [ ] `GET /api/erp/inventory`
  - [ ] `POST /api/erp/inventory/adjust`
  - [ ] `POST /api/erp/inventory/transfer`
  - [ ] `GET /api/erp/inventory/movements`
  - [ ] `GET /api/erp/inventory/low-stock`

#### Frontend Implementation
- [ ] Warehouse management
  - [ ] Warehouse list
  - [ ] Create/edit warehouse
  - [ ] Warehouse detail page
- [ ] Inventory dashboard
  - [ ] Total inventory value
  - [ ] Stock by warehouse
  - [ ] Low stock alerts
  - [ ] Out of stock items
  - [ ] Recent movements
- [ ] Inventory list page
  - [ ] Product/variant with stock levels
  - [ ] Filter by warehouse, status
  - [ ] Adjust stock button
  - [ ] Transfer stock button
- [ ] Stock adjustment modal
  - [ ] Select product/variant
  - [ ] Select warehouse
  - [ ] Adjustment quantity
  - [ ] Reason/notes
- [ ] Stock transfer modal
  - [ ] Select product/variant
  - [ ] From warehouse
  - [ ] To warehouse
  - [ ] Quantity
- [ ] Stock movement history
  - [ ] Filter by product, warehouse, type, date
  - [ ] Export to CSV

### 5.2 Purchase Orders

#### Database Schema
- [ ] Create `suppliers` table
  - [ ] id, name, code
  - [ ] contact_name, email, phone
  - [ ] address, city, state, zip, country
  - [ ] payment_terms (net 30, net 60, etc.)
  - [ ] currency
  - [ ] notes
  - [ ] is_active
  - [ ] created_at, updated_at
- [ ] Create `purchase_orders` table
  - [ ] id, po_number (human-readable)
  - [ ] supplier_id, warehouse_id
  - [ ] status (draft, submitted, approved, received, cancelled)
  - [ ] order_date, expected_date, received_date
  - [ ] subtotal, tax, shipping, total, currency
  - [ ] notes
  - [ ] created_by, approved_by
  - [ ] created_at, updated_at
- [ ] Create `po_items` table
  - [ ] id, po_id, product_id, variant_id
  - [ ] quantity, received_quantity
  - [ ] unit_cost, subtotal
  - [ ] notes

#### Backend Implementation
- [ ] Supplier model
- [ ] PurchaseOrder model
- [ ] PO service layer
  - [ ] Create PO
  - [ ] Submit PO for approval
  - [ ] Approve PO
  - [ ] Receive PO (full or partial)
  - [ ] Cancel PO
  - [ ] Generate PO PDF
- [ ] PO API endpoints
  - [ ] `GET /api/erp/purchase-orders`
  - [ ] `POST /api/erp/purchase-orders`
  - [ ] `GET /api/erp/purchase-orders/:id`
  - [ ] `PATCH /api/erp/purchase-orders/:id`
  - [ ] `POST /api/erp/purchase-orders/:id/submit`
  - [ ] `POST /api/erp/purchase-orders/:id/approve`
  - [ ] `POST /api/erp/purchase-orders/:id/receive`
  - [ ] `POST /api/erp/purchase-orders/:id/cancel`

#### Frontend Implementation
- [ ] Supplier management
  - [ ] Supplier list
  - [ ] Create/edit supplier
  - [ ] Supplier detail page
  - [ ] Purchase history
- [ ] PO list page (`/erp/purchase-orders`)
  - [ ] Filter by status, supplier, date
  - [ ] Create PO button
- [ ] PO detail page
  - [ ] PO header (number, date, supplier)
  - [ ] Line items table
  - [ ] Totals
  - [ ] Status indicator
  - [ ] Action buttons (submit, approve, receive, cancel)
  - [ ] Download PDF
- [ ] Create/edit PO form
  - [ ] Select supplier
  - [ ] Select warehouse
  - [ ] Add line items (product, quantity, cost)
  - [ ] Expected delivery date
  - [ ] Notes
- [ ] Receive PO modal
  - [ ] List items with expected quantity
  - [ ] Input received quantity
  - [ ] Partial receive support
  - [ ] Add to inventory button

### 5.3 Manufacturing & BOM (Optional)

#### Database Schema
- [ ] Create `bill_of_materials` table
  - [ ] id, product_id (finished good)
  - [ ] component_id (raw material/sub-assembly)
  - [ ] quantity
  - [ ] unit_cost
  - [ ] notes
- [ ] Create `work_orders` table
  - [ ] id, wo_number, product_id
  - [ ] quantity, completed_quantity
  - [ ] status (planned, in_progress, completed, cancelled)
  - [ ] start_date, end_date, completed_at
  - [ ] warehouse_id
  - [ ] notes
  - [ ] created_by, created_at

#### Backend Implementation
- [ ] BOM model
- [ ] WorkOrder model
- [ ] Manufacturing service layer
  - [ ] Create BOM
  - [ ] Calculate BOM cost
  - [ ] Create work order
  - [ ] Start production
  - [ ] Complete work order (consume components, add finished goods)
  - [ ] Cancel work order

#### Frontend Implementation
- [ ] BOM management
  - [ ] BOM list
  - [ ] Create/edit BOM
  - [ ] BOM detail (tree view)
  - [ ] Cost rollup
- [ ] Work order management
  - [ ] Work order list
  - [ ] Create work order
  - [ ] Work order detail
  - [ ] Start/complete buttons

### 5.4 Basic Accounting

#### Database Schema
- [ ] Create `gl_accounts` table
  - [ ] id, code, name
  - [ ] type (asset, liability, equity, revenue, expense)
  - [ ] balance (current balance)
  - [ ] is_active
  - [ ] created_at, updated_at
- [ ] Create `journal_entries` table
  - [ ] id, entry_number, date
  - [ ] description, reference
  - [ ] status (draft, posted)
  - [ ] created_by, posted_by
  - [ ] created_at, posted_at
- [ ] Create `journal_lines` table
  - [ ] id, entry_id, account_id
  - [ ] debit, credit
  - [ ] description

#### Backend Implementation
- [ ] GLAccount model
- [ ] JournalEntry model
- [ ] Accounting service layer
  - [ ] Create journal entry
  - [ ] Post journal entry (update account balances)
  - [ ] Void journal entry
  - [ ] Get account balance
  - [ ] Generate trial balance
  - [ ] Generate income statement
  - [ ] Generate balance sheet
- [ ] Automatic journal entries
  - [ ] On order payment (debit cash, credit revenue)
  - [ ] On inventory purchase (debit inventory, credit AP)
  - [ ] On expense (debit expense, credit cash)

#### Frontend Implementation
- [ ] Chart of accounts
  - [ ] Account list
  - [ ] Create/edit account
  - [ ] Account hierarchy
- [ ] Journal entry list
  - [ ] Filter by date, status
  - [ ] Create entry button
- [ ] Create/edit journal entry
  - [ ] Date, description
  - [ ] Add lines (account, debit, credit)
  - [ ] Balanced entry validation
  - [ ] Post button
- [ ] Financial reports
  - [ ] Trial balance
  - [ ] Income statement (P&L)
  - [ ] Balance sheet
  - [ ] Cash flow statement (future)
  - [ ] Date range selector
  - [ ] Export to PDF/Excel

---

## Phase 6: Advanced Features (Weeks 25-30)

### 6.1 Advanced Reporting & Analytics

#### Backend Implementation
- [ ] Reporting service layer
  - [ ] Sales reports (by period, product, category)
  - [ ] Customer reports (lifetime value, retention)
  - [ ] Inventory reports (turnover, valuation)
  - [ ] Financial reports (revenue, expenses, profit)
  - [ ] CRM reports (pipeline, conversion rates)
- [ ] Report API endpoints
  - [ ] `GET /api/reports/sales`
  - [ ] `GET /api/reports/customers`
  - [ ] `GET /api/reports/inventory`
  - [ ] `GET /api/reports/financial`
  - [ ] `GET /api/reports/crm`
- [ ] Report scheduling
  - [ ] Daily/weekly/monthly reports
  - [ ] Email delivery
  - [ ] Report templates

#### Frontend Implementation
- [ ] Reports dashboard (`/reports`)
  - [ ] Report categories
  - [ ] Saved reports
  - [ ] Recent reports
- [ ] Report builder
  - [ ] Select report type
  - [ ] Configure parameters (date range, filters)
  - [ ] Preview report
  - [ ] Export options (PDF, Excel, CSV)
  - [ ] Save report template
- [ ] Interactive charts
  - [ ] Line charts (trends over time)
  - [ ] Bar charts (comparisons)
  - [ ] Pie charts (distributions)
  - [ ] Drill-down capabilities
- [ ] Executive dashboard
  - [ ] Key metrics (revenue, orders, customers)
  - [ ] Charts (sales trend, top products)
  - [ ] Recent activity
  - [ ] Quick links

### 6.2 Email Campaigns (CRM)

#### Database Schema
- [ ] Create `campaigns` table
  - [ ] id, name, subject, from_name, from_email
  - [ ] content (HTML)
  - [ ] status (draft, scheduled, sending, sent, paused)
  - [ ] scheduled_at, sent_at
  - [ ] segment_id (target audience)
  - [ ] created_by, created_at
- [ ] Create `campaign_sends` table
  - [ ] id, campaign_id, contact_id
  - [ ] status (pending, sent, delivered, opened, clicked, bounced, complained)
  - [ ] sent_at, opened_at, clicked_at
  - [ ] error_message
- [ ] Create `segments` table
  - [ ] id, name, description
  - [ ] filters (JSONB: {status: "customer", tags: ["vip"]})
  - [ ] contact_count (cached)
  - [ ] created_at, updated_at

#### Backend Implementation
- [ ] Campaign model
- [ ] Segment model
- [ ] Campaign service layer
  - [ ] Create campaign
  - [ ] Build segment (apply filters)
  - [ ] Send test email
  - [ ] Schedule campaign
  - [ ] Send campaign (via Celery queue)
  - [ ] Track opens (tracking pixel)
  - [ ] Track clicks (redirect links)
  - [ ] Handle bounces/complaints (webhooks)
- [ ] Campaign API endpoints
  - [ ] `GET /api/crm/campaigns`
  - [ ] `POST /api/crm/campaigns`
  - [ ] `GET /api/crm/campaigns/:id`
  - [ ] `PATCH /api/crm/campaigns/:id`
  - [ ] `POST /api/crm/campaigns/:id/test`
  - [ ] `POST /api/crm/campaigns/:id/send`
  - [ ] `GET /api/crm/campaigns/:id/stats`

#### Frontend Implementation
- [ ] Campaign list page
  - [ ] Filter by status
  - [ ] Create campaign button
- [ ] Campaign builder
  - [ ] Campaign details (name, subject, from)
  - [ ] Email editor (WYSIWYG or HTML)
  - [ ] Template library
  - [ ] Merge tags ({{first_name}}, etc.)
  - [ ] Select segment
  - [ ] Preview email
  - [ ] Send test
  - [ ] Schedule or send now
- [ ] Campaign analytics
  - [ ] Sent, delivered, opened, clicked counts
  - [ ] Open rate, click rate
  - [ ] Link click heatmap
  - [ ] Bounces, complaints
  - [ ] Unsubscribes
- [ ] Segment builder
  - [ ] Filter by contact fields
  - [ ] Filter by tags
  - [ ] Filter by activity (opened email, clicked link)
  - [ ] Preview contact count

### 6.3 Workflow Automation

#### Database Schema
- [ ] Create `workflows` table
  - [ ] id, name, description
  - [ ] trigger_type (contact_created, deal_stage_changed, etc.)
  - [ ] trigger_config (JSONB)
  - [ ] actions (JSONB array)
  - [ ] is_active
  - [ ] created_by, created_at
- [ ] Create `workflow_executions` table
  - [ ] id, workflow_id
  - [ ] entity_type, entity_id (contact_id, deal_id, etc.)
  - [ ] status (running, completed, failed)
  - [ ] started_at, completed_at
  - [ ] error_message

#### Backend Implementation
- [ ] Workflow engine
  - [ ] Trigger detection
  - [ ] Action execution
  - [ ] Conditional logic (if/else)
  - [ ] Delays (wait X days)
- [ ] Available actions
  - [ ] Send email
  - [ ] Create task
  - [ ] Update field
  - [ ] Add tag
  - [ ] Assign to user
  - [ ] Create activity
  - [ ] Webhook (call external API)
- [ ] Workflow API endpoints
  - [ ] `GET /api/workflows`
  - [ ] `POST /api/workflows`
  - [ ] `GET /api/workflows/:id`
  - [ ] `PATCH /api/workflows/:id`
  - [ ] `POST /api/workflows/:id/activate`
  - [ ] `POST /api/workflows/:id/deactivate`

#### Frontend Implementation
- [ ] Workflow list page
  - [ ] Active/inactive workflows
  - [ ] Execution count
  - [ ] Create workflow button
- [ ] Workflow builder
  - [ ] Visual flow builder (drag & drop)
  - [ ] Trigger selection
  - [ ] Add action blocks
  - [ ] Conditional branches
  - [ ] Delay blocks
  - [ ] Test workflow
- [ ] Workflow analytics
  - [ ] Execution count
  - [ ] Success/failure rate
  - [ ] Average execution time

### 6.4 API & Webhooks

#### Backend Implementation
- [ ] API authentication
  - [ ] API key generation
  - [ ] JWT tokens for API
  - [ ] Rate limiting by API key
- [ ] Webhook system
  - [ ] Webhook registration (URL, events)
  - [ ] Webhook delivery (async via Celery)
  - [ ] Retry logic (exponential backoff)
  - [ ] Signature verification (HMAC)
  - [ ] Webhook logs
- [ ] Webhook events
  - [ ] `contact.created`, `contact.updated`, `contact.deleted`
  - [ ] `deal.created`, `deal.stage_changed`, `deal.won`, `deal.lost`
  - [ ] `order.created`, `order.paid`, `order.shipped`, `order.delivered`
  - [ ] `subscription.created`, `subscription.cancelled`, `subscription.renewed`
- [ ] API documentation
  - [ ] OpenAPI/Swagger spec
  - [ ] Interactive API docs (Swagger UI)
  - [ ] Code examples (Python, JavaScript, cURL)

#### Frontend Implementation
- [ ] API settings page
  - [ ] Generate API key
  - [ ] Revoke API key
  - [ ] API usage statistics
  - [ ] Rate limit info
- [ ] Webhook management
  - [ ] Webhook list
  - [ ] Add webhook (URL, events)
  - [ ] Test webhook
  - [ ] Webhook logs (deliveries, failures)
  - [ ] Retry failed webhooks

### 6.5 Third-Party Integrations

#### Ecommerce Platforms
- [ ] Shopify integration
  - [ ] Product sync (bidirectional)
  - [ ] Order sync
  - [ ] Inventory sync
  - [ ] Customer sync
- [ ] WooCommerce integration
  - [ ] Similar to Shopify

#### Accounting Software
- [ ] QuickBooks Online integration
  - [ ] Customer sync
  - [ ] Invoice sync
  - [ ] Payment sync
  - [ ] Expense sync
- [ ] Xero integration
  - [ ] Similar to QuickBooks

#### Email & Calendar
- [ ] Gmail integration
  - [ ] Email sync to activity timeline
  - [ ] Send emails from CRM
  - [ ] Email tracking
- [ ] Google Calendar integration
  - [ ] Sync meetings/calls
  - [ ] Create events from CRM
- [ ] Outlook integration
  - [ ] Similar to Gmail/Google Calendar

#### Communication
- [ ] Twilio integration
  - [ ] Click-to-call from CRM
  - [ ] SMS sending
  - [ ] Call logging
- [ ] Slack integration
  - [ ] Notifications (new lead, deal won)
  - [ ] Commands (/crm search John)

### 6.6 Mobile App

#### Features
- [ ] Authentication (login, biometric)
- [ ] Dashboard (key metrics)
- [ ] Contact list & detail
- [ ] Lead list & detail
- [ ] Deal pipeline (Kanban)
- [ ] Activity logging
- [ ] Task management
- [ ] Product catalog
- [ ] Order management
- [ ] Inventory lookup
- [ ] Barcode scanning (for inventory)
- [ ] Offline mode (sync when online)

#### Implementation
- [ ] React Native or Flutter
- [ ] API client
- [ ] Push notifications
- [ ] Camera access (for photos, barcodes)
- [ ] Local storage (SQLite)
- [ ] App store deployment (iOS, Android)

---

## Phase 7: Optimization & Scale (Weeks 31-36)

### 7.1 Performance Optimization

#### Database
- [ ] Query optimization
  - [ ] Identify slow queries (pg_stat_statements)
  - [ ] Add missing indexes
  - [ ] Optimize N+1 queries (eager loading)
  - [ ] Use database views for complex queries
- [ ] Database tuning
  - [ ] Adjust PostgreSQL config (shared_buffers, work_mem)
  - [ ] Connection pooling (PgBouncer)
  - [ ] Vacuum and analyze schedule
- [ ] Partitioning
  - [ ] Partition large tables (orders, activities) by date
  - [ ] Archive old data to separate tables
- [ ] Read replicas
  - [ ] Set up read replicas
  - [ ] Route read queries to replicas
  - [ ] Replication lag monitoring

#### Application
- [ ] Caching strategy
  - [ ] Cache frequently accessed data (products, categories)
  - [ ] Cache expensive queries (reports, aggregations)
  - [ ] Cache invalidation on updates
  - [ ] Cache warming (preload on deploy)
- [ ] Code optimization
  - [ ] Profile code (cProfile, py-spy)
  - [ ] Optimize hot paths
  - [ ] Reduce database calls
  - [ ] Use bulk operations
- [ ] Asset optimization
  - [ ] Minify CSS/JS
  - [ ] Image optimization (WebP, lazy loading)
  - [ ] CDN for static assets
  - [ ] Gzip compression

#### Frontend
- [ ] Page load optimization
  - [ ] Code splitting (lazy load routes)
  - [ ] Tree shaking (remove unused code)
  - [ ] Prefetch critical data
  - [ ] Service worker (PWA)
- [ ] Rendering optimization
  - [ ] Virtual scrolling (large lists)
  - [ ] Debounce/throttle user input
  - [ ] Memoization (React.memo, useMemo)

### 7.2 Load Testing & Tuning

- [ ] Load testing setup
  - [ ] Choose tool (Locust, JMeter, k6)
  - [ ] Define test scenarios (browse, search, checkout, API)
  - [ ] Set target metrics (req/sec, response time, error rate)
- [ ] Run load tests
  - [ ] Baseline test (current capacity)
  - [ ] Stress test (find breaking point)
  - [ ] Spike test (sudden traffic surge)
  - [ ] Endurance test (sustained load)
- [ ] Analyze results
  - [ ] Identify bottlenecks (database, CPU, memory, network)
  - [ ] Review error logs
  - [ ] Check resource utilization
- [ ] Tune and retest
  - [ ] Apply optimizations
  - [ ] Rerun tests
  - [ ] Compare results
  - [ ] Iterate until targets met

### 7.3 Multi-Tenancy (If Needed)

#### Database Strategy
- [ ] Choose approach
  - [ ] Shared database, shared schema (add tenant_id to all tables)
  - [ ] Shared database, separate schemas (one schema per tenant)
  - [ ] Separate databases (one database per tenant)
- [ ] Implement tenant isolation
  - [ ] Add tenant_id column to all tables
  - [ ] Row-Level Security (RLS) policies
  - [ ] Tenant context middleware
  - [ ] Tenant-aware queries (automatic filtering)
- [ ] Tenant management
  - [ ] Tenant provisioning (create tenant, admin user)
  - [ ] Tenant configuration (settings, branding)
  - [ ] Tenant billing (per-tenant subscriptions)

#### Application Changes
- [ ] Tenant identification
  - [ ] Subdomain routing (tenant1.app.com)
  - [ ] Custom domain support (tenant1.com)
  - [ ] Tenant context in session
- [ ] Data isolation
  - [ ] Ensure all queries filter by tenant_id
  - [ ] Prevent cross-tenant data access
  - [ ] Tenant-aware file storage (S3 prefixes)
- [ ] Tenant customization
  - [ ] Custom branding (logo, colors)
  - [ ] Custom email templates
  - [ ] Custom domain
  - [ ] Feature flags per tenant

### 7.4 Security Hardening

#### Application Security
- [ ] Security audit
  - [ ] Code review (manual + automated)
  - [ ] Dependency scanning (Snyk, Dependabot)
  - [ ] OWASP Top 10 checklist
- [ ] Input validation
  - [ ] Validate all user input
  - [ ] Sanitize HTML input
  - [ ] Use parameterized queries (prevent SQL injection)
  - [ ] Validate file uploads (type, size, content)
- [ ] Authentication hardening
  - [ ] Enforce strong passwords (min length, complexity)
  - [ ] Account lockout (after N failed attempts)
  - [ ] Password breach detection (HaveIBeenPwned API)
  - [ ] Session timeout
  - [ ] Secure session cookies (HttpOnly, Secure, SameSite)
- [ ] Authorization hardening
  - [ ] Enforce permission checks on all endpoints
  - [ ] Prevent insecure direct object references (IDOR)
  - [ ] Check resource ownership (user can only access own data)
- [ ] API security
  - [ ] Rate limiting (per user, per IP)
  - [ ] API key rotation
  - [ ] Request signing (HMAC)
  - [ ] CORS configuration

#### Infrastructure Security
- [ ] HTTPS enforcement
  - [ ] SSL/TLS certificates (Let's Encrypt)
  - [ ] HSTS headers
  - [ ] Redirect HTTP to HTTPS
- [ ] Security headers
  - [ ] Content-Security-Policy (CSP)
  - [ ] X-Frame-Options (prevent clickjacking)
  - [ ] X-Content-Type-Options (prevent MIME sniffing)
  - [ ] Referrer-Policy
- [ ] Database security
  - [ ] Encrypt data at rest
  - [ ] Encrypt connections (SSL)
  - [ ] Least privilege (app user has minimal permissions)
  - [ ] Regular backups (automated, tested)
- [ ] Secrets management
  - [ ] Use environment variables (never commit secrets)
  - [ ] Use secrets manager (AWS Secrets Manager, Vault)
  - [ ] Rotate secrets regularly
- [ ] Monitoring & alerting
  - [ ] Failed login attempts
  - [ ] Unusual API activity
  - [ ] Database connection failures
  - [ ] High error rates

#### Penetration Testing
- [ ] Hire security firm or use bug bounty
- [ ] Test for common vulnerabilities
  - [ ] SQL injection
  - [ ] XSS
  - [ ] CSRF
  - [ ] Authentication bypass
  - [ ] Authorization flaws
  - [ ] File upload vulnerabilities
- [ ] Fix identified issues
- [ ] Retest

### 7.5 Compliance

#### PCI DSS (Payment Card Industry)
- [ ] Never store full card numbers or CVV
- [ ] Use tokenization (Stripe, PayPal)
- [ ] Encrypt data in transit (HTTPS)
- [ ] Encrypt data at rest
- [ ] Restrict access to cardholder data
- [ ] Maintain security logs
- [ ] Regular security testing
- [ ] Self-Assessment Questionnaire (SAQ)

#### GDPR (General Data Protection Regulation)
- [ ] Data mapping (what data, where stored, who accesses)
- [ ] Privacy policy (clear, accessible)
- [ ] Consent management (opt-in for marketing)
- [ ] Right to access (user can export their data)
- [ ] Right to erasure (user can delete their account)
- [ ] Right to portability (export in machine-readable format)
- [ ] Data breach notification (within 72 hours)
- [ ] Data Protection Officer (if required)
- [ ] Data Processing Agreement (with vendors)

#### CCPA (California Consumer Privacy Act)
- [ ] Privacy notice (what data collected, why, with whom shared)
- [ ] Right to know (user can request data disclosure)
- [ ] Right to delete (user can request deletion)
- [ ] Right to opt-out (of data sale)
- [ ] Do Not Sell My Personal Information link

#### SOC 2 (Service Organization Control)
- [ ] Define security policies
- [ ] Implement controls (access, change management, monitoring)
- [ ] Conduct audit (by certified auditor)
- [ ] Obtain SOC 2 Type II report

### 7.6 Documentation

#### Technical Documentation
- [x] Architecture overview
- [ ] Database schema documentation (ERD diagrams)
- [ ] API documentation (OpenAPI/Swagger)
- [ ] Deployment guide
- [ ] Environment setup guide
- [ ] Configuration reference
- [ ] Troubleshooting guide

#### User Documentation
- [ ] User guide (for end users)
  - [ ] Getting started
  - [ ] Feature tutorials
  - [ ] FAQ
  - [ ] Video tutorials
- [ ] Admin guide (for administrators)
  - [ ] User management
  - [ ] Configuration
  - [ ] Reports
  - [ ] Integrations
- [ ] Developer guide (for API users)
  - [ ] Authentication
  - [ ] API reference
  - [ ] Webhooks
  - [ ] Code examples
  - [ ] SDKs (if available)

#### Process Documentation
- [ ] Development workflow
- [ ] Code review process
- [ ] Testing strategy
- [ ] Deployment process
- [ ] Incident response plan
- [ ] Backup & recovery procedures

---

## Ongoing Tasks

### Maintenance
- [ ] Dependency updates (weekly)
- [ ] Security patches (as needed)
- [ ] Database backups (daily, tested monthly)
- [ ] Log rotation (automated)
- [ ] Certificate renewal (automated)
- [ ] Performance monitoring (continuous)
- [ ] Error tracking (continuous)

### Support
- [ ] User support (email, chat, phone)
- [ ] Bug tracking (issue tracker)
- [ ] Feature requests (product roadmap)
- [ ] Status page (uptime monitoring)
- [ ] Release notes (for each deploy)

### Marketing
- [ ] Content marketing (blog, guides)
- [ ] SEO optimization
- [ ] Email marketing (newsletters)
- [ ] Social media
- [ ] Paid advertising (Google Ads, Facebook)
- [ ] Partnerships & integrations

### Product
- [ ] User feedback collection (surveys, interviews)
- [ ] Analytics (user behavior, feature usage)
- [ ] A/B testing (pricing, features, UI)
- [ ] Product roadmap (quarterly planning)
- [ ] Competitive analysis

---

## Success Metrics

### Technical Metrics
- [ ] Uptime: 99.9%+
- [ ] API response time: p95 < 500ms
- [ ] Page load time: < 3 seconds
- [ ] Error rate: < 0.1%
- [ ] Test coverage: > 80%

### Business Metrics
- [ ] Monthly Recurring Revenue (MRR)
- [ ] Customer Acquisition Cost (CAC)
- [ ] Customer Lifetime Value (CLV)
- [ ] Churn rate: < 5% monthly
- [ ] Net Promoter Score (NPS): > 50

### User Metrics
- [ ] Daily Active Users (DAU)
- [ ] Monthly Active Users (MAU)
- [ ] User retention (30-day, 90-day)
- [ ] Feature adoption rate
- [ ] Time to value (onboarding to first value)

---

## Notes

- This TODO list is a living document and should be updated as the project evolves.
- Priorities may shift based on user feedback, business needs, and technical constraints.
- Each task should be broken down into smaller subtasks as work begins.
- Use project management tools (Jira, Linear, GitHub Projects) to track progress.
- Regular retrospectives help identify what's working and what needs improvement.

---

**Last Updated**: 2026-01-28
