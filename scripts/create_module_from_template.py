#!/usr/bin/env python3
"""Create a new module from the template"""
import sys
import os
import shutil
import re

def create_module(module_name, object_name, object_lower, id_field):
    """Create a new module from template"""
    
    # Paths
    template_dir = 'app/modules/_template'
    new_dir = f'app/modules/{module_name}'
    
    if os.path.exists(new_dir):
        print(f"❌ Directory {new_dir} already exists!")
        return False
    
    # Copy template directory
    print(f"📁 Copying template to {new_dir}...")
    shutil.copytree(template_dir, new_dir)
    
    # Replace in files
    for root, dirs, files in os.walk(new_dir):
        for file in files:
            filepath = os.path.join(root, file)
            
            # Read file
            with open(filepath, 'r') as f:
                content = f.read()
            
            # Replace
            content = content.replace('Template', object_name)
            content = content.replace('template', module_name)
            content = content.replace('TemplateObject', object_name)
            content = content.replace('template_object', object_lower)
            content = content.replace('template_id', id_field)
            
            # Write file
            with open(filepath, 'w') as f:
                f.write(content)
    
    print(f"✅ Created {module_name} module!")
    return True

if __name__ == '__main__':
    if len(sys.argv) < 5:
        print("Usage: python create_module_from_template.py <module_name> <ObjectName> <object_lower> <id_field>")
        sys.exit(1)
    
    create_module(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
