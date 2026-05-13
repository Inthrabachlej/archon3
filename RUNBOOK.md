# Archon 3 — Runbook

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Uzupełnij: ANTHROPIC_API_KEY (lub OPENAI_API_KEY)
```

## Uruchomienie

```bash
source .venv/bin/activate
python main.py
```

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `API key not set` | sprawdź `.env` |
| Agent loop nieskończony | sprawdź max_iterations w configu |
| Import error | `pip install -r requirements.txt` |
