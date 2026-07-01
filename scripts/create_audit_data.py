#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Create Sample Audit Data
Generate sample audit logs and security events for testing

NOTE: The AuditLog model now uses the pluralized table name 'audit_logs' (see __tablename__ in app.modules.audit.models).
"""

import os
import sys
from datetime import datetime, timedelta
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from app.extensions import db
from app.modules.audit.models import AuditLog, SecurityEvent, EventCategory, EventType
from app.modules.users.models import User

def create_sample_audit_data():
    """Create sample audit logs and security events"""
    with app.app_context():
        print("=== Creating Sample Audit Data ===")
        
        # Get existing users
        users = User.query.all()
        if not users:
            print("ERROR: No users found. Please create users first.")
            return
        
        # Sample IP addresses
        ip_addresses = [
            '192.168.1.100', '192.168.1.101', '192.168.1.102',
            '10.0.0.50', '10.0.0.51', '172.16.0.10',
            '203.0.113.1', '203.0.113.2', '198.51.100.1'
        ]
        
        # Sample event types and categories
        event_types = [
            EventType.LOGIN_SUCCESS, EventType.LOGIN_FAILED, EventType.LOGOUT,
            EventType.PASSWORD_RESET_REQUESTED, EventType.PASSWORD_RESET_COMPLETED,
            EventType.USER_CREATED, EventType.USER_UPDATED, EventType.ACCESS_DENIED,
            EventType.SESSION_CREATED, EventType.SESSION_EXPIRED
        ]
        
        event_categories = [
            EventCategory.AUTHENTICATION, EventCategory.AUTHORIZATION,
            EventCategory.USER_MANAGEMENT, EventCategory.SESSION_MANAGEMENT,
            EventCategory.SECURITY, EventCategory.SYSTEM
        ]
        
        severities = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Create audit logs
        print("Creating audit logs...")
        for i in range(100):
            user = random.choice(users)
            event_type = random.choice(event_types)
            event_category = random.choice(event_categories)
            severity = random.choice(severities)
            ip_address = random.choice(ip_addresses)
            
            # Create timestamp within last 30 days
            days_ago = random.randint(0, 30)
            hours_ago = random.randint(0, 24)
            minutes_ago = random.randint(0, 60)
            timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago, minutes=minutes_ago)
            
            # Determine success based on event type
            success = event_type not in [EventType.LOGIN_FAILED, EventType.ACCESS_DENIED]
            
            log = AuditLog(
                timestamp=timestamp,
                event_type=event_type,
                event_category=event_category,
                user_uuid=user.user_uuid,
                ip_address=ip_address,
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                request_method='POST' if event_type in [EventType.LOGIN_SUCCESS, EventType.LOGIN_FAILED] else 'GET',
                request_url='/auth/' + event_type.lower().replace('_', '-'),
                session_id='session_' + str(random.randint(1000, 9999)),
                description=event_type.replace('_', ' ').title() + ' event for user ' + user.username,
                severity=severity,
                success=success,
                source='web',
                module='auth' if 'login' in event_type.lower() else 'user_management'
            )
            
            db.session.add(log)
        
        # Create security events
        print("Creating security events...")
        security_event_types = [
            'BRUTE_FORCE_ATTEMPT', 'SUSPICIOUS_ACTIVITY', 'ACCOUNT_LOCKED',
            'MULTIPLE_FAILED_LOGINS', 'UNUSUAL_ACCESS_PATTERN', 'IP_BLACKLISTED'
        ]
        
        threat_levels = ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
        
        for i in range(25):
            user = random.choice(users)
            event_type = random.choice(security_event_types)
            threat_level = random.choice(threat_levels)
            severity = threat_level
            ip_address = random.choice(ip_addresses)
            
            # Create timestamp within last 7 days
            days_ago = random.randint(0, 7)
            hours_ago = random.randint(0, 24)
            timestamp = datetime.utcnow() - timedelta(days=days_ago, hours=hours_ago)
            
            # Determine if resolved
            resolved = random.choice([True, False])
            resolved_at = timestamp + timedelta(hours=random.randint(1, 24)) if resolved else None
            
            event = SecurityEvent(
                timestamp=timestamp,
                event_type=event_type,
                user_uuid=user.user_uuid,
                ip_address=ip_address,
                threat_level=threat_level,
                risk_score=random.randint(1, 100),
                severity=severity,
                action_taken='BLOCKED' if threat_level in ['HIGH', 'CRITICAL'] else 'MONITORED',
                blocked=threat_level in ['HIGH', 'CRITICAL'],
                resolved=resolved,
                resolved_at=resolved_at,
                resolved_by=user.user_uuid if resolved else None,
                resolution_notes=('Resolved by ' + user.username) if resolved else None
            )
            
            db.session.add(event)
        
        # Commit all changes
        try:
            db.session.commit()
            print("SUCCESS: Created 100 audit logs and 25 security events")
            print("   Users: " + str(len(users)))
            print("   IP Addresses: " + str(len(ip_addresses)))
            print("   Event Types: " + str(len(event_types)))
            print("   Security Events: " + str(len(security_event_types)))
        except Exception as e:
            db.session.rollback()
            print("ERROR: Error creating sample data: " + str(e))
            return

if __name__ == '__main__':
    create_sample_audit_data() 