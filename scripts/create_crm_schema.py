"""
Create CRM Schema and Tables
Creates the CRM schema and all required tables for the CRM module
"""

import sys
import os

# Load environment variables (optional)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app import create_app
from app.extensions.core import db

def create_crm_schema():
    """Create CRM schema and tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create schema
            print("Creating CRM schema...")
            db.session.execute(text('CREATE SCHEMA IF NOT EXISTS crm'))
            db.session.commit()
            print("✅ CRM schema created")
            
            # Try to grant permissions to current user (may fail if user doesn't have grant privileges)
            try:
                result = db.session.execute(text('SELECT current_user'))
                db_user = result.scalar()
                print(f"Attempting to grant permissions to user: {db_user}")
                
                # Grant usage and create privileges
                db.session.execute(text(f'GRANT USAGE ON SCHEMA crm TO {db_user}'))
                db.session.execute(text(f'GRANT CREATE ON SCHEMA crm TO {db_user}'))
                db.session.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA crm GRANT ALL ON TABLES TO {db_user}'))
                db.session.execute(text(f'ALTER DEFAULT PRIVILEGES IN SCHEMA crm GRANT ALL ON SEQUENCES TO {db_user}'))
                db.session.commit()
                print("✅ Permissions granted")
            except Exception as perm_error:
                db.session.rollback()
                print(f"⚠️  Could not grant permissions (this is OK if you're not a superuser): {perm_error}")
                print("\n   To fix this, run the following SQL as postgres superuser:")
                print(f"   GRANT USAGE ON SCHEMA crm TO {db_user};")
                print(f"   GRANT CREATE ON SCHEMA crm TO {db_user};")
                print(f"   ALTER DEFAULT PRIVILEGES IN SCHEMA crm GRANT ALL ON TABLES TO {db_user};")
                print(f"   ALTER DEFAULT PRIVILEGES IN SCHEMA crm GRANT ALL ON SEQUENCES TO {db_user};")
                print("\n   Or use the provided script: scripts/grant_crm_permissions.sql")
            
            # Create all tables
            print("Creating CRM tables...")
            from app.models.crm import (
                Company, Contact, Lead, Deal, Activity, Task, Note,
                Campaign, CampaignRecipient, Segment, CustomField, CustomFieldValue, Tag
            )
            
            # Create tables
            db.create_all()
            db.session.commit()
            print("✅ CRM tables created")
            
            # Create indexes
            print("Creating indexes...")
            
            # Contact indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_contacts_email ON crm.contacts(email);
                CREATE INDEX IF NOT EXISTS idx_contacts_company ON crm.contacts(company_id);
                CREATE INDEX IF NOT EXISTS idx_contacts_owner ON crm.contacts(owner_id);
                CREATE INDEX IF NOT EXISTS idx_contacts_status ON crm.contacts(status);
                CREATE INDEX IF NOT EXISTS idx_contacts_tags ON crm.contacts USING gin(tags);
            """))
            
            # Company indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_companies_name ON crm.companies(name);
                CREATE INDEX IF NOT EXISTS idx_companies_owner ON crm.companies(owner_id);
                CREATE INDEX IF NOT EXISTS idx_companies_industry ON crm.companies(industry);
            """))
            
            # Deal indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_deals_contact ON crm.deals(contact_id);
                CREATE INDEX IF NOT EXISTS idx_deals_company ON crm.deals(company_id);
                CREATE INDEX IF NOT EXISTS idx_deals_owner ON crm.deals(owner_id);
                CREATE INDEX IF NOT EXISTS idx_deals_stage ON crm.deals(stage);
                CREATE INDEX IF NOT EXISTS idx_deals_close_date ON crm.deals(expected_close_date);
            """))
            
            # Activity indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_activities_contact ON crm.activities(contact_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_activities_company ON crm.activities(company_id);
                CREATE INDEX IF NOT EXISTS idx_activities_deal ON crm.activities(deal_id);
                CREATE INDEX IF NOT EXISTS idx_activities_type ON crm.activities(type);
                CREATE INDEX IF NOT EXISTS idx_activities_created_by ON crm.activities(created_by);
                CREATE INDEX IF NOT EXISTS idx_activities_due_date ON crm.activities(due_date) WHERE due_date IS NOT NULL;
            """))
            
            # Task indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON crm.tasks(assigned_to, status);
                CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON crm.tasks(due_date) WHERE status != 'completed';
                CREATE INDEX IF NOT EXISTS idx_tasks_contact ON crm.tasks(contact_id);
            """))
            
            # Lead indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_leads_status ON crm.leads(status);
                CREATE INDEX IF NOT EXISTS idx_leads_assigned ON crm.leads(assigned_to);
                CREATE INDEX IF NOT EXISTS idx_leads_score ON crm.leads(score DESC);
            """))
            
            # Campaign indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_campaigns_status ON crm.campaigns(status);
                CREATE INDEX IF NOT EXISTS idx_campaigns_scheduled ON crm.campaigns(scheduled_at) WHERE status = 'scheduled';
            """))
            
            # Campaign recipient indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_campaign_recipients_campaign ON crm.campaign_recipients(campaign_id);
                CREATE INDEX IF NOT EXISTS idx_campaign_recipients_contact ON crm.campaign_recipients(contact_id);
                CREATE INDEX IF NOT EXISTS idx_campaign_recipients_status ON crm.campaign_recipients(status);
            """))
            
            # Note indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_notes_contact ON crm.notes(contact_id, created_at DESC);
                CREATE INDEX IF NOT EXISTS idx_notes_company ON crm.notes(company_id);
                CREATE INDEX IF NOT EXISTS idx_notes_deal ON crm.notes(deal_id);
            """))
            
            # Segment indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_segments_name ON crm.segments(name);
            """))
            
            # Custom field indexes
            db.session.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_fields_unique ON crm.custom_fields(entity_type, field_name);
            """))
            
            # Custom field value indexes
            db.session.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_field_values_unique ON crm.custom_field_values(field_id, entity_type, entity_id);
                CREATE INDEX IF NOT EXISTS idx_custom_field_values_entity ON crm.custom_field_values(entity_type, entity_id);
            """))
            
            # Tag indexes
            db.session.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_tags_name ON crm.tags(name);
            """))
            
            db.session.commit()
            print("✅ Indexes created")
            
            print("\n🎉 CRM schema and tables created successfully!")
            print("\nTables created:")
            print("  - crm.companies")
            print("  - crm.contacts")
            print("  - crm.leads")
            print("  - crm.deals")
            print("  - crm.activities")
            print("  - crm.tasks")
            print("  - crm.notes")
            print("  - crm.campaigns")
            print("  - crm.campaign_recipients")
            print("  - crm.segments")
            print("  - crm.custom_fields")
            print("  - crm.custom_field_values")
            print("  - crm.tags")
            
        except Exception as e:
            db.session.rollback()
            print(f"❌ Error creating CRM schema: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True

if __name__ == '__main__':
    success = create_crm_schema()
    sys.exit(0 if success else 1)
