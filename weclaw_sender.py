import os
from datetime import datetime

import requests
from dotenv import load_dotenv

load_dotenv()


def _build_digest_text(digest: dict, date_str: str) -> str:
    events = digest.get("events", [])
    todos = digest.get("todos", [])
    funny = digest.get("funny_moment")
    encouragement = digest.get("encouragement")
    stats = digest.get("stats", {})

    lines = [
        f"Good morning - WeChat digest for {date_str}",
        "",
        f"Stats: {stats.get('conversation_count', 0)} conversations, {stats.get('message_count', 0)} messages",
        "",
        "Agenda:",
    ]
    if events:
        for ev in events:
            time_text = ev.get("time") or "All day"
            lines.append(f"- {ev.get('date')} {time_text} | {ev.get('title')} ({ev.get('source_chat')})")
    else:
        lines.append("- No events found")

    lines.extend(["", "Todos:"])
    if todos:
        for td in todos:
            lines.append(f"- {td.get('task')} (by {td.get('mentioned_by')} in {td.get('source_chat')})")
    else:
        lines.append("- No todos found")

    lines.extend(["", "Moment of the day:"])
    if funny:
        lines.append(f"- {funny.get('text')} ({funny.get('source_chat')})")
    elif encouragement:
        lines.append(f"- {encouragement}")
    else:
        lines.append("- Keep going, you've got this.")

    return "\n".join(lines)


def _chunk_text(text: str, max_len: int = 1200):
    chunks = []
    current = []
    size = 0
    for line in text.splitlines():
        candidate = len(line) + 1
        if size + candidate > max_len and current:
            chunks.append("\n".join(current))
            current = [line]
            size = candidate
        else:
            current.append(line)
            size += candidate
    if current:
        chunks.append("\n".join(current))
    return chunks


def send_digest(digest: dict, date_str: str | None = None):
    api_url = os.getenv("WECLAW_API_URL", "http://127.0.0.1:18011/api/send")
    target_chat = os.getenv("WECLAW_TARGET_CHAT")
    if not target_chat:
        raise ValueError("WECLAW_TARGET_CHAT is missing")

    digest_date = date_str or datetime.now().strftime("%Y-%m-%d")
    text = _build_digest_text(digest, digest_date)
    chunks = _chunk_text(text)

    for idx, chunk in enumerate(chunks, start=1):
        payload = {
            "chat": target_chat,
            "content": chunk if len(chunks) == 1 else f"[{idx}/{len(chunks)}]\n{chunk}",
        }
        resp = requests.post(api_url, json=payload, timeout=15)
        resp.raise_for_status()
        print(f"[weclaw_sender] sent chunk {idx}/{len(chunks)}")
