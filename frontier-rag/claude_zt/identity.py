"""
claude_zt/identity.py — Agent Identity (Foundation Tier)

Every agent session gets a unique, ephemeral identity.
UUID v4 uses the OS's cryptographic RNG — 128 bits of entropy,
impossible to predict or collide in practice.

Why ephemeral?
A new identity per session means a compromised session cannot
be replayed. If you see agent_id X in your audit logs, it maps
to exactly one session at one point in time. Nothing more.

Why role-scoped?
The retriever fetches documents. The synthesizer calls Claude.
They are separate roles with separate identities so you can
enforce different permissions on each in the future (Enterprise tier).
"""

import uuid
from datetime import datetime
from dataclasses import dataclass, field

VALID_ROLES = {"retriever", "synthesizer", "ingester"}


@dataclass
class AgentIdentity:
    role: str
    agent_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def __post_init__(self):
        if self.role not in VALID_ROLES:
            raise ValueError(f"Invalid role '{self.role}'. Must be one of: {VALID_ROLES}")

    def __str__(self):
        return f"[{self.role}:{self.agent_id[:8]}]"

    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "role": self.role,
            "created_at": self.created_at,
        }


def new_retriever() -> AgentIdentity:
    """Create a new retriever agent identity."""
    return AgentIdentity(role="retriever")


def new_synthesizer() -> AgentIdentity:
    """Create a new synthesizer agent identity."""
    return AgentIdentity(role="synthesizer")


def new_ingester() -> AgentIdentity:
    """Create a new ingester agent identity."""
    return AgentIdentity(role="ingester")
