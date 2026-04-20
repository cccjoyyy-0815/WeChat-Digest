import os
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
