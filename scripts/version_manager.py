#!/usr/bin/env python3
"""
Version Management Script for Flask Application Boilerplate
Handles version updates, phase transitions, and release management
"""

import sys
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from version import VERSION_INFO, get_roadmap, get_phase_info

class VersionManager:
    """Manages version updates and phase transitions"""
    
    def __init__(self):
        self.project_root = project_root
        self.version_file = self.project_root / "version.py"
        self.readme_file = self.project_root / "README.md"
        self.checklist_file = self.project_root / "docs" / "BOILERPLATE_CHECKLIST.md"
        self.roadmap_file = self.project_root / "docs" / "BOILERPLATE_ROADMAP.md"
    
    def run_git_command(self, command):
        """Run a git command and return the result"""
        try:
            result = subprocess.run(
                command, 
                shell=True, 
                cwd=self.project_root, 
                capture_output=True, 
                text=True, 
                check=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"❌ Git command failed: {e}")
            print(f"Error: {e.stderr}")
            return None
    
    def create_git_tag(self, version, message=None):
        """Create a git tag for the version"""
        if not message:
            phase_info = get_phase_info()
            message = f"Release {version}: {phase_info['phase']}"
        
        # Create annotated tag
        tag_command = f'git tag -a "v{version}" -m "{message}"'
        result = self.run_git_command(tag_command)
        
        if result is not None:
            print(f"✅ Created git tag: v{version}")
            return True
        else:
            print(f"❌ Failed to create git tag: v{version}")
            return False
    
    def push_git_tag(self, version):
        """Push git tag to remote repository"""
        push_command = f'git push origin "v{version}"'
        result = self.run_git_command(push_command)
        
        if result is not None:
            print(f"✅ Pushed git tag to remote: v{version}")
            return True
        else:
            print(f"❌ Failed to push git tag: v{version}")
            return False
    
    def list_git_tags(self):
        """List all git tags"""
        list_command = "git tag -l --sort=-version:refname"
        result = self.run_git_command(list_command)
        
        if result:
            tags = result.split('\n') if result else []
            return [tag for tag in tags if tag.startswith('v')]
        return []
    
    def get_git_commit_hash(self):
        """Get current git commit hash"""
        commit_command = "git rev-parse HEAD"
        result = self.run_git_command(commit_command)
        return result if result else None
    
    def get_git_short_hash(self):
        """Get current git short commit hash"""
        short_command = "git rev-parse --short HEAD"
        result = self.run_git_command(short_command)
        return result if result else None
    
    def get_current_version(self):
        """Get the current version from version.py"""
        with open(self.version_file, 'r') as f:
            content = f.read()
            version_match = re.search(r'__version__ = "([^"]+)"', content)
            return version_match.group(1) if version_match else "0.0.0"
    
    def get_current_phase(self):
        """Get the current phase from version.py"""
        with open(self.version_file, 'r') as f:
            content = f.read()
            phase_match = re.search(r'__phase__ = "([^"]+)"', content)
            return phase_match.group(1) if phase_match else "Unknown"
    
    def update_version(self, new_version, phase, phase_description, status="IN_PROGRESS"):
        """Update version information in version.py"""
        with open(self.version_file, 'r') as f:
            content = f.read()
        
        # Update version
        content = re.sub(r'__version__ = "[^"]+"', f'__version__ = "{new_version}"', content)
        
        # Update phase
        content = re.sub(r'__phase__ = "[^"]+"', f'__phase__ = "{phase}"', content)
        
        # Update phase description
        content = re.sub(r'__phase_description__ = "[^"]+"', f'__phase_description__ = "{phase_description}"', content)
        
        # Update phase status
        content = re.sub(r'__phase_status__ = "[^"]+"', f'__phase_status__ = "{status}"', content)
        
        # Update completion date
        completion_date = datetime.now().strftime("%Y-%m-%d")
        content = re.sub(r'__phase_completion_date__ = "[^"]+"', f'__phase_completion_date__ = "{completion_date}"', content)
        
        # Update VERSION_INFO
        major, minor, patch = new_version.split('.')
        content = re.sub(r'"major": \d+', f'"major": {major}', content)
        content = re.sub(r'"minor": \d+', f'"minor": {minor}', content)
        content = re.sub(r'"patch": \d+', f'"patch": {patch}', content)
        
        with open(self.version_file, 'w') as f:
            f.write(content)
        
        print(f"✅ Updated version to {new_version}")
        print(f"✅ Updated phase to {phase}")
        print(f"✅ Updated status to {status}")
    
    def complete_phase(self, phase_number, create_tag=True, push_tag=False):
        """Mark a phase as completed and prepare for next phase"""
        roadmap = get_roadmap()
        current_version = self.get_current_version()
        
        # First, create a tag for the current completed phase
        if create_tag:
            print(f"🏷️  Creating git tag for completed phase {phase_number}...")
            if not self.create_git_tag(current_version):
                print("⚠️  Warning: Failed to create git tag, continuing anyway...")
            
            if push_tag:
                print(f"📤 Pushing git tag to remote...")
                if not self.push_git_tag(current_version):
                    print("⚠️  Warning: Failed to push git tag, continuing anyway...")
        
        if phase_number == 1:
            # Phase 1 is already complete, prepare for Phase 2
            self.update_version(
                "0.2.0",
                "Phase 2: Core Services & Infrastructure",
                "API Infrastructure, Communication Services, Caching & Performance",
                "IN_PROGRESS"
            )
        elif phase_number == 2:
            self.update_version(
                "0.3.0", 
                "Phase 3: Business Application Modules",
                "Multi-Tenant Architecture, Core Business Modules, Application Templates",
                "IN_PROGRESS"
            )
        elif phase_number == 3:
            self.update_version(
                "0.4.0",
                "Phase 4: Integration Framework", 
                "External System Integration, Integration Management",
                "IN_PROGRESS"
            )
        elif phase_number == 4:
            self.update_version(
                "0.5.0",
                "Phase 5: Advanced Features",
                "Reporting & Analytics, Workflow Automation", 
                "IN_PROGRESS"
            )
        elif phase_number == 5:
            self.update_version(
                "0.6.0",
                "Phase 6: Security & Compliance",
                "Advanced Security, Compliance Features",
                "IN_PROGRESS"
            )
        elif phase_number == 6:
            self.update_version(
                "0.7.0",
                "Phase 7: Testing & Quality Assurance",
                "Comprehensive Testing, Quality Assurance",
                "IN_PROGRESS"
            )
        elif phase_number == 7:
            self.update_version(
                "0.8.0",
                "Phase 8: Deployment & Production",
                "Infrastructure Setup, Production Deployment",
                "IN_PROGRESS"
            )
        elif phase_number == 8:
            self.update_version(
                "0.9.0",
                "Phase 9: Documentation & Training",
                "Comprehensive Documentation, User Guides",
                "IN_PROGRESS"
            )
        elif phase_number == 9:
            self.update_version(
                "1.0.0",
                "Production Ready Release",
                "Complete boilerplate ready for 40+ business applications",
                "COMPLETED"
            )
        else:
            print(f"❌ Invalid phase number: {phase_number}")
            return False
        
        print(f"🎉 Phase {phase_number} completed! Moved to next phase.")
        return True
    
    def show_status(self):
        """Show current version and phase status"""
        current_version = self.get_current_version()
        current_phase = self.get_current_phase()
        
        print("=" * 60)
        print("🚀 FLASK APPLICATION BOILERPLATE - VERSION STATUS")
        print("=" * 60)
        print(f"Current Version: {current_version}")
        print(f"Current Phase: {current_phase}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # Show roadmap
        roadmap = get_roadmap()
        print("\n📋 VERSION ROADMAP:")
        print("-" * 60)
        for version, info in roadmap.items():
            status_icon = "✅" if info["status"] == "COMPLETED" else "🔄" if info["status"] == "IN_PROGRESS" else "⏳"
            print(f"{status_icon} {version}: {info['phase']}")
            print(f"   Status: {info['status']}")
            print(f"   Description: {info['description']}")
            print()
    
    def create_release_notes(self, version):
        """Create release notes for a version"""
        roadmap = get_roadmap()
        if version not in roadmap:
            print(f"❌ Version {version} not found in roadmap")
            return
        
        info = roadmap[version]
        release_notes = f"""# Release Notes - {version}

## {info['phase']}

**Status:** {info['status']}  
**Date:** {datetime.now().strftime('%Y-%m-%d')}

### Description
{info['description']}

### Changes
- [List specific changes and features implemented]

### Breaking Changes
- [List any breaking changes if applicable]

### New Features
- [List new features added]

### Bug Fixes
- [List bug fixes]

### Improvements
- [List improvements and optimizations]

### Documentation
- [List documentation updates]

### Migration Notes
- [List any migration steps required]

---
*Generated by Flask Application Boilerplate Version Manager*
"""
        
        release_notes_file = self.project_root / "docs" / "releases" / f"v{version}.md"
        release_notes_file.parent.mkdir(exist_ok=True)
        
        with open(release_notes_file, 'w') as f:
            f.write(release_notes)
        
        print(f"✅ Created release notes: {release_notes_file}")

def main():
    """Main CLI interface"""
    if len(sys.argv) < 2:
        print("Usage: python version_manager.py <command> [args]")
        print("\nCommands:")
        print("  status                    - Show current version and phase status")
        print("  complete-phase <number>   - Complete a phase and move to next")
        print("  update-version <version>  - Update to specific version")
        print("  release-notes <version>   - Create release notes for version")
        print("  roadmap                   - Show complete version roadmap")
        return
    
    manager = VersionManager()
    command = sys.argv[1]
    
    if command == "status":
        manager.show_status()
    elif command == "complete-phase":
        if len(sys.argv) < 3:
            print("❌ Please specify phase number")
            return
        try:
            phase_number = int(sys.argv[2])
            manager.complete_phase(phase_number)
        except ValueError:
            print("❌ Phase number must be an integer")
    elif command == "update-version":
        if len(sys.argv) < 3:
            print("❌ Please specify version")
            return
        version = sys.argv[2]
        manager.update_version(version, "Custom Version", "Custom phase", "IN_PROGRESS")
    elif command == "release-notes":
        if len(sys.argv) < 3:
            print("❌ Please specify version")
            return
        version = sys.argv[2]
        manager.create_release_notes(version)
    elif command == "roadmap":
        roadmap = get_roadmap()
        print("📋 COMPLETE VERSION ROADMAP:")
        print("=" * 80)
        for version, info in roadmap.items():
            status_icon = "✅" if info["status"] == "COMPLETED" else "🔄" if info["status"] == "IN_PROGRESS" else "⏳"
            print(f"{status_icon} {version}: {info['phase']}")
            print(f"   Status: {info['status']}")
            print(f"   Description: {info['description']}")
            print()
    else:
        print(f"❌ Unknown command: {command}")

if __name__ == "__main__":
    main() 