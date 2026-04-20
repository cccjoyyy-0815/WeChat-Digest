import argparse
import time
from datetime import datetime, timedelta

import schedule
from dotenv import load_dotenv

import calendar_sync
import database
import digest_agent
import weclaw_sender

load_dotenv()


def run_digest_for_yesterday():
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
    if database.is_date_processed(yesterday):
        print(f"[main] already processed {yesterday}; skipping")
        return

    messages = database.get_messages_for_date(yesterday)
    if not messages:
        print(f"[main] no messages for {yesterday}; skipping")
        return

    digest = digest_agent.analyze(messages)

    for event in digest.get("events", []):
        title = event.get("title")
        date_str = event.get("date")
        time_str = event.get("time")
        src = event.get("source_chat", "unknown_chat")
        participants = event.get("participants", "")
        desc = f"Source chat: {src}\nParticipants: {participants}"
        if title and date_str:
            calendar_sync.create_event(title, date_str, time_str, desc)

    weclaw_sender.send_digest(digest, date_str=yesterday)
    database.mark_date_processed(yesterday)
    print(f"[main] completed digest for {yesterday}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", action="store_true")
    args = parser.parse_args()

    database.init_db()
    send_time = __import__("os").getenv("DIGEST_SEND_TIME", "07:00")

    if args.test:
        run_digest_for_yesterday()
        return

    schedule.every().day.at(send_time).do(run_digest_for_yesterday)
    print(f"[main] scheduler started, daily run at {send_time}")
    try:
        while True:
            schedule.run_pending()
            time.sleep(30)
    except KeyboardInterrupt:
        print("[main] stopped by user")


if __name__ == "__main__":
    main()
