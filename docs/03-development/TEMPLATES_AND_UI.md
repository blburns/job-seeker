# Templates and UI Reference

## Overview

The application uses the **Vuexy** (Bootstrap 5) admin theme. Templates extend base layouts, and the sidebar menu is driven by `config/modules.py`.

---

## Base Templates

| Template | Use Case |
|----------|----------|
| **base.html** | Main app layout with sidebar and navbar (dashboard, modules). |
| **base_auth.html** | Auth pages (login, register, forgot/reset password) — no sidebar. |
| **base_misc.html** | Standalone misc pages (error pages: 403, 404, 400, 429, 500, CSRF) — no sidebar, centered content. |
| **base_simple.html** | Extends `base.html`; simple card layout for minimal pages (optional). |

**Theme assets:** `app/static/assets/` (Vuexy vendor CSS/JS, `page-misc.css` for error pages).

---

## Sidebar Menu Structure

The sidebar is built from **MENU_SECTIONS** and **MODULES** in `config/modules.py`. Only sections `dashboards`, `apps`, `pages`, and `account` are shown.

### Menu Sections (order)

1. **Dashboards** — Dashboard (main index).
2. **Apps** — Email, Chat, Calendar (placeholders), **Users**, **Roles & Permissions**.
3. **Pages** — **User Profile**, **Account Settings**.
4. **Account** — Settings, Logout.

### Users (Apps)

- **List** → User list.
- **View** (expandable):
  - Account, Security, Billing & Plans, Notifications, Connections (admin view of a user).

### User Profile (Pages)

- Profile, Teams, Projects, Connections (current user’s profile).

### Account Settings (Pages)

- **Account** → `/settings/account`
- **Security** → `/settings/security`
- **Billing & Plans** → `/settings/billing`
- **Notifications** → `/settings/notifications`
- **Connections** → `/settings/connections`

### Account (footer)

- **Settings** → redirects to `/settings/account`
- **Logout** → auth logout

**Adding/editing menu items:** Edit `config/modules.py` (`MENU_SECTIONS`, `MODULES`). Use `section`, `sort_order`, `children`, and `route` so the sidebar and `safe_url_for` resolve correctly.

---

## Users Module Template Organization

Templates under `app/templates/modules/users/` are grouped by purpose:

```
app/templates/modules/users/
├── list.html              # User list (CRUD)
├── create.html
├── edit.html
├── view_user.html         # Legacy single view (redirects to account tab)
│
├── profile/               # Current user profile (Pages → User Profile)
│   ├── profile.html
│   ├── edit_profile.html
│   ├── change_password.html
│   ├── teams.html
│   ├── projects.html
│   └── connections.html
│
├── view/                  # Admin viewing a specific user (Apps → Users → View)
│   ├── account.html
│   ├── security.html
│   ├── billing.html
│   ├── notifications.html
│   ├── connections.html
│   └── includes/
│       ├── user_view_sidebar.html
│       └── user_view_nav_pills.html
│
├── settings/              # Current user account settings (Pages → Account Settings)
│   ├── account.html
│   ├── security.html
│   ├── billing.html
│   ├── notifications.html
│   ├── connections.html
│   └── includes/
│       └── settings_nav_pills.html
│
├── access/                # Roles & Permissions (Apps → Roles & Permissions)
│   ├── roles_permissions_list.html
│   └── permissions_list.html
│
└── BACKUP/                # Legacy/backup templates (not in use)
```

### Route → Template Mapping (users blueprint)

| Route | Template | Purpose |
|-------|----------|--------|
| `profile` | `profile/profile.html` | Current user profile |
| `edit_profile` | `profile/edit_profile.html` | Edit own profile |
| `change_password` | `profile/change_password.html` | Change own password |
| `teams`, `projects`, `connections` | `profile/teams.html`, etc. | Profile sub-pages |
| `view_user`, `view_user_account`, … | `view/account.html`, etc. | Admin view of a user |
| `settings` | Redirect → `settings_account` | |
| `settings_account`, `settings_security`, … | `settings/account.html`, etc. | Current user account settings |
| `list_roles` | `access/roles_permissions_list.html` | Roles list |
| `list_permissions` | `access/permissions_list.html` | Permissions list |
| `list_users` | `list.html` | User list |
| `create_user` | `create.html` | Create user |
| `edit_user` | `edit.html` | Edit user |

---

## Error Pages

Error pages use **base_misc.html** (Vuexy misc layout: no sidebar, centered content, `.misc-wrapper`, background shape).

| File | HTTP / Context | Title / Content |
|------|----------------|-----------------|
| **errors/400.html** | 400 | Bad Request |
| **errors/403.html** | 403 | You are not authorized! (uses `page-misc-you-are-not-authorized.png`) |
| **errors/404.html** | 404 | Page Not Found (uses `page-misc-error.png`) |
| **errors/429.html** | 429 | Too Many Requests |
| **errors/500.html** | 500 | Server Error |
| **errors/csrf.html** | 419 | CSRF Token Error |

**Blocks in base_misc.html:** `title`, `misc_code`, `misc_heading`, `misc_description`, `misc_actions`, `misc_image` (optional).

---

## Template Blocks (base.html)

Common blocks when extending `base.html`:

- `title` — Page title.
- `extra_css` — Extra stylesheets.
- `extra_head` — Extra head content.
- `page_header` — Optional page header.
- `content` — Main content.
- `footer` — Optional footer.
- `extra_js` — Extra scripts.

---

## Shared Includes

- **users/view/includes/** — Sidebar and nav pills for “view user” (admin).
- **users/settings/includes/** — Nav pills for “account settings” (current user).

Use `url_for('users.view_user_account', user_id=user.id)` for view tabs and `url_for('users.settings_account')` (no `user_id`) for settings tabs.

---

## See Also

- [ARCHITECTURE.md](../02-architecture/ARCHITECTURE.md) — System design and theme.
- [MODULE_DEVELOPMENT.md](MODULE_DEVELOPMENT.md) — Adding modules and routes.
- [QUICK_REFERENCE.md](../QUICK_REFERENCE.md) — URL patterns and template blocks.
