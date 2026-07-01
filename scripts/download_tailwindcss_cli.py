#!/usr/bin/env python3

# scripts/download_tailwind.py

import os
import sys
import platform
import argparse
import requests
import re # For regular expressions to parse versions

def get_latest_release_version(major_minor_version=None):
    """
    Fetches the latest stable release version of Tailwind CSS from GitHub.
    Optionally, can fetch the latest for a specific major.minor version (e.g., '3.4').
    """
    repo_url = "https://api.github.com/repos/tailwindlabs/tailwindcss.com/releases"
    try:
        response = requests.get(repo_url, timeout=10)
        response.raise_for_status() # Raise an exception for HTTP errors
        releases = response.json()

        # Filter for stable releases and sort by version
        stable_releases = []
        for release in releases:
            # Only consider non-prerelease tags for stable versions
            if not release.get('prerelease') and release.get('tag_name', '').startswith('v'):
                version = release['tag_name'].lstrip('v')
                if major_minor_version:
                    # Check if the version matches the requested major.minor
                    if version.startswith(major_minor_version + '.'):
                        stable_releases.append(version)
                else:
                    stable_releases.append(version)

        if not stable_releases:
            return None

        # Sort versions to find the latest
        # Using packaging.version.parse for robust version comparison
        try:
            from packaging.version import parse as parse_version
        except ImportError:
            print("Warning: 'packaging' library not found. Version comparison might be less robust.", file=sys.stderr)
            # Fallback to simple string sorting if packaging is not available
            stable_releases.sort(key=lambda s: list(map(int, s.split('.'))), reverse=True)
            return stable_releases[0]

        stable_releases.sort(key=parse_version, reverse=True)
        return stable_releases[0]

    except requests.exceptions.RequestException as e:
        print(f"Error fetching latest release from GitHub: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}", file=sys.stderr)
        return None


def get_system_info():
    """Detects the current operating system and architecture."""
    os_name = platform.system().lower()
    arch_name = platform.machine().lower()

    # Map detected OS to Tailwind's naming convention
    if "linux" in os_name:
        detected_os = "linux"
    elif "darwin" in os_name: # macOS
        detected_os = "macos"
    elif "windows" in os_name:
        detected_os = "windows"
    else:
        detected_os = None

    # Map detected architecture to Tailwind's naming convention
    if "x86_64" in arch_name or "amd64" in arch_name:
        detected_arch = "x64"
    elif "arm64" in arch_name or "aarch64" in arch_name:
        detected_arch = "arm64"
    else:
        detected_arch = None

    return detected_os, detected_arch


def get_download_url(version, os_type, arch_type):
    """Constructs the download URL for the Tailwind CSS binary."""
    base_url = "https://github.com/tailwindlabs/tailwindcss/releases/download"
    filename = f"tailwindcss-{os_type}-{arch_type}"

    if os_type == "windows":
        filename += ".exe"

    return f"{base_url}/v{version}/{filename}"


def download_file(url, destination_path):
    """Downloads a file from a given URL to a specified path."""
    print(f"Downloading {url} to {destination_path}...")
    try:
        with requests.get(url, stream=True, timeout=30) as r:
            r.raise_for_status()
            with open(destination_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    f.write(chunk)
        print(f"Successfully downloaded {os.path.basename(destination_path)}")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error downloading file: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"An unexpected error occurred during download: {e}", file=sys.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(
        description="Download Tailwind CSS CLI binary from GitHub.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )

    parser.add_argument(
        '--version',
        type=str,
        default="3.4.17",
        help="Tailwind CSS CLI version to download (e.g., '3.4.17'). "
             "Use 'latest' for the absolute latest stable version. "
             "Use '3.x' (e.g., '3.4') for the latest patch in that major.minor series."
    )
    parser.add_argument(
        '--os',
        type=str,
        choices=['linux', 'macos', 'windows', 'auto'],
        default='auto',
        help="Operating system for the binary."
    )
    parser.add_argument(
        '--arch',
        type=str,
        choices=['x64', 'arm64', 'auto'],
        default='auto',
        help="Architecture for the binary."
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default=os.path.abspath(os.path.join(os.path.dirname(__file__), '..')), # Project root
        help="Directory to save the downloaded binary."
    )

    args = parser.parse_args()

    target_os = args.os
    target_arch = args.arch
    target_version = args.version

    # Auto-detect OS and Arch if requested
    if target_os == 'auto' or target_arch == 'auto':
        detected_os, detected_arch = get_system_info()
        if target_os == 'auto':
            if detected_os:
                target_os = detected_os
                print(f"Auto-detected OS: {target_os}")
            else:
                print("Could not auto-detect OS. Please specify with --os.", file=sys.stderr)
                sys.exit(1)
        if target_arch == 'auto':
            if detected_arch:
                target_arch = detected_arch
                print(f"Auto-detected Architecture: {target_arch}")
            else:
                print("Could not auto-detect architecture. Please specify with --arch.", file=sys.stderr)
                sys.exit(1)

    # Handle 'latest' or 'major.minor' version requests
    if target_version == 'latest':
        print("Fetching latest stable Tailwind CSS version...")
        actual_version = get_latest_release_version()
        if not actual_version:
            print("Failed to determine the latest version. Exiting.", file=sys.stderr)
            sys.exit(1)
        target_version = actual_version
        print(f"Using latest stable version: v{target_version}")
    elif re.match(r'^\d+\.\d+$', target_version): # e.g., '3.4'
        major_minor = target_version
        print(f"Fetching latest patch for Tailwind CSS v{major_minor}...")
        actual_version = get_latest_release_version(major_minor_version=major_minor)
        if not actual_version:
            print(f"Failed to determine the latest patch for v{major_minor}. Exiting.", file=sys.stderr)
            sys.exit(1)
        target_version = actual_version
        print(f"Using latest patch version: v{target_version}")
    elif not re.match(r'^\d+\.\d+\.\d+$', target_version):
        print(f"Invalid version format '{target_version}'. Please use 'X.Y.Z', 'latest', or 'X.Y'.", file=sys.stderr)
        sys.exit(1)

    download_url = get_download_url(target_version, target_os, target_arch)
    output_filename = f"tailwindcss-{target_os}-{target_arch}"
    if target_os == "windows":
        output_filename += ".exe"
    output_path = os.path.join(args.output_dir, output_filename)

    # Ensure the output directory exists
    os.makedirs(args.output_dir, exist_ok=True)

    if download_file(download_url, output_path):
        # Make the binary executable on Linux/macOS
        if target_os in ['linux', 'macos']:
            try:
                os.chmod(output_path, 0o755) # rwx r-x r-x
                print(f"Made {output_filename} executable.")
            except OSError as e:
                print(f"Warning: Could not make {output_filename} executable: {e}", file=sys.stderr)
        print(f"Tailwind CSS CLI binary saved to: {output_path}")
    else:
        print("Download failed.", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    # Add a check for 'packaging' library
    try:
        import packaging.version # noqa: F401
    except ImportError:
        print("The 'packaging' library is recommended for robust version comparison. Install it with: pip install packaging", file=sys.stderr)

    main()
