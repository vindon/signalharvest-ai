# SignalHarvest AI — CLAUDE.md

## What this is
Autonomous agentic lead intelligence system. Monitors open internet signals (Reddit, Google Trends, CFPB complaints, RSS feeds), classifies by category and intent, scores by velocity and urgency, and delivers curated lead digests to subscribing brands. Runs on a schedule. No human in the loop except optional approval gates.

---

First-time setup (API key, venv, deps, DB init, seeding) is in `README.md` — one-time onboarding, not needed every session, so it isn't duplicated here.

---

## Architecture

```
Coordinator (LangGraph StateGraph orchestrator)
├── Agent 1: Sentinel      — harvest signals from Reddit, Trends, CFPB, RSS
├── Agent 2: Classifier    — 40-category NLP taxonomy via Claude Sonnet
├── Agent 3: Scorer        — velocity + intent + engagement scoring (0–100)
├── Agent 4: Curator       — match scored signals to brand subscriptions
└── Agent 5: Publisher     — render CSV + summary text digest per brand
```

State persists to SQLite (WAL mode) between agents. Progress written to `claude-progress.txt` after every run for session continuity.

---

## File map
```
signalharvest/
├── CLAUDE.md
├── requirements.txt
├── .env.example
├── .gitignore
├── pytest.ini
├── agents/
│   ├── coordinator.py       ← LangGraph graph + run_pipeline()
│   ├── sentinel.py          ← Agent 1: harvest
│   ├── classifier.py        ← Agent 2: NLP classify via Claude
│   ├── scorer.py            ← Agent 3: score
│   ├── curator.py           ← Agent 4: brand match via Claude
│   └── publisher.py         ← Agent 5: render + deliver
├── tools/
│   ├── reddit_tool.py       ← PRAW ingestor
│   ├── trends_tool.py       ← pytrends ingestor
│   ├── cfpb_tool.py         ← CFPB complaint API ingestor
│   ├── rss_tool.py          ← RSS/Atom feed ingestor
│   └── scoring_tool.py      ← deterministic scoring functions
├── skills/
│   ├── taxonomy/SKILL.md    ← 40-category taxonomy (loaded by Classifier)
│   └── brand_match/SKILL.md ← matching logic (loaded by Curator)
├── schemas/
│   ├── signal.py            ← RawSignal → ClassifiedSignal → ScoredSignal → CuratedLead
│   ├── brand.py             ← BrandSubscription
│   └── digest.py            ← Digest, DigestSummary, PipelineRun
├── db/
│   ├── database.py          ← SQLite init, WAL mode, schema
│   ├── signal_store.py      ← signal CRUD
│   ├── brand_store.py       ← brand CRUD
│   └── state_store.py       ← pipeline run + agent state persistence
├── digest/
│   └── renderer.py          ← CSV + plain text digest renderer
├── config/
│   └── settings.py          ← all config from env vars
├── scripts/
│   ├── init_db.py           ← initialise database
│   ├── seed_brand.py        ← seed a test brand subscription
│   └── run_pipeline.py      ← CLI: --mode full | schedule
└── tests/
    ├── unit/
    │   ├── test_schemas.py
    │   ├── test_scoring.py
    │   ├── test_renderer.py
    │   └── test_classifier.py
    └── integration/
        └── test_pipeline.py
```

---

## Rules for Claude Code

1. **No hardcoded secrets.** All keys via environment variables through `config/settings.py`.
2. **Models:** `claude-sonnet-4-6` for reasoning (Classifier, Curator). `claude-haiku-4-5-20251001` for volume (Sentinel output parsing, Publisher).
3. **Every agent writes to SQLite before passing state.** State never held only in memory.
4. **After every run, `claude-progress.txt` is updated.** Read it at the start of each session.
5. **Pydantic v2 for all data validation.** No raw dicts between agents.
6. **All tools have try/except.** No silent failures.
7. **Rate limits:** Reddit PRAW 60 req/min (auto-managed). pytrends 1 req/5–8s with jitter. CFPB 1 req/2s. RSS 1 req/10s.
8. **`pytest tests/ -v` must pass 0 failures** before any phase is marked complete.
9. **No network calls in unit tests.** Mock all ingestors and Claude API calls.
10. **SQLite WAL mode** enabled in `db/database.py`. Do not change this.

---

## Adding a new brand
Edit `scripts/seed_brand.py`, change the brand config, re-run:
```bash
python scripts/seed_brand.py
```

## Adding a new signal source
1. Create `tools/your_source_tool.py` returning `list[RawSignal]`
2. Import and call it in `agents/sentinel.py`
3. Add rate limit comment and error handling
4. Add unit tests in `tests/unit/`

## Checking last run
```bash
cat claude-progress.txt
```

## Security posture
- `.env` in `.gitignore`. Never commit.
- `data/` and `output/` in `.gitignore`.
- API keys never logged, never printed, never in error messages.
- Signal text sanitised on ingest — HTML stripped, truncated at 2000 chars.
- No PII stored. Signals are public social content only.
