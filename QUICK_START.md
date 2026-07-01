# Quick Start Guide

Get your Flask application up and running in minutes!

---

## Prerequisites

- Python 3.8+
- PostgreSQL database
- Virtual environment

---

## Installation

### 1. Clone and Setup Virtual Environment

```bash
cd /Users/blburns/Workspace/Boilerplates/boilerplate-python3-flask
source venv/bin/activate
```

### 2. Install Core Dependencies

The application will run with just the core dependencies already installed. Optional features require additional packages.

### 3. Configure Environment

Create or update `.env` file:

```env
# Application
APP_NAME=My Application
SECRET_KEY=your-secret-key-change-in-production

# Database
DB_TYPE=postgresql
POSTGRES_USER=your-db-user
POSTGRES_PASSWORD=your-db-password
POSTGRES_DB=your-db-name
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Email (Console mode for development)
EMAIL_PROVIDER=console
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=My Application
```

### 4. Run the Application

```bash
python run.py
```

Visit: `http://localhost:5000`

---

## Optional Features

### Email Service (Production)

**For SendGrid:**
```bash
# Add to .env
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=your-api-key
```

**For Mailgun:**
```bash
# Add to .env
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=your-api-key
MAILGUN_DOMAIN=yourdomain.com
```

**For SMTP:**
```bash
# Add to .env
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
```

### Two-Factor Authentication (2FA)

**Install:**
```bash
pip install pyotp 'qrcode[pil]' Pillow
```

**Setup:**
```bash
python scripts/add_2fa_fields.py
```

**Usage:**
1. Go to Settings → Security
2. Click "Enable Two-Factor Authentication"
3. Scan QR code with Google Authenticator
4. Save backup codes

### OAuth Integration (Google, Microsoft, GitHub)

**Install:**
```bash
pip install Authlib requests
```

**Setup:**
```bash
python scripts/add_oauth_table.py
```

**Configure:**
```bash
# Add to .env
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

**Usage:**
1. Restart application
2. OAuth buttons appear on login/register pages
3. Click to sign in with provider

---

## Database Migrations

### Session Management
```bash
python scripts/add_sessions_table.py
```

### Two-Factor Authentication
```bash
python scripts/add_2fa_fields.py
```

### OAuth Integration
```bash
python scripts/add_oauth_table.py
```

---

## Current Status

✅ **Working Out of the Box:**
- User registration and login
- Email/password authentication
- Password reset
- User profile management
- Session tracking
- Email verification (console mode)

⏳ **Requires Additional Setup:**
- Production email (SendGrid/Mailgun/SMTP)
- Two-factor authentication (install pyotp)
- OAuth integration (install Authlib)

---

## Troubleshooting

### Application Won't Start

**Issue:** Import errors  
**Solution:** Make sure virtual environment is activated and dependencies are installed

### Database Connection Error

**Issue:** Can't connect to PostgreSQL  
**Solution:** Check database credentials in `.env` and ensure PostgreSQL is running

### OAuth Buttons Not Showing

**Issue:** OAuth buttons not visible  
**Solution:** Install Authlib and configure OAuth credentials in `.env`

### 2FA QR Code Not Displaying

**Issue:** QR code not showing  
**Solution:** Install required packages: `pip install pyotp 'qrcode[pil]' Pillow`

---

## Next Steps

1. **Configure Production Email** - Set up SendGrid, Mailgun, or SMTP
2. **Enable 2FA** - Install packages and run migration
3. **Setup OAuth** - Configure providers and install Authlib
4. **Customize Templates** - Update branding and styling
5. **Add Business Logic** - Implement your application features

---

## Documentation

- **Complete Setup:** `docs/03-development/PHASE_1_1_SETUP.md`
- **Email Service:** `docs/03-development/EMAIL_SERVICE_SETUP.md`
- **Session Management:** `docs/03-development/SESSION_MANAGEMENT.md`
- **Two-Factor Auth:** `docs/03-development/TWO_FACTOR_AUTH.md`
- **OAuth Integration:** `docs/03-development/OAUTH_INTEGRATION.md`

---

## Support

For detailed documentation and troubleshooting, see the `docs/` directory.

**Key Files:**
- `docs/06-planning/IMPLEMENTATION_TODO.md` - Implementation roadmap
- `docs/03-development/PHASE_1_1_SETUP.md` - Complete setup guide
- `docs/06-planning/PHASE_1_1_OAUTH_COMPLETE.md` - Feature summary

---

## Features Implemented

### Phase 1.1 - Authentication & User Management ✅

- ✅ Email Service Integration (multi-provider)
- ✅ Email Verification System
- ✅ Session Management (device tracking, remote revocation)
- ✅ Two-Factor Authentication (TOTP with Google Authenticator)
- ✅ OAuth Integration (Google, Microsoft, GitHub)

**Status:** Production-ready with comprehensive security features!

---

## Quick Commands

```bash
# Start application
python run.py

# Run all migrations
python scripts/add_sessions_table.py
python scripts/add_2fa_fields.py
python scripts/add_oauth_table.py

# Install optional features
pip install pyotp 'qrcode[pil]' Pillow  # 2FA
pip install Authlib requests              # OAuth

# Test application
python -c "from app import create_app; app = create_app(); print('✓ OK')"
```

---

**Ready to go!** 🚀
