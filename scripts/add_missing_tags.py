#!/usr/bin/env python3
"""
Add Missing Version Tags Script
Adds missing git tags for historical releases
"""

import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def create_tag(version, commit_hash, message):
    """Create a git tag for a specific commit"""
    project_root = Path(__file__).parent.parent
    
    # Create annotated tag
    cmd = ["git", "tag", "-a", f"v{version}", commit_hash, "-m", message]
    success, stdout, stderr = run_command(cmd, cwd=project_root)
    
    if success:
        print(f"✅ Created tag v{version} for commit {commit_hash}")
        return True
    else:
        print(f"❌ Failed to create tag v{version}: {stderr}")
        return False

def push_tag(version):
    """Push a tag to remote"""
    project_root = Path(__file__).parent.parent
    
    cmd = ["git", "push", "origin", f"v{version}"]
    success, stdout, stderr = run_command(cmd, cwd=project_root)
    
    if success:
        print(f"✅ Pushed tag v{version} to remote")
        return True
    else:
        print(f"❌ Failed to push tag v{version}: {stderr}")
        return False

def main():
    """Add missing version tags"""
    print("🏷️  Adding missing version tags...")
    
    # Define missing tags with their commit hashes and messages
    missing_tags = [
        {
            "version": "0.3.0",
            "commit": "79e4c5a",  # Merge pull request #8 from blburns/feature/registration-page
            "message": "Release 0.3.0: Enhanced User Management - Registration page, user module updates, and improved UI/UX"
        },
        {
            "version": "0.4.0", 
            "commit": "832b823",  # Merge pull request #19 from blburns/feature/migrate-userid-to-uuid
            "message": "Release 0.4.0: Audit & Logging System - UUID migration, audit logs, security events, and comprehensive monitoring"
        }
    ]
    
    for tag_info in missing_tags:
        version = tag_info["version"]
        commit = tag_info["commit"]
        message = tag_info["message"]
        
        print(f"\n📌 Creating tag v{version}...")
        if create_tag(version, commit, message):
            if push_tag(version):
                print(f"🎉 Successfully created and pushed v{version}")
            else:
                print(f"⚠️  Tag v{version} created but failed to push")
        else:
            print(f"❌ Failed to create tag v{version}")
    
    print("\n🏁 Tag creation process completed!")

if __name__ == "__main__":
    main() 