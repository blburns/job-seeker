"""
Security utilities: password hashing, verification, and strength validation
Enhanced version for enterprise boilerplate application
"""

from typing import Tuple
from flask_bcrypt import generate_password_hash, check_password_hash
import re


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt
    
    Args:
        password: Plain text password
        
    Returns:
        Hashed password string
    """
    return generate_password_hash(password).decode('utf-8')


def verify_password(password_hash: str, password: str) -> bool:
    """
    Verify a password against its hash
    
    Args:
        password_hash: Stored password hash
        password: Plain text password to verify
        
    Returns:
        True if password matches, False otherwise
    """
    return check_password_hash(password_hash, password)


def check_password(password_hash: str, password: str) -> bool:
    """
    Compatibility alias used by models and routes
    """
    return verify_password(password_hash, password)


def validate_password_strength(password: str) -> Tuple[bool, str]:
    """
    Validate password strength according to enterprise standards
    
    Args:
        password: Password to validate
        
    Returns:
        Tuple of (is_valid, message)
    """
    if not password:
        return False, 'Password is required.'
    
    if len(password) < 8:
        return False, 'Password must be at least 8 characters long.'
    
    if len(password) > 128:
        return False, 'Password must be less than 128 characters long.'
    
    # Check for at least one uppercase letter
    if not re.search(r'[A-Z]', password):
        return False, 'Password must contain at least one uppercase letter.'
    
    # Check for at least one lowercase letter
    if not re.search(r'[a-z]', password):
        return False, 'Password must contain at least one lowercase letter.'
    
    # Check for at least one digit
    if not re.search(r'\d', password):
        return False, 'Password must contain at least one digit.'
    
    # Check for at least one special character
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        return False, 'Password must contain at least one special character.'
    
    # Check for common weak patterns
    weak_patterns = [
        r'(.)\1{2,}',  # Repeated characters
        r'123456',      # Sequential numbers
        r'password',    # Common words
        r'qwerty',      # Common patterns
        r'admin',       # Common words
    ]
    
    password_lower = password.lower()
    for pattern in weak_patterns:
        if re.search(pattern, password_lower):
            return False, 'Password contains weak patterns and is not secure.'
    
    return True, 'Password meets security requirements.'


def generate_secure_token(length: int = 32) -> str:
    """
    Generate a secure random token
    
    Args:
        length: Length of token to generate
        
    Returns:
        Secure random token string
    """
    import secrets
    import string
    
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def validate_email_format(email: str) -> bool:
    """
    Validate email format using regex
    
    Args:
        email: Email address to validate
        
    Returns:
        True if email format is valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def sanitize_input(input_string: str, max_length: int = 255) -> str:
    """
    Sanitize user input to prevent XSS and other attacks
    
    Args:
        input_string: Input string to sanitize
        max_length: Maximum allowed length
        
    Returns:
        Sanitized string
    """
    if not input_string:
        return ''
    
    # Remove leading/trailing whitespace
    sanitized = input_string.strip()
    
    # Truncate if too long
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    # Remove potentially dangerous characters
    dangerous_chars = ['<', '>', '"', "'", '&', '\x00', '\r', '\n']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    return sanitized
