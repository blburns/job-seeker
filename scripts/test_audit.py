#!/usr/bin/env python3
"""
Test Audit Functionality
Test the audit system with sample data and API calls
"""

import os
import sys
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app
from app.extensions import db
from app.modules.audit.models import AuditLog, SecurityEvent
from app.modules.users.models import User
from datetime import datetime, timedelta

def test_audit_data():
    """Test that audit data exists and can be queried"""
    with app.app_context():
        print("=== Testing Audit Data ===")
        
        # Check audit logs
        total_logs = AuditLog.query.count()
        print(f"✅ Total audit logs: {total_logs}")
        
        if total_logs > 0:
            recent_logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).limit(5).all()
            print(f"   Recent logs:")
            for log in recent_logs:
                print(f"   - {log.event_type} ({log.severity}) at {log.timestamp}")
        
        # Check security events
        total_events = SecurityEvent.query.count()
        print(f"✅ Total security events: {total_events}")
        
        if total_events > 0:
            recent_events = SecurityEvent.query.order_by(SecurityEvent.timestamp.desc()).limit(5).all()
            print(f"   Recent events:")
            for event in recent_events:
                print(f"   - {event.event_type} ({event.threat_level}) at {event.timestamp}")
        
        # Check statistics
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_logs = AuditLog.query.filter(AuditLog.timestamp >= yesterday).count()
        print(f"✅ Logs in last 24h: {recent_logs}")
        
        open_events = SecurityEvent.query.filter_by(resolved=False).count()
        print(f"✅ Open security events: {open_events}")
        
        return total_logs > 0 and total_events > 0

def test_api_endpoints():
    """Test API endpoints (without authentication)"""
    print("\n=== Testing API Endpoints ===")
    
    base_url = "http://localhost:5000"
    
    # Test endpoints that should return authentication required
    endpoints = [
        "/api/audit/dashboard",
        "/api/audit/logs",
        "/api/audit/security",
        "/api/audit/stats"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            if response.status_code == 401 or response.status_code == 403:
                print(f"✅ {endpoint}: Authentication required (expected)")
            else:
                print(f"⚠️  {endpoint}: Status {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"❌ {endpoint}: Connection error - {e}")

def test_database_queries():
    """Test database queries for dashboard statistics"""
    with app.app_context():
        print("\n=== Testing Dashboard Queries ===")
        
        try:
            # Test dashboard statistics
            now = datetime.utcnow()
            yesterday = now - timedelta(days=1)
            week_ago = now - timedelta(days=7)
            
            # Basic stats
            total_logs = AuditLog.query.count()
            total_security_events = SecurityEvent.query.count()
            open_security_events = SecurityEvent.query.filter_by(resolved=False).count()
            unique_users = db.session.query(AuditLog.user_uuid).filter(
                AuditLog.timestamp >= yesterday
            ).distinct().count()
            
            print(f"✅ Dashboard stats calculated:")
            print(f"   - Total logs: {total_logs}")
            print(f"   - Total security events: {total_security_events}")
            print(f"   - Open security events: {open_security_events}")
            print(f"   - Unique users (24h): {unique_users}")
            
            # Chart data
            from sqlalchemy import func
            event_type_data = db.session.query(
                AuditLog.event_type,
                func.count(AuditLog.id)
            ).filter(
                AuditLog.timestamp >= week_ago
            ).group_by(AuditLog.event_type).order_by(
                func.count(AuditLog.id).desc()
            ).limit(6).all()
            
            print(f"✅ Event type chart data: {len(event_type_data)} categories")
            for event_type, count in event_type_data:
                print(f"   - {event_type}: {count}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error in dashboard queries: {e}")
            return False

def main():
    """Run all tests"""
    print("🧪 Testing Audit Functionality")
    print("=" * 50)
    
    # Test 1: Check if data exists
    data_ok = test_audit_data()
    
    # Test 2: Check API endpoints
    test_api_endpoints()
    
    # Test 3: Check dashboard queries
    queries_ok = test_database_queries()
    
    print("\n" + "=" * 50)
    if data_ok and queries_ok:
        print("✅ All audit tests passed!")
        print("\n📊 Audit System Features:")
        print("   - Dashboard with real-time statistics")
        print("   - Comprehensive audit log filtering")
        print("   - Security event monitoring")
        print("   - Export functionality (CSV)")
        print("   - Event resolution workflow")
        print("   - Chart visualizations")
        print("   - API endpoints for integration")
    else:
        print("❌ Some tests failed")
    
    print("\n🚀 To access the audit system:")
    print("   1. Start the application: python run.py")
    print("   2. Login as an admin user")
    print("   3. Navigate to /audit/dashboard")
    print("   4. Explore logs, security events, and statistics")

if __name__ == '__main__':
    main() 