import json
import os
from collections import defaultdict

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"


def _build_transcript(messages):
    grouped = defaultdict(list)
    for msg in messages:
        grouped[msg["chat_name"]].append(msg)

    blocks = []
    for chat_name, chat_msgs in grouped.items():
        lines = [f"## Chat: {chat_name}"]
        for m in chat_msgs:
            lines.append(f"- {m['sender']}: {m['content']}")
        blocks.append("\n".join(lines))
    return "\n\n".join(blocks)


def _strip_fences(raw: str) -> str:
    text = raw.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.startswith("json"):
            text = text[4:]
    return text.strip()


def analyze(messages):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY is missing")

    transcript = _build_transcript(messages)
    system_prompt = (
        "Return ONLY valid JSON. No markdown.\n"
        "Schema:\n"
        "{"
        '"events":[{"title":"string","date":"YYYY-MM-DD","time":"HH:MM or null","participants":"string","source_chat":"string"}],'
        '"todos":[{"task":"string","mentioned_by":"string","source_chat":"string"}],'
        '"funny_moment":{"text":"string","source_chat":"string","timestamp":"string"} or null,'
        '"encouragement":"string or null",'
        '"stats":{"conversation_count":0,"message_count":0}'
        "}"
    )

    client = Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=3000,
        system=system_prompt,
        messages=[
            {
                "role": "user",
                "content": f"Analyze this transcript and extract digest data:\n\n{transcript}",
            }
        ],
    )
    raw = "".join(block.text for block in resp.content if getattr(block, "type", "") == "text")
    cleaned = _strip_fences(raw)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"Claude returned non-JSON output: {cleaned[:400]}") from exc
    return parsed
