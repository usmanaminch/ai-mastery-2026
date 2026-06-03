"""
claude_zt — Zero Trust wrapper for AI agent calls (Foundation Tier)

Usage:
    from claude_zt.identity import new_retriever, new_synthesizer
    from claude_zt.validator import validate_query
    from claude_zt.audit import AuditLogger

    agent = new_retriever()
    result = validate_query(user_input)
    if result.is_valid:
        with AuditLogger(agent) as logger:
            # ... do retrieval ...
            logger.log(query_text=user_input, chunks_retrieved=5, response_text=answer)
"""
from claude_zt.identity import AgentIdentity, new_retriever, new_synthesizer, new_ingester
from claude_zt.validator import validate_query, ValidationResult
from claude_zt.audit import AuditLogger

__all__ = [
    "AgentIdentity",
    "new_retriever",
    "new_synthesizer",
    "new_ingester",
    "validate_query",
    "ValidationResult",
    "AuditLogger",
]
