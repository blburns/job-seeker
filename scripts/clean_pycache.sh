#!/bin/bash
# Remove all __pycache__ directories and Python bytecode files from the project

set -e

# Remove __pycache__ directories
echo "Removing all __pycache__ directories..."
find . -type d -name '__pycache__' -exec rm -rf {} +

# Remove .pyc and .pyo files
echo "Removing all .pyc and .pyo files..."
find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

echo "Cleanup complete." 