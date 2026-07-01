#!/usr/bin/env python3
"""
Version CLI for Flask Application Boilerplate
Provides command-line interface for version management
"""

import click
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from version import get_version, get_phase_info, VERSION_INFO, get_roadmap
from scripts.version_manager import VersionManager

@click.group()
def cli():
    """Flask Application Boilerplate Version Manager"""
    pass

@cli.command()
def status():
    """Show current version and phase status"""
    manager = VersionManager()
    manager.show_status()

@cli.command()
@click.argument('phase_number', type=int)
@click.option('--no-tag', is_flag=True, help='Skip creating git tag')
@click.option('--push-tag', is_flag=True, help='Push git tag to remote after creating')
def complete_phase(phase_number, no_tag, push_tag):
    """Complete a phase and move to the next version"""
    manager = VersionManager()
    create_tag = not no_tag
    if manager.complete_phase(phase_number, create_tag=create_tag, push_tag=push_tag):
        click.echo(f"✅ Phase {phase_number} completed successfully!")
    else:
        click.echo(f"❌ Failed to complete phase {phase_number}")

@cli.command()
@click.argument('version')
def update_version(version):
    """Update to a specific version"""
    manager = VersionManager()
    manager.update_version(version, "Custom Version", "Custom phase", "IN_PROGRESS")
    click.echo(f"✅ Updated to version {version}")

@cli.command()
@click.argument('version')
def release_notes(version):
    """Create release notes for a version"""
    manager = VersionManager()
    manager.create_release_notes(version)
    click.echo(f"✅ Created release notes for version {version}")

@cli.command()
def roadmap():
    """Show complete version roadmap"""
    roadmap = get_roadmap()
    click.echo("📋 COMPLETE VERSION ROADMAP:")
    click.echo("=" * 80)
    for version, info in roadmap.items():
        status_icon = "✅" if info["status"] == "COMPLETED" else "🔄" if info["status"] == "IN_PROGRESS" else "⏳"
        click.echo(f"{status_icon} {version}: {info['phase']}")
        click.echo(f"   Status: {info['status']}")
        click.echo(f"   Description: {info['description']}")
        click.echo()

@cli.command()
def info():
    """Show detailed version information"""
    click.echo("🚀 FLASK APPLICATION BOILERPLATE - VERSION INFO")
    click.echo("=" * 60)
    click.echo(f"Version: {get_version()}")
    click.echo(f"Phase: {get_phase_info()['phase']}")
    click.echo(f"Status: {get_phase_info()['status']}")
    click.echo(f"Description: {get_phase_info()['description']}")
    click.echo(f"Completion Date: {get_phase_info()['completion_date']}")
    click.echo("=" * 60)
    click.echo("\nVersion Details:")
    for key, value in VERSION_INFO.items():
        click.echo(f"  {key}: {value}")

if __name__ == '__main__':
    cli()
