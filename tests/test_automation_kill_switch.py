"""Automation kill switch (env + file flag) tests."""

import pytest

from app.services import automation_kill_switch as kill_switch
from app.services.apply_submission_service import apply_submission_service


@pytest.fixture
def flag_path(tmp_path, monkeypatch):
    path = tmp_path / 'automation_disabled.flag'
    monkeypatch.setattr(kill_switch, 'FLAG_PATH', path)
    monkeypatch.setenv('AUTOMATION_DISABLED', 'false')
    if path.exists():
        path.unlink()
    yield path
    if path.exists():
        path.unlink()


def test_env_kill_switch(monkeypatch, flag_path):
    monkeypatch.setenv('AUTOMATION_DISABLED', 'true')
    assert kill_switch.is_automation_disabled() is True
    assert 'env' in kill_switch.kill_switch_source()


def test_file_kill_switch_no_restart(flag_path, monkeypatch):
    monkeypatch.setenv('AUTOMATION_DISABLED', 'false')
    assert kill_switch.is_automation_disabled() is False
    kill_switch.set_file_kill_switch(True)
    assert flag_path.is_file()
    assert kill_switch.is_automation_disabled() is True
    assert 'file' in kill_switch.kill_switch_source()
    kill_switch.set_file_kill_switch(False)
    assert not flag_path.exists()
    assert kill_switch.is_automation_disabled() is False


def test_file_kill_switch_blocks_automation(flag_path, monkeypatch):
    monkeypatch.setenv('AUTOMATION_DISABLED', 'false')
    monkeypatch.setenv('APPLY_AUTOMATION_ENABLED', 'true')
    kill_switch.set_file_kill_switch(True)
    reason = apply_submission_service.automation_blocked()
    assert reason
    assert 'kill switch' in reason.lower() or 'disabled' in reason.lower()
