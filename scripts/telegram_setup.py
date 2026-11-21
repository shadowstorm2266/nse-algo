"""Telegram set-up for the IPO recorder's send-only alerts (nsealgo.notify).

    <python> -s scripts/venv_run.py scripts/telegram_setup.py         # print your chat id
    <python> -s scripts/venv_run.py scripts/telegram_setup.py --test  # one test message

The bot token comes from TELEGRAM_BOT_TOKEN through nsealgo.settings and is never
printed. Without --test: press Start in the bot (or send it any message) first; this
calls getUpdates once and prints only the id of each private chat found, nothing else
from the updates. Put yours in .env as TELEGRAM_CHAT_ID. With --test: sends one message
to TELEGRAM_CHAT_ID.
"""

import argparse
import sys
from datetime import datetime

from nsealgo.data.calendar import IST
from nsealgo.notify import (
    TelegramError,
    bot_from_settings,
    notifier_from_settings,
    private_chat_ids,
)

TEST_TEXT = "nse-algo IPO recorder: test message ({at:%d %b %Y %H:%M} IST). Alerts reach you."


def print_chat_ids() -> int:
    bot = bot_from_settings()
    if bot is None:
        print("TELEGRAM_BOT_TOKEN is not set in .env")
        return 2
    ids = private_chat_ids(bot.call("getUpdates", {"allowed_updates": ["message"]}))
    if not ids:
        print("no private chat found: press Start in the bot (or send it a message), rerun")
        return 1
    for cid in ids:
        print(cid)
    return 0


def send_test() -> int:
    notifier = notifier_from_settings()
    if notifier is None:
        print("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID is not set in .env")
        return 2
    notifier.send(TEST_TEXT.format(at=datetime.now(IST)))
    print("test message sent")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--test", action="store_true", help="send one test message")
    args = parser.parse_args(argv)
    try:
        return send_test() if args.test else print_chat_ids()
    except TelegramError as err:  # its text never contains the token
        print(f"Telegram error: {err}")
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
