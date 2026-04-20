# Cursor Setup Notes (from PRD v2.1)

## 1) Open this folder in Cursor
- Folder: `wechat-digest`
- Cursor will use `AGENTS.md` as persistent project guidance.

## 2) Create virtual environment
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3) Initialize local configuration
```bash
cp .env.example .env
```
Then fill in real values:
- `ANTHROPIC_API_KEY`
- `WECLAW_TARGET_CHAT`

## 4) Recommended implementation order
1. `database.py`
2. `collector.py`
3. `digest_agent.py`
4. `calendar_sync.py`
5. `templates/digest_email.html`
6. `weclaw_sender.py`
7. `main.py`

## 5) Runtime split (important)
- Run collector as one process (`collector.py`).
- Run scheduler as another process (`main.py`).
- In production, each should be a separate systemd service.

## 6) First validation checks
- `curl http://127.0.0.1:5000/health`
- `python main.py --test`

## 7) Do-not-commit list
- `.env`
- `credentials.json`
- `token.json`
- `messages.db`
