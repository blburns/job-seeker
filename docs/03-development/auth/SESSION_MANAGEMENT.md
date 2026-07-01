# Session Management System

Complete guide to the session management system including active sessions tracking, device detection, and remote revocation.

---

## Overview

The session management system provides:
- **Active Session Tracking** - Track all user sessions across devices
- **Device Detection** - Identify browser, OS, and device type
- **Remote Revocation** - Sign out from any device
- **Remember Me** - Extended session duration (30 days)
- **Security Monitoring** - IP tracking and suspicious activity detection

---

## Database Schema

### user_sessions Table

```sql
CREATE TABLE auth.user_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    session_token VARCHAR(255) UNIQUE NOT NULL,
    device_info JSONB,
    ip_address VARCHAR(45),
    user_agent TEXT,
    last_activity TIMESTAMP DEFAULT NOW(),
    expires_at TIMESTAMP NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    remember_me BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW(),
    revoked_at TIMESTAMP
);

CREATE INDEX idx_user_sessions_user_id ON auth.user_sessions(user_id);
CREATE INDEX idx_user_sessions_token ON auth.user_sessions(session_token);
CREATE INDEX idx_user_sessions_expires ON auth.user_sessions(expires_at);
CREATE INDEX idx_user_sessions_active ON auth.user_sessions(is_active);
```

### Device Info Structure (JSONB)

```json
{
  "browser": "Chrome",
  "os": "macOS 14.2",
  "device": "MacBook Pro",
  "device_type": "desktop"
}
```

---

## Setup Instructions

### 1. Create Sessions Table

Run the migration script:

```bash
# Activate virtual environment
source venv/bin/activate

# Run migration script
python scripts/add_sessions_table.py
```

Or run manually in PostgreSQL:

```sql
-- Connect to your database
psql -U your_user -d your_database

-- Run the CREATE TABLE statement above
```

### 2. Verify Installation

Check that the table was created:

```sql
\dt auth.*
SELECT * FROM auth.user_sessions LIMIT 1;
```

---

## How It Works

### Session Creation (Login)

When a user logs in:

1. **Generate Session Token** - 32-character secure random token
2. **Parse User Agent** - Extract browser, OS, device info
3. **Calculate Expiration**:
   - Standard: 24 hours
   - Remember Me: 30 days
4. **Store Session** - Save to `user_sessions` table
5. **Set Flask Session** - Store `session_token` and `session_id`

```python
# In auth/routes.py
session_token = generate_secure_token(32)
user_session = UserSession.create_session(
    user_id=user.id,
    session_token=session_token,
    request=request,
    remember_me=remember_me
)
db.session.add(user_session)
db.session.commit()

session['session_token'] = session_token
session['session_id'] = str(user_session.id)
```

### Session Validation (Middleware)

On each request (optional, not yet implemented):

1. Check if session token exists in Flask session
2. Lookup session in database
3. Verify session is active and not expired
4. Update `last_activity` timestamp
5. If invalid, force logout

### Session Revocation (Logout)

When a user logs out:

1. Find session by token
2. Set `is_active = False`
3. Set `revoked_at = NOW()`
4. Clear Flask session
5. Logout user

```python
# In auth/routes.py
session_token = session.get('session_token')
if session_token:
    user_session = UserSession.query.filter_by(session_token=session_token).first()
    if user_session:
        user_session.revoke()
        db.session.commit()
```

---

## User Interface

### Viewing Active Sessions

Users can view all their active sessions at:
```
/users/settings/sessions
```

The page displays:
- Device name (browser + OS)
- IP address and location
- Last activity timestamp
- Session status (Active/Expired/Revoked)
- Current session indicator
- Remember Me badge

### Revoking Sessions

**Single Session:**
- Click "Sign Out" button next to any session (except current)
- Confirms with dialog
- Revokes session immediately

**All Other Sessions:**
- Click "Sign Out All Other Sessions" button
- Confirms with dialog
- Revokes all sessions except current one

---

## API Endpoints

### Session Management Routes

```
GET  /users/settings/sessions              - View active sessions
POST /users/settings/sessions/<id>/revoke  - Revoke specific session
POST /users/settings/sessions/revoke-all   - Revoke all except current
```

---

## Device Detection

### Supported Browsers
- Chrome
- Firefox
- Safari
- Edge
- Opera
- Internet Explorer

### Supported Operating Systems
- Windows (7, 8, 8.1, 10, 11)
- macOS (with version detection)
- iOS
- iPadOS
- Android (with version detection)
- Linux (Ubuntu, generic)
- Chrome OS

### Device Types
- **Desktop** - Laptop/desktop computers
- **Mobile** - Smartphones
- **Tablet** - Tablets and iPads

### Device Detection Examples

```python
from app.utils.device_parser import parse_user_agent

ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

device_info = parse_user_agent(ua)
# Returns:
# {
#   'browser': 'Chrome',
#   'os': 'macOS 10.15.7',
#   'device': '',
#   'device_type': 'desktop'
# }
```

---

## Security Features

### Session Token Security
- **Length**: 32 characters
- **Randomness**: Cryptographically secure random generation
- **Uniqueness**: Enforced by database constraint
- **Storage**: Stored in Flask session (encrypted cookie)

### Expiration
- **Standard Sessions**: 24 hours from last activity
- **Remember Me**: 30 days from creation
- **Automatic Cleanup**: Expired sessions can be cleaned periodically

### IP Tracking
- Stores IP address on session creation
- Can be used for:
  - Suspicious activity detection
  - Geographic location (with GeoIP service)
  - Access logs

### Revocation
- Immediate effect (no delay)
- Cannot be undone
- User must log in again

---

## Maintenance Tasks

### Clean Up Expired Sessions

Run periodically (e.g., daily cron job):

```python
from app.models.session import UserSession

# Delete expired sessions
count = UserSession.cleanup_expired_sessions()
print(f"Deleted {count} expired sessions")
```

### Revoke All User Sessions

Useful for security incidents:

```python
from app.models.session import UserSession

# Revoke all sessions for a user
count = UserSession.revoke_all_user_sessions(user_id=user.id)
print(f"Revoked {count} sessions")
```

---

## Advanced Features

### Session Activity Middleware (Future)

Add middleware to update `last_activity` on each request:

```python
@app.before_request
def update_session_activity():
    if current_user.is_authenticated:
        session_token = session.get('session_token')
        if session_token:
            user_session = UserSession.query.filter_by(
                session_token=session_token
            ).first()
            if user_session and user_session.is_valid():
                user_session.update_activity()
                db.session.commit()
            elif user_session and not user_session.is_valid():
                # Force logout if session is invalid
                logout_user()
                session.clear()
                flash('Your session has expired. Please log in again.', 'warning')
                return redirect(url_for('auth.login'))
```

### GeoIP Location Detection (Future)

Add location detection using a GeoIP service:

```python
import geoip2.database

def get_location_from_ip(ip_address):
    """Get location from IP address using GeoIP"""
    try:
        reader = geoip2.database.Reader('GeoLite2-City.mmdb')
        response = reader.city(ip_address)
        return f"{response.city.name}, {response.country.name}"
    except:
        return "Unknown"
```

### Suspicious Activity Detection (Future)

Detect suspicious login patterns:

```python
def check_suspicious_activity(user_id, ip_address, device_info):
    """Check for suspicious login activity"""
    # Get recent sessions
    recent_sessions = UserSession.query.filter_by(
        user_id=user_id
    ).order_by(UserSession.created_at.desc()).limit(5).all()
    
    # Check for:
    # 1. Login from new country
    # 2. Login from new device type
    # 3. Multiple failed attempts
    # 4. Impossible travel (location change too fast)
    
    # If suspicious, send alert email
    if is_suspicious:
        send_security_alert(user_id, ip_address, device_info)
```

---

## Configuration

### Session Duration

Configure in `app/models/session.py`:

```python
# Standard session duration
STANDARD_SESSION_HOURS = 24

# Remember me duration
REMEMBER_ME_DAYS = 30
```

### Cleanup Schedule

Add to cron (daily at 2 AM):

```bash
0 2 * * * cd /path/to/app && /path/to/venv/bin/python -c "from app.models.session import UserSession; UserSession.cleanup_expired_sessions()"
```

---

## Testing

### Test Session Creation

```python
# Register and login
POST /auth/register
POST /auth/login
  - username: testuser
  - password: password
  - remember: on

# Check sessions table
SELECT * FROM auth.user_sessions WHERE user_id = '<user_id>';
```

### Test Session Revocation

```python
# Login from multiple devices
# Go to /users/settings/sessions
# Click "Sign Out" on one session
# Verify session is revoked in database
SELECT * FROM auth.user_sessions WHERE id = '<session_id>';
# is_active should be FALSE
# revoked_at should be set
```

### Test Remember Me

```python
# Login with remember me checked
# Check session expiration
SELECT expires_at FROM auth.user_sessions WHERE session_token = '<token>';
# Should be 30 days in the future

# Login without remember me
# Check session expiration
# Should be 24 hours in the future
```

---

## Troubleshooting

### Sessions Not Being Created

**Check:**
1. Database table exists: `\dt auth.user_sessions`
2. User has permission to insert: `GRANT INSERT ON auth.user_sessions TO your_user;`
3. Check logs for errors: `tail -f logs/app.log`

### Sessions Not Showing in UI

**Check:**
1. Route is accessible: `curl http://localhost:5000/users/settings/sessions`
2. User is logged in
3. Sessions exist in database: `SELECT * FROM auth.user_sessions WHERE user_id = '<user_id>';`

### Remember Me Not Working

**Check:**
1. Checkbox is checked on login form
2. Session has `remember_me = TRUE` in database
3. Session `expires_at` is 30 days in future
4. Flask-Login `remember` parameter is set

---

## Security Considerations

### Best Practices

1. **Use HTTPS** - Always use HTTPS in production
2. **Secure Cookies** - Set `SESSION_COOKIE_SECURE = True` in production
3. **HttpOnly Cookies** - Set `SESSION_COOKIE_HTTPONLY = True`
4. **SameSite** - Set `SESSION_COOKIE_SAMESITE = 'Lax'`
5. **Regular Cleanup** - Clean expired sessions daily
6. **Monitor Activity** - Log suspicious login patterns
7. **Rate Limiting** - Limit login attempts per IP
8. **2FA** - Require 2FA for sensitive accounts

### Security Headers

Add to production config:

```python
@app.after_request
def set_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

---

## Future Enhancements

- [ ] Session activity middleware (auto-update last_activity)
- [ ] GeoIP location detection
- [ ] Suspicious activity alerts
- [ ] Session history (keep revoked sessions for audit)
- [ ] Device fingerprinting (more accurate device detection)
- [ ] Push notifications for new logins
- [ ] Session limits (max N concurrent sessions)
- [ ] Trusted devices (skip 2FA on trusted devices)

---

## Related Documentation

- [Authentication Routes](../app/modules/auth/routes.py)
- [Session Model](../app/models/session.py)
- [Device Parser](../app/utils/device_parser.py)
- [User Model](../app/models/auth.py)
