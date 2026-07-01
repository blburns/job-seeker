"""
TailwindCSS Management
Handles TailwindCSS compilation and management using the standalone binary
"""

import subprocess
import os
import platform
import hashlib
import time
from pathlib import Path
from flask import Flask


def get_tailwind_binary():
    """Get the correct TailwindCSS binary based on the current OS"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map platform combinations to binary names
    if system == 'darwin':  # macOS
        if machine in ['arm64', 'aarch64']:
            return './tailwindcss-macos-arm64'
        else:
            return './tailwindcss-macos-x64'
    elif system == 'linux':
        if machine in ['arm64', 'aarch64']:
            return './tailwindcss-linux-arm64'
        else:
            return './tailwindcss-linux-x64'
    elif system == 'windows':
        if machine in ['arm64', 'aarch64']:
            return './tailwindcss-windows-arm64.exe'
        else:
            return './tailwindcss-windows-x64.exe'
    else:
        # Fallback to generic binary name
        return './tailwindcss'


def get_file_hash(file_path):
    """Get MD5 hash of a file for change detection"""
    if not os.path.exists(file_path):
        return None
    
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def should_rebuild_tailwind():
    """Check if TailwindCSS needs to be rebuilt"""
    input_file = Path('app/static/css/input.css')
    output_file = Path('app/static/css/output.css')
    config_file = Path('tailwind.config.js')
    
    # If output doesn't exist, we need to build
    if not output_file.exists():
        return True
    
    # Get modification times
    output_mtime = output_file.stat().st_mtime
    
    # Check if input file is newer than output
    if input_file.exists() and input_file.stat().st_mtime > output_mtime:
        return True
    
    # Check if config file is newer than output
    if config_file.exists() and config_file.stat().st_mtime > output_mtime:
        return True
    
    # Check if any template files have changed (basic check)
    templates_dir = Path('app/templates')
    if templates_dir.exists():
        for template_file in templates_dir.rglob('*.html'):
            if template_file.stat().st_mtime > output_mtime:
                return True
    
    return False


def init_tailwind(app: Flask) -> None:
    """
    Initialize TailwindCSS
    
    Args:
        app: Flask application instance
    """
    # Ensure output directory exists
    output_dir = os.path.join(app.static_folder, 'css')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Only build TailwindCSS if output doesn't exist or input has changed
    if app.config.get('FLASK_ENV') == 'development':
        if should_rebuild_tailwind():
            build_tailwind()
        # Don't print anything if skipping - keeps logs clean


def build_tailwind(force=False) -> None:
    """Build TailwindCSS assets using the standalone binary"""
    if not force and not should_rebuild_tailwind():
        print("TailwindCSS output is up to date, skipping compilation")
        return
    
    tailwind_binary = get_tailwind_binary()
    
    # Check if input file exists
    input_file = Path('app/static/css/input.css')
    if not input_file.exists():
        print("Warning: TailwindCSS input file not found at app/static/css/input.css")
        return
    
    try:
        print("Building TailwindCSS...")
        start_time = time.time()
        
        # Use the TailwindCSS binary directly
        result = subprocess.run([
            tailwind_binary,
            '-i', 'app/static/css/input.css',
            '-o', 'app/static/css/output.css',
            '--minify'  # Minify for production
        ], check=True, capture_output=True, text=True)
        
        end_time = time.time()
        print(f"TailwindCSS compiled successfully in {end_time - start_time:.2f}s")
        
    except subprocess.CalledProcessError as e:
        print(f"Warning: Failed to build TailwindCSS: {e}")
        if e.stderr:
            print(f"Error details: {e.stderr}")
    except FileNotFoundError:
        print(f"Warning: TailwindCSS binary not found at {tailwind_binary}")
        print("Please download the appropriate TailwindCSS binary for your system:")
        print(f"  OS: {platform.system()} {platform.machine()}")
        print("  Expected binary: " + tailwind_binary)


def start_tailwind_watch() -> subprocess.Popen:
    """Start TailwindCSS watch process"""
    tailwind_binary = get_tailwind_binary()
    
    try:
        return subprocess.Popen([
            tailwind_binary,
            '-i', 'app/static/css/input.css',
            '-o', 'app/static/css/output.css',
            '--watch',
        ])
    except FileNotFoundError:
        print(f"Warning: TailwindCSS binary not found at {tailwind_binary}")
        print("Please download the appropriate TailwindCSS binary for your system:")
        print(f"  OS: {platform.system()} {platform.machine()}")
        print("  Expected binary: " + tailwind_binary)
        return None
    except Exception as e:
        print(f"Warning: Failed to start TailwindCSS watch process: {e}")
        return None


def stop_tailwind() -> None:
    """Stop TailwindCSS watch process"""
    tailwind_binary = get_tailwind_binary()
    
    try:
        # Find and kill TailwindCSS processes
        subprocess.run(['pkill', '-f', tailwind_binary], check=False)
        print("TailwindCSS watch process stopped")
    except Exception as e:
        print(f"Warning: Failed to stop TailwindCSS watch process: {e}")


# Global tailwind manager instance
tailwind_manager = None
