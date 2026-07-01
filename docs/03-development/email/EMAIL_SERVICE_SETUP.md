# Email Service Setup Guide

This guide explains how to configure and use the email service in the application.

---

## Overview

The application includes a flexible email service that supports multiple providers:
- **Console** (Development) - Prints emails to console
- **SendGrid** - Cloud email service
- **Mailgun** - Cloud email service
- **SMTP** - Standard SMTP server (Gmail, Outlook, etc.)

---

## Quick Start (Development)

The default configuration uses the **Console** provider, which requires no setup:

```bash
# .env file (default)
EMAIL_PROVIDER=console
EMAIL_FROM=noreply@example.com
EMAIL_FROM_NAME=My Application
```

Emails will be printed to the console/terminal where you run the app.

---

## Production Setup

### Option 1: SendGrid (Recommended)

**1. Create SendGrid Account**
- Sign up at [https://sendgrid.com](https://sendgrid.com)
- Free tier: 100 emails/day

**2. Get API Key**
- Go to Settings → API Keys
- Create API Key with "Mail Send" permission
- Copy the API key

**3. Configure Application**
```bash
# .env file
EMAIL_PROVIDER=sendgrid
SENDGRID_API_KEY=SG.xxxxxxxxxxxxxxxxxxxxx
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Your App Name
```

**4. Verify Sender**
- Go to Settings → Sender Authentication
- Verify your sender email or domain

**5. Install SendGrid Library**
```bash
pip install sendgrid
```

---

### Option 2: Mailgun

**1. Create Mailgun Account**
- Sign up at [https://www.mailgun.com](https://www.mailgun.com)
- Free tier: 5,000 emails/month for 3 months

**2. Get API Key and Domain**
- Go to Settings → API Keys
- Copy your API key
- Note your sandbox domain (or add your own domain)

**3. Configure Application**
```bash
# .env file
EMAIL_PROVIDER=mailgun
MAILGUN_API_KEY=your-api-key-here
MAILGUN_DOMAIN=sandboxXXXXXXXX.mailgun.org
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=Your App Name
```

**4. Install Requests Library** (if not already installed)
```bash
pip install requests
```

---

### Option 3: SMTP (Gmail Example)

**1. Enable 2-Step Verification**
- Go to Google Account settings
- Security → 2-Step Verification → Turn On

**2. Create App Password**
- Security → App passwords
- Select "Mail" and your device
- Copy the 16-character password

**3. Configure Application**
```bash
# .env file
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your.email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=True
EMAIL_FROM=your.email@gmail.com
EMAIL_FROM_NAME=Your App Name
```

**Note**: Gmail has a sending limit of 500 emails/day for free accounts.

---

### Option 4: SMTP (Outlook/Office 365)

```bash
# .env file
EMAIL_PROVIDER=smtp
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USERNAME=your.email@outlook.com
SMTP_PASSWORD=your-password
SMTP_USE_TLS=True
EMAIL_FROM=your.email@outlook.com
EMAIL_FROM_NAME=Your App Name
```

---

## Email Templates

Email templates are located in `app/templates/emails/`.

### Available Templates

1. **verify_email.html** - Email verification
2. **password_reset.html** - Password reset
3. **welcome.html** - Welcome email after verification
4. **base.html** - Base template for custom emails (used by invoice, order, etc.)
5. **invoice.html** - Invoice email (uses `invoice`, `user`, `config`)
6. **order_confirmation.html** - Order confirmation (uses `order`, `user`)
7. **shipping_notification.html** - Shipping notice (uses `order`, `shipment`, `user`)
8. **account_suspension.html** - Account suspension notice (uses `suspension`, `user`, `config`)

### Admin Email Templates (UI)

Admins can manage templates from **Admin → Communications → Templates** (`/admin/email/templates`):

- **List**: All `.html` files under `app/templates/emails/` with usage count from `EmailLog`
- **Preview**: Opens the template in a new tab with **sample context only** (no real user data). Sample data includes mock `user`, `invoice`, `order`, `shipment`, `suspension`, `config`, and URLs
- **Create template**: Form with template name (lowercase letters, numbers, underscores only) and HTML content. Writes a new file to `app/templates/emails/<name>.html`
- **Edit**: Edit existing template HTML and save. Preview and Edit buttons appear on the same line per row

Template name rules for create: only `a-z`, `0-9`, and `_`; file is saved as `<name>.html` in `templates/emails/`.

### Customizing Templates (Files)

Edit the HTML files directly, or use the Admin **Edit** form:

```html
<!-- app/templates/emails/verify_email.html -->
<div class="email-header">
    <h1>{{ app_name|default('Your App Name') }}</h1>
</div>
```

### Template Variables

All templates receive these variables (when sent by the app or in preview):
- `app_name` - Application name
- `base_url` - Application base URL
- `year` - Current year
- `user_name` - User's full name

Template-specific variables:
- **verify_email.html**: `verification_url`, `expiry_hours`
- **password_reset.html**: `reset_url`, `expiry_hours`
- **welcome.html**: `dashboard_url`
- **invoice.html**: `invoice`, `user`, `config`, `invoice_url`
- **order_confirmation.html**: `order`, `user`, `order_url`
- **shipping_notification.html**: `order`, `shipment`, `user`, `tracking_url`; `shipment.items` (name, quantity)
- **account_suspension.html**: `suspension`, `user`, `config`, `appeal_url`

---

## Sending Emails

### From Code

```python
from app.services.email_service import email_service

# Send simple email
email_service.send_email(
    to_email='user@example.com',
    subject='Test Email',
    html_content='<h1>Hello World</h1>',
    text_content='Hello World'
)

# Send template email
email_service.send_template_email(
    to_email='user@example.com',
    subject='Welcome!',
    template_name='welcome',
    template_data={
        'user_name': 'John Doe',
        'dashboard_url': 'https://app.com/dashboard',
        'app_name': 'My App',
        'base_url': 'https://app.com',
        'year': 2026
    }
)
```

---

## Testing

### Test Email Verification

1. Register a new user
2. Check console/email for verification link
3. Click link to verify
4. Check for welcome email

### Test Password Reset

1. Go to `/auth/forgot-password`
2. Enter email address
3. Check console/email for reset link
4. Click link and set new password

### Test Resend Verification

1. Register user but don't verify
2. Go to `/auth/resend-verification`
3. Enter email address
4. Check console/email for new verification link

---

## Troubleshooting

### Emails Not Sending

**Console Provider:**
- Check terminal output
- Ensure `EMAIL_PROVIDER=console` in .env

**SendGrid:**
- Verify API key is correct
- Check sender is verified
- Review SendGrid activity log
- Ensure `sendgrid` package is installed

**Mailgun:**
- Verify API key and domain are correct
- Check Mailgun logs
- Verify sender domain
- Ensure `requests` package is installed

**SMTP:**
- Verify host, port, username, password
- Check if TLS is required
- Ensure firewall allows SMTP connections
- Check email provider's sending limits

### Emails Going to Spam

1. **Verify sender domain** (SPF, DKIM, DMARC records)
2. **Use a real domain** (not @gmail.com for production)
3. **Warm up your IP** (start with low volume)
4. **Include unsubscribe link**
5. **Use proper email formatting**
6. **Avoid spam trigger words**

### Rate Limiting

**SendGrid:**
- Free: 100 emails/day
- Paid: Up to millions/month

**Mailgun:**
- Free trial: 5,000 emails/month for 3 months
- Paid: From $35/month for 50,000 emails

**Gmail:**
- Free: 500 emails/day
- Google Workspace: 2,000 emails/day

**Outlook:**
- Free: 300 emails/day
- Office 365: 10,000 emails/day

---

## Production Best Practices

### 1. Use a Dedicated Email Service
Don't use Gmail/Outlook for production. Use SendGrid or Mailgun.

### 2. Set Up Domain Authentication
Configure SPF, DKIM, and DMARC records for your domain.

### 3. Implement Email Queue
Use Celery + Redis for async email sending:
```python
@celery.task
def send_email_task(to_email, subject, template_name, template_data):
    email_service.send_template_email(
        to_email, subject, template_name, template_data
    )
```

### 4. Monitor Email Delivery
- Track bounce rates
- Monitor spam complaints
- Review delivery logs
- Set up alerts for failures

### 5. Handle Bounces
- Remove hard bounces from your list
- Retry soft bounces
- Respect unsubscribe requests

### 6. Rate Limiting
- Implement sending limits
- Use exponential backoff for retries
- Respect provider rate limits

---

## Environment Variables Reference

```bash
# Email Service Configuration
EMAIL_PROVIDER=console          # console, sendgrid, mailgun, smtp
EMAIL_FROM=noreply@example.com  # Sender email address
EMAIL_FROM_NAME=Application     # Sender name

# SendGrid
SENDGRID_API_KEY=SG.xxxxx      # SendGrid API key

# Mailgun
MAILGUN_API_KEY=key-xxxxx      # Mailgun API key
MAILGUN_DOMAIN=mg.example.com  # Mailgun domain

# SMTP
SMTP_HOST=smtp.gmail.com       # SMTP server host
SMTP_PORT=587                  # SMTP server port
SMTP_USERNAME=user@example.com # SMTP username
SMTP_PASSWORD=password         # SMTP password
SMTP_USE_TLS=True             # Use TLS encryption

# Application
APP_NAME=My Application        # Used in email templates
```

---

## Next Steps

1. ✅ Set up email provider (SendGrid recommended)
2. ✅ Configure environment variables
3. ✅ Test email sending
4. ✅ Customize email templates
5. ⏳ Set up domain authentication (SPF/DKIM/DMARC)
6. ⏳ Implement email queue (Celery)
7. ⏳ Add email delivery tracking
8. ⏳ Set up monitoring and alerts

---

## Additional Resources

- [SendGrid Documentation](https://docs.sendgrid.com/)
- [Mailgun Documentation](https://documentation.mailgun.com/)
- [Gmail SMTP Settings](https://support.google.com/mail/answer/7126229)
- [Email Best Practices](https://www.mailgun.com/blog/email-best-practices/)
- [SPF/DKIM/DMARC Guide](https://www.mailgun.com/blog/email-authentication-spf-dkim-dmarc/)
