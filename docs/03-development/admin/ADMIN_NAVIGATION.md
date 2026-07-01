# Admin Navigation & Structure

The administrative interface is organized by domain with full implementations for dashboard, monitoring, user management, communications, and system tools.

## 🧭 Sidebar Structure

The sidebar is divided into logical sections (see [ADMIN_SIDEBAR_MENU.md](ADMIN_SIDEBAR_MENU.md) for full menu tree):

### 1. Dashboards
- **Dashboard**: Main application overview

### 2. Management (Admin Only)

#### **Overview**
- **Dashboard**: Admin dashboard with key metrics (users, sessions, signups, emails, system health, recent logins/actions)
- **System Monitoring**: Real-time system health, detailed metrics, and activity tables with auto-refresh

#### **User Management**
- **Users**: List and manage users (redirects to users module)
- **Roles**: List roles with summary stats, view/edit/create/delete, manage role permissions, user assignment counts
- **Permissions**: List permissions grouped by module with stats, create/edit/delete, view roles that have each permission

#### **Communications**
- **Email Logs**: View email sending history, status, and filters
- **Templates**: List email templates under `app/templates/emails/`, **Preview** (sample context in new tab), **Create template**, **Edit** (per template). Preview and Edit buttons appear on the same line per row.

#### **System**
- **Settings**: Read-only view of application configuration (from env); sections: General, Security, Database, Cache, Email, OAuth, Logging; sensitive values masked
- **System Logs**: Log viewer with file selection (access, app, error, security, audit), line count and level filters, optional auto-refresh via API
- **Reports**: Aggregated reports by period (7/30/90 days): user activity, sessions, emails, security, RBAC; report cards and detailed tables

### 3. Developer (Admin Only)
- **Sitemap**: All registered routes grouped by blueprint, sorted alphabetically, with method and description; total blueprint and route counts; external links use `rel="noopener noreferrer"`

### 4. Apps (End User)
- **Profile**: User profile, teams, projects

### 5. Account
- **Settings**: Personal account settings (account, security, sessions, billing, notifications, connections)
- **Logout**

---

## 🛠️ Implementation Details

### **Configuration**
The menu structure is defined in `config/modules.py`:
- Menu hierarchy (Sections > Parents > Children)
- Icons (Tabler Icons: `ti ti-*`)
- Colors and permissions (e.g. `admin.access`, `users.view`)

### **Routes**
Admin routes live in `app/modules/admin/routes.py`. Key endpoints:

| Feature | Route | Notes |
|--------|--------|--------|
| Dashboard | `/admin`, `/admin/dashboard` | AJAX-loaded summary |
| Monitoring | `/admin/monitoring` | Health, metrics, activity |
| Permissions | `/admin/permissions`, `/admin/permissions/create`, `/admin/permissions/<id>/edit` | List, create, edit, delete |
| Roles | `/admin/roles`, `/admin/roles/create`, `/admin/roles/<id>`, `/admin/roles/<id>/edit`, `/admin/roles/<id>/permissions` | Full CRUD, permissions UI |
| Email Logs | `/admin/email/logs` | Filterable log list |
| Email Templates | `/admin/email/templates` | List with Preview + Edit per row |
| Template Preview | `/admin/email/templates/<name>/preview` | Rendered with sample context |
| Create Template | `/admin/email/templates/create` | GET/POST; name + HTML content |
| Edit Template | `/admin/email/templates/<name>/edit` | GET/POST; HTML content only |
| Settings | `/admin/settings` | Read-only config display |
| System Logs | `/admin/logs` | File, lines, level; optional auto-refresh |
| Reports | `/admin/reports` | Period filter, report cards |
| Developer Sitemap | `/admin/developer/sitemap` | All routes by blueprint |

### **Templates**
- **Sidebar**: `app/templates/components/sidebar.html` (driven by `config/modules.py`)
- **Dashboard**: `app/templates/modules/admin/dashboard.html`
- **Email**: `app/templates/modules/admin/email/` — `templates.html`, `template_form.html`, `logs.html`
- **Other**: `app/templates/modules/admin/` — `settings.html`, `logs.html`, `reports.html`, `monitoring.html`, `developer/sitemap.html`, roles/permissions templates

### **Services**
- **admin_service** (`app/services/admin_service.py`): Settings display config, log tail, reports data, email template list/read/write/preview context, system health checks

---

## Related Documentation

- [ADMIN_SIDEBAR_MENU.md](ADMIN_SIDEBAR_MENU.md) — Full menu structure and config
- [DEVELOPER_SITEMAP.md](DEVELOPER_SITEMAP.md) — Sitemap tool
- [EMAIL_SERVICE_SETUP.md](../email/EMAIL_SERVICE_SETUP.md) — Email config and **Admin Email Templates**
- [RBAC_QUICK_START.md](../rbac/RBAC_QUICK_START.md) — Roles and permissions
