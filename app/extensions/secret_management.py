"""
Secret Management System
Handles secure storage and retrieval of secrets and sensitive configuration
"""

import os
import base64
import json
from typing import Dict, Any, Optional
from cryptography.fernet import Fernet
from flask import current_app


class SecretManager:
    """Manages application secrets securely"""
    
    def __init__(self):
        self.encryption_key = self._get_or_create_encryption_key()
        self.cipher_suite = Fernet(self.encryption_key)
    
    def _get_or_create_encryption_key(self) -> bytes:
        """Get or create encryption key for secrets"""
        key_file = os.path.join(os.getcwd(), '.secrets', 'encryption.key')
        
        # Create secrets directory if it doesn't exist
        os.makedirs(os.path.dirname(key_file), exist_ok=True)
        
        if os.path.exists(key_file):
            with open(key_file, 'rb') as f:
                return f.read()
        else:
            # Generate new key
            key = Fernet.generate_key()
            with open(key_file, 'wb') as f:
                f.write(key)
            # Set restrictive permissions
            os.chmod(key_file, 0o600)
            return key
    
    def encrypt_secret(self, secret: str) -> str:
        """Encrypt a secret value"""
        if not secret:
            return secret
        
        encrypted_bytes = self.cipher_suite.encrypt(secret.encode('utf-8'))
        return base64.b64encode(encrypted_bytes).decode('utf-8')
    
    def decrypt_secret(self, encrypted_secret: str) -> str:
        """Decrypt a secret value"""
        if not encrypted_secret:
            return encrypted_secret
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_secret.encode('utf-8'))
            decrypted_bytes = self.cipher_suite.decrypt(encrypted_bytes)
            return decrypted_bytes.decode('utf-8')
        except Exception:
            # If decryption fails, return the original value
            return encrypted_secret
    
    def store_secret(self, key: str, value: str) -> None:
        """Store a secret securely"""
        secrets_file = os.path.join(os.getcwd(), '.secrets', 'secrets.json')
        
        # Load existing secrets
        secrets = {}
        if os.path.exists(secrets_file):
            try:
                with open(secrets_file, 'r') as f:
                    secrets = json.load(f)
            except (json.JSONDecodeError, FileNotFoundError):
                secrets = {}
        
        # Encrypt and store the secret
        secrets[key] = self.encrypt_secret(value)
        
        # Save secrets
        os.makedirs(os.path.dirname(secrets_file), exist_ok=True)
        with open(secrets_file, 'w') as f:
            json.dump(secrets, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(secrets_file, 0o600)
    
    def get_secret(self, key: str, default: str = None) -> Optional[str]:
        """Retrieve a secret"""
        secrets_file = os.path.join(os.getcwd(), '.secrets', 'secrets.json')
        
        if not os.path.exists(secrets_file):
            return default
        
        try:
            with open(secrets_file, 'r') as f:
                secrets = json.load(f)
            
            encrypted_value = secrets.get(key)
            if encrypted_value:
                return self.decrypt_secret(encrypted_value)
            return default
        except (json.JSONDecodeError, KeyError):
            return default
    
    def load_secrets_to_environment(self) -> None:
        """Load all secrets into environment variables"""
        secrets_file = os.path.join(os.getcwd(), '.secrets', 'secrets.json')
        
        if not os.path.exists(secrets_file):
            return
        
        try:
            with open(secrets_file, 'r') as f:
                secrets = json.load(f)
            
            for key, encrypted_value in secrets.items():
                decrypted_value = self.decrypt_secret(encrypted_value)
                if decrypted_value and key not in os.environ:
                    os.environ[key] = decrypted_value
        except (json.JSONDecodeError, KeyError):
            pass


# Global secret manager instance
secret_manager = SecretManager()


def init_secret_management(app) -> None:
    """Initialize secret management for the application"""
    # Load secrets into environment
    secret_manager.load_secrets_to_environment()
    
    # Add secret manager to app context
    app.secret_manager = secret_manager
