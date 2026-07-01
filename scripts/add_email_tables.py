"""
Add Email Tables Migration
Creates tables for email logging and preferences (PostgreSQL only).
Loads DB_* from .env (same as the app).
"""

import os
import sys

# Add parent directory to path and load .env before any app imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
os.chdir(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from dotenv import load_dotenv
load_dotenv()

def run_migration():
    """Run the migration to add email tables (PostgreSQL only)."""
    db_type = os.environ.get('DB_TYPE', 'sqlite')
    if db_type != 'postgresql':
        print("This script creates PostgreSQL tables. Set DB_TYPE=postgresql and DB_* in .env, then run again.")
        sys.exit(1)

    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    host = os.environ.get('DB_HOST', 'localhost')
    port = int(os.environ.get('DB_PORT', '5432'))
    database = os.environ.get('DB_NAME', '')
    user = os.environ.get('DB_USER', '')
    password = os.environ.get('DB_PASSWORD', '')
    if not all([database, user, password]):
        print("Set DB_NAME, DB_USER, and DB_PASSWORD in .env (and optionally DB_HOST, DB_PORT).")
        sys.exit(1)

    conn = psycopg2.connect(
        host=host,
        port=port,
        database=database,
        user=user,
        password=password
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = conn.cursor()
    
    try:
        print("Creating email schema and tables...")
        
        # Create emails schema (operational email data; user preferences stay in auth)
        cursor.execute("CREATE SCHEMA IF NOT EXISTS emails;")
        print("✓ emails schema created")
        
        # Create email_logs table in emails schema
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS emails.email_logs (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                to_email VARCHAR(255) NOT NULL,
                from_email VARCHAR(255),
                subject VARCHAR(500) NOT NULL,
                template VARCHAR(100),
                status VARCHAR(20) NOT NULL,
                error_message TEXT,
                task_id VARCHAR(100),
                sent_at TIMESTAMP,
                delivered_at TIMESTAMP,
                opened_at TIMESTAMP,
                clicked_at TIMESTAMP,
                bounced_at TIMESTAMP,
                provider VARCHAR(50),
                provider_message_id VARCHAR(255),
                user_id UUID REFERENCES auth.users(id) ON DELETE SET NULL,
                ip_address VARCHAR(45),
                user_agent VARCHAR(500),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✓ emails.email_logs table created")
        
        # Create email_preferences table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS auth.email_preferences (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                user_id UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE UNIQUE,
                marketing_emails BOOLEAN DEFAULT TRUE,
                product_updates BOOLEAN DEFAULT TRUE,
                newsletter BOOLEAN DEFAULT TRUE,
                order_notifications BOOLEAN DEFAULT TRUE,
                account_notifications BOOLEAN DEFAULT TRUE,
                security_alerts BOOLEAN DEFAULT TRUE,
                email_frequency VARCHAR(20) DEFAULT 'immediate',
                unsubscribed_all BOOLEAN DEFAULT FALSE,
                unsubscribed_at TIMESTAMP,
                unsubscribe_token VARCHAR(100) UNIQUE,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        print("✓ email_preferences table created")
        
        # Create indexes
        print("\nCreating indexes...")
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_logs_to_email 
            ON emails.email_logs(to_email);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_logs_status 
            ON emails.email_logs(status);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_logs_task_id 
            ON emails.email_logs(task_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_logs_user_id 
            ON emails.email_logs(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_logs_created_at 
            ON emails.email_logs(created_at);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_preferences_user_id 
            ON auth.email_preferences(user_id);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_email_preferences_token 
            ON auth.email_preferences(unsubscribe_token);
        """)
        
        print("✓ Indexes created for all email tables")
        
        # Create trigger for updated_at
        cursor.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = CURRENT_TIMESTAMP;
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_email_logs_updated_at ON emails.email_logs;
            CREATE TRIGGER update_email_logs_updated_at
                BEFORE UPDATE ON emails.email_logs
                FOR EACH ROW
                EXECUTE PROCEDURE update_updated_at_column();
        """)
        
        cursor.execute("""
            DROP TRIGGER IF EXISTS update_email_preferences_updated_at ON auth.email_preferences;
            CREATE TRIGGER update_email_preferences_updated_at
                BEFORE UPDATE ON auth.email_preferences
                FOR EACH ROW
                EXECUTE PROCEDURE update_updated_at_column();
        """)
        
        print("✓ Triggers created for updated_at columns")
        
        print("\n" + "="*60)
        print("✓ Email tables migration completed successfully!")
        print("="*60)
        print("\nTables created:")
        print("  - emails.email_logs")
        print("  - auth.email_preferences")
        print("\nIndexes created for performance")
        print("Triggers created for automatic timestamp updates")
        
    except Exception as e:
        print(f"\n✗ Error during migration: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    run_migration()
