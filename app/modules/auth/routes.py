"""
Authentication routes for enterprise boilerplate application
Comprehensive login, logout, register, and password reset functionality
"""

import logging
from datetime import datetime, timedelta
from flask import render_template, redirect, url_for, request, flash, jsonify, Blueprint, current_app, session
from flask_login import login_user, login_required, logout_user, current_user
from app.extensions.core import db, csrf
from app.main.models import User
from app.models.auth import FailedLogin
from app.models.session import UserSession
from app.utils.security import validate_password_strength, validate_email_format, sanitize_input, generate_secure_token
from app.services.email_service import email_service
from app.services.oauth_service import oauth_service
from app.models.oauth import OAuthAccount

logger = logging.getLogger(__name__)

# Create auth blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
@csrf.exempt
def login():
    """User login endpoint with comprehensive security features"""
    try:
        if request.method == 'POST':
            # Get credentials from form or JSON
            username_or_email = request.form.get('username') or (request.json and request.json.get('username'))
            password = request.form.get('password') or (request.json and request.json.get('password'))
            
            # Sanitize input
            username_or_email = sanitize_input(username_or_email, 120) if username_or_email else None
            
            if not username_or_email or not password:
                msg = 'Username/email and password are required'
                if request.is_json:
                    return jsonify({'status': 'error', 'message': msg}), 400
                flash(msg, 'warning')
                return render_template('modules/auth/login.html')
            
            # Find user by username or email
            user = User.query.filter(
                (User.username == username_or_email) | (User.email == username_or_email)
            ).first()
            
            if user and user.check_password(password):
                # Check if account is locked out
                if user.is_locked_out():
                    # Log failed login attempt
                    try:
                        failed_login = FailedLogin(
                            username_or_email=username_or_email,
                            ip_address=request.remote_addr,
                            user_agent=request.user_agent.string if request.user_agent else None,
                            reason='account_locked'
                        )
                        db.session.add(failed_login)
                        db.session.commit()
                    except Exception as e:
                        logger.error(f"Failed to log failed login attempt: {e}")

                    msg = 'Account is temporarily locked due to multiple failed login attempts. Please try again later.'
                    if request.is_json:
                        return jsonify({'status': 'error', 'message': msg}), 423
                    flash(msg, 'warning')
                    return render_template('modules/auth/login.html')
                
                # Check if account is active
                if not user.is_active:
                    # Log failed login attempt
                    try:
                        failed_login = FailedLogin(
                            username_or_email=username_or_email,
                            ip_address=request.remote_addr,
                            user_agent=request.user_agent.string if request.user_agent else None,
                            reason='account_inactive'
                        )
                        db.session.add(failed_login)
                        db.session.commit()
                    except Exception as e:
                        logger.error(f"Failed to log failed login attempt: {e}")

                    msg = 'Account is deactivated. Please contact an administrator.'
                    if request.is_json:
                        return jsonify({'status': 'error', 'message': msg}), 403
                    flash(msg, 'warning')
                    return render_template('modules/auth/login.html')
                
                # Check if 2FA is enabled
                if user.totp_enabled:
                    # Store user ID in session for 2FA verification
                    session['2fa_user_id'] = str(user.id)
                    session['2fa_remember'] = request.form.get('remember') == 'on'
                    session['2fa_next'] = request.args.get('next')
                    
                    # Redirect to 2FA verification page
                    return redirect(url_for('auth.verify_2fa'))
                
                # No 2FA - proceed with normal login
                user.last_login = datetime.utcnow()
                user.last_activity = datetime.utcnow()
                user.reset_failed_login()  # Reset failed login attempts
                
                # Check for remember me
                remember_me = request.form.get('remember') == 'on'
                
                # Create session tracking
                session_token = generate_secure_token(32)
                user_session = UserSession.create_session(
                    user_id=user.id,
                    session_token=session_token,
                    request=request,
                    remember_me=remember_me
                )
                db.session.add(user_session)
                db.session.commit()
                
                # Store session token in Flask session
                session['session_token'] = session_token
                session['session_id'] = str(user_session.id)
                
                # Login user with Flask-Login
                login_user(user, remember=remember_me)
                
                logger.info(f"User {user.username} logged in successfully from {request.remote_addr}")
                
                # Redirect to dashboard or next page
                next_page = request.args.get('next')
                if next_page:
                    return redirect(next_page)
                
                return redirect(url_for('main.index'))
            
            else:
                # Failed login - increment failed attempts
                if user:
                    user.increment_failed_login()
                    db.session.commit()
                
                # Log failed login attempt
                try:
                    failed_login = FailedLogin(
                        username_or_email=username_or_email,
                        ip_address=request.remote_addr,
                        user_agent=request.user_agent.string if request.user_agent else None,
                        reason='invalid_credentials'
                    )
                    db.session.add(failed_login)
                    db.session.commit()
                except Exception as e:
                    logger.error(f"Failed to log failed login attempt: {e}")
                
                msg = 'Invalid credentials'
                if request.is_json:
                    return jsonify({'status': 'error', 'message': msg}), 401
                flash(msg, 'danger')
        
        return render_template('modules/auth/login.html')
    
    except Exception as e:
        logger.exception('Error in login route')
        db.session.rollback()
        if request.is_json or request.accept_mimetypes['application/json']:
            return jsonify({'status': 'error', 'message': 'Internal server error'}), 500
        return render_template('errors/500.html'), 500


@auth_bp.route('/logout')
@login_required
def logout():
    """User logout endpoint"""
    try:
        # Revoke current session
        session_token = session.get('session_token')
        if session_token:
            user_session = UserSession.query.filter_by(session_token=session_token).first()
            if user_session:
                user_session.revoke()
                db.session.commit()
        
        # Clear Flask session
        session.clear()
        
        # Logout user
        logout_user()
        flash('You have been logged out successfully.', 'info')
        return redirect(url_for('auth.login'))
    except Exception as e:
        logger.exception('Error in logout route')
        return render_template('errors/500.html'), 500


@auth_bp.route('/register', methods=['GET', 'POST'])
@csrf.exempt
def register():
    """User registration endpoint with comprehensive validation"""
    try:
        if request.method == 'POST':
            # Get form data
            username = sanitize_input(request.form.get('username', '').strip(), 64)
            email = sanitize_input(request.form.get('email', '').strip().lower(), 120)
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            firstname = sanitize_input(request.form.get('firstname', '').strip(), 64)
            lastname = sanitize_input(request.form.get('lastname', '').strip(), 64)
            
            # Validation
            if not all([username, email, password, confirm_password]):
                flash('All required fields must be filled', 'warning')
                return render_template('modules/auth/register.html', 
                                      username=username, email=email, firstname=firstname, lastname=lastname)
            
            # Username validation
            if len(username) < 3 or len(username) > 64:
                flash('Username must be between 3 and 64 characters', 'warning')
                return render_template('modules/auth/register.html', 
                                      username=username, email=email, firstname=firstname, lastname=lastname)
            
            # Email validation
            if not validate_email_format(email):
                flash('Please enter a valid email address', 'warning')
                return render_template('modules/auth/register.html', 
                                      username=username, email=email, firstname=firstname, lastname=lastname)
            
            # Password validation
            if password != confirm_password:
                flash('Passwords do not match', 'warning')
                return render_template('modules/auth/register.html', 
                                      username=username, email=email, firstname=firstname, lastname=lastname)
            
            is_valid, message = validate_password_strength(password)
            if not is_valid:
                flash(message, 'warning')
                return render_template('modules/auth/register.html', 
                                      username=username, email=email, firstname=firstname, lastname=lastname)
            
            # Check if username already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'warning')
                return render_template('modules/auth/register.html', 
                                      username=username, email=email, firstname=firstname, lastname=lastname)
            
            # Check if email already exists
            if User.query.filter_by(email=email).first():
                flash('Email already exists', 'warning')
                return render_template('modules/auth/register.html', 
                                      username=username, email=email, firstname=firstname, lastname=lastname)
            
            # Create new user
            user = User(
                username=username,
                email=email,
                firstname=firstname,
                lastname=lastname,
                display_name=f"{firstname} {lastname}".strip() if firstname or lastname else username,
                email_verified=False  # Require email verification
            )
            user.set_password(password)
            
            # Generate email verification token
            user.email_verification_token = generate_secure_token(32)
            user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
            
            db.session.add(user)
            db.session.commit()
            
            # Send verification email
            try:
                verification_url = url_for(
                    'auth.verify_email',
                    token=user.email_verification_token,
                    _external=True
                )
                
                email_service.send_template_email(
                    to_email=user.email,
                    subject='Verify Your Email Address',
                    template_name='verify_email',
                    template_data={
                        'user_name': user.get_full_name(),
                        'verification_url': verification_url,
                        'app_name': current_app.config.get('APP_NAME', 'Application'),
                        'base_url': request.url_root.rstrip('/'),
                        'expiry_hours': 24,
                        'year': datetime.utcnow().year
                    }
                )
                logger.info(f"Verification email sent to {user.email}")
            except Exception as e:
                logger.exception(f"Failed to send verification email: {e}")
            
            flash('Registration successful! Please check your email to verify your account.', 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('modules/auth/register.html')
    
    except Exception as e:
        logger.exception('Error in register route')
        db.session.rollback()
        flash('An error occurred during registration. Please try again.', 'danger')
        return render_template('modules/auth/register.html'), 500


@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
@csrf.exempt
def forgot_password():
    """Password reset request endpoint"""
    try:
        if request.method == 'POST':
            email = sanitize_input(request.form.get('email', '').strip().lower(), 120)
            
            if not email or not validate_email_format(email):
                flash('Please enter a valid email address', 'warning')
                return render_template('modules/auth/forgot_password.html')
            
            user = User.query.filter_by(email=email).first()
            if user and user.is_active:
                # Generate password reset token
                user.password_reset_token = generate_secure_token(32)
                user.password_reset_expires = datetime.utcnow() + timedelta(hours=1)
                db.session.commit()
                
                # Send password reset email
                try:
                    reset_url = url_for(
                        'auth.reset_password',
                        token=user.password_reset_token,
                        _external=True
                    )
                    
                    email_service.send_template_email(
                        to_email=user.email,
                        subject='Reset Your Password',
                        template_name='password_reset',
                        template_data={
                            'user_name': user.get_full_name(),
                            'reset_url': reset_url,
                            'app_name': current_app.config.get('APP_NAME', 'Application'),
                            'base_url': request.url_root.rstrip('/'),
                            'expiry_hours': 1,
                            'year': datetime.utcnow().year
                        }
                    )
                    logger.info(f"Password reset email sent to {user.email}")
                except Exception as e:
                    logger.exception(f"Failed to send password reset email: {e}")
            
            # Always show success message for security (don't reveal if email exists)
            flash('If an account with that email exists, a password reset link has been sent.', 'info')
            return redirect(url_for('auth.login'))
        
        return render_template('modules/auth/forgot_password.html')
    
    except Exception as e:
        logger.exception('Error in forgot_password route')
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        return render_template('modules/auth/forgot_password.html'), 500


@auth_bp.route('/reset-password/<token>', methods=['GET', 'POST'])
@csrf.exempt
def reset_password(token):
    """Password reset with token endpoint"""
    try:
        user = User.query.filter_by(password_reset_token=token).first()
        
        if not user or not user.password_reset_expires or datetime.utcnow() > user.password_reset_expires:
            flash('Invalid or expired password reset token', 'danger')
            return redirect(url_for('auth.forgot_password'))
        
        if request.method == 'POST':
            password = request.form.get('password')
            confirm_password = request.form.get('confirm_password')
            
            if password != confirm_password:
                flash('Passwords do not match', 'warning')
                return render_template('modules/auth/reset_password.html', token=token)
            
            is_valid, message = validate_password_strength(password)
            if not is_valid:
                flash(message, 'warning')
                return render_template('modules/auth/reset_password.html', token=token)
            
            # Update password and clear reset token
            user.set_password(password)
            user.password_reset_token = None
            user.password_reset_expires = None
            user.reset_failed_login()  # Reset failed login attempts
            db.session.commit()
            
            flash('Password reset successful! Please log in with your new password.', 'success')
            return redirect(url_for('auth.login'))
        
        return render_template('modules/auth/reset_password.html', token=token)
    
    except Exception as e:
        logger.exception('Error in reset_password route')
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        return render_template('modules/auth/reset_password.html', token=token), 500


@auth_bp.route('/verify-email/<token>')
@csrf.exempt
def verify_email(token):
    """Email verification endpoint"""
    try:
        user = User.query.filter_by(email_verification_token=token).first()
        
        if not user:
            flash('Invalid verification link', 'danger')
            return redirect(url_for('auth.login'))
        
        if not user.email_verification_expires or datetime.utcnow() > user.email_verification_expires:
            flash('Verification link has expired. Please request a new one.', 'warning')
            return redirect(url_for('auth.resend_verification', email=user.email))
        
        # Verify email
        user.email_verified = True
        user.email_verification_token = None
        user.email_verification_expires = None
        db.session.commit()
        
        # Send welcome email
        try:
            dashboard_url = url_for('main.index', _external=True)
            
            email_service.send_template_email(
                to_email=user.email,
                subject='Welcome to ' + current_app.config.get('APP_NAME', 'Application'),
                template_name='welcome',
                template_data={
                    'user_name': user.get_full_name(),
                    'dashboard_url': dashboard_url,
                    'app_name': current_app.config.get('APP_NAME', 'Application'),
                    'base_url': request.url_root.rstrip('/'),
                    'year': datetime.utcnow().year
                }
            )
            logger.info(f"Welcome email sent to {user.email}")
        except Exception as e:
            logger.exception(f"Failed to send welcome email: {e}")
        
        flash('Email verified successfully! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    except Exception as e:
        logger.exception('Error in verify_email route')
        db.session.rollback()
        flash('An error occurred during verification. Please try again.', 'danger')
        return redirect(url_for('auth.login')), 500


@auth_bp.route('/resend-verification', methods=['GET', 'POST'])
@csrf.exempt
def resend_verification():
    """Resend email verification link"""
    try:
        if request.method == 'POST':
            email = sanitize_input(request.form.get('email', '').strip().lower(), 120)
            
            if not email or not validate_email_format(email):
                flash('Please enter a valid email address', 'warning')
                return render_template('modules/auth/resend_verification.html')
            
            user = User.query.filter_by(email=email).first()
            if user and not user.email_verified:
                # Generate new verification token
                user.email_verification_token = generate_secure_token(32)
                user.email_verification_expires = datetime.utcnow() + timedelta(hours=24)
                db.session.commit()
                
                # Send verification email
                try:
                    verification_url = url_for(
                        'auth.verify_email',
                        token=user.email_verification_token,
                        _external=True
                    )
                    
                    email_service.send_template_email(
                        to_email=user.email,
                        subject='Verify Your Email Address',
                        template_name='verify_email',
                        template_data={
                            'user_name': user.get_full_name(),
                            'verification_url': verification_url,
                            'app_name': current_app.config.get('APP_NAME', 'Application'),
                            'base_url': request.url_root.rstrip('/'),
                            'expiry_hours': 24,
                            'year': datetime.utcnow().year
                        }
                    )
                    logger.info(f"Verification email resent to {user.email}")
                except Exception as e:
                    logger.exception(f"Failed to send verification email: {e}")
            
            # Always show success message for security
            flash('If an unverified account exists with that email, a verification link has been sent.', 'info')
            return redirect(url_for('auth.login'))
        
        email = request.args.get('email', '')
        return render_template('modules/auth/resend_verification.html', email=email)
    
    except Exception as e:
        logger.exception('Error in resend_verification route')
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        return render_template('modules/auth/resend_verification.html'), 500


@auth_bp.route('/verify-2fa', methods=['GET', 'POST'])
@csrf.exempt
def verify_2fa():
    """Verify two-factor authentication code"""
    try:
        from app.services.totp_service import totp_service
        
        # Check if 2FA verification is required
        user_id = session.get('2fa_user_id')
        if not user_id:
            flash('Please log in first', 'warning')
            return redirect(url_for('auth.login'))
        
        user = User.query.get(user_id)
        if not user or not user.totp_enabled:
            session.pop('2fa_user_id', None)
            flash('2FA verification not required', 'info')
            return redirect(url_for('auth.login'))
        
        if request.method == 'POST':
            token = request.form.get('token', '').strip()
            use_backup = request.form.get('use_backup') == '1'
            
            if not token:
                flash('Please enter a verification code', 'warning')
                return render_template('modules/auth/verify_2fa.html', user=user)
            
            verified = False
            
            if use_backup:
                # Verify backup code
                if user.backup_codes:
                    is_valid, matched_hash = totp_service.verify_backup_code(token, user.backup_codes)
                    if is_valid:
                        # Remove used backup code
                        user.backup_codes.remove(matched_hash)
                        db.session.commit()
                        verified = True
                        flash('Backup code used successfully. Please generate new backup codes.', 'warning')
            else:
                # Verify TOTP token
                verified = totp_service.verify_token(user.totp_secret, token)
            
            if verified:
                # Complete login process
                user.last_login = datetime.utcnow()
                user.last_activity = datetime.utcnow()
                user.reset_failed_login()
                
                # Get remember me preference
                remember_me = session.get('2fa_remember', False)
                
                # Create session tracking
                session_token = generate_secure_token(32)
                user_session = UserSession.create_session(
                    user_id=user.id,
                    session_token=session_token,
                    request=request,
                    remember_me=remember_me
                )
                db.session.add(user_session)
                db.session.commit()
                
                # Store session token
                session['session_token'] = session_token
                session['session_id'] = str(user_session.id)
                
                # Clear 2FA session data
                next_page = session.pop('2fa_next', None)
                session.pop('2fa_user_id', None)
                session.pop('2fa_remember', None)
                
                # Login user
                login_user(user, remember=remember_me)
                
                logger.info(f"User {user.username} logged in with 2FA from {request.remote_addr}")
                
                flash('Successfully logged in with 2FA', 'success')
                return redirect(next_page or url_for('main.index'))
            else:
                flash('Invalid verification code. Please try again.', 'danger')
                return render_template('modules/auth/verify_2fa.html', user=user)
        
        return render_template('modules/auth/verify_2fa.html', user=user)
    
    except Exception as e:
        logger.exception('Error in verify_2fa route')
        db.session.rollback()
        flash('An error occurred during verification', 'danger')
        return redirect(url_for('auth.login')), 500


@auth_bp.route('/two-steps', methods=['GET', 'POST'])
@csrf.exempt
@login_required
def two_steps():
    """
    Two-step verification page.
    NOTE: This is a UI-only implementation for now; it validates a 6-digit code but
    does not yet integrate with an actual 2FA backend.
    """
    try:
        # Derive a masked email for display if possible
        masked_email = None
        if current_user.is_authenticated and current_user.email:
            email = current_user.email
            try:
                local, domain = email.split('@', 1)
                if len(local) > 2:
                    masked_local = local[0] + '***' + local[-1]
                else:
                    masked_local = local[0] + '***'
                masked_email = f'{masked_local}@{domain}'
            except ValueError:
                masked_email = email

        if request.method == 'POST':
            # Collect 6 individual digits
            digits = [request.form.get(f'code_{i}', '').strip() for i in range(6)]
            code = ''.join(digits)

            if len(code) != 6 or not code.isdigit():
                flash('Please enter a valid 6-digit verification code.', 'warning')
                return render_template('modules/auth/two_steps.html', masked_email=masked_email)

            # Placeholder success behaviour
            flash('Two-step verification successful.', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('main.index'))

        return render_template('modules/auth/two_steps.html', masked_email=masked_email)

    except Exception:
        logger.exception('Error in two_steps route')
        db.session.rollback()
        flash('An error occurred. Please try again.', 'danger')
        return render_template('modules/auth/two_steps.html'), 500


# ============================================================================
# OAuth Routes
# ============================================================================

@auth_bp.route('/oauth/<provider>')
@csrf.exempt
def oauth_login(provider):
    """
    Initiate OAuth login flow
    
    Args:
        provider: OAuth provider name (google, microsoft, github)
    """
    try:
        # Check if provider is configured
        if not oauth_service.is_provider_configured(provider):
            flash(f'{provider.title()} OAuth is not configured', 'warning')
            return redirect(url_for('auth.login'))
        
        # Get OAuth client
        oauth_client = oauth_service.get_provider(provider)
        
        # Generate redirect URI
        redirect_uri = oauth_service.get_redirect_uri(provider)
        
        # Store next URL in session
        next_url = request.args.get('next')
        if next_url:
            session['oauth_next'] = next_url
        
        # Redirect to provider's authorization page
        return oauth_client.authorize_redirect(redirect_uri)
    
    except Exception as e:
        logger.exception(f'Error initiating {provider} OAuth')
        flash('An error occurred during OAuth login', 'danger')
        return redirect(url_for('auth.login'))


@auth_bp.route('/oauth/<provider>/callback')
@csrf.exempt
def oauth_callback(provider):
    """
    Handle OAuth callback from provider
    
    Args:
        provider: OAuth provider name (google, microsoft, github)
    """
    try:
        # Check if provider is configured
        if not oauth_service.is_provider_configured(provider):
            flash(f'{provider.title()} OAuth is not configured', 'warning')
            return redirect(url_for('auth.login'))
        
        # Get OAuth client
        oauth_client = oauth_service.get_provider(provider)
        
        # Get access token
        try:
            token = oauth_client.authorize_access_token()
        except Exception as e:
            logger.error(f'OAuth token error for {provider}: {e}')
            flash('OAuth authentication failed. Please try again.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Get user info from provider
        if provider == 'google':
            user_info = oauth_client.get('https://www.googleapis.com/oauth2/v3/userinfo').json()
        elif provider == 'microsoft':
            user_info = oauth_client.get('https://graph.microsoft.com/v1.0/me').json()
        elif provider == 'github':
            user_info = oauth_client.get('https://api.github.com/user').json()
            # GitHub requires separate call for email if not public
            if not user_info.get('email'):
                emails = oauth_client.get('https://api.github.com/user/emails').json()
                primary_email = next((e['email'] for e in emails if e['primary']), None)
                if primary_email:
                    user_info['email'] = primary_email
        else:
            flash('Unsupported OAuth provider', 'danger')
            return redirect(url_for('auth.login'))
        
        # Normalize user info
        normalized_info = oauth_service.normalize_user_info(provider, user_info)
        
        if not normalized_info.get('id') or not normalized_info.get('email'):
            flash('Could not retrieve user information from OAuth provider', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if OAuth account exists
        oauth_account = OAuthAccount.find_by_provider(provider, normalized_info['id'])
        
        if oauth_account:
            # Existing OAuth account - log in user
            user = oauth_account.user
            
            # Check if account is active
            if not user.is_active:
                flash('Account is deactivated. Please contact an administrator.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Update OAuth account info
            oauth_account.update_tokens(
                access_token=token.get('access_token'),
                refresh_token=token.get('refresh_token'),
                expires_at=None  # Calculate from expires_in if needed
            )
            oauth_account.update_profile(
                email=normalized_info.get('email'),
                name=normalized_info.get('name'),
                picture=normalized_info.get('picture'),
                data=user_info
            )
            oauth_account.mark_used()
            
            # Update user activity
            user.last_login = datetime.utcnow()
            user.last_activity = datetime.utcnow()
            
            # Create session tracking
            remember_me = True  # OAuth logins are remembered by default
            session_token = generate_secure_token(32)
            user_session = UserSession.create_session(
                user_id=user.id,
                session_token=session_token,
                request=request,
                remember_me=remember_me
            )
            db.session.add(user_session)
            db.session.commit()
            
            # Store session token
            session['session_token'] = session_token
            session['session_id'] = str(user_session.id)
            
            # Login user
            login_user(user, remember=remember_me)
            
            logger.info(f"User {user.username} logged in via {provider} OAuth")
            
            flash(f'Successfully logged in with {provider.title()}!', 'success')
            
            # Redirect to next page or dashboard
            next_page = session.pop('oauth_next', None)
            return redirect(next_page or url_for('main.index'))
        
        else:
            # New OAuth account - check if user exists by email
            user = User.query.filter_by(email=normalized_info['email']).first()
            
            if user:
                # User exists - link OAuth account
                if not user.is_active:
                    flash('Account is deactivated. Please contact an administrator.', 'warning')
                    return redirect(url_for('auth.login'))
                
                # Create OAuth account link
                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=normalized_info['id'],
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token'),
                    provider_email=normalized_info.get('email'),
                    provider_name=normalized_info.get('name'),
                    provider_picture=normalized_info.get('picture'),
                    provider_data=user_info,
                    last_used_at=datetime.utcnow()
                )
                db.session.add(oauth_account)
                
                # Update user activity
                user.last_login = datetime.utcnow()
                user.last_activity = datetime.utcnow()
                
                # If email from OAuth is verified, mark user email as verified
                if normalized_info.get('email_verified') and not user.email_verified:
                    user.email_verified = True
                    user.email_verification_token = None
                    user.email_verification_expires = None
                
                # Create session tracking
                remember_me = True
                session_token = generate_secure_token(32)
                user_session = UserSession.create_session(
                    user_id=user.id,
                    session_token=session_token,
                    request=request,
                    remember_me=remember_me
                )
                db.session.add(user_session)
                db.session.commit()
                
                # Store session token
                session['session_token'] = session_token
                session['session_id'] = str(user_session.id)
                
                # Login user
                login_user(user, remember=remember_me)
                
                logger.info(f"OAuth account linked and user {user.username} logged in via {provider}")
                
                flash(f'{provider.title()} account linked successfully!', 'success')
                
                # Redirect to next page or dashboard
                next_page = session.pop('oauth_next', None)
                return redirect(next_page or url_for('main.index'))
            
            else:
                # New user - create account
                # Generate username from email
                username = normalized_info['email'].split('@')[0]
                base_username = username
                counter = 1
                while User.query.filter_by(username=username).first():
                    username = f"{base_username}{counter}"
                    counter += 1
                
                # Create new user
                user = User(
                    username=username,
                    email=normalized_info['email'],
                    firstname=normalized_info.get('name', '').split()[0] if normalized_info.get('name') else '',
                    lastname=' '.join(normalized_info.get('name', '').split()[1:]) if normalized_info.get('name') and len(normalized_info.get('name', '').split()) > 1 else '',
                    email_verified=normalized_info.get('email_verified', True),  # OAuth emails are usually verified
                    is_active=True,
                    profile_photo=normalized_info.get('picture')
                )
                
                # Set a random password (user won't use it, they'll use OAuth)
                user.set_password(generate_secure_token(32))
                
                db.session.add(user)
                db.session.flush()  # Get user ID
                
                # Create OAuth account link
                oauth_account = OAuthAccount(
                    user_id=user.id,
                    provider=provider,
                    provider_user_id=normalized_info['id'],
                    access_token=token.get('access_token'),
                    refresh_token=token.get('refresh_token'),
                    provider_email=normalized_info.get('email'),
                    provider_name=normalized_info.get('name'),
                    provider_picture=normalized_info.get('picture'),
                    provider_data=user_info,
                    last_used_at=datetime.utcnow()
                )
                db.session.add(oauth_account)
                
                # Create session tracking
                remember_me = True
                session_token = generate_secure_token(32)
                user_session = UserSession.create_session(
                    user_id=user.id,
                    session_token=session_token,
                    request=request,
                    remember_me=remember_me
                )
                db.session.add(user_session)
                db.session.commit()
                
                # Store session token
                session['session_token'] = session_token
                session['session_id'] = str(user_session.id)
                
                # Login user
                login_user(user, remember=remember_me)
                
                logger.info(f"New user {user.username} created and logged in via {provider} OAuth")
                
                # Send welcome email
                try:
                    email_service.send_template_email(
                        to_email=user.email,
                        subject='Welcome to ' + current_app.config.get('APP_NAME', 'Application'),
                        template_name='welcome',
                        template_data={
                            'user': user,
                            'app_name': current_app.config.get('APP_NAME', 'Application'),
                            'login_url': url_for('auth.login', _external=True)
                        }
                    )
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {e}")
                
                flash(f'Account created successfully! Welcome!', 'success')
                
                # Redirect to next page or dashboard
                next_page = session.pop('oauth_next', None)
                return redirect(next_page or url_for('main.index'))
    
    except Exception as e:
        logger.exception(f'Error in {provider} OAuth callback')
        db.session.rollback()
        flash('An error occurred during OAuth authentication', 'danger')
        return redirect(url_for('auth.login'))
