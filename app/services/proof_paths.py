"""Canonical locations for scrape and submission proof screenshots."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List, Optional, Tuple

# Keep scrape vs submission proofs in separate folders under instance/.
SCRAPE_PROOF_DIR = os.path.join('instance', 'scrape_proofs')
SUBMISSION_PROOF_DIR = os.path.join('instance', 'submission_proofs')


def ensure_proof_dirs() -> None:
    os.makedirs(SCRAPE_PROOF_DIR, exist_ok=True)
    os.makedirs(SUBMISSION_PROOF_DIR, exist_ok=True)


def scrape_proof_path(name: str) -> str:
    ensure_proof_dirs()
    safe = Path(name).name
    if not safe.endswith('.png'):
        safe = f'{safe}.png'
    return os.path.join(SCRAPE_PROOF_DIR, safe)


def submission_proof_path(application_id: str, portal: str = '') -> str:
    ensure_proof_dirs()
    suffix = f'_{portal}' if portal else ''
    return os.path.join(SUBMISSION_PROOF_DIR, f'{application_id}{suffix}.png')


def allowed_proof_roots() -> Tuple[Path, ...]:
    return (
        Path(SCRAPE_PROOF_DIR).resolve(),
        Path(SUBMISSION_PROOF_DIR).resolve(),
    )


def resolve_safe_proof_path(stored_path: str) -> Optional[Path]:
    """Return an absolute Path if stored_path is under an allowed proof root."""
    if not stored_path:
        return None
    candidate = Path(stored_path)
    if not candidate.is_absolute():
        candidate = Path.cwd() / candidate
    try:
        resolved = candidate.resolve()
    except OSError:
        return None
    for root in allowed_proof_roots():
        try:
            resolved.relative_to(root)
            if resolved.is_file():
                return resolved
        except ValueError:
            continue
    return None


def list_proof_files(kind: str = 'all', limit: int = 100) -> List[dict]:
    """List proof PNGs for admin audit UI. kind: scrape|submission|all."""
    ensure_proof_dirs()
    roots: Iterable[Tuple[str, Path]] = []
    if kind in ('scrape', 'all'):
        roots = list(roots) + [('scrape', Path(SCRAPE_PROOF_DIR))]
    if kind in ('submission', 'all'):
        roots = list(roots) + [('submission', Path(SUBMISSION_PROOF_DIR))]

    items = []
    for label, root in roots:
        if not root.exists():
            continue
        for path in sorted(root.glob('*.png'), key=lambda p: p.stat().st_mtime, reverse=True):
            stat = path.stat()
            items.append({
                'kind': label,
                'name': path.name,
                'path': str(path),
                'size': stat.st_size,
                'modified': stat.st_mtime,
            })
            if len(items) >= limit:
                return items
    return items
