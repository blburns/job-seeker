"""
TOTP (Time-based One-Time Password) Service
Handles two-factor authentication with Google Authenticator
"""

import pyotp
import qrcode
import io
import base64
import secrets
import hashlib
from typing import Tuple, List, Optional


class TOTPService:
    """Service for managing TOTP-based 2FA"""
    
    @staticmethod
    def generate_secret() -> str:
        """
        Generate a new TOTP secret
        
        Returns:
            str: Base32 encoded secret (16 characters)
        """
        return pyotp.random_base32()
    
    @staticmethod
    def get_totp_uri(secret: str, username: str, issuer: str = "Application") -> str:
        """
        Generate TOTP provisioning URI for QR code
        
        Args:
            secret: Base32 encoded TOTP secret
            username: User's username or email
            issuer: Application name
        
        Returns:
            str: TOTP URI (otpauth://totp/...)
        """
        totp = pyotp.TOTP(secret)
        return totp.provisioning_uri(name=username, issuer_name=issuer)
    
    @staticmethod
    def generate_qr_code(uri: str) -> str:
        """
        Generate QR code image from TOTP URI
        
        Args:
            uri: TOTP provisioning URI
        
        Returns:
            str: Base64 encoded PNG image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        img_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{img_base64}"
    
    @staticmethod
    def verify_token(secret: str, token: str) -> bool:
        """
        Verify a TOTP token
        
        Args:
            secret: Base32 encoded TOTP secret
            token: 6-digit TOTP code
        
        Returns:
            bool: True if token is valid
        """
        if not secret or not token:
            return False
        
        try:
            totp = pyotp.TOTP(secret)
            # Allow 1 time step before/after for clock skew (30 seconds)
            return totp.verify(token, valid_window=1)
        except Exception:
            return False
    
    @staticmethod
    def generate_backup_codes(count: int = 10) -> List[str]:
        """
        Generate backup codes for account recovery
        
        Args:
            count: Number of backup codes to generate
        
        Returns:
            List[str]: List of backup codes (8 characters each)
        """
        codes = []
        for _ in range(count):
            # Generate 8-character alphanumeric code
            code = ''.join(secrets.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(8))
            # Format as XXXX-XXXX for readability
            formatted_code = f"{code[:4]}-{code[4:]}"
            codes.append(formatted_code)
        return codes
    
    @staticmethod
    def hash_backup_code(code: str) -> str:
        """
        Hash a backup code for storage
        
        Args:
            code: Plain text backup code
        
        Returns:
            str: SHA-256 hash of the code
        """
        # Remove dashes and convert to uppercase
        clean_code = code.replace('-', '').upper()
        return hashlib.sha256(clean_code.encode()).hexdigest()
    
    @staticmethod
    def verify_backup_code(code: str, hashed_codes: List[str]) -> Tuple[bool, Optional[str]]:
        """
        Verify a backup code against stored hashes
        
        Args:
            code: Plain text backup code to verify
            hashed_codes: List of hashed backup codes
        
        Returns:
            Tuple[bool, Optional[str]]: (is_valid, matched_hash)
        """
        if not code or not hashed_codes:
            return False, None
        
        code_hash = TOTPService.hash_backup_code(code)
        
        if code_hash in hashed_codes:
            return True, code_hash
        
        return False, None
    
    @staticmethod
    def get_current_token(secret: str) -> str:
        """
        Get current TOTP token (for testing/debugging only)
        
        Args:
            secret: Base32 encoded TOTP secret
        
        Returns:
            str: Current 6-digit TOTP code
        """
        totp = pyotp.TOTP(secret)
        return totp.now()


# Global TOTP service instance
totp_service = TOTPService()
