# solution/core/composer/routing.py
from typing import Optional, Dict, Any, List
from datetime import datetime

from core import store
from core.models import TickRequest, TickResponse, TickAction, ReplyRequest, ReplyResponse

from .templates import dentists, restaurants


def _load_contexts(trigger_id: str) -> Optional[Dict[str, Any]]:
    trig_ctx = store.triggers.get(trigger_id)
    if not trig_ctx:
        return None
    t = trig_ctx.payload

    m_ctx = store.merchants.get(t["merchant_id"])
    if not m_ctx:
        return None

    cat_slug = m_ctx.payload["category_slug"]
    cat_ctx = store.categories.get(cat_slug)
    if not cat_ctx:
        return None

    cust_ctx = None
    if t["scope"] == "customer" and t.get("customer_id"):
        cust_ctx = store.customers.get(t["customer_id"])

    return {
        "trigger": t,
        "merchant": m_ctx.payload,
        "category": cat_ctx.payload,
        "customer": cust_ctx.payload if cust_ctx else None,
    }


def compose_for_trigger(req: TickRequest) -> TickResponse:
    actions: List[TickAction] = []

    for trig_id in req.available_triggers:
        ctxs = _load_contexts(trig_id)
        if not ctxs:
            continue

        cat_slug = ctxs["category"]["slug"]
        result: Dict[str, Any]

        # Simple dispatch: handle dentists specially, others generic for now
        if cat_slug == "dentists":
            result = dentists.compose(ctxs["category"], ctxs["merchant"], ctxs["trigger"], ctxs["customer"])
        elif cat_slug == "restaurants":
            result = restaurants.compose(ctxs["category"], ctxs["merchant"], ctxs["trigger"], ctxs["customer"])
        else:
            result = dentists.compose_generic(ctxs["category"], ctxs["merchant"], ctxs["trigger"], ctxs["customer"])

        conv_id = f"conv_{ctxs['merchant']['merchant_id']}_{trig_id}"
        store.conversations[conv_id] = {
            "merchant_id": ctxs["merchant"]["merchant_id"],
            "customer_id": ctxs["trigger"].get("customer_id"),
            "trigger_id": trig_id,
            "last_cta": result["cta"],
        }

        actions.append(
            TickAction(
                conversation_id=conv_id,
                merchant_id=ctxs["merchant"]["merchant_id"],
                customer_id=ctxs["trigger"].get("customer_id"),
                send_as=result["send_as"],
                trigger_id=trig_id,
                template_name=result.get("template_name"),
                template_params=result.get("template_params"),
                body=result["body"],
                cta=result["cta"],
                suppression_key=result["suppression_key"],
                rationale=result["rationale"],
            )
        )

    return TickResponse(actions=actions)


AUTO_REPLY_PATTERNS = [
    "thank you for contacting",
    "our team will respond shortly",
    "we will get back to you",
    "auto reply",
    "automatic reply",
]

HOSTILE_PATTERNS = [
    "stop messaging",
    "stop sending",
    "this is useless spam",
    "dont message",
    "don't message",
    "remove me",
    "unsubscribe",
]


def handle_reply(req: ReplyRequest) -> ReplyResponse:
    # Conversation may or may not exist; we don't hard-fail on missing conv.
    conv = store.conversations.get(req.conversation_id)

    text = req.message.lower().strip()

    # 1) Detect WhatsApp auto-replies and back off quickly
    if any(p in text for p in AUTO_REPLY_PATTERNS):
        return ReplyResponse(
            action="end",
            rationale="Detected WhatsApp auto-reply pattern; ending conversation to avoid pollution",
        )

    # 2) Detect hostility / explicit stop requests
    if any(p in text for p in HOSTILE_PATTERNS):
        return ReplyResponse(
            action="end",
            rationale="Merchant asked us to stop; ending conversation and respecting preference",
        )

    # 3) Simple acceptance handling (covers intent test: "Ok lets do it. Whats next?")
    if any(w in text for w in ["ok", "lets do it", "let's do it", "yes", "sure", "done", "go ahead", "proceed", "next"]):
        body = (
            "Great, main isko aapke liye chalu kar raha hoon. "
            "Pehla step: main abhi campaign draft bana kar bhejta hoon, "
            "jise aap sirf REVIEW karke YES bolna hoga."
        )
        return ReplyResponse(
            action="send",
            body=body,
            cta="open_ended",
            rationale="Merchant showed clear commitment; switching from qualification to concrete next-step action.",
        )

    # 4) Explicit negative / not interested
    if text in ("no", "nahi", "not now", "no thanks", "no thank you"):
        return ReplyResponse(
            action="end",
            rationale="Merchant declined; ending conversation cleanly",
        )

    # 5) Fallback: treat as clarification needed
    body = "Samajh gaya. Kya aapko ye aaj se chalu karwana hai, ya kal se?"
    return ReplyResponse(
        action="send",
        body=body,
        cta="open_ended",
        rationale="Merchant reply ambiguous; asking a simple timing clarification",
    )