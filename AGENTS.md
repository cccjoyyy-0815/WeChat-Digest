# WeChat Digest Agent - Cursor Guidance

## Product Intent
- Build a VPS-hosted WeChat morning digest system.
- Use WeClaw as a real-time relay only; do not implement history polling from WeClaw.
- Preserve architecture: `collector.py` receives incoming messages, SQLite stores messages, scheduler processes yesterday's data, Claude returns structured digest JSON, then calendar and WeClaw send actions run.

## Core Architecture Constraints
- Keep `collector.py` and `main.py` as separate long-running processes.
- `collector.py` must expose:
  - `POST /collect` (OpenAI-compatible inbound payload and outbound response shape)
  - `GET /health` (`status` + today's message count)
- `main.py` must:
  - Run scheduled daily digest job based on `DIGEST_SEND_TIME`
  - Support `--test` for immediate one-off run for yesterday
  - Skip duplicate daily sends using `processed_dates`

## Data and Schema Requirements
- SQLite tables:
  - `messages(id, chat_name, sender, content, timestamp, created_at)`
  - `processed_dates(date PRIMARY KEY)`
- Database module should provide:
  - `init_db()`
  - `insert_message(chat_name, sender, content, timestamp)`
  - `get_messages_for_date(date_str)`
  - `mark_date_processed(date_str)`
  - `is_date_processed(date_str)`

## AI Output Contract
- Claude response must be parsed as JSON only (strip markdown fences if present).
- Enforce schema fields:
  - `events[]`: `title`, `date`, `time|null`, `participants`, `source_chat`
  - `todos[]`: `task`, `mentioned_by`, `source_chat`
  - `funny_moment`: object or null
  - `encouragement`: string or null
  - `stats`: `conversation_count`, `message_count`
- Raise clear errors when parsing or validation fails.

## Security and Privacy Guardrails
- Never commit secrets or personal data:
  - `.env`, `credentials.json`, `token.json`, `messages.db`
- Assume collector and WeClaw APIs are local-only (`127.0.0.1`) and should not be exposed publicly.
- Use least-privilege defaults and avoid adding unnecessary external services.

## Coding Standards
- Python 3.11+ compatible.
- Prefer small, focused modules matching PRD file boundaries.
- Add concise logging around ingestion, scheduling, API calls, and error paths.
- Handle failures gracefully (network/API errors, malformed payloads, empty-message days).
- Keep changes incremental and avoid unrelated refactors.

## Delivery Checklist for Agent Work
- Keep files aligned with PRD v2.1 names:
  - `collector.py`, `database.py`, `digest_agent.py`, `calendar_sync.py`, `weclaw_sender.py`, `main.py`
- If creating systemd units, match service order:
  - `weclaw.service` -> `wechat-collector.service` -> `wechat-digest.service`
- Include quick verification steps:
  - health endpoint check
  - `main.py --test` run
