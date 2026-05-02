from typing import Dict, Any, Optional


def _owner_name(merchant: Dict[str, Any]) -> str:
    ident = merchant["identity"]
    return ident.get("owner_first_name") or ident.get("name")


def _build_suppression(trigger: Dict[str, Any], category_slug: str) -> str:
    base = trigger.get("suppression_key") or trigger["id"]
    return f"{category_slug}:{base}"


def compose_ipl_match_today(category: Dict[str, Any],
                            merchant: Dict[str, Any],
                            trigger: Dict[str, Any],
                            customer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Restaurant IPL match trigger, following the case-study shape:
    skip Saturday dine-in promo, lean into delivery using existing offers.
    """
    owner = _owner_name(merchant)
    payload = trigger["payload"]
    match = payload["match"]          # e.g. "DC vs MI"
    venue = payload["venue"]
    city = payload["city"]
    is_weeknight = payload.get("is_weeknight", False)

    offers = merchant.get("offers", [])
    bogo = next((o for o in offers if "BOGO" in o["title"].upper() or "Buy 1 Pizza Get 1" in o["title"]), None)

    if is_weeknight:
        # Simple match-night push on weekdays
        body = (
            f"Suresh, aaj ka match {match} {venue} ({city}) mein hai — weeknight games usually "
            "deliveries + dine-in dono badhate hain.\n\n"
            f"Aapka active offer: \"{bogo['title']}\".\n"
            "Kya isko aaj ke match-night ke liye spotlight kar dein Swiggy/Zomato + Insta story par?"
        )
        cta = "Reply YES and I’ll draft the Swiggy banner + Insta story copy"
    else:
        # Weekend contrarian guidance: follow case-study 5 shape
        body = (
            f"Quick heads-up {owner}, aaj ka match {match} {venue} ({city}) mein hai, 7:30pm.\n\n"
            "Important: Saturday IPL matches usually shift ~12% restaurant covers home pe — log TV pe dekhte hain.\n"
            "Isliye aaj dine-in match-night promo skip karna better hai. Instead, aapka existing "
            f"offer \"{bogo['title']}\" ko delivery-only Saturday special bana dete hain.\n\n"
            "Kya main aapke liye Swiggy banner + ek short Insta story draft kar doon? 10 min mein ready."
        )
        cta = "Reply YES for Swiggy banner + Insta story draft"

    return {
        "body": body,
        "cta": cta,
        "send_as": "vera",
        "suppression_key": _build_suppression(trigger, category["slug"]),
        "template_name": "restaurant_ipl_match_v1",
        "template_params": [],
        "rationale": (
            "Trigger=ipl_match_today for restaurant; using match details and weekend vs weeknight behavior "
            "to recommend either match-night push (weeknight) or delivery-only focus (Saturday) "
            "with existing BOGO offer."
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
        f"{owner}, last 30 din mein aapke restaurant ke numbers: {views} views, {calls} calls, "
        f"CTR {ctr:.1%}. Chaho to main ek simple 1-page summary bana sakta hoon "
        "jisme dine-in vs delivery levers clearly dikhunga."
    )
    cta = "Reply YES for the 1-page performance summary"

    return {
        "body": body,
        "cta": cta,
        "send_as": "vera",
        "suppression_key": _build_suppression(trigger, category["slug"]),
        "template_name": "restaurant_generic_summary_v1",
        "template_params": [],
        "rationale": "Generic restaurant nudge when no specialised handler; offers low-friction performance summary.",
    }


def compose(category: Dict[str, Any],
            merchant: Dict[str, Any],
            trigger: Dict[str, Any],
            customer: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    kind = trigger["kind"]

    if kind == "ipl_match_today":
        return compose_ipl_match_today(category, merchant, trigger, customer)

    # TODO: add active_planning_intent, seasonal_perfdip, review_theme_emerged
    return compose_generic(category, merchant, trigger, customer)