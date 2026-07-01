#!/usr/bin/env python3
"""
Script to add data attributes to all permission checkboxes in the permissions template.
This adds data-action and data-role attributes to make real-time permission toggles work.
"""

import re
import os

def add_data_attributes_to_checkboxes():
    template_path = 'app/templates/modules/settings/permissions.html'
    
    with open(template_path, 'r') as f:
        content = f.read()
    
    # Define the actions and their corresponding roles
    actions = [
        'View Users', 'Create Users', 'Edit Users', 'Delete Users', 'Manage Users',
        'View Contacts', 'Create Contacts', 'Edit Contacts', 'Delete Contacts', 'Manage Contacts',
        'View Documents', 'Upload Documents', 'Download Documents', 'Delete Documents', 'Manage Documents',
        'View Email Settings', 'Send Emails', 'Configure Email', 'View Email Logs',
        'View Settings', 'Global Settings', 'Admin Settings', 'Super Admin Settings',
        'View Analytics', 'Export Reports', 'Manage Analytics'
    ]
    
    roles = ['Super Admin', 'Admin', 'Manager', 'User', 'Public']
    
    # Process each action
    for action in actions:
        # Find the table row for this action
        action_pattern = rf'<tr>\s*<td[^>]*>{re.escape(action)}</td>'
        action_match = re.search(action_pattern, content, re.DOTALL)
        
        if action_match:
            # Find all checkboxes in this row
            row_start = action_match.start()
            row_end = content.find('</tr>', row_start) + 5
            
            row_content = content[row_start:row_end]
            
            # Replace each checkbox with data attributes
            for i, role in enumerate(roles):
                checkbox_pattern = rf'<input type="checkbox"[^>]*class="h-4 w-4 text-blue-600 rounded border-gray-300"([^>]*)>'
                
                def replace_checkbox(match):
                    attrs = match.group(1)
                    is_disabled = 'disabled' in attrs
                    is_checked = 'checked' in attrs
                    
                    if is_disabled:
                        # Super Admin checkboxes are disabled
                        return f'<input type="checkbox" checked disabled class="h-4 w-4 text-blue-600 rounded border-gray-300" data-action="{action}" data-role="{role}">'
                    else:
                        # Other checkboxes are toggleable
                        checked_attr = ' checked' if is_checked else ''
                        return f'<input type="checkbox"{checked_attr} class="h-4 w-4 text-blue-600 rounded border-gray-300 permission-toggle" data-action="{action}" data-role="{role}">'
                
                row_content = re.sub(checkbox_pattern, replace_checkbox, row_content)
            
            # Replace the original row with the updated one
            content = content[:row_start] + row_content + content[row_end:]
    
    # Write the updated content back
    with open(template_path, 'w') as f:
        f.write(content)
    
    print("✅ Added data attributes to all permission checkboxes")
    print(f"   - Added data-action and data-role attributes")
    print(f"   - Added 'permission-toggle' class to non-disabled checkboxes")
    print(f"   - Processed {len(actions)} actions across {len(roles)} roles")

if __name__ == '__main__':
    add_data_attributes_to_checkboxes()
