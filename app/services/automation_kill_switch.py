"""Runtime automation kill switch (env + file flag, no restart required for file)."""

from __future__ import annotations

import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

FLAG_PATH = Path('instance') / 'automation_disabled.flag'


def is_automation_disabled() -> bool:
    """True if env kill switch or instance flag file is set."""
    if os.getenv('AUTOMATION_DISABLED', 'false').lower() in ('true', '1', 'yes'):
        return True
    try:
        return FLAG_PATH.is_file()
    except OSError:
        return False


def kill_switch_source() -> str:
    """Human-readable reason for admin display."""
    env_on = os.getenv('AUTOMATION_DISABLED', 'false').lower() in ('true', '1', 'yes')
    file_on = False
    try:
        file_on = FLAG_PATH.is_file()
    except OSError:
        file_on = False
    if env_on and file_on:
        return 'env + file'
    if env_on:
        return 'env (AUTOMATION_DISABLED)'
    if file_on:
        return 'file (instance/automation_disabled.flag)'
    return 'off'


def set_file_kill_switch(enabled: bool) -> None:
    """Toggle the no-restart file flag. Env override still wins when set."""
    FLAG_PATH.parent.mkdir(parents=True, exist_ok=True)
    if enabled:
        FLAG_PATH.write_text('1\n', encoding='utf-8')
        logger.warning('Automation kill switch FILE enabled at %s', FLAG_PATH)
    else:
        if FLAG_PATH.exists():
            FLAG_PATH.unlink()
            logger.info('Automation kill switch FILE cleared at %s', FLAG_PATH)


def file_kill_switch_enabled() -> bool:
    try:
        return FLAG_PATH.is_file()
    except OSError:
        return False
