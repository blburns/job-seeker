#!/usr/bin/env python3
"""
TailwindCSS Binary Helper
Detects the current system and provides download instructions for the appropriate TailwindCSS binary
"""

import platform
import os
import subprocess
import sys


def get_system_info():
    """Get detailed system information"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    release = platform.release()
    
    return {
        'system': system,
        'machine': machine,
        'release': release,
        'platform': platform.platform()
    }


def get_tailwind_binary_name():
    """Get the correct TailwindCSS binary name for the current system"""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    # Map platform combinations to binary names
    if system == 'darwin':  # macOS
        if machine in ['arm64', 'aarch64']:
            return 'tailwindcss-macos-arm64'
        else:
            return 'tailwindcss-macos-x64'
    elif system == 'linux':
        if machine in ['arm64', 'aarch64']:
            return 'tailwindcss-linux-arm64'
        else:
            return 'tailwindcss-linux-x64'
    elif system == 'windows':
        if machine in ['arm64', 'aarch64']:
            return 'tailwindcss-windows-arm64.exe'
        else:
            return 'tailwindcss-windows-x64.exe'
    else:
        # Fallback to generic binary name
        return 'tailwindcss'


def check_binary_exists():
    """Check if the appropriate TailwindCSS binary exists"""
    binary_name = get_tailwind_binary_name()
    return os.path.exists(f'./{binary_name}')


def get_download_url():
    """Get the download URL for the appropriate TailwindCSS binary"""
    binary_name = get_tailwind_binary_name()
    
    # TailwindCSS releases are available at:
    # https://github.com/tailwindlabs/tailwindcss/releases
    base_url = "https://github.com/tailwindlabs/tailwindcss/releases/latest/download"
    
    return f"{base_url}/{binary_name}"


def test_binary():
    """Test if the current binary works"""
    binary_name = get_tailwind_binary_name()
    binary_path = f'./{binary_name}'
    
    if not os.path.exists(binary_path):
        return False, f"Binary {binary_path} not found"
    
    try:
        # Try to run the binary with a test build
        result = subprocess.run([binary_path, '-i', 'app/static/css/input.css', '-o', '/tmp/test_output.css'], 
                              capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, "Binary works correctly"
        else:
            return False, f"Binary returned error: {result.stderr}"
    except subprocess.TimeoutExpired:
        return False, "Binary timed out"
    except Exception as e:
        return False, f"Error testing binary: {e}"


def main():
    """Main function"""
    print("TailwindCSS Binary Helper")
    print("=" * 50)
    
    # Get system information
    sys_info = get_system_info()
    binary_name = get_tailwind_binary_name()
    
    print(f"System: {sys_info['platform']}")
    print(f"Expected binary: {binary_name}")
    print()
    
    # Check if binary exists
    if check_binary_exists():
        print(f"✓ Binary {binary_name} found")
        
        # Test the binary
        works, message = test_binary()
        if works:
            print(f"✓ Binary works correctly")
            print(f"  Version: {message}")
        else:
            print(f"✗ Binary found but doesn't work: {message}")
            print("  You may need to download a fresh binary")
    else:
        print(f"✗ Binary {binary_name} not found")
    
    print()
    print("Download Instructions:")
    print("-" * 30)
    print(f"1. Go to: https://github.com/tailwindlabs/tailwindcss/releases/latest")
    print(f"2. Download: {binary_name}")
    print(f"3. Or use direct link: {get_download_url()}")
    print(f"4. Place the binary in the project root directory")
    print(f"5. Make it executable: chmod +x {binary_name}")
    print()
    
    # Show current directory
    print(f"Current directory: {os.getcwd()}")
    print(f"Binary should be placed at: {os.path.join(os.getcwd(), binary_name)}")


if __name__ == '__main__':
    main()
