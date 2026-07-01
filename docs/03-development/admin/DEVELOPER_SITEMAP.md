# Developer Sitemap

The **Developer Sitemap** is a dynamic tool built into the Admin module that lists every registered route in the application. It is designed to help developers identify all features, pages, modules, and apps.

## 📍 Access
- **URL**: `/admin/developer/sitemap`
- **Menu**: Admin Sidebar > Developer > Sitemap
- **Permission**: Requires `admin.access` (Admin or Superadmin role)

## 🔄 Dynamic Generation
The sitemap is generated dynamically by inspecting the Flask application's `url_map`. This means it is **always up-to-date** with the latest code changes. No manual updates are required.

## 📊 Features
- **Grouped by Module**: Routes are organized by their Blueprint (e.g., `auth`, `admin`, `users`, `main`). Blueprints are sorted alphabetically.
- **Totals**: Displays total number of blueprints and total number of routes.
- **Method Display**: Shows allowed HTTP methods (GET, POST, etc.) for each route.
- **Parameter Detection**: Identifies routes with dynamic parameters (e.g., `<user_id>`).
- **Documentation**: Displays the docstring from the view function as a description.
- **External Links**: External URLs use `rel="noopener noreferrer"` for security.

## 🛠️ Usage for Developers
1.  **Feature Discovery**: Quickly find the URL pattern for a specific feature.
2.  **Audit**: Verify that routes are correctly registered and have the expected methods.
3.  **Documentation**: Ensure view functions have meaningful docstrings, as they appear in the sitemap.

## 📝 Example Output

| URL Pattern | Methods | Endpoint | Description |
| :--- | :--- | :--- | :--- |
| **admin** | | | |
| `/admin/dashboard` | GET | `admin.dashboard` | Enhanced admin dashboard |
| `/admin/email/templates` | GET | `admin.email_templates` | List email templates |
| `/admin/email/templates/<name>/preview` | GET | `admin.email_template_preview` | Preview template with sample context |
| `/admin/email/templates/create` | GET, POST | `admin.email_template_create` | Create new template |
| `/admin/email/templates/<name>/edit` | GET, POST | `admin.email_template_edit` | Edit template |
| `/admin/settings` | GET | `admin.system_settings` | Read-only config view |
| `/admin/logs` | GET | `admin.system_logs` | Log file viewer |
| `/admin/reports` | GET | `admin.reports` | Aggregated reports |
| `/admin/developer/sitemap` | GET | `admin.developer_sitemap` | This sitemap |
| **auth** | | | |
| `/auth/login` | GET, POST | `auth.login` | User login page |
