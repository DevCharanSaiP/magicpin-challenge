# magicpin-vera-bot

An HTTP service implementing a merchant AI assistant compatible with the **magicpin AI Challenge** specification. The service consumes structured category, merchant, trigger, and customer contexts and produces WhatsApp-ready messages that help merchants run better marketing and customer communication workflows.

---

## 1. Overview

This repository contains:

- A FastAPI-based web service exposing the required endpoints:
  - `GET  /v1/healthz`
  - `GET  /v1/metadata`
  - `POST /v1/context`
  - `POST /v1/tick`
  - `POST /v1/reply`
- A rule-based, deterministic “composer” that:
  - Interprets the 4-context framework defined in the challenge brief.
  - Chooses when to send a message for an active trigger.
  - Constructs messages that are specific, category-appropriate, and action-oriented.
- Local tooling (`judge_simulator.py`) to run the same test harness the organisers use.

The service is currently deployed at:

- `https://magicpin-vera-bot-x6mj.onrender.com`

---

## 2. Architecture

### 2.1 High-level design

The system is deliberately simple and deterministic:

- The HTTP layer is implemented in FastAPI and Uvicorn.
- Contexts are stored in memory for the duration of a test run.
- Composition is handled by a set of category-specific template modules selected by `category.slug` and `trigger.kind`. 
- Multi-turn behaviour (auto-reply detection, hostile exits, intent transition) is implemented in a small reply handler.

LLMs are used only in the external judge harness (not in this service) to score outputs. The service itself does not call any external LLM APIs during composition.

### 2.2 Code layout

Key directories and files:

- `solution/app/main.py`  
  FastAPI application, endpoint definitions, and wiring into the core modules.

- `solution/core/models.py`  
  Pydantic models matching the request/response shapes for `v1/context`, `v1/tick`, `v1/reply`, together with the internal `StoredContext` model.

- `solution/core/store.py`  
  In-memory data store:
  - Category, merchant, customer, and trigger contexts keyed by `context_id`.
  - Conversation state keyed by `conversation_id`.
  - Version-aware, idempotent writes for `/v1/context`.

- `solution/core/composer/routing.py`  
  Orchestrates composition:
  - Loads the four contexts for each trigger.
  - Dispatches to the appropriate category template module.
  - Builds `TickResponse.actions` for `/v1/tick`.
  - Implements `/v1/reply` behaviour including:
    - Auto-reply detection.
    - Hostile “stop messaging me” exits.
    - Intent transition when a merchant says “Ok, let’s do it. What’s next?”. 

- `solution/core/composer/templates/`  
  Category-specific composition logic, for example:
  - `dentists.py` for research digests, performance dips, and recall reminders.
  - `restaurants.py` for IPL match-day decisions and performance nudges.
  Additional modules for salons, gyms, and pharmacies can be added here. 

---

## 3. Composition Strategy

The composer operates on the four contexts defined in the challenge brief: `CategoryContext`, `MerchantContext`, `TriggerContext`, and `CustomerContext`.

### 3.1 Trigger-driven routing

For each `v1/tick` call:

1. The judge provides a list of active `trigger_id`s.
2. The service loads the associated trigger, merchant, category, and optional customer.
3. Based on `category.slug` and `trigger.kind`, it selects a specialised handler. For example:
   - Dentists:
     - `research_digest` → research update with source-cited anchor and patient-education CTA.
     - `perf_dip` → 7-day offer campaign targeting a measurable performance dip.
     - `recall_due` → customer-facing recall reminder with slots.
   - Restaurants:
     - `ipl_match_today` → guidance on whether to run a match-night promo (weekday vs Saturday) and how to position existing offers.

If there is no specialised handler for a given `(category, kind)` combination, the service opts not to send anything for that trigger. This “strict routing” design matches the brief’s guidance that restraint is preferable to generic low-value messaging. 

### 3.2 Message characteristics

For each supported trigger, the templates aim to ensure:

- **Specificity**  
  Messages refer to concrete, verifiable facts: number of views, calls, CTR, recall dates, batch IDs, match details, etc., always taken from the contexts, never invented. 

- **Category fit**  
  Tone and vocabulary match the vertical:
  - Dentists: clinical peer tone, research citations, no cure/guaranteed language.
  - Restaurants: operator language such as covers, CTR, match-night behaviour.

- **Merchant fit**  
  Messages reference the merchant’s own:
  - Offers (`MerchantContext.offers`).
  - Signals (e.g., `ctr_below_peer_median`).
  - Performance metrics and location where relevant.

- **Trigger relevance and decision quality**  
  Every message answers “why now?” based on the trigger, and usually proposes one concrete next action (e.g. 7-day campaign, IPL special, recall slot hold).

- **Engagement compulsion**  
  CTAs are low-friction and clearly stated in the last sentence, typically:
  - Binary: “Reply YES to launch the campaign.”
  - Slot choice: “Reply 1 for Wed 6pm, 2 for Thu 5pm.”

---

## 4. Multi-turn Behaviour

The `/v1/reply` endpoint implements a small but robust state machine aligned with the challenge replay scenarios.

It handles:

- **Auto-reply detection**  
  Recognises canonical WhatsApp Business auto-replies (“Thank you for contacting…”) and ends the conversation early to avoid polluting engagement metrics.

- **Intent transition**  
  When a merchant sends an explicit commitment (“Ok, let’s do it. What’s next?”), the bot switches from qualification mode to executing the next concrete step.

- **Hostile exits**  
  For messages such as “Stop messaging me. This is spam.” the bot ends the conversation immediately with a clear rationale and does not attempt to re-engage.

---

## 5. Running Locally

### 5.1 Prerequisites

- Python 3.10+
- `pip` / virtualenv

### 5.2 Setup

```bash
git clone https://github.com/<your-username>/magicpin-ai-challenge.git
cd magicpin-ai-challenge/solution

python -m venv .venv
source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### 5.3 Start the service

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8080
```

The OpenAPI UI will be available at `http://localhost:8080/docs`.

---

## 6. Judge Simulator

The repository includes `judge_simulator.py`, which mirrors the magicpin judge harness for local testing.

Basic usage:

1. Configure at the top of `judge_simulator.py`:

   ```python
   BOT_URL      = "http://localhost:8080"
   LLM_PROVIDER = "gemini"          # or another supported provider
   LLM_API_KEY  = "<your-key>"
   LLM_MODEL    = "gemini-flash-latest"
   TEST_SCENARIO = "phase2_short"
   ```

2. Run from the repository root:

   ```bash
   python judge_simulator.py
   ```

This will:

- Push a subset of the dataset to `/v1/context`.
- Call `/v1/tick` with active triggers.
- Call `/v1/reply` with simulated merchant responses.
- Print per-dimension scores and qualitative hints.

---

## 7. Deployment (Render)

The service is deployed as a Render web service with:

- Root directory: `solution`
- Build command: `pip install -r requirements.txt`
- Start command:

  ```bash
  uvicorn app.main:app --host 0.0.0.0 --port $PORT
  ```

`$PORT` is provided by Render at runtime; the service binds to `0.0.0.0` so it is reachable externally. 

---

## 8. Limitations and Future Work

- Category coverage is deepest for dentists and restaurants; salons, gyms, and pharmacies can be extended with additional trigger-specific handlers (for example, bridal follow-up for salons, seasonal acquisition dips and member winbacks for gyms, compliance alerts and chronic refills for pharmacies).
- The current composer is fully rule-based and deterministic; it can be augmented with LLM-backed prompting while preserving the strict routing and validation layers.

---

## 9. License and Usage Notes

- The dataset and challenge briefs are owned by magicpin and are provided for challenge purposes only.
- Code in this repository is intended to be used for experimentation, evaluation, and as a reference implementation of the challenge HTTP contract.
