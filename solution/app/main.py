# solution/app/main.py
from fastapi import FastAPI
from datetime import datetime
import time

from core import store
from core.models import (
    ContextPushRequest, ContextPushResponse,
    TickRequest, TickResponse,
    ReplyRequest, ReplyResponse,
)
from core.composer.routing import compose_for_trigger, handle_reply

app = FastAPI(title="magicpin-vera-bot")

START_TIME = time.time()

TEAM_META = {
    "team_name": "YourTeamName",
    "team_members": ["Your Name"],
    "model": "rule-based composer",
    "approach": "deterministic 4-context composer with per-category templates",
    "contact_email": "you@example.com",
    "version": "composer_v1",
    "submitted_at": datetime.utcnow().isoformat() + "Z",
}


@app.get("/v1/healthz")
def healthz():
    return {
        "status": "ok",
        "uptime_seconds": int(time.time() - START_TIME),
        "contexts_loaded": store.get_counts(),
    }


@app.get("/v1/metadata")
def metadata():
    return TEAM_META


@app.post("/v1/context", response_model=ContextPushResponse)
def push_context(req: ContextPushRequest):
    return store.save_context(req)


@app.post("/v1/tick", response_model=TickResponse)
def tick(req: TickRequest):
    return compose_for_trigger(req)


@app.post("/v1/reply", response_model=ReplyResponse)
def reply(req: ReplyRequest):
    return handle_reply(req)