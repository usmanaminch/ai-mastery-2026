"""
claude_zt/audit.py — Audit Logger (Foundation Tier)

Logs every agent action to the queries table.
Every row has: agent_id, agent_role, query_text,
mode, chunks_retrieved, response_text, latency_ms.

This is the audit trail a compliance auditor wants to see:
- WHO performed the action (agent_id + role)
- WHAT they asked (query_text)
- WHAT context they used (mode)
- WHAT they retrieved (chunks_retrieved)
- WHAT they returned (response_text)
- HOW LONG it took (latency_ms)

For FedRAMP or SOC 2, this table IS the evidence of human oversight.
"""

import time
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from db.connection import get_engine
from claude_zt.identity import AgentIdentity


class AuditLogger:
    def __init__(self, agent: AgentIdentity):
        self.agent = agent
        self._start_time = None

    def start_query(self):
        """Call this when a query begins to start the latency timer."""
        self._start_time = time.time()

    def log(
        self,
        query_text: str,
        mode: str = "standard",
        chunks_retrieved: int = 0,
        response_text: str = "",
    ):
        """Write a completed query to the audit log."""
        latency_ms = None
        if self._start_time:
            latency_ms = int((time.time() - self._start_time) * 1000)

        try:
            engine = get_engine()
            with engine.connect() as conn:
                conn.execute(text("""
                    INSERT INTO queries
                        (agent_id, agent_role, query_text, mode,
                         chunks_retrieved, response_text, latency_ms)
                    VALUES
                        (:agent_id, :agent_role, :query_text, :mode,
                         :chunks_retrieved, :response_text, :latency_ms)
                """), {
                    "agent_id": self.agent.agent_id,
                    "agent_role": self.agent.role,
                    "query_text": query_text[:2000],
                    "mode": mode,
                    "chunks_retrieved": chunks_retrieved,
                    "response_text": response_text[:10000] if response_text else "",
                    "latency_ms": latency_ms,
                })
                conn.commit()
        except Exception as e:
            # Audit logging must never crash the main application
            print(f"[audit warning] Failed to log query: {e}", flush=True)

    def __enter__(self):
        self.start_query()
        return self

    def __exit__(self, *args):
        pass
