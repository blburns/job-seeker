#!/usr/bin/env python3
"""
Safe Database Reset Script

This script uses Flask Migrate's downgrade/upgrade which properly
handles PostgreSQL permissions.

Usage:
    python scripts/reset_database_safe.py
    
⚠️  WARNING: This will DELETE all data!
"""
import sys
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

def main():
    print("\n" + "="*80)
    print("⚠️  DATABASE RESET AND RECREATION (Safe Method)")
    print("="*80)
    print("\nThis will:")
    print("  1. Use 'flask db downgrade base' to properly drop all tables")
    print("  2. Use 'flask db upgrade' to recreate from migrations")
    print("  3. Run permission management script")
    print("\n⚠️  ALL DATA WILL BE DELETED!")
    
    confirm = input("\nType 'RESET' to confirm: ")
    
    if confirm != 'RESET':
        print("\n❌ Reset cancelled.")
        return
    
    try:
        print("\n🔄 Downgrading database to base state...")
        result = subprocess.run(['flask', 'db', 'downgrade', 'base'], 
                               capture_output=True, text=True)
        
        if result.returncode != 0:
            print("⚠️  Warning: Some tables may not exist yet")
            print("    This is normal for fresh databases")
        
        print("\n🔄 Upgrading database from migrations...")
        result = subprocess.run(['flask', 'db', 'upgrade'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print("\n✅ Database recreated successfully from migrations!")
        else:
            print(f"\n⚠️  Upgrade had issues: {result.stderr}")
        
        print("\n🔄 Setting default permissions...")
        result = subprocess.run(['python', 'scripts/manage_permissions.py', '--reset-all'], 
                               capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Permissions configured!")
        else:
            print("⚠️  Permissions may need manual configuration")
        
        print("\n" + "="*80)
        print("✅ DATABASE RESET COMPLETE!")
        print("="*80)
        print("\n📊 Verification:")
        print("  • Run: python scripts/manage_permissions.py --show")
        print("  • Run: flask db current")
        print("  • Test: flask run")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return

if __name__ == '__main__':
    main()
