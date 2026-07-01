#!/usr/bin/env python3
"""
Flask Application Runner
Simple script to run the Flask application.
"""

import os
from app import create_app


def main():
    """Main entry point"""
    app = create_app()
    
    # Get configuration from environment
    debug = os.getenv('FLASK_DEBUG', 'False') == 'True'
    host = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    port = int(os.getenv('FLASK_RUN_PORT', 5000))
    environment = os.getenv('FLASK_ENV', 'development')
    
    print(f"Starting Flask application...")
    print(f"Environment: {environment}")
    print(f"Debug mode: {debug}")
    print(f"Host: {host}")
    print(f"Port: {port}")
    print(f"URL: http://{host}:{port}")
    
    app.run(debug=debug, host=host, port=port)

if __name__ == '__main__':
    main()
