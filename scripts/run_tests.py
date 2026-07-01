#!/usr/bin/env python3
"""
Test Runner Script
Run different categories of tests with various options
"""

import os
import sys
import subprocess
import questionary
import json
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd)}")
    print(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        print(f"\n✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {description} failed with exit code {e.returncode}")
        return False


def run_unit_tests(verbose=False, coverage=True):
    """Run unit tests"""
    cmd = ["python", "-m", "pytest", "tests/unit/", "-m", "unit"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    return run_command(cmd, "Unit Tests")


def run_integration_tests(verbose=False, coverage=True):
    """Run integration tests"""
    cmd = ["python", "-m", "pytest", "tests/integration/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing"])
    
    return run_command(cmd, "Integration Tests")


def run_performance_tests(verbose=False):
    """Run performance tests"""
    cmd = ["python", "-m", "pytest", "tests/performance/", "-m", "performance"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Performance Tests")


def run_all_tests(verbose=False, coverage=True, exclude_slow=False):
    """Run all tests"""
    cmd = ["python", "-m", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if exclude_slow:
        cmd.extend(["-m", "not slow"])
    
    if coverage:
        cmd.extend(["--cov=app", "--cov-report=term-missing", "--cov-report=html:htmlcov"])
    
    return run_command(cmd, "All Tests")


def run_coverage_report():
    """Generate detailed coverage report"""
    cmd = ["python", "-m", "pytest", "--cov=app", "--cov-report=html:htmlcov", "--cov-report=term-missing"]
    return run_command(cmd, "Coverage Report")


def run_specific_test(test_path, verbose=False):
    """Run a specific test file or test function"""
    cmd = ["python", "-m", "pytest", test_path]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, f"Specific Test: {test_path}")


def discover_test_files():
    """Recursively find all test_*.py files in the tests/ directory."""
    test_dir = Path(__file__).parent.parent / 'tests'
    return sorted([str(p.relative_to(test_dir.parent)) for p in test_dir.rglob('test_*.py')])

def load_test_config():
    """Load test_scripts.json if it exists for grouping/custom scripts."""
    config_path = Path(__file__).parent.parent / 'tests' / 'test_scripts.json'
    if config_path.exists():
        with open(config_path) as f:
            return json.load(f)
    return None

def main():
    test_files = discover_test_files()
    config = load_test_config()
    menu_choices = []
    if config and 'groups' in config:
        # Add groups as menu options
        for group, files in config['groups'].items():
            menu_choices.append(questionary.Choice(f"[Group] {group}", value=files))
        menu_choices.append(questionary.Separator())
    # Add individual test files
    menu_choices += [questionary.Choice(f, value=[f]) for f in test_files]
    if not menu_choices:
        print("No test files found.")
        sys.exit(1)
    print("\nSelect tests to run (space to select, enter to run):\n")
    selected = questionary.checkbox(
        "Choose test files or groups:",
        choices=menu_choices,
        validate=lambda x: True if x else "Select at least one test or group."
    ).ask()
    if not selected:
        print("No tests selected. Exiting.")
        sys.exit(0)
    # Flatten list in case of group selection
    files_to_run = sorted(set(f for group in selected for f in (group if isinstance(group, list) else [group])))
    # Run pytest on selected files
    print(f"\nRunning pytest on: {', '.join(files_to_run)}\n")
    result = subprocess.run([sys.executable, '-m', 'pytest'] + files_to_run)
    sys.exit(result.returncode)


if __name__ == "__main__":
    main() 