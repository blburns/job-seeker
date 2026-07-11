"""Tests for proof path helpers."""

from pathlib import Path

from app.services.proof_paths import (
    SCRAPE_PROOF_DIR,
    SUBMISSION_PROOF_DIR,
    list_proof_files,
    resolve_safe_proof_path,
    scrape_proof_path,
    submission_proof_path,
)


def test_scrape_and_submission_dirs_are_distinct():
    assert SCRAPE_PROOF_DIR != SUBMISSION_PROOF_DIR
    assert SCRAPE_PROOF_DIR.endswith('scrape_proofs')
    assert SUBMISSION_PROOF_DIR.endswith('submission_proofs')


def test_resolve_safe_proof_path_rejects_escape(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(SCRAPE_PROOF_DIR).mkdir(parents=True)
    good = Path(SCRAPE_PROOF_DIR) / 'ok.png'
    good.write_bytes(b'png')
    assert resolve_safe_proof_path(str(good)) == good.resolve()

    outside = tmp_path / 'evil.png'
    outside.write_bytes(b'x')
    assert resolve_safe_proof_path(str(outside)) is None


def test_list_proof_files(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    Path(SCRAPE_PROOF_DIR).mkdir(parents=True)
    Path(SUBMISSION_PROOF_DIR).mkdir(parents=True)
    (Path(SCRAPE_PROOF_DIR) / 'a.png').write_bytes(b'a')
    (Path(SUBMISSION_PROOF_DIR) / 'b.png').write_bytes(b'b')
    all_items = list_proof_files(kind='all')
    assert {i['kind'] for i in all_items} == {'scrape', 'submission'}
    assert scrape_proof_path('demo').endswith('.png')
    assert 'indeed' in submission_proof_path('app-1', 'indeed')
