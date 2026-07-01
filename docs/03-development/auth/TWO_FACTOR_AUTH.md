# Two-Factor Authentication (2FA) Guide

Complete guide to the TOTP-based two-factor authentication system.

---

## Overview

The 2FA system provides:
- **TOTP (Time-based One-Time Password)** - Works with Google Authenticator, Microsoft Authenticator, Authy
- **QR Code Setup** - Easy enrollment with QR code scanning
- **Backup Codes** - 10 single-use backup codes for account recovery
- **Secure Storage** - Backup codes are hashed with SHA-256
- **Flexible Management** - Enable, disable, and regenerate codes

---

## Quick Start

### Prerequisites

**Install Required Packages:**
```bash
pip install -r requirements-2fa.txt
```

This installs:
- `pyotp` - TOTP implementation
- `qrcode[pil]` - QR code generation
- `Pillow` - Image processing

**Note**: If you encounter SSL certificate errors, you may need to install packages manually or configure your Python environment's SSL certificates.

### Database Setup ✅ DONE

The 2FA fields have been added to the `auth.users` table:
```
✓ 2FA fields added to users table successfully
✓ Index created for 2FA enabled users
```

---

## Database Schema

### 2FA Fields in `auth.users`

```sql
ALTER TABLE auth.users 
ADD COLUMN totp_secret VARCHAR(32),        -- Base32 encoded TOTP secret
ADD COLUMN totp_enabled BOOLEAN DEFAULT FALSE,
ADD COLUMN totp_enabled_at TIMESTAMP,
ADD COLUMN backup_codes JSON;              -- Array of hashed backup codes

CREATE INDEX idx_users_totp_enabled ON auth.users(totp_enabled) WHERE totp_enabled = TRUE;
```

**Field Descriptions:**
- `totp_secret` - Base32 encoded secret key (16 characters)
- `totp_enabled` - Whether 2FA is active for this user
- `totp_enabled_at` - Timestamp when 2FA was enabled
- `backup_codes` - JSON array of SHA-256 hashed backup codes

---

## User Flow

### 1. Enable 2FA

**Step 1: Navigate to Security Settings**
```
/users/settings/security → Click "Enable Two-Factor Authentication"
```

**Step 2: Scan QR Code**
- System generates a new TOTP secret
- QR code is displayed for scanning
- Manual entry code is provided as fallback

**Step 3: Verify Setup**
- User enters 6-digit code from authenticator app
- System verifies the code
- If valid, 2FA is enabled

**Step 4: Save Backup Codes**
- System generates 10 backup codes
- User must confirm they've saved the codes
- Codes are displayed with print/download/copy options

### 2. Login with 2FA

**Step 1: Enter Credentials**
- User enters username/email and password
- System validates credentials

**Step 2: 2FA Check**
- If 2FA is enabled, redirect to verification page
- If 2FA is disabled, complete login normally

**Step 3: Enter Verification Code**
- User enters 6-digit TOTP code
- OR user can switch to backup code mode
- System verifies the code

**Step 4: Complete Login**
- If verified, create session and log in user
- If backup code used, remove it from available codes
- Redirect to dashboard or next page

### 3. Manage 2FA

**Regenerate Backup Codes:**
```
Security Settings → Regenerate Backup Codes
- Enter password to confirm
- New codes are generated
- Old codes are invalidated
```

**Disable 2FA:**
```
Security Settings → Disable 2FA
- Enter password to confirm
- 2FA is disabled
- Backup codes are cleared
```

---

## API Endpoints

### 2FA Setup & Management

```
GET  /users/settings/security                          - View 2FA status
GET  /users/settings/security/2fa/setup                - Start 2FA setup
POST /users/settings/security/2fa/setup                - Verify and enable 2FA
GET  /users/settings/security/2fa/backup-codes         - View backup codes
POST /users/settings/security/2fa/backup-codes/confirm - Confirm codes saved
POST /users/settings/security/2fa/disable              - Disable 2FA
POST /users/settings/security/2fa/regenerate-backup-codes - Regenerate codes
```

### 2FA Verification

```
GET  /auth/verify-2fa  - Show 2FA verification page
POST /auth/verify-2fa  - Verify TOTP or backup code
```

---

## TOTP Service

### Core Functions

**Generate Secret:**
```python
from app.services.totp_service import totp_service

secret = totp_service.generate_secret()
# Returns: 'JBSWY3DPEHPK3PXP' (16-character Base32 string)
```

**Generate QR Code:**
```python
uri = totp_service.get_totp_uri(secret, user.email, "My App")
qr_code = totp_service.generate_qr_code(uri)
# Returns: 'data:image/png;base64,...' (base64 encoded PNG)
```

**Verify Token:**
```python
is_valid = totp_service.verify_token(secret, '123456')
# Returns: True if valid, False otherwise
# Allows 1 time step (30 seconds) before/after for clock skew
```

**Generate Backup Codes:**
```python
codes = totp_service.generate_backup_codes(10)
# Returns: ['ABCD-EFGH', 'IJKL-MNOP', ...]
```

**Hash Backup Code:**
```python
hashed = totp_service.hash_backup_code('ABCD-EFGH')
# Returns: SHA-256 hash of the code
```

**Verify Backup Code:**
```python
is_valid, matched_hash = totp_service.verify_backup_code('ABCD-EFGH', user.backup_codes)
# Returns: (True, hash) if valid, (False, None) otherwise
```

---

## Security Features

### TOTP Security
- **Secret Length**: 16 characters (128 bits of entropy)
- **Algorithm**: SHA-1 (TOTP standard)
- **Time Step**: 30 seconds
- **Code Length**: 6 digits
- **Clock Skew**: ±30 seconds (1 time step)

### Backup Code Security
- **Format**: 8 characters (XXXX-XXXX)
- **Character Set**: A-Z, 2-9 (excluding confusing characters: 0, 1, I, O)
- **Storage**: SHA-256 hashed
- **Single Use**: Removed after successful use
- **Count**: 10 codes per user

### Session Security
- **2FA Session**: Temporary session during verification
- **User ID Storage**: Stored in Flask session during 2FA flow
- **Session Cleanup**: 2FA session data cleared after login
- **Remember Me**: Preserved through 2FA verification

---

## Testing

### Test 2FA Setup

**1. Enable 2FA:**
```
1. Go to /users/settings/security
2. Click "Enable Two-Factor Authentication"
3. Scan QR code with authenticator app
4. Enter 6-digit code
5. Verify 2FA is enabled
6. Save backup codes
```

**2. Verify Database:**
```sql
SELECT 
    username,
    totp_enabled,
    totp_enabled_at,
    LENGTH(totp_secret) as secret_length,
    JSON_ARRAY_LENGTH(backup_codes) as backup_code_count
FROM auth.users
WHERE totp_enabled = TRUE;
```

### Test 2FA Login

**1. Logout and Login:**
```
1. Logout completely
2. Login with username/password
3. Should redirect to /auth/verify-2fa
4. Enter code from authenticator app
5. Should complete login successfully
```

**2. Test Backup Code:**
```
1. Logout
2. Login with username/password
3. Click "Use a backup code instead"
4. Enter one of your backup codes
5. Should complete login successfully
6. Verify backup code was removed from database
```

### Test 2FA Management

**1. Regenerate Backup Codes:**
```
1. Go to /users/settings/security
2. Click "Regenerate Backup Codes"
3. Enter password
4. Verify new codes are displayed
5. Check database - old codes should be replaced
```

**2. Disable 2FA:**
```
1. Go to /users/settings/security
2. Click "Disable 2FA"
3. Enter password
4. Verify 2FA is disabled
5. Check database - totp fields should be cleared
```

---

## Troubleshooting

### QR Code Not Displaying

**Issue**: QR code image not showing  
**Causes**:
- `qrcode` or `Pillow` not installed
- Error generating QR code

**Fix**:
```bash
pip install 'qrcode[pil]' Pillow
```

**Check**:
```python
from app.services.totp_service import totp_service
secret = totp_service.generate_secret()
uri = totp_service.get_totp_uri(secret, 'test@example.com', 'Test App')
qr = totp_service.generate_qr_code(uri)
print(qr[:50])  # Should start with 'data:image/png;base64,'
```

### Invalid Code Errors

**Issue**: Valid codes are rejected  
**Causes**:
- Clock skew (server time != phone time)
- Wrong secret being used
- Code already used (within 30-second window)

**Fix**:
1. Check server time: `date`
2. Check phone time
3. Sync time on both devices
4. Increase `valid_window` in `verify_token()` (temporarily for testing)

**Debug**:
```python
from app.services.totp_service import totp_service
secret = 'YOUR_SECRET_HERE'
current_token = totp_service.get_current_token(secret)
print(f"Current valid token: {current_token}")
```

### Backup Codes Not Working

**Issue**: Backup codes are rejected  
**Causes**:
- Incorrect format (missing dash, wrong case)
- Code already used
- Codes not properly stored

**Fix**:
1. Verify backup codes exist: `SELECT backup_codes FROM auth.users WHERE id = '<user_id>';`
2. Check code format: Should be 'XXXX-XXXX'
3. Verify hashing: Test with `totp_service.hash_backup_code('YOUR-CODE')`

### 2FA Session Issues

**Issue**: Stuck in 2FA verification loop  
**Causes**:
- Session data not being cleared
- User ID not in session

**Fix**:
```python
# Clear 2FA session data
from flask import session
session.pop('2fa_user_id', None)
session.pop('2fa_remember', None)
session.pop('2fa_next', None)
```

---

## Best Practices

### For Users

1. **Use a Reputable Authenticator App**
   - Google Authenticator
   - Microsoft Authenticator
   - Authy (supports cloud backup)

2. **Save Backup Codes Securely**
   - Store in password manager
   - Print and keep in safe location
   - Don't store in plain text on your computer

3. **Enable 2FA on Important Accounts**
   - Admin accounts
   - Accounts with sensitive data
   - Accounts with financial access

### For Developers

1. **Never Log Secrets**
   ```python
   # BAD
   logger.info(f"TOTP secret: {user.totp_secret}")
   
   # GOOD
   logger.info(f"2FA enabled for user {user.id}")
   ```

2. **Validate Input**
   ```python
   # Validate token format
   if not token or len(token) != 6 or not token.isdigit():
       return False
   ```

3. **Handle Clock Skew**
   ```python
   # Allow ±30 seconds for clock differences
   totp.verify(token, valid_window=1)
   ```

4. **Secure Backup Codes**
   ```python
   # Always hash backup codes before storage
   hashed_codes = [totp_service.hash_backup_code(code) for code in codes]
   user.backup_codes = hashed_codes
   ```

5. **Require Password for Sensitive Operations**
   ```python
   # Always verify password before disabling 2FA
   if not user.check_password(password):
       return error('Invalid password')
   ```

---

## Advanced Features

### Enforce 2FA for Admin Roles

Add to login route:

```python
# After successful login
if user.is_admin and not user.totp_enabled:
    flash('Administrators must enable 2FA', 'warning')
    return redirect(url_for('users.setup_2fa'))
```

### Trusted Devices (Future)

Skip 2FA on trusted devices:

```python
# Store device fingerprint
device_id = hash(user_agent + ip_address)
if device_id in user.trusted_devices:
    # Skip 2FA
    pass
```

### 2FA Recovery Email (Future)

Send recovery codes via email:

```python
def send_recovery_codes(user):
    email_service.send_template_email(
        to_email=user.email,
        subject='2FA Recovery Codes',
        template_name='2fa_recovery',
        template_data={'codes': user.backup_codes}
    )
```

### Push Notifications (Future)

Approve login via push notification:

```python
# Send push notification
send_push_notification(
    user_id=user.id,
    title='Login Attempt',
    body='Approve login from Chrome on Windows?',
    action_url=url_for('auth.approve_login', token=token)
)
```

---

## Configuration

### TOTP Settings

Configure in `app/services/totp_service.py`:

```python
# Time step (seconds)
TIME_STEP = 30

# Code digits
CODE_DIGITS = 6

# Valid window (time steps)
VALID_WINDOW = 1  # ±30 seconds

# Backup code count
BACKUP_CODE_COUNT = 10

# Backup code length
BACKUP_CODE_LENGTH = 8
```

### Security Settings

Configure in production config:

```python
# Require 2FA for admins
REQUIRE_2FA_FOR_ADMINS = True

# 2FA grace period (days)
TWO_FA_GRACE_PERIOD = 7

# Maximum backup codes
MAX_BACKUP_CODES = 10
```

---

## Maintenance

### Monitor 2FA Usage

```sql
-- Count users with 2FA enabled
SELECT COUNT(*) as users_with_2fa
FROM auth.users
WHERE totp_enabled = TRUE;

-- 2FA adoption rate
SELECT 
    COUNT(CASE WHEN totp_enabled THEN 1 END) * 100.0 / COUNT(*) as adoption_rate
FROM auth.users
WHERE is_active = TRUE;

-- Recent 2FA enrollments
SELECT 
    username,
    email,
    totp_enabled_at
FROM auth.users
WHERE totp_enabled = TRUE
ORDER BY totp_enabled_at DESC
LIMIT 10;
```

### Clean Up Old Sessions

```python
# Remove 2FA session data older than 1 hour
from datetime import datetime, timedelta
from flask import session

if '2fa_user_id' in session:
    # Check if session is stale
    if datetime.utcnow() - session.get('2fa_started_at', datetime.utcnow()) > timedelta(hours=1):
        session.pop('2fa_user_id', None)
        session.pop('2fa_remember', None)
        session.pop('2fa_next', None)
```

---

## Related Documentation

- [Session Management](./SESSION_MANAGEMENT.md)
- [Email Service](../email/EMAIL_SERVICE_SETUP.md)
- [Security Best Practices](../02-architecture/SECURITY.md)

---

## References

- [RFC 6238 - TOTP](https://tools.ietf.org/html/rfc6238)
- [Google Authenticator](https://support.google.com/accounts/answer/1066447)
- [pyotp Documentation](https://pyotp.readthedocs.io/)
- [QR Code Generation](https://github.com/lincolnloop/python-qrcode)
