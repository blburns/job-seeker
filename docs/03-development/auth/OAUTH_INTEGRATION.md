# OAuth Integration Guide

Complete guide to OAuth authentication with Google, Microsoft, and GitHub.

---

## Overview

The OAuth integration provides:
- **Social Login** - Sign in with Google, Microsoft, or GitHub
- **Account Linking** - Link OAuth accounts to existing users
- **Auto Registration** - Create new accounts via OAuth
- **Token Management** - Store and refresh OAuth tokens
- **Profile Sync** - Sync profile data from OAuth providers

---

## Quick Start

### Prerequisites

**Install Required Packages:**
```bash
pip install -r requirements-oauth.txt
```

This installs:
- `Authlib` - OAuth 2.0 client library
- `requests` - HTTP library for API calls

**Database Setup:**
```bash
python scripts/add_oauth_table.py
```

This creates the `auth.oauth_accounts` table.

---

## Configuration

### Environment Variables

Add OAuth credentials to your `.env` file:

```env
# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-google-client-secret

# Microsoft OAuth
MICROSOFT_CLIENT_ID=your-microsoft-client-id
MICROSOFT_CLIENT_SECRET=your-microsoft-client-secret

# GitHub OAuth
GITHUB_CLIENT_ID=your-github-client-id
GITHUB_CLIENT_SECRET=your-github-client-secret
```

### Provider Setup

#### Google OAuth

1. **Create OAuth Credentials:**
   - Go to [Google Cloud Console](https://console.cloud.google.com/)
   - Create a new project or select existing
   - Enable Google+ API
   - Go to "Credentials" → "Create Credentials" → "OAuth 2.0 Client ID"
   - Application type: Web application
   - Add authorized redirect URI: `http://localhost:5000/auth/oauth/google/callback`
   - For production: `https://yourdomain.com/auth/oauth/google/callback`

2. **Copy Credentials:**
   - Copy Client ID and Client Secret
   - Add to `.env` file

3. **Scopes Used:**
   - `openid` - Basic authentication
   - `email` - User's email address
   - `profile` - User's profile information

#### Microsoft OAuth

1. **Register Application:**
   - Go to [Azure Portal](https://portal.azure.com/)
   - Navigate to "Azure Active Directory" → "App registrations"
   - Click "New registration"
   - Name: Your App Name
   - Supported account types: "Accounts in any organizational directory and personal Microsoft accounts"
   - Redirect URI: `http://localhost:5000/auth/oauth/microsoft/callback`
   - For production: `https://yourdomain.com/auth/oauth/microsoft/callback`

2. **Create Client Secret:**
   - Go to "Certificates & secrets"
   - Click "New client secret"
   - Copy the secret value (shown only once!)

3. **Copy Credentials:**
   - Application (client) ID → MICROSOFT_CLIENT_ID
   - Client secret value → MICROSOFT_CLIENT_SECRET

4. **Scopes Used:**
   - `openid` - Basic authentication
   - `email` - User's email address
   - `profile` - User's profile information

#### GitHub OAuth

1. **Create OAuth App:**
   - Go to [GitHub Developer Settings](https://github.com/settings/developers)
   - Click "New OAuth App"
   - Application name: Your App Name
   - Homepage URL: `http://localhost:5000` (or your domain)
   - Authorization callback URL: `http://localhost:5000/auth/oauth/github/callback`
   - For production: `https://yourdomain.com/auth/oauth/github/callback`

2. **Copy Credentials:**
   - Copy Client ID and Client Secret
   - Add to `.env` file

3. **Scopes Used:**
   - `user:email` - Access to user's email addresses

---

## Database Schema

### OAuth Accounts Table

```sql
CREATE TABLE auth.oauth_accounts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    provider VARCHAR(50) NOT NULL,              -- google, microsoft, github
    provider_user_id VARCHAR(255) NOT NULL,     -- Unique ID from provider
    access_token TEXT,                          -- OAuth access token
    refresh_token TEXT,                         -- OAuth refresh token
    token_expires_at TIMESTAMP,                 -- Token expiration
    provider_email VARCHAR(255),                -- Email from provider
    provider_name VARCHAR(255),                 -- Display name from provider
    provider_picture VARCHAR(500),              -- Profile picture URL
    provider_data JSONB,                        -- Additional provider data
    created_at TIMESTAMP DEFAULT NOW() NOT NULL,
    updated_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    CONSTRAINT uq_oauth_provider_user UNIQUE (provider, provider_user_id)
);

CREATE INDEX idx_oauth_user_id ON auth.oauth_accounts(user_id);
CREATE INDEX idx_oauth_provider ON auth.oauth_accounts(provider);
CREATE INDEX idx_oauth_provider_user_id ON auth.oauth_accounts(provider, provider_user_id);
```

---

## User Flow

### 1. OAuth Login (Existing User)

**Step 1: Click OAuth Button**
- User clicks "Sign in with Google" (or Microsoft/GitHub)
- System redirects to OAuth provider

**Step 2: Provider Authorization**
- User authorizes the application
- Provider redirects back with authorization code

**Step 3: Token Exchange**
- System exchanges code for access token
- Retrieves user profile from provider

**Step 4: Account Lookup**
- System finds OAuth account by provider + provider_user_id
- Loads associated user account

**Step 5: Login**
- Updates OAuth account tokens and profile
- Creates user session
- Logs in user
- Redirects to dashboard

### 2. OAuth Registration (New User)

**Step 1-3: Same as Login**

**Step 4: No Account Found**
- System checks if user exists by email
- If yes: Links OAuth account to existing user
- If no: Creates new user account

**Step 5: Account Creation**
- Generates username from email
- Creates user with OAuth profile data
- Marks email as verified (OAuth emails are verified)
- Creates OAuth account link
- Sends welcome email
- Logs in user

### 3. Account Linking

**Scenario:** User has email account, wants to link Google OAuth

**Step 1: Login with Email**
- User logs in with email/password

**Step 2: Click OAuth Button**
- User clicks "Sign in with Google"

**Step 3: OAuth Flow**
- System retrieves Google profile
- Finds existing user by email

**Step 4: Link Accounts**
- Creates OAuth account record
- Links to existing user
- User can now login with either method

---

## API Endpoints

### OAuth Routes

```
GET  /auth/oauth/<provider>              - Initiate OAuth login
GET  /auth/oauth/<provider>/callback     - Handle OAuth callback
```

**Supported Providers:**
- `google`
- `microsoft`
- `github`

**Example:**
```
GET /auth/oauth/google
GET /auth/oauth/google/callback
```

---

## OAuth Service

### Core Functions

**Check if Provider is Configured:**
```python
from app.services.oauth_service import oauth_service

if oauth_service.is_provider_configured('google'):
    # Google OAuth is configured
    pass
```

**Get OAuth Client:**
```python
google = oauth_service.get_provider('google')
```

**Get Redirect URI:**
```python
redirect_uri = oauth_service.get_redirect_uri('google')
# Returns: http://localhost:5000/auth/oauth/google/callback
```

**Normalize User Info:**
```python
normalized = oauth_service.normalize_user_info('google', raw_user_info)
# Returns: {'id': '...', 'email': '...', 'name': '...', 'picture': '...', 'email_verified': True}
```

---

## OAuth Account Model

### Methods

**Find by Provider:**
```python
from app.models.oauth import OAuthAccount

oauth_account = OAuthAccount.find_by_provider('google', 'google-user-id-123')
```

**Find by User and Provider:**
```python
oauth_account = OAuthAccount.find_by_user_and_provider(user.id, 'google')
```

**Update Tokens:**
```python
oauth_account.update_tokens(
    access_token='new-token',
    refresh_token='new-refresh-token',
    expires_at=datetime.utcnow() + timedelta(hours=1)
)
db.session.commit()
```

**Update Profile:**
```python
oauth_account.update_profile(
    email='user@example.com',
    name='John Doe',
    picture='https://...',
    data={'additional': 'data'}
)
db.session.commit()
```

**Mark as Used:**
```python
oauth_account.mark_used()
db.session.commit()
```

---

## Security Features

### Token Storage
- **Access Tokens**: Stored in database (encrypt in production!)
- **Refresh Tokens**: Stored in database (encrypt in production!)
- **Token Expiration**: Tracked but not auto-refreshed (implement if needed)

### Account Linking
- **Email Matching**: Links OAuth accounts to existing users by email
- **Unique Constraint**: One OAuth account per provider per user
- **Cascade Delete**: OAuth accounts deleted when user is deleted

### Email Verification
- **OAuth Emails**: Marked as verified automatically
- **Existing Users**: Email verification status preserved

### Session Management
- **Remember Me**: OAuth logins are remembered by default
- **Session Tracking**: Full session tracking with device info
- **2FA**: OAuth logins bypass 2FA (consider adding option to require)

---

## Testing

### Test OAuth Flow

**1. Configure Provider:**
```bash
# Add to .env
GOOGLE_CLIENT_ID=your-client-id
GOOGLE_CLIENT_SECRET=your-client-secret
```

**2. Start Application:**
```bash
python run.py
```

**3. Test Login:**
```
1. Go to http://localhost:5000/auth/login
2. Click "Sign in with Google"
3. Authorize the application
4. Should redirect back and log you in
5. Check database for OAuth account record
```

**4. Verify Database:**
```sql
SELECT 
    u.username,
    u.email,
    oa.provider,
    oa.provider_email,
    oa.provider_name,
    oa.created_at,
    oa.last_used_at
FROM auth.users u
JOIN auth.oauth_accounts oa ON u.id = oa.user_id
ORDER BY oa.created_at DESC;
```

### Test Account Linking

**1. Create Email Account:**
```
1. Register with email: test@example.com
2. Verify email
3. Logout
```

**2. Link OAuth Account:**
```
1. Click "Sign in with Google"
2. Use same email: test@example.com
3. Should link accounts and log in
4. Check database - should see OAuth account linked to user
```

### Test New User Registration

**1. Use New Email:**
```
1. Click "Sign in with GitHub"
2. Use email that doesn't exist in system
3. Should create new user account
4. Should receive welcome email
5. Check database - new user and OAuth account created
```

---

## Troubleshooting

### OAuth Buttons Not Showing

**Issue**: OAuth buttons not visible on login page  
**Cause**: OAuth credentials not configured

**Fix**:
1. Check `.env` file has OAuth credentials
2. Restart application to reload config
3. Check browser console for errors

**Verify**:
```python
from flask import current_app
print(current_app.config.get('GOOGLE_CLIENT_ID'))
```

### Redirect URI Mismatch

**Issue**: "redirect_uri_mismatch" error from OAuth provider  
**Cause**: Callback URL doesn't match registered URL

**Fix**:
1. Check provider console for registered redirect URIs
2. Ensure it matches exactly: `http://localhost:5000/auth/oauth/google/callback`
3. For production: Update to `https://yourdomain.com/auth/oauth/google/callback`
4. No trailing slashes!

### Invalid Client Error

**Issue**: "invalid_client" error  
**Cause**: Wrong client ID or secret

**Fix**:
1. Verify credentials in provider console
2. Check for extra spaces in `.env` file
3. Regenerate client secret if needed
4. Restart application

### Email Not Retrieved

**Issue**: GitHub OAuth doesn't return email  
**Cause**: Email is private on GitHub

**Fix**:
1. System automatically requests email via API
2. User must have at least one verified email on GitHub
3. Check GitHub → Settings → Emails → "Keep my email addresses private"

### Token Expired

**Issue**: OAuth token expired  
**Cause**: Access token has limited lifetime

**Fix**:
1. Implement token refresh (future enhancement)
2. For now, user must re-authenticate
3. Tokens are refreshed on each login

---

## Best Practices

### For Users

1. **Link Multiple Providers**
   - Link Google, Microsoft, and GitHub to same account
   - Provides multiple login options
   - Reduces lockout risk

2. **Keep Email Verified**
   - Ensure OAuth provider email matches account email
   - Verify email in provider settings

3. **Review Connected Apps**
   - Periodically review OAuth authorizations
   - Revoke access for unused apps

### For Developers

1. **Secure Token Storage**
   ```python
   # TODO: Encrypt tokens in production
   from cryptography.fernet import Fernet
   
   def encrypt_token(token):
       f = Fernet(app.config['ENCRYPTION_KEY'])
       return f.encrypt(token.encode()).decode()
   ```

2. **Handle Token Refresh**
   ```python
   def refresh_oauth_token(oauth_account):
       if oauth_account.is_token_expired and oauth_account.refresh_token:
           # Implement token refresh logic
           pass
   ```

3. **Validate Provider Data**
   ```python
   # Always validate data from OAuth providers
   email = normalized_info.get('email')
   if not email or '@' not in email:
       raise ValueError('Invalid email from OAuth provider')
   ```

4. **Log OAuth Events**
   ```python
   logger.info(f"OAuth login: {provider} - {user.email}")
   logger.warning(f"OAuth account linked: {provider} - {user.email}")
   ```

5. **Handle Provider Errors**
   ```python
   try:
       token = oauth_client.authorize_access_token()
   except Exception as e:
       logger.error(f"OAuth token error: {e}")
       flash('Authentication failed. Please try again.', 'danger')
       return redirect(url_for('auth.login'))
   ```

---

## Advanced Features

### Multiple OAuth Accounts

Allow users to link multiple providers:

```python
# In user settings
@users_bp.route('/settings/oauth/link/<provider>')
@login_required
def link_oauth_account(provider):
    # Redirect to OAuth flow
    return redirect(url_for('auth.oauth_login', provider=provider))
```

### Unlink OAuth Account

Allow users to unlink providers:

```python
@users_bp.route('/settings/oauth/unlink/<provider>', methods=['POST'])
@login_required
def unlink_oauth_account(provider):
    oauth_account = OAuthAccount.find_by_user_and_provider(current_user.id, provider)
    if oauth_account:
        db.session.delete(oauth_account)
        db.session.commit()
        flash(f'{provider.title()} account unlinked', 'success')
    return redirect(url_for('users.settings_security'))
```

### Token Refresh

Implement automatic token refresh:

```python
def refresh_token_if_needed(oauth_account):
    if oauth_account.is_token_expired and oauth_account.refresh_token:
        oauth_client = oauth_service.get_provider(oauth_account.provider)
        
        # Refresh token
        token = oauth_client.fetch_access_token(
            refresh_token=oauth_account.refresh_token
        )
        
        # Update account
        oauth_account.update_tokens(
            access_token=token['access_token'],
            refresh_token=token.get('refresh_token'),
            expires_at=datetime.utcnow() + timedelta(seconds=token.get('expires_in', 3600))
        )
        db.session.commit()
```

### Profile Picture Sync

Sync profile pictures from OAuth:

```python
def sync_profile_picture(user, oauth_account):
    if oauth_account.provider_picture and not user.profile_photo:
        # Download and save profile picture
        response = requests.get(oauth_account.provider_picture)
        if response.status_code == 200:
            # Save to storage
            filename = f"profile_{user.id}.jpg"
            # ... save file logic ...
            user.profile_photo = filename
            db.session.commit()
```

---

## Configuration

### OAuth Settings

Configure in `app/services/oauth_service.py`:

```python
# OAuth scopes
GOOGLE_SCOPES = 'openid email profile'
MICROSOFT_SCOPES = 'openid email profile'
GITHUB_SCOPES = 'user:email'

# Token expiration (seconds)
TOKEN_EXPIRATION = 3600  # 1 hour

# Auto-link accounts by email
AUTO_LINK_BY_EMAIL = True

# Auto-verify email from OAuth
AUTO_VERIFY_OAUTH_EMAIL = True
```

### Security Settings

Configure in production config:

```python
# Encrypt OAuth tokens
ENCRYPT_OAUTH_TOKENS = True
OAUTH_ENCRYPTION_KEY = os.environ.get('OAUTH_ENCRYPTION_KEY')

# Require 2FA for OAuth logins
REQUIRE_2FA_FOR_OAUTH = False

# Allow OAuth registration
ALLOW_OAUTH_REGISTRATION = True
```

---

## Maintenance

### Monitor OAuth Usage

```sql
-- Count OAuth accounts by provider
SELECT 
    provider,
    COUNT(*) as account_count
FROM auth.oauth_accounts
GROUP BY provider
ORDER BY account_count DESC;

-- Recent OAuth logins
SELECT 
    u.username,
    u.email,
    oa.provider,
    oa.last_used_at
FROM auth.users u
JOIN auth.oauth_accounts oa ON u.id = oa.user_id
ORDER BY oa.last_used_at DESC
LIMIT 20;

-- Users with multiple OAuth accounts
SELECT 
    u.username,
    u.email,
    COUNT(oa.id) as oauth_account_count,
    STRING_AGG(oa.provider, ', ') as providers
FROM auth.users u
JOIN auth.oauth_accounts oa ON u.id = oa.user_id
GROUP BY u.id, u.username, u.email
HAVING COUNT(oa.id) > 1
ORDER BY oauth_account_count DESC;
```

### Clean Up Unused Tokens

```python
# Remove expired tokens (optional)
from datetime import datetime, timedelta

def clean_expired_tokens():
    expired_date = datetime.utcnow() - timedelta(days=90)
    
    OAuthAccount.query.filter(
        OAuthAccount.last_used_at < expired_date
    ).update({
        'access_token': None,
        'refresh_token': None
    })
    
    db.session.commit()
```

---

## Related Documentation

- [Two-Factor Authentication](./TWO_FACTOR_AUTH.md)
- [Session Management](./SESSION_MANAGEMENT.md)
- [Email Service](../email/EMAIL_SERVICE_SETUP.md)

---

## References

- [Authlib Documentation](https://docs.authlib.org/)
- [Google OAuth 2.0](https://developers.google.com/identity/protocols/oauth2)
- [Microsoft Identity Platform](https://docs.microsoft.com/en-us/azure/active-directory/develop/)
- [GitHub OAuth Apps](https://docs.github.com/en/developers/apps/building-oauth-apps)
- [OAuth 2.0 RFC](https://tools.ietf.org/html/rfc6749)
