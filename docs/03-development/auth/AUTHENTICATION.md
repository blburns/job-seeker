# Authentication Guide

## Overview

This application implements a comprehensive authentication system with multiple security features including password hashing, account lockout, email verification, and password reset.

## Authentication Flow

### Login Process

1. User submits credentials (username/email + password)
2. System validates input and sanitizes
3. User lookup (by username or email)
4. Password verification (bcrypt hash comparison)
5. Security checks:
   - Account lockout status
   - Account active status
   - Failed login attempts
6. Session creation (Flask-Login)
7. Redirect to dashboard

### Registration Process

1. User submits registration form
2. Validation:
   - Username uniqueness
   - Email format and uniqueness
   - Password strength
3. Password hashing (bcrypt)
4. User account creation
5. Email verification token generation (optional)
6. Welcome email sent (optional)
7. Auto-login or email verification required

## Security Features

### Password Hashing

**Algorithm:** Bcrypt with salt

```python
from app.utils.security import hash_password, check_password

# Hash password
password_hash = hash_password("user_password")

# Verify password
is_valid = check_password(password_hash, "user_password")
```

**Password Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- At least one special character

### Account Lockout

**Trigger:** 5 failed login attempts

**Duration:** 30 minutes

**Reset:** Automatic after lockout period or manual reset

```python
# Check if account is locked
if user.is_locked_out():
    # Account is locked
    pass

# Reset lockout
user.reset_failed_login()
```

### Failed Login Tracking

```python
# Increment failed attempts
user.increment_failed_login()

# Reset after successful login
user.reset_failed_login()
```

### Email Verification

**Process:**
1. Token generated on registration
2. Token expires after 24 hours
3. User clicks verification link
4. Account marked as verified

**Token Generation:**
```python
user.email_verification_token = generate_secure_token()
user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
```

### Password Reset

**Process:**
1. User requests password reset
2. Token generated and stored
3. Email sent with reset link
4. Token expires after 1 hour
5. User submits new password
6. Password updated, token invalidated

**Token Generation:**
```python
user.password_reset_token = generate_secure_token()
user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
```

## Authentication Routes

### Login

**Route:** `POST /auth/login`

**Form Fields:**
- `username` - Username or email
- `password` - Password
- `remember_me` - Remember session (optional)

**Response:**
- Success: Redirect to dashboard
- Error: Flash message + login form

### Registration

**Route:** `POST /auth/register`

**Form Fields:**
- `username` - Unique username
- `email` - Unique email
- `password` - Password
- `confirm_password` - Password confirmation
- `firstname` - First name
- `lastname` - Last name
- `terms` - Terms acceptance (required)

**Validation:**
- Username: 3-64 characters, alphanumeric + underscore
- Email: Valid email format
- Password: Strength requirements
- Password match: Both passwords must match

### Logout

**Route:** `GET /auth/logout`

**Process:**
1. Flask-Login logout
2. Session cleared
3. Redirect to login

### Forgot Password

**Route:** `POST /auth/forgot_password`

**Form Fields:**
- `email` - User email

**Process:**
1. Lookup user by email
2. Generate reset token
3. Send email with reset link
4. Show confirmation message

### Reset Password

**Route:** `POST /auth/reset_password/<token>`

**Form Fields:**
- `password` - New password
- `confirm_password` - Password confirmation

**Validation:**
- Token validity
- Token expiration
- Password strength
- Password match

## Session Management

### Flask-Login Integration

```python
from flask_login import login_user, logout_user, current_user, login_required

# Login user
login_user(user, remember=remember_me)

# Logout user
logout_user()

# Check if logged in
if current_user.is_authenticated:
    # User is logged in
    pass

# Require login
@login_required
def protected_route():
    pass
```

### Session Configuration

**Session Cookie:**
- `SECURE` - HTTPS only (production)
- `HTTPONLY` - Not accessible via JavaScript
- `SAMESITE` - CSRF protection

**Session Timeout:**
- Default: Browser session
- With `remember_me`: 30 days

## User Model Methods

### Authentication Methods

```python
# Set password
user.set_password("new_password")

# Check password
if user.check_password("password"):
    # Password correct
    pass

# Check lockout
if user.is_locked_out():
    # Account locked
    pass

# Increment failed login
user.increment_failed_login()

# Reset failed login
user.reset_failed_login()
```

### User Information

```python
# Get full name
full_name = user.get_full_name()  # "John Doe" or username

# Get display name
display_name = user.display_name or user.username

# Check if admin
if user.is_admin or user.is_superadmin:
    # Admin user
    pass
```

## CSRF Protection

All forms include CSRF tokens:

```jinja2
<form method="POST">
    <input type="hidden" name="csrf_token" value="{{ csrf_token() }}"/>
    <!-- Form fields -->
</form>
```

**API Endpoints:**
- CSRF exempt for API routes
- Use JWT tokens for API authentication

## Password Strength Validation

**Requirements:**
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special character

**Validation:**
```python
from app.utils.security import validate_password_strength

result = validate_password_strength("password")
if not result['valid']:
    errors = result['errors']
```

## Email Verification

### Manual Verification

```python
# Generate verification token
user.email_verification_token = generate_secure_token()
user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
db.session.commit()

# Send verification email
send_verification_email(user)
```

### Verify Token

```python
# Check token
if user.email_verification_token == token:
    if datetime.utcnow() < user.email_verification_expires:
        user.email_verified = True
        user.email_verification_token = None
        db.session.commit()
```

## Password Reset Flow

### Request Reset

```python
# Generate reset token
user.password_reset_token = generate_secure_token()
user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
db.session.commit()

# Send reset email
send_password_reset_email(user)
```

### Reset Password

```python
# Verify token
if user.password_reset_token == token:
    if datetime.utcnow() < user.password_reset_expires:
        # Set new password
        user.set_password(new_password)
        user.password_reset_token = None
        user.password_reset_expires = None
        db.session.commit()
```

## Security Best Practices

### 1. Never Store Plain Text Passwords

Always use password hashing:
```python
user.set_password(password)  # Automatically hashes
```

### 2. Validate Input

Sanitize all user input:
```python
from app.utils.security import sanitize_input

username = sanitize_input(request.form.get('username'), max_length=64)
```

### 3. Rate Limit Login Attempts

Already implemented:
- 5 failed attempts = 30 minute lockout
- Rate limiting on API endpoints

### 4. Use HTTPS in Production

```env
SESSION_COOKIE_SECURE=True
```

### 5. Regular Password Updates

Encourage users to change passwords regularly.

### 6. Monitor Failed Logins

Check `failed_login_attempts` and `last_failed_login` fields.

## Troubleshooting

### Login Not Working

1. Check password hash matches
2. Verify account is active (`is_active=True`)
3. Check account lockout status
4. Verify email/username is correct
5. Check database connection

### Password Reset Not Working

1. Verify token matches
2. Check token expiration
3. Verify email exists
4. Check email service is configured

### Session Expiring Too Quickly

1. Check `remember_me` is set
2. Verify session configuration
3. Check browser cookie settings

## See Also

- [RBAC_GUIDE.md](../rbac/RBAC_GUIDE.md) - Permission system
- [CONFIGURATION.md](../../04-operations/CONFIGURATION.md) - Security configuration
