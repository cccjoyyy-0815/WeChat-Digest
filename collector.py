import os
import time
from datetime import datetime

from dotenv import load_dotenv
from flask import Flask, jsonify, request

import database

load_dotenv()

app = Flask(__name__)


def _extract_content(messages):
    if not messages:
        return ""
    content = messages[-1].get("content", "")
    return content if isinstance(content, str) else str(content)


def _last_user_message_text(messages):
    if not isinstance(messages, list):
        return ""
    for m in reversed(messages):
        if not isinstance(m, dict):
            continue
        if m.get("role") != "user":
            continue
        c = m.get("content", "")
        return c if isinstance(c, str) else str(c)
    return ""


def _bridge_identity():
    """WeClaw HTTP agent does not send from_user_id in JSON; optional header if you patch WeClaw."""
    conv = request.headers.get("X-Weclaw-Conversation-Id") or request.headers.get(
        "X-WeClaw-Conversation-Id"
    )
    if conv:
        return conv, f"weclaw:{conv}"
    sender = os.getenv("DIGEST_BRIDGE_SENDER", "unknown")
    chat = os.getenv("DIGEST_BRIDGE_CHAT", "weclaw")
    return sender, chat


@app.post("/v1/chat/completions")
def chat_completions():
    """
    OpenAI-compatible endpoint for WeClaw HTTP agents.
    Stock WeClaw posts {"model","messages"} only; optional X-Weclaw-Conversation-Id if you add it upstream.
    """
    payload = request.get_json(silent=True) or {}
    messages = payload.get("messages") or []
    content = _last_user_message_text(messages)
    sender, chat_name = _bridge_identity()
    timestamp = int(datetime.now().timestamp())

    if content.strip():
        database.insert_message(
            chat_name=chat_name, sender=sender, content=content, timestamp=timestamp
        )
        preview = content[:80].replace("\n", " ")
        print(
            f"[bridge] ts={timestamp} chat={chat_name} sender={sender} content='{preview}'",
            flush=True,
        )

    model = payload.get("model") or "wechat-digest-bridge"
    return jsonify(
        {
            "id": "chatcmpl-bridge",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": model,
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": "ok"},
                    "finish_reason": "stop",
                }
            ],
        }
    )


@app.post("/collect")
def collect():
    payload = request.get_json(silent=True) or {}
    metadata = payload.get("metadata", {})

    sender = metadata.get("from", "unknown_sender")
    chat_name = metadata.get("chat", "unknown_chat")
    timestamp = int(metadata.get("timestamp", int(datetime.now().timestamp())))
    content = _extract_content(payload.get("messages", []))

    database.insert_message(chat_name=chat_name, sender=sender, content=content, timestamp=timestamp)

    preview = content[:80].replace("\n", " ")
    print(
        f"[collect] ts={timestamp} chat={chat_name} sender={sender} content='{preview}'",
        flush=True,
    )
    return jsonify({"choices": [{"message": {"role": "assistant", "content": "ok"}}]})


@app.get("/health")
def health():
    today = datetime.now().strftime("%Y-%m-%d")
    count = database.count_messages_for_date(today)
    return jsonify({"status": "ok", "messages_today": count})


if __name__ == "__main__":
    database.init_db()
    port = int(os.getenv("COLLECTOR_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False)
