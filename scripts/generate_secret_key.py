#!/usr/bin/env python3
import os
import secrets
import sys

ENV_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), '.env')
SECRET_KEY_VAR = 'FLASK_SECRET_KEY'

WARNING = f"""
WARNING: Changing your Flask secret key will invalidate all existing sessions, cookies, and tokens.
This may log out all users and break password reset or email confirmation links.

Are you sure you want to generate and set a new secret key in your .env file? (yes/no): """

confirm = input(WARNING)
if confirm.strip().lower() not in ('yes', 'y'):
    print("Aborted. No changes made.")
    sys.exit(1)

# Generate a new secure secret key
new_key = secrets.token_urlsafe(64)

# Read existing .env or create new content
if os.path.exists(ENV_PATH):
    with open(ENV_PATH, 'r') as f:
        lines = f.readlines()
else:
    lines = []

found = False
for i, line in enumerate(lines):
    if line.startswith(SECRET_KEY_VAR + '='):
        lines[i] = f'{SECRET_KEY_VAR}={new_key}\n'
        found = True
        break

if not found:
    lines.append(f'{SECRET_KEY_VAR}={new_key}\n')

with open(ENV_PATH, 'w') as f:
    f.writelines(lines)

print(f'New secret key written to .env as {SECRET_KEY_VAR}') 