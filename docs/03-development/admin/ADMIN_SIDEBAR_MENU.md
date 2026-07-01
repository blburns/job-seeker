# Admin Sidebar Menu

Complete navigation structure for the Admin section in Phase 1.4.

## Menu Structure

The Admin-related menus appear in the **Management** section of the sidebar and are visible to users with `admin.access` (or equivalent admin/superadmin status). Individual items may require additional permissions (e.g. `users.view`, `permissions.view`).

```
Management
├── Overview (admin.access)
│   ├── Dashboard
│   └── System Monitoring
├── User Management (users.view)
│   ├── Users
│   ├── Roles
│   └── Permissions
├── Communications (admin.access)
│   ├── Email Logs
│   └── Templates
├── System (admin.access)
│   ├── Settings
│   ├── System Logs
│   └── Reports
└── (Account section)
    └── ...

Developer (admin.access)
└── Sitemap
```

## Menu Items

### 1. Admin Dashboard
**Route:** `/admin` or `/admin/dashboard`  
**Icon:** Dashboard icon  
**Description:** Enhanced admin dashboard with comprehensive metrics

**Features:**
- User metrics cards (total users, active sessions, signups, emails)
- System health status (DB, Redis, Celery, Disk)
- RBAC statistics
- Recent logins (last 10)
- Recent actions (last 10)
- Quick actions panel

---

### 2. System Monitoring
**Route:** `/admin/monitoring`  
**Icon:** Activity/monitoring icon  
**Description:** Dedicated system monitoring and health dashboard

**Features:**
- Detailed system health cards for each component
- Comprehensive metrics breakdown:
  - User metrics (total, active, verified, admins, 2FA)
  - Session metrics (active, total, expired, by device)
  - Email metrics (sent, failed, delivered, bounced, success rate)
  - Signup metrics (30-day total, daily average)
- Extended activity tables:
  - Recent logins (last 20) with IP, device, browser
  - Recent actions (last 20) with timestamps
- Auto-refresh every 30 seconds
- Manual refresh button

---

### 3. Permissions (Submenu)

#### 3.1 List Permissions
**Route:** `/admin/permissions`  
**Permission:** `permissions.view`  
**Description:** View all permissions grouped by module

**Features:**
- Permissions grouped by module
- Edit and delete actions
- Permission details (name, display name, description)

#### 3.2 Create Permission
**Route:** `/admin/permissions/create`  
**Permission:** `permissions.manage`  
**Description:** Create new permission

**Features:**
- Form to create new permission
- Module selection
- Display name and description
- Active status toggle

---

### 4. Roles (Submenu)

#### 4.1 List Roles
**Route:** `/admin/roles`  
**Permission:** `roles.view`  
**Description:** View all roles

**Features:**
- List of all roles
- View, edit, and delete actions
- Manage role permissions
- User assignment count

#### 4.2 Create Role
**Route:** `/admin/roles/create`  
**Permission:** `roles.create`  
**Description:** Create new role

**Features:**
- Form to create new role
- Display name and description
- Active status toggle
- Assign permissions

---

### 5. Communications (Email)

#### 5.1 Email Logs
**Route:** `/admin/email/logs`  
**Permission:** `admin.access`  
**Description:** View email sending history

**Features:**
- List of sent emails with status, recipient, template, timestamps
- Filters (days, status)

#### 5.2 Email Templates
**Route:** `/admin/email/templates`  
**Permission:** `admin.access`  
**Description:** List, create, edit, and preview email templates

**Features:**
- List templates under `app/templates/emails/` with usage count
- **Preview** (new tab) with sample context
- **Edit** per template (HTML content)
- **Create template** (name + HTML); name: lowercase letters, numbers, underscores only

---

### 6. System

#### 6.1 Settings
**Route:** `/admin/settings`  
**Permission:** `admin.access`  
**Description:** Read-only view of application configuration (from env)

**Features:**
- Sections: General, Security, Database, Cache, Email, OAuth, Logging
- Sensitive values masked or shown as "Set"/"Not set"

#### 6.2 System Logs
**Route:** `/admin/logs`  
**Permission:** `admin.access`  
**Description:** Log file viewer

**Features:**
- File selection: access, app, error, security, audit
- Line count and level filters; optional auto-refresh via API

#### 6.3 Reports
**Route:** `/admin/reports`  
**Permission:** `admin.access`  
**Description:** Aggregated reports

**Features:**
- Period filter (7/30/90 days)
- Report cards: users, sessions, emails, security, RBAC
- Detailed tables (e.g. failed logins, user growth)

---

### 7. Developer

#### 7.1 Sitemap
**Route:** `/admin/developer/sitemap`  
**Permission:** `admin.access`  
**Description:** All registered routes by blueprint

**Features:**
- Grouped by blueprint, sorted alphabetically
- Method and description per route; total blueprint and route counts
- External links use `rel="noopener noreferrer"`

---

## Access Control

### Visibility
The Admin menu is only visible to users who have:
- `is_admin = True`, OR
- `is_superadmin = True`

### Permission Checks
Individual menu items may have additional permission requirements:
- **Dashboard & Monitoring:** Requires `@admin_required()` (is_admin or is_superadmin)
- **Permissions:** Requires specific permissions (`permissions.view`, `permissions.manage`)
- **Roles:** Requires specific permissions (`roles.view`, `roles.create`, `roles.update`)

---

## Visual Design

### Icons
- **Admin (parent):** Dashboard/admin icon (tabler-dashboard)
- **Dashboard:** Smart home icon
- **System Monitoring:** Activity icon
- **Permissions:** Shield icon
- **Roles:** Users group icon

### Colors
- **Admin menu:** Danger/red theme (`bg-red-100`, `text-red-600`)
- **Active state:** Highlighted with theme color
- **Hover state:** Subtle background change

### Layout
- Collapsible accordion-style menu
- Nested submenus for Permissions and Roles
- Active page highlighting
- Smooth transitions

---

## Configuration

The menu is configured in `config/modules.py`. Management section includes separate top-level items:

- **Overview** — Dashboard, System Monitoring (`admin` module)
- **User Management** — Users, Roles, Permissions (`admin` / `users` blueprints)
- **Communications** — Email Logs, Templates (`admin` blueprint)
- **System** — Settings, System Logs, Reports (`admin` blueprint)

Developer section:

- **Developer Tools** — Sitemap (`admin` blueprint)

Each item has `display_name`, `route`, `permission`, `icon`, `color`, etc. See `config/modules.py` for the full structure.

---

## Usage Examples

### For Regular Users
- Admin menu is **not visible** in sidebar
- Direct URL access is blocked with 403 Forbidden

### For Admin Users
1. In the **Management** section, use:
   - **Overview** → Dashboard, System Monitoring
   - **User Management** → Users, Roles, Permissions
   - **Communications** → Email Logs, Templates
   - **System** → Settings, System Logs, Reports
2. In **Developer**, use **Sitemap** to view all routes
3. Click any item to navigate; current page is highlighted

### For Superadmin Users
- Full access to all admin features
- Same menu structure as admin users
- Additional capabilities in certain areas

---

## API Endpoints

All admin features are also accessible via API:

```bash
# System Health
GET /admin/api/monitoring/health

# All Metrics
GET /admin/api/monitoring/metrics

# RBAC Statistics
GET /admin/api/stats

# Permissions
GET /admin/api/permissions
POST /admin/api/permissions
PUT /admin/api/permissions/<id>
DELETE /admin/api/permissions/<id>

# Roles
GET /admin/api/roles
POST /admin/api/roles
PUT /admin/api/roles/<id>
DELETE /admin/api/roles/<id>
```

---

## Responsive Design

The sidebar menu is fully responsive:
- **Desktop:** Full sidebar with icons and text
- **Tablet:** Collapsible sidebar
- **Mobile:** Hidden by default, accessible via hamburger menu

---

## Future Enhancements

Potential additions:
- **Audit Logs** viewer (beyond security.log)
- **Backup & Restore** tools
- **Scheduled Reports** export

---

## Related Documentation

- [ADMIN_NAVIGATION.md](ADMIN_NAVIGATION.md) — Admin structure and routes
- [DEVELOPER_SITEMAP.md](DEVELOPER_SITEMAP.md) — Sitemap tool
- [EMAIL_SERVICE_SETUP.md](../email/EMAIL_SERVICE_SETUP.md) — Email and Admin Email Templates
- [RBAC_QUICK_START.md](../rbac/RBAC_QUICK_START.md) — Roles and permissions
- [Phase 1.4 Complete](../../06-planning/PHASE_1_4_COMPLETE.md)
