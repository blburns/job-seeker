"""
Main CLI Entry Point
Registers all CLI commands for the application
"""

from flask.cli import FlaskGroup
from app import create_app_for_cli
from app.modules.settings.cli import settings

# Create Flask CLI group
cli = FlaskGroup(create_app=create_app_for_cli)

# Register command groups
cli.add_command(settings)

if __name__ == '__main__':
    cli()
