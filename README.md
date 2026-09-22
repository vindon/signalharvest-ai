# SignalHarvest AI

Autonomous agentic lead intelligence system. Monitors open internet signals (Reddit, Google Trends, CFPB complaints, RSS feeds), classifies by category and intent, scores by velocity and urgency, and delivers curated lead digests to subscribing brands. Runs on a schedule. No human in the loop except optional approval gates.

See `CLAUDE.md` for architecture, file map, and operating rules.

## First-time setup on M5 Mac

### 1. Get your Anthropic API key
- Go to https://console.anthropic.com → API Keys → Create Key
- Copy the key (starts with `sk-ant-`)

### 2. Set the key permanently
```bash
echo 'export ANTHROPIC_API_KEY="sk-ant-YOUR_KEY_HERE"' >> ~/.zshrc
source ~/.zshrc
echo $ANTHROPIC_API_KEY   # confirm it prints
```

### 3. Install dependencies
```bash
cd ~/Projects/signalharvest
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 4. Copy env file and edit
```bash
cp .env.example .env
# Edit .env — set ANTHROPIC_API_KEY at minimum
# Reddit credentials are optional (Reddit signals skipped if absent)
```

### 5. Initialise database
```bash
python scripts/init_db.py
```

### 6. Seed a test brand
```bash
python scripts/seed_brand.py
```

### 7. Run the full pipeline once
```bash
python scripts/run_pipeline.py
```

### 8. Run tests
```bash
pytest tests/ -v
```

### 9. Run on a daily schedule
```bash
python scripts/run_pipeline.py --mode schedule
```
