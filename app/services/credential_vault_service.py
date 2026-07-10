"""Encrypted credential storage for portal sessions."""

import json
import logging
import os
from datetime import datetime
from typing import Any, Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

from app.extensions.core import db
from app.models.jobs import PortalCredential

logger = logging.getLogger(__name__)


class CredentialVaultService:
    _runtime_key: Optional[bytes] = None

    @classmethod
    def encryption_key_configured(cls) -> bool:
        return bool(os.getenv('CREDENTIAL_ENCRYPTION_KEY', '').strip())

    @classmethod
    def _fernet(cls) -> Fernet:
        key = os.getenv('CREDENTIAL_ENCRYPTION_KEY', '').strip()
        if key:
            return Fernet(key.encode())
        if cls._runtime_key is None:
            cls._runtime_key = Fernet.generate_key()
            logger.warning(
                'CREDENTIAL_ENCRYPTION_KEY not set; using ephemeral key for this process only'
            )
        return Fernet(cls._runtime_key)

    @classmethod
    def normalize_credential_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Accept Playwright storage_state export or legacy session_cookie."""
        if 'storage_state' in data:
            if isinstance(data['storage_state'], str):
                data['storage_state'] = json.loads(data['storage_state'])
            data.setdefault('connected_at', datetime.utcnow().isoformat())
            return data
        if 'cookies' in data and 'origins' in data:
            return {
                'storage_state': data,
                'connected_at': datetime.utcnow().isoformat(),
            }
        return data

    @classmethod
    def validate_portal_data(cls, portal: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure scraped portal credentials have a usable Playwright storage_state."""
        data = cls.normalize_credential_data(data)
        if portal not in ('linkedin', 'indeed', 'greenhouse'):
            return data

        storage_state = data.get('storage_state')
        if portal == 'linkedin' and not storage_state:
            raise ValueError(
                'LinkedIn requires Playwright storage_state JSON '
                '(object with "cookies" and "origins"). Paste the full export file.'
            )
        if portal == 'greenhouse' and not storage_state:
            raise ValueError(
                'MyGreenhouse requires Playwright storage_state JSON. '
                'Run: python scripts/export_playwright_storage.py greenhouse'
            )
        if not storage_state:
            return data

        cookies = storage_state.get('cookies') or []
        if portal == 'linkedin':
            if not any(c.get('name') == 'li_at' for c in cookies):
                raise ValueError(
                    'LinkedIn export is missing the li_at session cookie. '
                    'Re-run export_playwright_storage.py after completing login.'
                )
        return data

    @classmethod
    def store(cls, user_id, portal: str, data: Dict[str, Any], label: str = '') -> PortalCredential:
        data = cls.validate_portal_data(portal, data)
        existing = PortalCredential.query.filter_by(
            user_id=user_id, portal=portal, is_deleted=False
        ).all()
        for cred in existing:
            cred.is_active = False
            cred.soft_delete()
        encrypted = cls._fernet().encrypt(json.dumps(data).encode()).decode()
        cred = PortalCredential(
            user_id=user_id,
            portal=portal,
            label=label or portal,
            encrypted_data=encrypted,
            is_active=True,
            expires_at=None,
            last_used_at=None,
        )
        db.session.add(cred)
        db.session.commit()
        return cred

    @classmethod
    def delete(cls, user_id, credential_id) -> bool:
        cred = PortalCredential.query.filter_by(
            id=credential_id, user_id=user_id, is_deleted=False
        ).first()
        if not cred:
            return False
        cred.is_active = False
        cred.soft_delete()
        db.session.commit()
        return True

    @classmethod
    def delete_for_portal(cls, user_id, portal: str) -> int:
        creds = PortalCredential.query.filter_by(
            user_id=user_id, portal=portal, is_deleted=False
        ).all()
        for cred in creds:
            cred.is_active = False
            cred.soft_delete()
        db.session.commit()
        return len(creds)

    @classmethod
    def has_active(cls, user_id, portal: str) -> bool:
        return PortalCredential.query.filter_by(
            user_id=user_id, portal=portal, is_active=True, is_deleted=False
        ).first() is not None

    @classmethod
    def retrieve(cls, user_id, portal: str) -> Optional[Dict[str, Any]]:
        data, _ = cls.retrieve_with_status(user_id, portal)
        return data

    @classmethod
    def retrieve_with_status(cls, user_id, portal: str) -> tuple[Optional[Dict[str, Any]], Optional[str]]:
        """Return (data, error_code). error_code: not_found | decrypt_failed."""
        cred = PortalCredential.query.filter_by(
            user_id=user_id, portal=portal, is_active=True, is_deleted=False
        ).order_by(PortalCredential.created_at.desc()).first()
        if not cred:
            return None, 'not_found'
        try:
            raw = cls._fernet().decrypt(cred.encrypted_data.encode())
            cred.last_used_at = datetime.utcnow()
            db.session.commit()
            return json.loads(raw.decode()), None
        except InvalidToken:
            logger.error('Failed to decrypt credential for portal %s', portal)
            return None, 'decrypt_failed'

    @classmethod
    def list_credentials(cls, user_id):
        return PortalCredential.query.filter_by(
            user_id=user_id, is_deleted=False
        ).order_by(PortalCredential.created_at.desc()).all()


credential_vault_service = CredentialVaultService()
