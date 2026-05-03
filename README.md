# magicpin-vera-bot 🧠📲

An AI-powered WhatsApp assistant for magicpin merchants, built for the **magicpin AI Challenge**.  
It reads structured context about categories, merchants, triggers, and customers, then composes **decision-focused, WhatsApp-ready messages** that feel like a smart, domain-aware version of Vera. [file:16][file:19]

---

## 🚀 Live Bot

- **Base URL:** `https://magicpin-vera-bot-x6mj.onrender.com`
- **OpenAPI docs:** `https://magicpin-vera-bot-x6mj.onrender.com/docs`

The bot exposes the exact HTTP contract defined in the testing brief:

- `GET  /v1/healthz`
- `GET  /v1/metadata`
- `POST /v1/context`
- `POST /v1/tick`
- `POST /v1/reply` [file:19]

---

## 🧩 What This Bot Does

Given four structured contexts:

- **CategoryContext** – vertical playbook (voice, offers, peer stats, research digest).  
- **MerchantContext** – specific merchant’s identity, performance, offers, signals.  
- **TriggerContext** – “why now?” event (perf dip, recall due, IPL match, etc.).  
- **CustomerContext** (optional) – individual customer state, preferences, consent. [file:16]

the bot acts as a **deterministic composer**:

```text
compose(category, merchant, trigger, customer?) -> message + CTA
```

For each active trigger it decides:

- **Whether to send anything at all** (strict trigger-based routing; restraint over spam).
- **What to say** (category-correct tone, real numbers, real offers).
- **Who to send as** (`vera` vs `merchant_on_behalf`).
- **What CTA to use** (simple binary or slot choice).
- **How to explain itself** (`rationale` field for the judge).

---

## 🏗 Architecture

**Tech stack**

- **Backend:** FastAPI (Python)
- **Runtime:** Uvicorn ASGI server
- **State:** In-memory context + conversation store (per test run)
- **Deployment:** Render (Free Web Service)

**Key modules**

- `solution/app/main.py`  
  FastAPI app wiring all 5 endpoints and delegating to the core logic.

- `solution/core/models.py`  
  Pydantic models for:
  - stored contexts
  - `/v1/context`, `/v1/tick`, `/v1/reply` request/response schemas

- `solution/core/store.py`  
  Lightweight in-memory “DB”:
  - Category, merchant, customer, trigger contexts
  - Conversation state keyed by `conversation_id`
  - Proper versioning and idempotency for `/v1/context` [file:19]

- `solution/core/composer/routing.py`  
  The orchestration layer:
  - Loads the 4 contexts for each trigger
  - Dispatches to category-specific composers
  - Creates `TickAction`s for `/v1/tick`
  - Handles `/v1/reply` (auto-reply detection, intent transition, hostility exit)

- `solution/core/composer/templates/`  
  Category-specific templates and decision logic, e.g.:
  - `dentists.py` – research digest, performance dip, recall reminders.
  - `restaurants.py` – IPL match-day decisions, delivery vs dine-in focus.
  - (Hooks ready for salons, gyms, pharmacies.)

---

## 🧠 Design Philosophy

1. **Decision engine, not reporting engine**  
   No generic “last 30 days numbers” spam. Every send must be clearly justified by the **trigger kind + payload** (perf dip, research digest, recall due, IPL match, etc.). [file:22]

2. **Strict trigger-based routing**  
   For each category, only specific trigger kinds are handled. Unknown kinds → no message. This matches the brief’s guidance that restraint is better than low-value noise. [file:19]

3. **Category- and merchant-aware copy**
   - Dentists → clinical, peer tone, no miracle claims, source-cited research.
   - Restaurants → operator voice, covers/CTR/AOV language, IPL and match-night realities.
   - Messages always anchor on **real numbers** from the pushed contexts: views, calls, CTR, recall dates, batch IDs, etc. [file:16][file:22]

4. **Simple, compelling CTAs**
   - Binary: “Reply YES to launch the 7-day campaign.”
   - Slot choice: “Reply 1 for Wed 6pm, 2 for Thu 5pm.”
   - No multi-CTA overload; the last line is always the next step.

5. **Robust multi-turn behavior**
   - Detects WhatsApp auto-replies (“Thank you for contacting…”) and exits cleanly.
   - Switches from qualification to action when the merchant says “Ok, let’s do it. What’s next?”
   - Ends gracefully on hostility (“Stop messaging me. This is spam.”). [file:19][file:21]

---

## 🧪 Local Development & Testing

### 1. Setup

```bash
git clone https://github.com/<your-username>/magicpin-ai-challenge.git
cd magicpin-ai-challenge/solution

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run the bot locally

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

Swagger UI (OpenAPI docs) will be at:

- `http://localhost:8080/docs`

### 3. Run the judge simulator (optional but recommended)

From the repo root, configure `judge_simulator.py`:

```python
BOT_URL      = "http://localhost:8080"
LLM_PROVIDER = "gemini"            # or groq/openai/etc.
LLM_API_KEY  = "<your-key>"
LLM_MODEL    = "gemini-flash-latest"
TEST_SCENARIO = "phase2_short"     # or "all", "warmup", "full_evaluation"
```

Then:

```bash
python judge_simulator.py
```

This runs a mini version of the official harness against your bot and prints per-dimension scores plus hints. [file:17]

---

## ☁️ Deployment (Render)

The service is deployed as a **Python Web Service** on Render with:

- **Root Directory:** `solution`
- **Build Command:** `pip install -r requirements.txt`
- **Start Command:**

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

Render injects `$PORT` automatically and expects the app to listen on `0.0.0.0`. [web:59][web:63]

---

## 🔍 Limitations & Next Steps

- Current implementation focuses deeply on dentists and restaurants; salons, gyms, and pharmacies have basic or stub handlers and can be expanded with:
  - Bridal follow-up flows for salons.
  - Seasonal dip reframe and lapsed-member winbacks for gyms.
  - Compliance alerts and chronic refill reminders for pharmacies. [file:22][file:23]

- LLM use is intentionally **deterministic** (temperature ~0) and could be swapped in behind the rule-based templates for more nuanced language while preserving strict trigger/category routing.

---

## 📄 License & Attribution

- Dataset and challenge specification are provided by **magicpin** as part of the **magicpin AI Challenge** and should be used only for this competition context. [file:16]
- All code in this repository is authored by the participant unless otherwise noted.

---

If you’re reviewing this repo as a judge: jump into `solution/core/composer/` to see the trigger-based decision logic, or hit `/docs` on the live URL to explore the endpoints interactively.