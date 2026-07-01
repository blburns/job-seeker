#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive Endpoint Testing Script
Tests all endpoints in the Identity Manager application and generates a status report.
"""

import requests
import json
import time
from datetime import datetime
from urllib.parse import urljoin
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EndpointTester:
    def __init__(self, base_url="http://127.0.0.1:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.results = []
        self.auth_token = None
        self.csrf_token = None
        
        # Test user credentials (you may need to create this user first)
        self.test_user = {
            'username': 'testuser',
            'password': 'P@ssw0rd'
        }
        
        # Define all endpoints to test
        self.endpoints = [
            # Main routes
            {'url': '/', 'method': 'GET', 'name': 'Index', 'auth_required': False, 'category': 'Main'},
            {'url': '/health', 'method': 'GET', 'name': 'Health Check', 'auth_required': False, 'category': 'Main'},
            {'url': '/health/detailed', 'method': 'GET', 'name': 'Detailed Health', 'auth_required': False, 'category': 'Main'},
            {'url': '/health/force', 'method': 'GET', 'name': 'Force Health Check', 'auth_required': False, 'category': 'Main'},
            {'url': '/metrics', 'method': 'GET', 'name': 'System Metrics', 'auth_required': False, 'category': 'Main'},
            {'url': '/favicon.ico', 'method': 'GET', 'name': 'Favicon', 'auth_required': False, 'category': 'Main'},
            
            # Auth routes (web)
            {'url': '/login', 'method': 'GET', 'name': 'Login Page', 'auth_required': False, 'category': 'Auth'},
            {'url': '/logout', 'method': 'GET', 'name': 'Logout', 'auth_required': True, 'category': 'Auth'},
            {'url': '/register', 'method': 'GET', 'name': 'Register Page', 'auth_required': False, 'category': 'Auth'},
            {'url': '/password/reset', 'method': 'GET', 'name': 'Password Reset Page', 'auth_required': False, 'category': 'Auth'},
            
            # Auth API routes
            {'url': '/api/auth/login', 'method': 'POST', 'name': 'API Login', 'auth_required': False, 'category': 'Auth API'},
            {'url': '/api/auth/register', 'method': 'POST', 'name': 'API Register', 'auth_required': False, 'category': 'Auth API'},
            {'url': '/api/auth/password-reset', 'method': 'POST', 'name': 'API Password Reset', 'auth_required': False, 'category': 'Auth API'},
            {'url': '/api/auth/status', 'method': 'GET', 'name': 'Auth Status', 'auth_required': False, 'category': 'Auth API'},
            {'url': '/api/auth/csrf-token', 'method': 'GET', 'name': 'CSRF Token', 'auth_required': False, 'category': 'Auth API'},
            
            # User routes (web)
            {'url': '/users/', 'method': 'GET', 'name': 'Users Home', 'auth_required': True, 'category': 'Users'},
            {'url': '/users/profile', 'method': 'GET', 'name': 'User Profile', 'auth_required': True, 'category': 'Users'},
            {'url': '/users/settings', 'method': 'GET', 'name': 'User Settings', 'auth_required': True, 'category': 'Users'},
            
            # User API routes
            {'url': '/api/users/me/profile', 'method': 'PATCH', 'name': 'Update Profile', 'auth_required': True, 'category': 'Users API'},
            {'url': '/api/users', 'method': 'GET', 'name': 'Get All Users', 'auth_required': True, 'category': 'Users API'},
            {'url': '/api/users/admin', 'method': 'GET', 'name': 'Get User by UUID', 'auth_required': True, 'category': 'Users API'},
            {'url': '/api/users', 'method': 'POST', 'name': 'Create User', 'auth_required': True, 'category': 'Users API'},
            {'url': '/api/users/admin', 'method': 'PUT', 'name': 'Update User', 'auth_required': True, 'category': 'Users API'},
            {'url': '/api/users/admin', 'method': 'DELETE', 'name': 'Delete User', 'auth_required': True, 'category': 'Users API'},
            
            # Admin routes (web)
            {'url': '/admin/dashboard', 'method': 'GET', 'name': 'Admin Dashboard', 'auth_required': True, 'category': 'Admin'},
            {'url': '/admin/users', 'method': 'GET', 'name': 'Admin Users', 'auth_required': True, 'category': 'Admin'},
            {'url': '/admin/settings', 'method': 'GET', 'name': 'Admin Settings', 'auth_required': True, 'category': 'Admin'},
            {'url': '/admin/lockouts', 'method': 'GET', 'name': 'Admin Lockouts', 'auth_required': True, 'category': 'Admin'},
            
            # Admin API routes
            {'url': '/api/admin/dashboard', 'method': 'GET', 'name': 'Admin Dashboard API', 'auth_required': True, 'category': 'Admin API'},
            {'url': '/api/admin/lockouts/users', 'method': 'GET', 'name': 'User Lockouts', 'auth_required': True, 'category': 'Admin API'},
            {'url': '/api/admin/lockouts/ips', 'method': 'GET', 'name': 'IP Lockouts', 'auth_required': True, 'category': 'Admin API'},
            {'url': '/api/admin/lockouts/users/unlock', 'method': 'POST', 'name': 'Unlock User', 'auth_required': True, 'category': 'Admin API'},
            {'url': '/api/admin/lockouts/ips/unlock', 'method': 'POST', 'name': 'Unlock IP', 'auth_required': True, 'category': 'Admin API'},
            {'url': '/api/admin/settings/email', 'method': 'GET', 'name': 'Email Settings', 'auth_required': True, 'category': 'Admin API'},
            {'url': '/api/admin/settings/email', 'method': 'POST', 'name': 'Update Email Settings', 'auth_required': True, 'category': 'Admin API'},
            {'url': '/api/admin/settings/email/reset', 'method': 'POST', 'name': 'Reset Email Settings', 'auth_required': True, 'category': 'Admin API'},
            
            # Audit routes (web)
            {'url': '/audit/', 'method': 'GET', 'name': 'Audit Home', 'auth_required': True, 'category': 'Audit'},
            {'url': '/audit/dashboard', 'method': 'GET', 'name': 'Audit Dashboard', 'auth_required': True, 'category': 'Audit'},
            {'url': '/audit/logs', 'method': 'GET', 'name': 'Audit Logs', 'auth_required': True, 'category': 'Audit'},
            {'url': '/audit/security-events', 'method': 'GET', 'name': 'Security Events', 'auth_required': True, 'category': 'Audit'},
            {'url': '/audit/stats', 'method': 'GET', 'name': 'Audit Stats', 'auth_required': True, 'category': 'Audit'},
            
            # Audit API routes
            {'url': '/api/audit/logs', 'method': 'GET', 'name': 'Audit Logs API', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/security', 'method': 'GET', 'name': 'Security Events API', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/stats', 'method': 'GET', 'name': 'Audit Stats API', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/dashboard', 'method': 'GET', 'name': 'Audit Dashboard API', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/logs/1', 'method': 'GET', 'name': 'Get Audit Log', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/security-events/1', 'method': 'GET', 'name': 'Get Security Event', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/security-events/1/resolve', 'method': 'POST', 'name': 'Resolve Security Event', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/logs/export', 'method': 'GET', 'name': 'Export Audit Logs', 'auth_required': True, 'category': 'Audit API'},
            {'url': '/api/audit/security-events/export', 'method': 'GET', 'name': 'Export Security Events', 'auth_required': True, 'category': 'Audit API'},
            
            # Account routes
            {'url': '/account/settings', 'method': 'GET', 'name': 'Account Settings', 'auth_required': True, 'category': 'Account'},
            {'url': '/api/account/settings', 'method': 'GET', 'name': 'Account Settings API', 'auth_required': True, 'category': 'Account API'},
            
            # Auth API routes (from auth/routes.py)
            {'url': '/api/login', 'method': 'POST', 'name': 'Legacy API Login', 'auth_required': False, 'category': 'Auth API'},
            {'url': '/api/register', 'method': 'POST', 'name': 'Legacy API Register', 'auth_required': False, 'category': 'Auth API'},
            {'url': '/api/password/reset', 'method': 'POST', 'name': 'Legacy API Password Reset', 'auth_required': False, 'category': 'Auth API'},
            {'url': '/api/sessions', 'method': 'GET', 'name': 'Get Sessions', 'auth_required': True, 'category': 'Auth API'},
            {'url': '/api/sessions/admin', 'method': 'DELETE', 'name': 'Delete Session', 'auth_required': True, 'category': 'Auth API'},
            {'url': '/api/sessions/revoke-all', 'method': 'POST', 'name': 'Revoke All Sessions', 'auth_required': True, 'category': 'Auth API'},
            {'url': '/api/sessions/refresh', 'method': 'POST', 'name': 'Refresh Session', 'auth_required': True, 'category': 'Auth API'},
        ]
    
    def login(self):
        """Attempt to login and get authentication tokens"""
        try:
            # Get CSRF token first
            csrf_response = self.session.get(urljoin(self.base_url, '/api/auth/csrf-token'))
            if csrf_response.status_code == 200:
                csrf_data = csrf_response.json()
                self.csrf_token = csrf_data.get('data', {}).get('csrf_token')
            
            # Attempt login
            login_data = {
                'username': self.test_user['username'],
                'password': self.test_user['password']
            }
            
            headers = {'Content-Type': 'application/json'}
            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token
            
            login_response = self.session.post(
                urljoin(self.base_url, '/api/auth/login'),
                json=login_data,
                headers=headers
            )
            
            if login_response.status_code == 200:
                print("[OK] Successfully logged in")
                return True
            else:
                print(f"[ERROR] Login failed: {login_response.status_code}")
                return False
                
        except Exception as e:
            print(f"[ERROR] Login error: {e}")
            return False
    
    def test_endpoint(self, endpoint):
        """Test a single endpoint"""
        url = urljoin(self.base_url, endpoint['url'])
        method = endpoint['method']
        name = endpoint['name']
        auth_required = endpoint['auth_required']
        category = endpoint['category']
        
        try:
            headers = {'Content-Type': 'application/json'}
            if self.csrf_token:
                headers['X-CSRFToken'] = self.csrf_token
            
            # Prepare request data for POST/PUT requests
            data = None
            if method in ['POST', 'PUT', 'PATCH']:
                if 'login' in endpoint['url'].lower():
                    data = {'username': 'test', 'password': 'test'}
                elif 'register' in endpoint['url'].lower():
                    data = {'username': 'test', 'email': 'test@test.com', 'password': 'test123'}
                elif 'password' in endpoint['url'].lower():
                    data = {'email': 'test@test.com'}
                elif 'unlock' in endpoint['url'].lower():
                    data = {'user_uuid': 'test-uuid'}
                elif 'resolve' in endpoint['url'].lower():
                    data = {'resolution_notes': 'Test resolution'}
                else:
                    data = {}
            
            # Make the request
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method == 'PATCH':
                response = self.session.patch(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)
            else:
                response = None
            
            # Analyze response
            if response is None:
                status = 'ERROR'
                message = 'Invalid method'
            elif response.status_code == 200:
                status = '[OK] WORKING'
                message = 'Success'
            elif response.status_code == 401 and auth_required:
                status = '[AUTH] AUTH_REQUIRED'
                message = 'Authentication required (expected)'
            elif response.status_code == 403 and auth_required:
                status = '[AUTH] FORBIDDEN'
                message = 'Access forbidden (expected for non-admin)'
            elif response.status_code == 404:
                status = '[ERROR] NOT_FOUND'
                message = 'Endpoint not found'
            elif response.status_code == 405:
                status = '[ERROR] METHOD_NOT_ALLOWED'
                message = 'Method not allowed'
            else:
                status = f'[ERROR] ERROR_{response.status_code}'
                message = f'HTTP {response.status_code}'
            
            result = {
                'url': endpoint['url'],
                'method': method,
                'name': name,
                'category': category,
                'status': status,
                'message': message,
                'status_code': response.status_code if response else None,
                'auth_required': auth_required
            }
            
            self.results.append(result)
            return result
            
        except requests.exceptions.ConnectionError:
            result = {
                'url': endpoint['url'],
                'method': method,
                'name': name,
                'category': category,
                'status': '[ERROR] CONNECTION_ERROR',
                'message': 'Connection refused - server not running?',
                'status_code': None,
                'auth_required': auth_required
            }
            self.results.append(result)
            return result
        except Exception as e:
            result = {
                'url': endpoint['url'],
                'method': method,
                'name': name,
                'category': category,
                'status': '[ERROR] EXCEPTION',
                'message': str(e),
                'status_code': None,
                'auth_required': auth_required
            }
            self.results.append(result)
            return result
    
    def run_tests(self):
        """Run all endpoint tests"""
        print("Testing all endpoints...")
        print("=" * 80)
        
        # Try to login first
        print("Attempting login...")
        login_success = self.login()
        
        # Test all endpoints
        for i, endpoint in enumerate(self.endpoints, 1):
            print(f"[{i:2d}/{len(self.endpoints)}] Testing {endpoint['method']} {endpoint['url']} - {endpoint['name']}")
            result = self.test_endpoint(endpoint)
            print(f"    {result['status']}: {result['message']}")
            time.sleep(0.1)  # Small delay to avoid overwhelming the server
        
        print("\n" + "=" * 80)
        print("Test Results Summary")
        print("=" * 80)
    
    def generate_report(self):
        """Generate a comprehensive report"""
        # Count by status
        status_counts = {}
        category_counts = {}
        
        for result in self.results:
            status = result['status']
            category = result['category']
            
            status_counts[status] = status_counts.get(status, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Generate HTML report
        html_content = self.generate_html_report(status_counts, category_counts)
        
        # Save HTML report
        with open('endpoint_test_report.html', 'w') as f:
            f.write(html_content)
        
        # Generate markdown report
        md_content = self.generate_markdown_report(status_counts, category_counts)
        
        # Save markdown report
        with open('endpoint_test_report.md', 'w') as f:
            f.write(md_content)
        
        print(f"Reports generated:")
        print(f"   - endpoint_test_report.html")
        print(f"   - endpoint_test_report.md")
        
        # Print summary
        print("\nSummary:")
        for status, count in status_counts.items():
            print(f"   {status}: {count}")
        
        print(f"\nBy Category:")
        for category, count in category_counts.items():
            print(f"   {category}: {count}")
    
    def generate_html_report(self, status_counts, category_counts):
        """Generate HTML report"""
        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Endpoint Test Report - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .header {{ background: #f5f5f5; padding: 20px; border-radius: 5px; margin-bottom: 20px; }}
        .summary {{ display: flex; gap: 20px; margin-bottom: 20px; }}
        .summary-box {{ background: #fff; border: 1px solid #ddd; padding: 15px; border-radius: 5px; flex: 1; }}
        table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background: #f5f5f5; }}
        .working {{ color: green; }}
        .auth-required {{ color: orange; }}
        .error {{ color: red; }}
        .category-header {{ background: #e9ecef; font-weight: bold; }}
        a {{ color: #007bff; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Endpoint Test Report</h1>
        <p>Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Base URL: {self.base_url}</p>
    </div>
    
    <div class="summary">
        <div class="summary-box">
            <h3>Status Summary</h3>
"""
        
        for status, count in status_counts.items():
            css_class = 'working' if '[OK]' in status else 'auth-required' if '[AUTH]' in status else 'error'
            html += f'            <p class="{css_class}">{status}: {count}</p>\n'
        
        html += """
        </div>
        <div class="summary-box">
            <h3>Category Summary</h3>
"""
        
        for category, count in category_counts.items():
            html += f'            <p>{category}: {count}</p>\n'
        
        html += """
        </div>
    </div>
    
    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>Category</th>
            <th>Method</th>
            <th>Endpoint</th>
            <th>Name</th>
            <th>Status</th>
            <th>Message</th>
            <th>Auth Required</th>
        </tr>
"""
        
        current_category = None
        for result in self.results:
            if result['category'] != current_category:
                current_category = result['category']
                html += f'        <tr class="category-header"><td colspan="7">{current_category}</td></tr>\n'
            
            css_class = 'working' if '[OK]' in result['status'] else 'auth-required' if '[AUTH]' in result['status'] else 'error'
            test_url = f"{self.base_url}{result['url']}"
            
            html += f"""
        <tr class="{css_class}">
            <td>{result['category']}</td>
            <td>{result['method']}</td>
            <td><a href="{test_url}" target="_blank">{result['url']}</a></td>
            <td>{result['name']}</td>
            <td>{result['status']}</td>
            <td>{result['message']}</td>
            <td>{'Yes' if result['auth_required'] else 'No'}</td>
        </tr>
"""
        
        html += """
    </table>
</body>
</html>
"""
        return html
    
    def generate_markdown_report(self, status_counts, category_counts):
        """Generate markdown report"""
        md = f"""# Endpoint Test Report

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Base URL:** {self.base_url}

## Summary

### Status Summary
"""
        
        for status, count in status_counts.items():
            md += f"- {status}: {count}\n"
        
        md += "\n### Category Summary\n"
        for category, count in category_counts.items():
            md += f"- {category}: {count}\n"
        
        md += "\n## Detailed Results\n\n"
        md += "| Category | Method | Endpoint | Name | Status | Message | Auth Required |\n"
        md += "|----------|--------|----------|------|--------|---------|---------------|\n"
        
        for result in self.results:
            test_url = f"{self.base_url}{result['url']}"
            md += f"| {result['category']} | {result['method']} | [{result['url']}]({test_url}) | {result['name']} | {result['status']} | {result['message']} | {'Yes' if result['auth_required'] else 'No'} |\n"
        
        return md

def main():
    """Main function"""
    print("Identity Manager Endpoint Tester")
    print("=" * 50)
    
    # Check if server is running
    base_url = "http://localhost:5000"
    
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"[OK] Server is running at {base_url}")
        else:
            print(f"[WARN] Server responded with status {response.status_code}")
    except requests.exceptions.ConnectionError:
        print(f"[ERROR] Cannot connect to {base_url}")
        print("Please make sure the Flask application is running:")
        print("   python run.py")
        return
    except Exception as e:
        print(f"[ERROR] Error connecting to server: {e}")
        return
    
    # Run tests
    tester = EndpointTester(base_url)
    tester.run_tests()
    tester.generate_report()
    
    print("\nTesting complete!")

if __name__ == "__main__":
    main() 
