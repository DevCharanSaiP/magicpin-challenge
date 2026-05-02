# solution/core/composer/templates/dentists.py
from typing import Dict, Any, Optional


def _owner_name(merchant: Dict[str, Any]) -> str:
    ident = merchant["identity"]
    return ident.get("owner_first_name") or ident.get("name")


def _build_suppression(trigger: Dict[str, Any], category_slug: str) -> str:
    base = trigger.get("suppression_key") or trigger["id"]
    return f"{category_slug}:{base}"


def compose_research_digest(category: Dict[str, Any],
                            merchant: Dict[str, Any],
                            trigger: Dict[str, Any],
                            customer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    owner = _owner_name(merchant)
    digest_items = category["digest"]
    top_id = trigger["payload"]["top_item_id"]
    top_item = next(d for d in digest_items if d["id"] == top_id)
    title = top_item["title"]
    source = top_item["source"]
    actionable = top_item.get("actionable", "")

    body = (
        f"Dr. {owner}, ek quick research update: \"{title}\" ({source}).\n\n"
        f"{actionable}\n\n"
        "Kya main isko aapke high-risk adult patients ke liye "
        "60-sec WhatsApp explain mein convert kar doon?"
    )
    cta = "Reply YES for the 60-sec patient WhatsApp draft"

    return {
        "body": body,
        "cta": cta,
        "send_as": "vera",
        "suppression_key": _build_suppression(trigger, category["slug"]),
        "template_name": "dentist_research_digest_v1",
        "template_params": [],
        "rationale": (
            "Trigger=research_digest (merchant scope) for dentist; using top digest item with source-cited "
            "clinical anchor and offering low-friction patient-ed draft as next step."
        ),
    }


def compose_perf_dip(category: Dict[str, Any],
                     merchant: Dict[str, Any],
                     trigger: Dict[str, Any],
                     customer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Handle perf_dip on calls/views, framed as a concrete growth nudge.
    """
    owner = _owner_name(merchant)
    payload = trigger["payload"]
    metric = payload["metric"]          # e.g. "calls"
    delta_pct = payload["delta_pct"]   # e.g. -0.50
    window = payload["window"]         # "7d"
    baseline = payload.get("vs_baseline")

    perf = merchant["performance"]
    calls = perf.get("calls")
    views = perf.get("views")
    ctr = perf.get("ctr")

    metric_human = "phone calls" if metric == "calls" else metric
    drop_pct = int(abs(delta_pct) * 100)

    body = (
        f"Dr. {owner}, last {window} mein aapke {metric_human} ~{drop_pct}% neeche gaye hain "
        f"(baseline ~{baseline} tha). Abhi 30d numbers: {views} views, {calls} calls, CTR {ctr:.1%}.\n\n"
        "Sabse fast fix: ek simple \"Dental Cleaning @ ₹299\" type offer ko Google Business Profile post "
        "aur WhatsApp dono par 7 din ke liye chala dete hain.\n\n"
        "Kya main aapke liye ye 7-day cleaning campaign draft kar doon?"
    )
    cta = "Reply YES to launch the 7-day cleaning campaign draft"

    return {
        "body": body,
        "cta": cta,
        "send_as": "vera",
        "suppression_key": _build_suppression(trigger, category["slug"]),
        "template_name": "dentist_perf_dip_v1",
        "template_params": [],
        "rationale": (
            "Trigger=perf_dip on calls; combining drop %, baseline and current 30d stats to recommend a "
            "7-day cleaning offer campaign as the lowest-friction fix."
        ),
    }


def compose_recall_due_customer(category: Dict[str, Any],
                                merchant: Dict[str, Any],
                                trigger: Dict[str, Any],
                                customer: Dict[str, Any]) -> Dict[str, Any]:
    """
    Customer-facing recall message using due date + available slots + language preference.
    """
    owner = _owner_name(merchant)
    cust_name = customer["identity"]["name"]
    lang = customer["identity"].get("language_pref", "en").lower()
    payload = trigger["payload"]
    service_due = payload["service_due"]          # e.g. "6_month_cleaning"
    due_date = payload["due_date"]
    slots = payload.get("available_slots", [])
    label1 = slots[0]["label"] if slots else "next week"

    service_text = service_due.replace("_", " ")

    if "hi" in lang:
        body = (
            f"Hi {cust_name}, Dr. {owner} yahan. "
            f"Aapka {service_text} {due_date} ke aas-paas due hai. "
            f"Kya main aapke liye {label1} slot block kar doon?\n\n"
            "Reply 1 agar yahi time theek hai, ya 2 agar aapko koi aur din/slot chahiye."
        )
        cta = "Reply 1 to confirm this slot, 2 for another day"
    else:
        body = (
            f"Hi {cust_name}, this is Dr. {owner}. "
            f"Your {service_text} is due around {due_date}. "
            f"Shall I block {label1} for you?\n\n"
            "Reply 1 if this time works, or 2 if you prefer a different day/slot."
        )
        cta = "Reply 1 to confirm, 2 for a different slot"

    return {
        "body": body,
        "cta": cta,
        "send_as": "merchant_on_behalf",
        "suppression_key": _build_suppression(trigger, category["slug"]),
        "template_name": "dentist_recall_due_v1",
        "template_params": [],
        "rationale": (
            "Trigger=recall_due (customer scope); using due date and first available slot plus "
            "customer language preference to send a low-friction 1/2 slot-confirmation ask."
        ),
    }


def compose_generic(category: Dict[str, Any],
                    merchant: Dict[str, Any],
                    trigger: Dict[str, Any],
                    customer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    owner = _owner_name(merchant)
    perf = merchant.get("performance", {})
    views = perf.get("views")
    calls = perf.get("calls")
    ctr = perf.get("ctr")

    body = (
        f"Dr. {owner}, last 30 din mein aapke profile numbers: {views} views, {calls} calls, "
        f"CTR {ctr:.1%}. Chaho to main ek simple 1-page summary bana sakta hoon "
        "jisme views, calls aur peer-comparison clearly dikhunga."
    )
    cta = "Reply YES for the 1-page performance summary"

    return {
        "body": body,
        "cta": cta,
        "send_as": "vera" if trigger["scope"] == "merchant" else "merchant_on_behalf",
        "suppression_key": _build_suppression(trigger, category["slug"]),
        "template_name": "generic_summary_v1",
        "template_params": [],
        "rationale": "Generic dentist nudge when no specialised handler; offers low-friction performance summary.",
    }


def compose(category: Dict[str, Any],
            merchant: Dict[str, Any],
            trigger: Dict[str, Any],
            customer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    kind = trigger["kind"]
    scope = trigger["scope"]

    if kind == "research_digest" and scope == "merchant":
        return compose_research_digest(category, merchant, trigger, customer)

    if kind == "perf_dip" and scope == "merchant":
        return compose_perf_dip(category, merchant, trigger, customer)

    if kind == "recall_due" and scope == "customer" and customer is not None:
        return compose_recall_due_customer(category, merchant, trigger, customer)

    # TODO: handle renewal_due, review_theme_emerged, etc.

    return compose_generic(category, merchant, trigger, customer)