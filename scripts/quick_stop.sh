#!/bin/bash

# Quick Daily Stopping Point Script
# Usage: ./scripts/quick_stop.sh

echo "🛑 Quick Daily Stopping Point"
echo "============================="
echo "Date: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Get current status
BRANCH=$(git branch --show-current)
CHANGES=$(git status --porcelain | wc -l)

echo "📍 Current Status:"
echo "  Branch: $BRANCH"
echo "  Uncommitted changes: $CHANGES"
echo ""

# Show uncommitted changes
if [ $CHANGES -gt 0 ]; then
    echo "📝 Uncommitted Changes:"
    git status --porcelain | sed 's/^/  /'
    echo ""
fi

# Ask for commit message
if [ $CHANGES -gt 0 ]; then
    echo "💾 Committing changes..."
    read -p "Enter commit message (or press Enter for default): " COMMIT_MSG
    
    if [ -z "$COMMIT_MSG" ]; then
        COMMIT_MSG="📝 Daily progress update - $(date '+%Y-%m-%d %H:%M')"
    fi
    
    git add .
    git commit -m "$COMMIT_MSG"
    
    if [ $? -eq 0 ]; then
        echo "✅ Changes committed successfully"
        
        # Push changes
        echo "🚀 Pushing to remote..."
        git push origin $BRANCH
        
        if [ $? -eq 0 ]; then
            echo "✅ Changes pushed successfully"
        else
            echo "❌ Failed to push changes"
        fi
    else
        echo "❌ Failed to commit changes"
    fi
else
    echo "✅ No changes to commit"
fi

echo ""
echo "📋 Quick Checklist:"
echo "  [ ] Code committed and pushed"
echo "  [ ] Tests passing"
echo "  [ ] Documentation updated"
echo "  [ ] Next steps planned"
echo "  [ ] No critical issues"
echo ""
echo "🎯 Ready to stop for the day!"
echo ""
echo "💡 Next time you start:"
echo "  git pull origin $BRANCH"
echo "  python -m pytest  # Run tests"
echo "  python run.py     # Start development server" 