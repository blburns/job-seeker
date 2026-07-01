# Template and UI Status

## Overview

This document tracks the template and UI implementation status. The application uses the **Vuexy** (Bootstrap 5) admin theme. All user-facing and error templates have been aligned with Vuexy.

**Full reference:** [TEMPLATES_AND_UI.md](../03-development/TEMPLATES_AND_UI.md) — sidebar menu, users template layout, error pages, base templates.

---

## Base Templates

| Template | Status | Use |
|----------|--------|-----|
| **base.html** | ✅ Vuexy | Main app (sidebar, navbar, content). |
| **base_auth.html** | ✅ Vuexy | Login, register, forgot/reset password. |
| **base_misc.html** | ✅ Vuexy | Error and misc pages (no sidebar). |
| **base_simple.html** | ✅ Vuexy | Optional simple card layout (extends base.html). |

---

## Error Pages (templates/errors/)

All extend **base_misc.html** and use Vuexy misc layout (centered content, illustrations).

| Template | Status | Notes |
|----------|--------|-------|
| 400.html | ✅ | Bad Request |
| 403.html | ✅ | Not authorized (uses not-authorized illustration) |
| 404.html | ✅ | Page Not Found (Go Back with history fallback) |
| 429.html | ✅ | Too Many Requests |
| 500.html | ✅ | Server Error |
| csrf.html | ✅ | CSRF / 419 |

---

## Users Module Templates

### Profile (current user) — `modules/users/profile/`

| Template | Status |
|----------|--------|
| profile.html | ✅ Vuexy |
| edit_profile.html | ✅ Vuexy |
| change_password.html | ✅ Vuexy |
| teams.html | ✅ Vuexy |
| projects.html | ✅ Vuexy |
| connections.html | ✅ Vuexy |

### View User (admin) — `modules/users/view/`

| Template | Status |
|----------|--------|
| account.html | ✅ Vuexy |
| security.html | ✅ Vuexy |
| billing.html | ✅ Vuexy |
| notifications.html | ✅ Vuexy |
| connections.html | ✅ Vuexy |
| includes/user_view_sidebar.html | ✅ |
| includes/user_view_nav_pills.html | ✅ |

### Account Settings (current user) — `modules/users/settings/`

| Template | Status |
|----------|--------|
| account.html | ✅ Vuexy (pages-account-settings-account style) |
| security.html | ✅ Vuexy |
| billing.html | ✅ Vuexy |
| notifications.html | ✅ Vuexy |
| connections.html | ✅ Vuexy |
| includes/settings_nav_pills.html | ✅ |

### Access (roles & permissions) — `modules/users/access/`

| Template | Status |
|----------|--------|
| roles_permissions_list.html | ✅ Vuexy (app-access-roles style) |
| permissions_list.html | ✅ Vuexy (app-access-permission style) |

### CRUD (root) — `modules/users/`

| Template | Status |
|----------|--------|
| list.html | ✅ Vuexy |
| create.html | ✅ Vuexy |
| edit.html | ✅ Vuexy |
| view_user.html | ✅ Legacy (redirects to view account) |

---

## Sidebar Menu

Configured in **config/modules.py**. Sections: Dashboards, Apps, Pages, Account.  
Account Settings has children: Account, Security, Billing & Plans, Notifications, Connections.  
See [TEMPLATES_AND_UI.md](../03-development/TEMPLATES_AND_UI.md).

---

## Vuexy Components Used

- **Layout:** `layout-wrapper`, `layout-menu`, `content-wrapper`, `container-xxl`, `container-p-y`
- **Cards:** `card`, `card-header`, `card-body`
- **Forms:** `form-control`, `form-label`, `form-check`, `btn`, `btn-primary`, `btn-label-secondary`
- **Nav:** `nav nav-pills`, `nav-link`, `menu-link`, `menu-sub`
- **Tables:** `table`, `table-responsive`
- **Icons:** `icon-base ti tabler-*` (Tabler Icons)
- **Misc pages:** `misc-wrapper`, `misc-bg-wrapper`, `page-misc.css`

---

## Notes

- All app templates extend `base.html` (or `base_auth.html` / `base_misc.html` as appropriate).
- Users templates are grouped under `profile/`, `view/`, `view/includes/`, `settings/`, `settings/includes/`, and `access/`.
- Error pages use `base_misc.html` and static illustrations under `assets/img/illustrations/`.
