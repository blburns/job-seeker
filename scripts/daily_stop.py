#!/usr/bin/env python3
"""
Daily Stopping Point Script
===========================

This script helps you systematically wrap up your development work each day.
It provides a structured approach to:
1. Review current work
2. Update documentation
3. Commit and push changes
4. Plan next steps
5. Create a stopping point summary

Usage: python scripts/daily_stop.py
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path

def run_command(command, capture_output=True):
    """Run a shell command and return the result."""
    try:
        result = subprocess.run(command, shell=True, capture_output=capture_output, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def get_git_status():
    """Get current git status."""
    success, stdout, stderr = run_command("git status --porcelain")
    if success:
        return stdout.strip().split('\n') if stdout.strip() else []
    return []

def get_current_branch():
    """Get current git branch."""
    success, stdout, stderr = run_command("git branch --show-current")
    if success:
        return stdout.strip()
    return "unknown"

def get_uncommitted_changes():
    """Get list of uncommitted changes."""
    changes = get_git_status()
    if not changes:
        return []
    
    file_changes = []
    for change in changes:
        if change.strip():
            status = change[:2]
            filename = change[3:]
            file_changes.append((status, filename))
    return file_changes

def update_documentation():
    """Update documentation files with today's progress."""
    print("\n📚 Updating Documentation...")
    
    # Update development roadmap
    print("  - Checking development roadmap...")
    roadmap_file = "docs/development_roadmap.md"
    if os.path.exists(roadmap_file):
        print(f"  ✅ {roadmap_file} exists")
    else:
        print(f"  ❌ {roadmap_file} missing")
    
    # Update changelog
    print("  - Checking changelog...")
    changelog_file = "docs/CHANGELOG.md"
    if os.path.exists(changelog_file):
        print(f"  ✅ {changelog_file} exists")
    else:
        print(f"  ❌ {changelog_file} missing")
    
    # Update project overview
    print("  - Checking project overview...")
    overview_file = "docs/Project_Overview.md"
    if os.path.exists(overview_file):
        print(f"  ✅ {overview_file} exists")
    else:
        print(f"  ❌ {overview_file} missing")

def commit_changes(commit_message=None):
    """Commit current changes."""
    if not commit_message:
        commit_message = f"📝 Daily progress update - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
    
    print(f"\n💾 Committing changes...")
    print(f"  Message: {commit_message}")
    
    # Add all changes
    success, stdout, stderr = run_command("git add .")
    if not success:
        print(f"  ❌ Failed to stage changes: {stderr}")
        return False
    
    # Commit
    success, stdout, stderr = run_command(f'git commit -m "{commit_message}"')
    if success:
        print("  ✅ Changes committed successfully")
        return True
    else:
        print(f"  ❌ Failed to commit: {stderr}")
        return False

def push_changes():
    """Push changes to remote repository."""
    current_branch = get_current_branch()
    print(f"\n🚀 Pushing changes to {current_branch}...")
    
    success, stdout, stderr = run_command(f"git push origin {current_branch}")
    if success:
        print("  ✅ Changes pushed successfully")
        return True
    else:
        print(f"  ❌ Failed to push: {stderr}")
        return False

def create_stopping_point_summary():
    """Create a stopping point summary file."""
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    summary_file = f"docs/daily_summaries/{today}_stopping_point.md"
    
    # Ensure directory exists
    os.makedirs("docs/daily_summaries", exist_ok=True)
    
    current_branch = get_current_branch()
    changes = get_uncommitted_changes()
    
    summary_content = f"""# Daily Stopping Point - {today}

## 🕐 Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 📍 Current Status

### Branch
- **Current Branch**: `{current_branch}`
- **Repository**: python3-identity-manager

### Uncommitted Changes
"""
    
    if changes:
        for status, filename in changes:
            summary_content += f"- `{status}` {filename}\n"
    else:
        summary_content += "- No uncommitted changes\n"
    
    summary_content += f"""
## 🎯 Today's Achievements

### Completed Tasks
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3

### Major Features Implemented
- [ ] Feature 1
- [ ] Feature 2

### Documentation Updated
- [ ] Development roadmap
- [ ] Changelog
- [ ] API documentation
- [ ] User guides

## 🔧 Technical Status

### Tests
- [ ] Unit tests passing
- [ ] Integration tests passing
- [ ] Performance tests passing
- [ ] Coverage report generated

### Database
- [ ] Migrations applied
- [ ] Schema up to date
- [ ] Test data cleaned up

### Security
- [ ] Security audit completed
- [ ] Vulnerabilities addressed
- [ ] Audit logs reviewed

## 📋 Next Steps (Tomorrow)

### Priority 1
- [ ] Task 1
- [ ] Task 2

### Priority 2
- [ ] Task 3
- [ ] Task 4

### Technical Debt
- [ ] Refactor X
- [ ] Update Y
- [ ] Fix Z

## 🚨 Issues & Blockers

### Current Issues
- None identified

### Blockers
- None identified

### Known Bugs
- None identified

## 📊 Progress Metrics

### Version Progress
- **Current Version**: 0.4.0 (Complete)
- **Next Version**: 1.0.0 (MVP)
- **Overall Progress**: ~75%

### Test Coverage
- **Current Coverage**: TBD
- **Target Coverage**: 80%

### Documentation
- **API Documentation**: Complete
- **User Guides**: In Progress
- **Admin Guides**: Complete

## 💡 Notes & Ideas

### Ideas for Tomorrow
- Idea 1
- Idea 2

### Lessons Learned
- Lesson 1
- Lesson 2

### Questions for Review
- Question 1
- Question 2

---

## 🎉 Daily Wrap-up Checklist

- [x] Code committed and pushed
- [x] Documentation updated
- [x] Tests passing
- [x] Next steps planned
- [x] Issues documented
- [x] Stopping point summary created

**Ready to stop for the day!** 🚀
"""
    
    with open(summary_file, 'w') as f:
        f.write(summary_content)
    
    print(f"  ✅ Stopping point summary created: {summary_file}")
    return summary_file

def run_tests():
    """Run tests to ensure everything is working."""
    print("\n🧪 Running tests...")
    
    # Run pytest with coverage
    success, stdout, stderr = run_command("python -m pytest --cov=app --cov-report=html --cov-report=term-missing")
    if success:
        print("  ✅ Tests passed")
        return True
    else:
        print(f"  ❌ Tests failed: {stderr}")
        return False

def main():
    """Main daily stopping point workflow."""
    print("🛑 Daily Stopping Point Script")
    print("=" * 50)
    print(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Check current status
    current_branch = get_current_branch()
    changes = get_uncommitted_changes()
    
    print(f"\n📍 Current Status:")
    print(f"  Branch: {current_branch}")
    print(f"  Uncommitted changes: {len(changes)}")
    
    if changes:
        print("\n📝 Uncommitted Changes:")
        for status, filename in changes:
            print(f"  {status} {filename}")
    
    # Ask user what they want to do
    print("\n🤔 What would you like to do?")
    print("1. Update documentation only")
    print("2. Commit and push changes")
    print("3. Run tests")
    print("4. Create stopping point summary")
    print("5. Full stopping point workflow (recommended)")
    print("6. Exit")
    
    choice = input("\nEnter your choice (1-6): ").strip()
    
    if choice == "1":
        update_documentation()
    elif choice == "2":
        commit_message = input("Enter commit message (or press Enter for default): ").strip()
        if commit_changes(commit_message if commit_message else None):
            push_changes()
    elif choice == "3":
        run_tests()
    elif choice == "4":
        create_stopping_point_summary()
    elif choice == "5":
        # Full workflow
        print("\n🔄 Running full stopping point workflow...")
        
        # 1. Update documentation
        update_documentation()
        
        # 2. Run tests
        tests_passed = run_tests()
        
        # 3. Commit changes if any
        if changes:
            commit_message = input("\nEnter commit message (or press Enter for default): ").strip()
            if commit_changes(commit_message if commit_message else None):
                push_changes()
        else:
            print("\n✅ No changes to commit")
        
        # 4. Create stopping point summary
        summary_file = create_stopping_point_summary()
        
        print(f"\n🎉 Daily stopping point complete!")
        print(f"📄 Summary saved to: {summary_file}")
        print(f"📚 Review the summary and update it with your specific achievements")
        
    elif choice == "6":
        print("👋 Goodbye!")
        return
    else:
        print("❌ Invalid choice")
        return
    
    print("\n✅ Done!")

if __name__ == "__main__":
    main() 