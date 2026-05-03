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
    owner = _owner_name(merchant)
    payload = trigger["payload"]
    metric = payload["metric"]          # "calls" or "views"
    delta_pct = payload["delta_pct"]   # e.g. -0.50
    window = payload["window"]         # "7d"
    baseline = payload.get("vs_baseline")

    perf = merchant["performance"]
    views = perf.get("views")
    calls = perf.get("calls")
    ctr = perf.get("ctr")

    peer_stats = category.get("peer_stats", {})
    peer_ctr = peer_stats.get("avg_ctr")

    signals = merchant.get("signals", [])
    active_offers = [o for o in merchant.get("offers", []) if o.get("status") == "active"]
    cleaning_offer = next(
        (o for o in active_offers if "Cleaning" in o["title"]), active_offers[0] if active_offers else None
    )

    metric_label = "phone calls" if metric == "calls" else metric
    drop_pct = int(abs(delta_pct) * 100)

    peer_line = ""
    if peer_ctr is not None:
        peer_line = f" peers ~{peer_ctr*100:.1f}% CTR ke aas-paas hain."

    signal_line = ""
    if "ctr_below_peer_median" in signals:
        signal_line = " Aapki CTR already peer median se neeche flag hui hai."

    offer_text = cleaning_offer["title"] if cleaning_offer else "Dental Cleaning @ ₹299 type offer"

    body = (
        f"Dr. {owner}, last {window} mein aapke {metric_label} ~{drop_pct}% neeche gaye hain "
        f"(baseline ~{baseline} tha). Abhi 30d numbers: {views} views, {calls} calls, CTR {ctr*100:.1f}%."
        f"{peer_line}{signal_line}\n\n"
        f"Sabse fast fix: aapka \"{offer_text}\" ko Google Business Profile post + "
        "WhatsApp dono par next 7 din ke liye highlight kar dete hain.\n\n"
        "Kya main ye 7-day campaign draft kar doon jo aapke high-intent search wale patients ko target kare?"
    )

    cta = "Reply YES to draft the 7-day recovery campaign"

    return {
        "body": body,
        "cta": cta,
        "send_as": "vera",
        "suppression_key": _build_suppression(trigger, category["slug"]),
        "template_name": "dentist_perf_dip_v2",
        "template_params": [],
        "rationale": (
            "Trigger=perf_dip on calls; using drop %, baseline, current 30d metrics, peer CTR and signals to "
            "propose a concrete 7-day campaign around the merchant's active cleaning offer."
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
                    customer: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    return None

    
def compose(category, merchant, trigger, customer) -> Optional[Dict[str, Any]]:
    kind = trigger["kind"]
    scope = trigger["scope"]

    if kind == "research_digest" and scope == "merchant":
        return compose_research_digest(category, merchant, trigger, customer)

    if kind == "perf_dip" and scope == "merchant":
        return compose_perf_dip(category, merchant, trigger, customer)

    if kind == "recall_due" and scope == "customer" and customer is not None:
        return compose_recall_due_customer(category, merchant, trigger, customer)

    # Unknown trigger for dentists → stay silent
    return compose_generic(category, merchant, trigger, customer)