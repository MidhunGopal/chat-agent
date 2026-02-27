"""Shared utility helpers."""

from __future__ import annotations

import uuid
from datetime import datetime


def new_id(prefix: str = "id") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:12]}"


def now_iso() -> str:
    return datetime.utcnow().isoformat()


def truncate(text: str, max_len: int = 500) -> str:
    return text[:max_len] + "..." if len(text) > max_len else text
