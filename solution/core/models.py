# solution/core/models.py
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Dict, List, Optional


class StoredContext(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: datetime


# /v1/context
class ContextPushRequest(BaseModel):
    scope: str
    context_id: str
    version: int
    payload: Dict[str, Any]
    delivered_at: datetime


class ContextPushResponse(BaseModel):
    accepted: bool
    ack_id: Optional[str] = None
    stored_at: Optional[datetime] = None
    reason: Optional[str] = None
    current_version: Optional[int] = None
    details: Optional[str] = None


# /v1/tick
class TickRequest(BaseModel):
    now: datetime
    available_triggers: List[str]


class TickAction(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str]
    send_as: str
    trigger_id: str
    template_name: Optional[str] = None
    template_params: Optional[List[str]] = None
    body: str
    cta: str
    suppression_key: str
    rationale: str


class TickResponse(BaseModel):
    actions: List[TickAction]


# /v1/reply
class ReplyRequest(BaseModel):
    conversation_id: str
    merchant_id: str
    customer_id: Optional[str]
    from_role: str
    message: str
    received_at: datetime
    turn_number: int


class ReplyResponse(BaseModel):
    action: str  # "send" | "wait" | "end"
    body: Optional[str] = None
    cta: Optional[str] = None
    wait_seconds: Optional[int] = None
    rationale: str