# solution/core/store.py
from datetime import datetime
from typing import Dict, Any, Optional

from .models import StoredContext, ContextPushRequest, ContextPushResponse

categories: Dict[str, StoredContext] = {}
merchants: Dict[str, StoredContext] = {}
customers: Dict[str, StoredContext] = {}
triggers: Dict[str, StoredContext] = {}

conversations: Dict[str, Dict[str, Any]] = {}  # conv_id -> state dict


def _store_for_scope(scope: str) -> Optional[Dict[str, StoredContext]]:
    if scope == "category":
        return categories
    if scope == "merchant":
        return merchants
    if scope == "customer":
        return customers
    if scope == "trigger":
        return triggers
    return None


def save_context(req: ContextPushRequest) -> ContextPushResponse:
    store = _store_for_scope(req.scope)
    if store is None:
        return ContextPushResponse(
            accepted=False,
            reason="invalid_scope",
            details=f"Unknown scope {req.scope}",
        )

    existing = store.get(req.context_id)
    if existing:
        if req.version < existing.version:
            return ContextPushResponse(
                accepted=False,
                reason="stale_version",
                current_version=existing.version,
            )
        if req.version == existing.version:
            # idempotent re-push of same version
            return ContextPushResponse(
                accepted=False,
                reason="stale_version",
                current_version=existing.version,
            )

    stored = StoredContext(
        scope=req.scope,
        context_id=req.context_id,
        version=req.version,
        payload=req.payload,
        delivered_at=req.delivered_at,
    )
    store[req.context_id] = stored

    return ContextPushResponse(
        accepted=True,
        ack_id=f"ack_{req.context_id}_v{req.version}",
        stored_at=datetime.utcnow(),
    )


def get_counts():
    return {
        "category": len(categories),
        "merchant": len(merchants),
        "customer": len(customers),
        "trigger": len(triggers),
    }