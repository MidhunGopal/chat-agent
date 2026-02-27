"""
Data Hub – Persistent SQLite database simulating the backend systems
(ApplicationSystem, UnderwritingSystem, PolicyAdminSystem, CommunicationSystem) with an event-stream style interaction log.
"""

from __future__ import annotations

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, List, Optional

import config


def _ensure_dir(path: str):
    d = os.path.dirname(path)
    if d:
        os.makedirs(d, exist_ok=True)


class DataHub:
    """Central data layer backed by SQLite (persistent)."""

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or config.SQLITE_DB_PATH
        _ensure_dir(self.db_path)
        self._init_tables()

    # ── Connection helper ────────────────────────────────────────────────

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    # ── Schema bootstrap ─────────────────────────────────────────────────

    def _init_tables(self):
        with self._conn() as conn:
            conn.executescript(
                """
                -- Users table (authentication & roles)
                CREATE TABLE IF NOT EXISTS users (
                    user_id    TEXT PRIMARY KEY,
                    username   TEXT UNIQUE NOT NULL,
                    password   TEXT NOT NULL,
                    full_name  TEXT NOT NULL,
                    role       TEXT NOT NULL DEFAULT 'customer',
                    email      TEXT,
                    created_at TEXT
                );

                -- ApplicationSystem: policies
                CREATE TABLE IF NOT EXISTS policies (
                    policy_id      TEXT PRIMARY KEY,
                    holder_name    TEXT NOT NULL,
                    policy_type    TEXT NOT NULL,
                    status         TEXT NOT NULL DEFAULT 'active',
                    premium        REAL NOT NULL DEFAULT 0.0,
                    start_date     TEXT,
                    end_date       TEXT,
                    details        TEXT DEFAULT '{}',
                    customer_id    TEXT,
                    agent_id       TEXT
                );

                -- UnderwritingSystem: applications
                CREATE TABLE IF NOT EXISTS applications (
                    application_id       TEXT PRIMARY KEY,
                    applicant_name       TEXT NOT NULL,
                    application_type     TEXT NOT NULL,
                    status               TEXT NOT NULL DEFAULT 'submitted',
                    submitted_date       TEXT,
                    underwriting_status  TEXT DEFAULT 'pending',
                    details              TEXT DEFAULT '{}',
                    customer_id          TEXT,
                    agent_id             TEXT
                );

                -- PolicyAdminSystem: underwriting
                CREATE TABLE IF NOT EXISTS underwriting (
                    underwriting_id  TEXT PRIMARY KEY,
                    application_id   TEXT NOT NULL,
                    status           TEXT NOT NULL DEFAULT 'pending',
                    risk_score       REAL,
                    notes            TEXT DEFAULT '',
                    updated_at       TEXT
                );

                -- CommunicationSystem: correspondence / documents
                CREATE TABLE IF NOT EXISTS documents (
                    document_id   TEXT PRIMARY KEY,
                    reference_id  TEXT,
                    doc_type      TEXT NOT NULL,
                    content       TEXT,
                    metadata      TEXT DEFAULT '{}',
                    created_at    TEXT
                );

                -- Event stream / interaction log
                CREATE TABLE IF NOT EXISTS interaction_log (
                    log_id           TEXT PRIMARY KEY,
                    session_id       TEXT,
                    channel          TEXT,
                    intent           TEXT,
                    agent_used       TEXT,
                    user_query       TEXT,
                    response         TEXT,
                    sentiment_score  REAL DEFAULT 0.0,
                    escalated        INTEGER DEFAULT 0,
                    timestamp        TEXT
                );

                -- Knowledge base articles
                CREATE TABLE IF NOT EXISTS knowledge_base (
                    article_id   TEXT PRIMARY KEY,
                    category     TEXT,
                    title        TEXT,
                    content      TEXT,
                    created_at   TEXT
                );
                """
            )

    # ── Policy (POLICYADMINSYSTEM) ──────────────────────────────────────

    def get_policy(self, policy_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM policies WHERE policy_id = ?", (policy_id,)
            ).fetchone()
            return dict(row) if row else None

    def search_policies(self, holder_name: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM policies WHERE holder_name LIKE ?",
                (f"%{holder_name}%",),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_policies(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM policies").fetchall()
            return [dict(r) for r in rows]

    def get_policies_for_user(self, user_id: str, role: str) -> List[Dict[str, Any]]:
        """Get policies filtered by user role."""
        with self._conn() as conn:
            if role == "admin":
                rows = conn.execute("SELECT * FROM policies").fetchall()
            elif role == "agent":
                rows = conn.execute(
                    "SELECT * FROM policies WHERE agent_id = ?", (user_id,)
                ).fetchall()
            else:  # customer
                rows = conn.execute(
                    "SELECT * FROM policies WHERE customer_id = ?", (user_id,)
                ).fetchall()
            return [dict(r) for r in rows]

    def get_applications_for_user(self, user_id: str, role: str) -> List[Dict[str, Any]]:
        """Get applications filtered by user role."""
        with self._conn() as conn:
            if role == "admin":
                rows = conn.execute("SELECT * FROM applications").fetchall()
            elif role == "agent":
                rows = conn.execute(
                    "SELECT * FROM applications WHERE agent_id = ?", (user_id,)
                ).fetchall()
            else:  # customer
                rows = conn.execute(
                    "SELECT * FROM applications WHERE customer_id = ?", (user_id,)
                ).fetchall()
            return [dict(r) for r in rows]

    def upsert_policy(self, data: Dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO policies
                   (policy_id, holder_name, policy_type, status, premium,
                    start_date, end_date, details, customer_id, agent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["policy_id"],
                    data["holder_name"],
                    data["policy_type"],
                    data.get("status", "active"),
                    data.get("premium", 0.0),
                    data.get("start_date", ""),
                    data.get("end_date", ""),
                    json.dumps(data.get("details", {})),
                    data.get("customer_id", ""),
                    data.get("agent_id", ""),
                ),
            )

    # ── Application (APPLICATIONSYSTEM) ────────────────────────────────

    def get_application(self, application_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM applications WHERE application_id = ?",
                (application_id,),
            ).fetchone()
            return dict(row) if row else None

    def search_applications(self, applicant_name: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM applications WHERE applicant_name LIKE ?",
                (f"%{applicant_name}%",),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_all_applications(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM applications").fetchall()
            return [dict(r) for r in rows]

    def upsert_application(self, data: Dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO applications
                   (application_id, applicant_name, application_type, status,
                    submitted_date, underwriting_status, details, customer_id, agent_id)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["application_id"],
                    data["applicant_name"],
                    data["application_type"],
                    data.get("status", "submitted"),
                    data.get("submitted_date", ""),
                    data.get("underwriting_status", "pending"),
                    json.dumps(data.get("details", {})),
                    data.get("customer_id", ""),
                    data.get("agent_id", ""),
                ),
            )

    # ── Underwriting (UNDERWRITINGSYSTEM) ───────────────────────────────

    def get_underwriting(self, application_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM underwriting WHERE application_id = ?",
                (application_id,),
            ).fetchone()
            return dict(row) if row else None

    def upsert_underwriting(self, data: Dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO underwriting
                   (underwriting_id, application_id, status, risk_score, notes, updated_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data["underwriting_id"],
                    data["application_id"],
                    data.get("status", "pending"),
                    data.get("risk_score"),
                    data.get("notes", ""),
                    data.get("updated_at", datetime.utcnow().isoformat()),
                ),
            )

    # ── Documents (COMMUNICATIONSYSTEM) ────────────────────────────────

    def get_document(self, document_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM documents WHERE document_id = ?", (document_id,)
            ).fetchone()
            return dict(row) if row else None

    def store_document(self, data: Dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO documents
                   (document_id, reference_id, doc_type, content, metadata, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    data["document_id"],
                    data.get("reference_id", ""),
                    data["doc_type"],
                    data.get("content", ""),
                    json.dumps(data.get("metadata", {})),
                    data.get("created_at", datetime.utcnow().isoformat()),
                ),
            )

    def search_documents(self, reference_id: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM documents WHERE reference_id = ?", (reference_id,)
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Interaction log (Event Stream) ───────────────────────────────────

    def log_interaction(self, data: Dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO interaction_log
                   (log_id, session_id, channel, intent, agent_used,
                    user_query, response, sentiment_score, escalated, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["log_id"],
                    data.get("session_id", ""),
                    data.get("channel", ""),
                    data.get("intent", ""),
                    data.get("agent_used", ""),
                    data.get("user_query", ""),
                    data.get("response", ""),
                    data.get("sentiment_score", 0.0),
                    1 if data.get("escalated", False) else 0,
                    data.get("timestamp", datetime.utcnow().isoformat()),
                ),
            )

    def get_session_history(self, session_id: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM interaction_log WHERE session_id = ? ORDER BY timestamp",
                (session_id,),
            ).fetchall()
            return [dict(r) for r in rows]

    def get_recent_interactions(self, limit: int = 50) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM interaction_log ORDER BY timestamp DESC LIMIT ?",
                (limit,),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Knowledge base ───────────────────────────────────────────────────

    def add_knowledge_article(self, data: Dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO knowledge_base
                   (article_id, category, title, content, created_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (
                    data["article_id"],
                    data.get("category", "general"),
                    data.get("title", ""),
                    data.get("content", ""),
                    data.get("created_at", datetime.utcnow().isoformat()),
                ),
            )

    def search_knowledge(self, keyword: str) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM knowledge_base WHERE content LIKE ? OR title LIKE ?",
                (f"%{keyword}%", f"%{keyword}%"),
            ).fetchall()
            return [dict(r) for r in rows]

    # ── Users / Authentication ───────────────────────────────────────────

    def upsert_user(self, data: Dict[str, Any]):
        with self._conn() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO users
                   (user_id, username, password, full_name, role, email, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    data["user_id"],
                    data["username"],
                    data["password"],
                    data["full_name"],
                    data.get("role", "customer"),
                    data.get("email", ""),
                    data.get("created_at", datetime.utcnow().isoformat()),
                ),
            )

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Validate credentials and return user record if valid."""
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE username = ? AND password = ?",
                (username, password),
            ).fetchone()
            return dict(row) if row else None

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        with self._conn() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_all_users(self) -> List[Dict[str, Any]]:
        with self._conn() as conn:
            rows = conn.execute("SELECT user_id, username, full_name, role, email FROM users").fetchall()
            return [dict(r) for r in rows]

    def get_policy_for_user(self, policy_id: str, user_id: str, role: str) -> Optional[Dict[str, Any]]:
        """Get a specific policy, filtered by user access."""
        with self._conn() as conn:
            if role == "admin":
                row = conn.execute(
                    "SELECT * FROM policies WHERE policy_id = ?", (policy_id,)
                ).fetchone()
            elif role == "agent":
                row = conn.execute(
                    "SELECT * FROM policies WHERE policy_id = ? AND agent_id = ?",
                    (policy_id, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM policies WHERE policy_id = ? AND customer_id = ?",
                    (policy_id, user_id),
                ).fetchone()
            return dict(row) if row else None

    def get_application_for_user(self, application_id: str, user_id: str, role: str) -> Optional[Dict[str, Any]]:
        """Get a specific application, filtered by user access."""
        with self._conn() as conn:
            if role == "admin":
                row = conn.execute(
                    "SELECT * FROM applications WHERE application_id = ?", (application_id,)
                ).fetchone()
            elif role == "agent":
                row = conn.execute(
                    "SELECT * FROM applications WHERE application_id = ? AND agent_id = ?",
                    (application_id, user_id),
                ).fetchone()
            else:
                row = conn.execute(
                    "SELECT * FROM applications WHERE application_id = ? AND customer_id = ?",
                    (application_id, user_id),
                ).fetchone()
            return dict(row) if row else None

    def search_policies_for_user(self, holder_name: str, user_id: str, role: str) -> List[Dict[str, Any]]:
        """Search policies by holder name, filtered by user access."""
        with self._conn() as conn:
            if role == "admin":
                rows = conn.execute(
                    "SELECT * FROM policies WHERE holder_name LIKE ?",
                    (f"%{holder_name}%",),
                ).fetchall()
            elif role == "agent":
                rows = conn.execute(
                    "SELECT * FROM policies WHERE holder_name LIKE ? AND agent_id = ?",
                    (f"%{holder_name}%", user_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM policies WHERE holder_name LIKE ? AND customer_id = ?",
                    (f"%{holder_name}%", user_id),
                ).fetchall()
            return [dict(r) for r in rows]

    def search_applications_for_user(self, applicant_name: str, user_id: str, role: str) -> List[Dict[str, Any]]:
        """Search applications by applicant name, filtered by user access."""
        with self._conn() as conn:
            if role == "admin":
                rows = conn.execute(
                    "SELECT * FROM applications WHERE applicant_name LIKE ?",
                    (f"%{applicant_name}%",),
                ).fetchall()
            elif role == "agent":
                rows = conn.execute(
                    "SELECT * FROM applications WHERE applicant_name LIKE ? AND agent_id = ?",
                    (f"%{applicant_name}%", user_id),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM applications WHERE applicant_name LIKE ? AND customer_id = ?",
                    (f"%{applicant_name}%", user_id),
                ).fetchall()
            return [dict(r) for r in rows]


# ── Singleton ────────────────────────────────────────────────────────────────

_hub: Optional[DataHub] = None


def get_data_hub() -> DataHub:
    global _hub
    if _hub is None:
        _hub = DataHub()
    return _hub
