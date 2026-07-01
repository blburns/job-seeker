# Phase 1.1 Complete Setup Guide

Complete setup instructions for all Phase 1.1 features: Email Service, Email Verification, Session Management, Two-Factor Authentication, and OAuth Integration.

---

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Virtual environment activated
- Flask application installed

---

## Quick Setup (All Features)

### 1. Install All Dependencies

```bash
# Install all Phase 1.1 requirements
pip install pyotp 'qrcode[pil]' Pillow Authlib requests

# Or use requirements files
pip install -r requirements-2fa.txt
pip install -r requirements-oauth.txt
```

### 2. Run All Database Migrations

```bash
# Session management
python scripts/add_sessions_table.py

# Two-factor authentication
python scripts/add_2fa_fields.py

# OAuth integration
python scripts/add_oauth_table.py
```

Expected output:
```
✓ Sessions table created successfully
✓ 2FA fields added successfully
✓ OAuth accounts table created successfully
```

### 3. Configure Environment Variables

Add to your `.env` file:

```env
# Email Service (choose one provider)
EMAIL_PROVIDER=console  # Options: console, sendgrid, mailgun, smtp
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Your App Name

# SendGrid (if using)
SENDGRID_API_KEY=your-sendgrid-api-key

# Mailgun (if using)
MAILGUN_API_KEY=your-mailgun-api-key
MAILGUN_DOMAIN=yourdomain.com

# SMTP (if using)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True

# Google OAuth (optional)
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth (optional)
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### 4. Restart Application

```bash
python run.py
```

### 5. Test All Features

**Email Service:**
```
1. Register new account
2. Check console/email for verification email
```

**Email Verification:**
```
1. Click verification link in email
2. Should activate account
```

**Session Management:**
```
1. Login to account
2. Go to Settings → Sessions
3. View active sessions
4. Test "Sign Out" on a session
```

**Two-Factor Authentication:**
```
1. Go to Settings → Security
2. Click "Enable Two-Factor Authentication"
3. Scan QR code with Google Authenticator
4. Enter verification code
5. Save backup codes
6. Logout and test 2FA login
```

**OAuth Integration:**
```
1. Go to Login page
2. Click "Sign in with Google" (or other provider)
3. Authorize application
4. Should create account and log in
```

---

## Detailed Setup by Feature

### Email Service Setup

**1. Choose Email Provider:**

**Option A: Console (Development)**
```env
EMAIL_PROVIDER=console
```
Emails printed to console. No additional setup needed.

**Option B: SendGrid (Production)**
```env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-api-key
```
1. Sign up at [SendGrid](https://sendgrid.com/)
2. Create API key
3. Add to `.env`

**Option C: Mailgun (Production)**
```env
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=your-api-key
MAILGUN_DOMAIN=yourdomain.com
```
1. Sign up at [Mailgun](https://www.mailgun.com/)
2. Add domain and verify
3. Get API key
4. Add to `.env`

**Option D: SMTP (Any Provider)**
```env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=True
```

**2. Test Email Service:**
```bash
python -c "
from app import create_app
from app.services.email_service import email_service

app = create_app()
with app.app_context():
    result = email_service.send_email(
        to_email='test@example.com',
        subject='Test Email',
        html_content='<p>This is a test email</p>'
    )
    print('Email sent!' if result else 'Email failed!')
"
```

**Documentation:** `docs/03-development/email/EMAIL_SERVICE_SETUP.md`

---

### Session Management Setup

**1. Run Migration:**
```bash
python scripts/add_sessions_table.py
```

**2. Verify Database:**
```sql
SELECT * FROM auth.user_sessions LIMIT 5;
```

**3. Test Session Tracking:**
```
1. Login to application
2. Go to /users/settings/sessions
3. Should see current session with device info
4. Open in different browser
5. Login again
6. Should see both sessions
```

**4. Test Session Revocation:**
```
1. View sessions page
2. Click "Sign Out" on a session
3. Session should be marked as revoked
4. Try to use that session - should be logged out
```

**Documentation:** `docs/03-development/SESSION_MANAGEMENT.md`

---

### Two-Factor Authentication Setup

**1. Install Dependencies:**
```bash
pip install pyotp 'qrcode[pil]' Pillow
```

**2. Run Migration:**
```bash
python scripts/add_2fa_fields.py
```

**3. Verify Database:**
```sql
SELECT username, totp_enabled, totp_enabled_at 
FROM auth.users 
WHERE totp_enabled = TRUE;
```

**4. Test 2FA Setup:**
```
1. Login to application
2. Go to Settings → Security
3. Click "Enable Two-Factor Authentication"
4. Scan QR code with Google Authenticator app
5. Enter 6-digit code
6. Save backup codes (print or download)
7. Click "I've Saved My Backup Codes"
```

**5. Test 2FA Login:**
```
1. Logout completely
2. Login with username/password
3. Should redirect to 2FA verification page
4. Enter code from authenticator app
5. Should complete login
```

**6. Test Backup Code:**
```
1. Logout
2. Login with username/password
3. Click "Use a backup code instead"
4. Enter one of your backup codes
5. Should complete login
6. Backup code should be removed from database
```

**Documentation:** `docs/03-development/auth/TWO_FACTOR_AUTH.md`

---

### OAuth Integration Setup

**1. Install Dependencies:**
```bash
pip install Authlib requests
```

**2. Run Migration:**
```bash
python scripts/add_oauth_table.py
```

**3. Configure OAuth Providers:**

**Google OAuth:**
```
1. Go to https://console.cloud.google.com/
2. Create project or select existing
3. Enable Google+ API
4. Go to Credentials → Create OAuth 2.0 Client ID
5. Application type: Web application
6. Authorized redirect URIs:
   - Development: http://localhost:5000/auth/oauth/google/callback
   - Production: https://yourdomain.com/auth/oauth/google/callback
7. Copy Client ID and Client Secret
8. Add to .env:
   GOOGLE_CLIENT_ID=...
   GOOGLE_CLIENT_SECRET=...
```

**Microsoft OAuth:**
```
1. Go to https://portal.azure.com/
2. Azure Active Directory → App registrations
3. New registration
4. Supported account types: Personal and organizational
5. Redirect URI: http://localhost:5000/auth/oauth/microsoft/callback
6. Certificates & secrets → New client secret
7. Copy Application (client) ID and secret value
8. Add to .env:
   MICROSOFT_CLIENT_ID=...
   MICROSOFT_CLIENT_SECRET=...
```

**GitHub OAuth:**
```
1. Go to https://github.com/settings/developers
2. New OAuth App
3. Homepage URL: http://localhost:5000
4. Authorization callback URL: http://localhost:5000/auth/oauth/github/callback
5. Copy Client ID and Client Secret
6. Add to .env:
   GITHUB_CLIENT_ID=...
   GITHUB_CLIENT_SECRET=...
```

**4. Restart Application:**
```bash
python run.py
```

**5. Test OAuth Login:**
```
1. Go to /auth/login
2. Click "Sign in with Google" (or other provider)
3. Authorize application
4. Should create account and log in
5. Check database for OAuth account record
```

**6. Test Account Linking:**
```
1. Create account with email: test@example.com
2. Logout
3. Click "Sign in with Google"
4. Use same email: test@example.com
5. Should link accounts and log in
6. Check database - OAuth account should be linked
```

**Documentation:** `docs/03-development/auth/OAUTH_INTEGRATION.md`

---

## Verification Checklist

### Email Service ✓
- [ ] Email provider configured in `.env`
- [ ] Test email sends successfully
- [ ] Registration sends verification email
- [ ] Password reset sends email
- [ ] Welcome email sent on registration

### Email Verification ✓
- [ ] Verification email received
- [ ] Verification link works
- [ ] Account activated after verification
- [ ] Resend verification works
- [ ] Expired tokens handled

### Session Management ✓
- [ ] Sessions table created
- [ ] Login creates session record
- [ ] Sessions page shows active sessions
- [ ] Device info displayed correctly
- [ ] Session revocation works
- [ ] Logout revokes session
- [ ] Remember me works

### Two-Factor Authentication ✓
- [ ] 2FA fields added to users table
- [ ] QR code displays correctly
- [ ] Authenticator app setup works
- [ ] Backup codes generated
- [ ] 2FA verification on login works
- [ ] Backup code login works
- [ ] Disable 2FA works
- [ ] Regenerate backup codes works

### OAuth Integration ✓
- [ ] OAuth table created
- [ ] At least one provider configured
- [ ] OAuth buttons visible on login page
- [ ] OAuth login works
- [ ] New account creation works
- [ ] Account linking by email works
- [ ] OAuth account stored in database
- [ ] Profile data synced

---

## Troubleshooting

### Email Not Sending

**Problem:** Emails not being sent

**Solutions:**
1. Check `EMAIL_PROVIDER` is set correctly
2. Verify API keys/credentials in `.env`
3. Check console output for errors
4. Test with `console` provider first
5. Verify email service is initialized: Check logs for "Email service initialized"

### Sessions Not Tracking

**Problem:** Sessions not appearing in database

**Solutions:**
1. Verify sessions table exists: `SELECT * FROM auth.user_sessions;`
2. Check for migration errors
3. Ensure `UserSession` model is imported in routes
4. Check Flask session is working: `session['session_token']`

### 2FA QR Code Not Showing

**Problem:** QR code image not displaying

**Solutions:**
1. Install dependencies: `pip install 'qrcode[pil]' Pillow`
2. Check browser console for errors
3. Verify QR code data starts with `data:image/png;base64,`
4. Test QR generation manually

### OAuth Redirect URI Mismatch

**Problem:** "redirect_uri_mismatch" error

**Solutions:**
1. Check provider console for registered URIs
2. Ensure exact match (no trailing slashes)
3. Development: `http://localhost:5000/auth/oauth/google/callback`
4. Production: `https://yourdomain.com/auth/oauth/google/callback`
5. Restart application after changing `.env`

### OAuth Buttons Not Showing

**Problem:** OAuth buttons not visible

**Solutions:**
1. Check OAuth credentials in `.env`
2. Restart application to reload config
3. Verify config: `print(app.config.get('GOOGLE_CLIENT_ID'))`
4. Check template conditional: `{% if config.get('GOOGLE_CLIENT_ID') %}`

---

## Database Schema Summary

### Tables Created

```sql
-- Session Management
auth.user_sessions (
    id, user_id, session_token, device_info, ip_address,
    user_agent, last_activity, expires_at, is_active,
    remember_me, created_at, revoked_at
)

-- Two-Factor Authentication (fields added to auth.users)
auth.users (
    ...,
    totp_secret, totp_enabled, totp_enabled_at, backup_codes
)

-- OAuth Integration
auth.oauth_accounts (
    id, user_id, provider, provider_user_id,
    access_token, refresh_token, token_expires_at,
    provider_email, provider_name, provider_picture,
    provider_data, created_at, updated_at, last_used_at
)
```

---

## Configuration Summary

### Required Environment Variables

```env
# Application
APP_NAME=Your Application Name
SECRET_KEY=your-secret-key

# Database
DB_TYPE=postgresql
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=your-db-name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Email Service (choose one)
EMAIL_PROVIDER=console|sendgrid|mailgun|smtp
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Your App Name

# Email Provider Credentials (if not using console)
SENDGRID_API_KEY=...
MAILGUN_API_KEY=...
MAILGUN_DOMAIN=...
SMTP_HOST=...
SMTP_PORT=...
SMTP_USERNAME=...
SMTP_PASSWORD=...

# OAuth (optional)
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
MICROSOFT_CLIENT_ID=...
MICROSOFT_CLIENT_SECRET=...
GITHUB_CLIENT_ID=...
GITHUB_CLIENT_SECRET=...
```

---

## Next Steps

After completing Phase 1.1 setup:

1. **Test All Features** - Go through verification checklist
2. **Review Documentation** - Read feature-specific docs
3. **Configure Production** - Set up production email and OAuth
4. **Security Review** - Review security settings
5. **Move to Phase 1.2** - Implement RBAC and permissions

---

## Support

For issues or questions:
1. Check troubleshooting section
2. Review feature-specific documentation
3. Check application logs
4. Verify database schema
5. Test with minimal configuration first

---

## Documentation Links

- [Email Service Setup](./EMAIL_SERVICE_SETUP.md)
- [Session Management](./SESSION_MANAGEMENT.md)
- [Two-Factor Authentication](./TWO_FACTOR_AUTH.md)
- [OAuth Integration](./OAUTH_INTEGRATION.md)
- [Phase 1.1 Complete Summary](../06-planning/PHASE_1_1_OAUTH_COMPLETE.md)
