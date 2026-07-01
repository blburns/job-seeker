# Troubleshooting Guide

## Common Issues and Solutions

This guide covers common issues you may encounter and how to resolve them.

## Database Issues

### Connection Refused

**Symptoms:**
- `psycopg2.OperationalError: could not connect to server`
- `Connection refused`

**Solutions:**

1. **Check PostgreSQL is running:**
   ```bash
   sudo systemctl status postgresql
   sudo systemctl start postgresql
   ```

2. **Verify connection settings in `.env`:**
   ```env
   DB_HOST=localhost
   DB_PORT=5432
   DB_NAME=your_database
   DB_USER=your_user
   DB_PASSWORD=your_password
   ```

3. **Test connection manually:**
   ```bash
   psql -U your_user -d your_database -h localhost
   ```

4. **Check PostgreSQL configuration:**
   ```bash
   # Check pg_hba.conf allows connections
   sudo nano /etc/postgresql/14/main/pg_hba.conf
   ```

### Permission Denied

**Symptoms:**
- `permission denied for schema`
- `permission denied for table`

**Solutions:**

1. **Grant schema permissions:**
   ```sql
   GRANT USAGE ON SCHEMA schema_name TO your_user;
   GRANT CREATE ON SCHEMA schema_name TO your_user;
   GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA schema_name TO your_user;
   ```

2. **Use superuser for migrations:**
   ```bash
   python3 scripts/migrate_to_schemas.py --confirm --superuser postgres
   ```

3. **Check user permissions:**
   ```sql
   SELECT * FROM pg_user WHERE usename = 'your_user';
   ```

### Table Does Not Exist

**Symptoms:**
- `relation "table_name" does not exist`
- Tables not found after migration

**Solutions:**

1. **Check table exists:**
   ```sql
   SELECT table_schema, table_name 
   FROM information_schema.tables 
   WHERE table_name = 'your_table';
   ```

2. **Verify schema:**
   ```python
   # Check model schema
   print(User.__table__.fullname)  # Should show schema.table
   ```

3. **Run migrations:**
   ```bash
   flask db upgrade
   ```

### Foreign Key Violations

**Symptoms:**
- `foreign key constraint fails`
- `referenced key not found`

**Solutions:**

1. **Check foreign key references:**
   ```sql
   SELECT * FROM information_schema.table_constraints 
   WHERE constraint_type = 'FOREIGN KEY';
   ```

2. **Verify referenced data exists:**
   ```sql
   SELECT * FROM auth.users WHERE id = 'referenced_uuid';
   ```

3. **Check schema qualification:**
   ```python
   # Foreign keys must use schema-qualified names
   db.ForeignKey('auth.users.id')  # Correct
   db.ForeignKey('users.id')       # Wrong (missing schema)
   ```

## Authentication Issues

### Login Not Working

**Symptoms:**
- Login form submits but doesn't authenticate
- Redirects back to login page

**Solutions:**

1. **Check password hash:**
   ```python
   user = User.query.filter_by(username='test').first()
   print(user.check_password('password'))  # Should return True
   ```

2. **Verify account status:**
   ```python
   print(user.is_active)      # Should be True
   print(user.is_locked_out()) # Should be False
   ```

3. **Check Flask-Login:**
   ```python
   # Verify user_loader works
   from app.extensions.initialization import load_user
   user = load_user(user_id)
   ```

4. **Check session:**
   ```python
   # Verify session is created
   from flask import session
   print(session)
   ```

### Password Reset Not Working

**Symptoms:**
- Reset email not received
- Reset link doesn't work

**Solutions:**

1. **Check email configuration:**
   ```env
   MAIL_SERVER=smtp.gmail.com
   MAIL_PORT=587
   MAIL_USERNAME=your-email@gmail.com
   MAIL_PASSWORD=your-app-password
   ```

2. **Verify token:**
   ```python
   user = User.query.filter_by(password_reset_token=token).first()
   if user and datetime.utcnow() < user.password_reset_expires:
       # Token is valid
   ```

3. **Check email service:**
   ```bash
   # Test email sending
   flask test-email
   ```

### Account Locked Out

**Symptoms:**
- "Account is temporarily locked" message
- Cannot login even with correct password

**Solutions:**

1. **Check lockout status:**
   ```python
   user = User.query.filter_by(username='user').first()
   print(user.lockout_until)  # Shows lockout expiration
   ```

2. **Manual reset:**
   ```python
   user.reset_failed_login()
   db.session.commit()
   ```

3. **Wait for expiration:**
   - Lockout expires after 30 minutes

## Application Issues

### Import Errors

**Symptoms:**
- `ModuleNotFoundError: No module named 'app.models'`
- `ImportError: cannot import name 'X'`

**Solutions:**

1. **Verify virtual environment:**
   ```bash
   which python3  # Should show venv path
   source venv/bin/activate
   ```

2. **Reinstall dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Check Python path:**
   ```python
   import sys
   print(sys.path)  # Should include project root
   ```

4. **Verify module structure:**
   ```bash
   ls -la app/models/  # Should show model files
   ```

### Template Not Found

**Symptoms:**
- `TemplateNotFound: modules/users/dashboard.html`
- Template errors

**Solutions:**

1. **Check template exists:**
   ```bash
   ls -la app/templates/modules/users/dashboard.html
   ```

2. **Verify template path:**
   ```python
   # Template should be relative to templates/ directory
   render_template('modules/users/dashboard.html')  # Correct
   ```

3. **Check template inheritance:**
   ```jinja2
   {% extends "base_metronic.html" %}  # Base template must exist
   ```

### Blueprint Not Registered

**Symptoms:**
- `werkzeug.routing.exceptions.BuildError`
- Route not found

**Solutions:**

1. **Check blueprint registration:**
   ```python
   # In app/extensions/blueprints.py
   if HAS_USERS:
       app.register_blueprint(users_bp)
   ```

2. **Verify blueprint import:**
   ```python
   # Check if module exists
   try:
       from app.modules.users import users_bp
   except ImportError as e:
       print(f"Import error: {e}")
   ```

3. **Check route name:**
   ```python
   # Use blueprint prefix
   url_for('users.dashboard')  # Correct
   url_for('dashboard')        # Wrong (missing blueprint)
   ```

## Performance Issues

### Slow Database Queries

**Symptoms:**
- Page loads slowly
- Timeout errors

**Solutions:**

1. **Add database indexes:**
   ```sql
   CREATE INDEX idx_users_email ON auth.users(email);
   CREATE INDEX idx_accounts_name ON accounts.accounts(account_name);
   ```

2. **Optimize queries:**
   ```python
   # Use eager loading
   users = User.query.options(db.joinedload(User.roles)).all()
   ```

3. **Enable query logging:**
   ```env
   SQLALCHEMY_ECHO=True
   ```

4. **Check connection pooling:**
   ```env
   DB_POOL_SIZE=10
   DB_MAX_OVERFLOW=20
   ```

### High Memory Usage

**Symptoms:**
- Server running out of memory
- Application crashes

**Solutions:**

1. **Reduce Gunicorn workers:**
   ```bash
   # In systemd service
   --workers 2  # Reduce from 4
   ```

2. **Enable caching:**
   ```env
   CACHE_TYPE=redis
   REDIS_URL=redis://localhost:6379/0
   ```

3. **Check for memory leaks:**
   ```bash
   # Monitor memory
   htop
   ```

## Schema Migration Issues

### Tables in Wrong Schema

**Symptoms:**
- Tables still in `public` schema
- Models can't find tables

**Solutions:**

1. **Check current schema:**
   ```sql
   SELECT table_schema, table_name 
   FROM information_schema.tables 
   WHERE table_name = 'users';
   ```

2. **Re-run migration:**
   ```bash
   python3 scripts/migrate_to_schemas.py --confirm --superuser postgres
   ```

3. **Verify model schema:**
   ```python
   print(User.__table__.fullname)  # Should be auth.users
   ```

### Foreign Key Errors After Migration

**Symptoms:**
- Foreign key constraints fail
- Cross-schema references broken

**Solutions:**

1. **Verify foreign key syntax:**
   ```python
   # Must use schema-qualified names
   db.ForeignKey('auth.users.id')  # Correct
   ```

2. **Check constraint definitions:**
   ```sql
   SELECT * FROM information_schema.table_constraints 
   WHERE constraint_type = 'FOREIGN KEY';
   ```

3. **Recreate constraints if needed:**
   ```sql
   ALTER TABLE accounts.accounts 
   DROP CONSTRAINT IF EXISTS accounts_created_by_fkey;
   
   ALTER TABLE accounts.accounts 
   ADD CONSTRAINT accounts_created_by_fkey 
   FOREIGN KEY (created_by) REFERENCES auth.users(id);
   ```

## Configuration Issues

### Environment Variables Not Loading

**Symptoms:**
- Default values used instead of `.env` values
- Configuration not applied

**Solutions:**

1. **Check `.env` file location:**
   ```bash
   # Should be in project root
   ls -la .env
   ```

2. **Verify file format:**
   ```env
   # No spaces around =
   DB_TYPE=postgresql  # Correct
   DB_TYPE = postgresql  # Wrong
   ```

3. **Check file permissions:**
   ```bash
   chmod 600 .env
   ```

4. **Restart application:**
   ```bash
   # After changing .env
   sudo systemctl restart boilerplate
   ```

### Secret Key Warnings

**Symptoms:**
- "Using default SECRET_KEY" warnings
- Security warnings in logs

**Solutions:**

1. **Generate new secret key:**
   ```bash
   python3 scripts/generate_secret_key.py
   ```

2. **Update `.env`:**
   ```env
   SECRET_KEY=<generated-key>
   JWT_SECRET_KEY=<different-generated-key>
   ```

3. **Restart application**

## Frontend Issues

### Metronic Components Not Displaying

**Symptoms:**
- Components not styled correctly
- JavaScript not working

**Solutions:**

1. **Check static file paths:**
   ```jinja2
   {{ url_for('static', filename='assets/css/style.css') }}
   ```

2. **Verify Metronic assets:**
   ```bash
   ls -la app/static/assets/
   ```

3. **Check JavaScript loading:**
   ```html
   <!-- Verify scripts are included -->
   {% block extra_js %}{% endblock %}
   ```

## Getting Help

### Debug Mode

Enable debug mode for detailed errors:

```env
FLASK_DEBUG=True
FLASK_ENV=development
```

**Warning:** Never enable in production!

### Log Files

Check these log files:

- Application: `logs/app.log`
- Access: `/var/log/boilerplate/access.log`
- Error: `/var/log/boilerplate/error.log`
- System: `journalctl -u boilerplate -n 100`

### Database Health

```bash
# Check database health
flask db-health

# Or via API
curl http://localhost:5000/health/database
```

### Application Health

```bash
# Check application health
curl http://localhost:5000/health

# Check all health endpoints
curl http://localhost:5000/health/database
curl http://localhost:5000/health/cache
```

## Common Error Messages

### "No filter named 'date'"

**Solution:** Custom filter already added in `template_context.py`. Verify it's registered.

### "Could not build url for endpoint"

**Solution:** Use `safe_url_for()` helper or verify blueprint is registered.

### "permission denied for schema"

**Solution:** Grant schema permissions or use superuser for migrations.

### "relation does not exist"

**Solution:** Check table is in correct schema, run migrations.

## See Also

- [GETTING_STARTED.md](GETTING_STARTED.md) - Initial setup
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration details
- [SCHEMA_MIGRATION.md](SCHEMA_MIGRATION.md) - Database migrations
