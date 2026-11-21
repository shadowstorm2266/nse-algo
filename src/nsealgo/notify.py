"""Send-only Telegram messages to the owner's chat (the live IPO recorder's alerts).

The bot has no commands and reads nothing but the one getUpdates call made by
scripts/telegram_setup.py. Credentials come only from nsealgo.settings (hard rule 3):
TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in `.env`. The token is never printed, logged or
put in an exception message: every error leaving this module is a TelegramError whose
text has the token replaced by "<token>", raised without its cause.
"""

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass

from pydantic import SecretStr

from nsealgo.settings import Settings

API = "https://api.telegram.org"
TIMEOUT_SECONDS = 15
MAX_TEXT = 4000  # Telegram allows 4096 characters per message

Post = Callable[[str, bytes], bytes]  # (url, JSON body) -> response body; raises on failure


class TelegramError(Exception):
    """A failed Bot API call. The message never contains the token."""


def http_post(url: str, body: bytes) -> bytes:
    request = urllib.request.Request(
        url, data=body, headers={"Content-Type": "application/json"}, method="POST"
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
        return response.read()


def _http_error_reply(err: urllib.error.HTTPError) -> dict:
    """Telegram's JSON error body ({"ok": false, "description": ...}) if it sent one."""
    try:
        reply = json.loads(err.read())
        if isinstance(reply, dict):
            return reply
    except Exception:
        pass
    return {"ok": False, "description": f"HTTP {err.code}"}


@dataclass(frozen=True)
class Bot:
    token: SecretStr
    api: str = API
    post: Post = http_post

    def scrub(self, text: str) -> str:
        secret = self.token.get_secret_value()
        return text.replace(secret, "<token>") if secret else text

    def call(self, method: str, payload: dict) -> object:
        """One Bot API call; its `result`, or TelegramError."""
        url = f"{self.api}/bot{self.token.get_secret_value()}/{method}"
        try:
            reply = json.loads(self.post(url, json.dumps(payload).encode("utf-8")))
        except urllib.error.HTTPError as err:
            reply = _http_error_reply(err)
        except Exception as err:
            raise TelegramError(self.scrub(f"{method}: {type(err).__name__}: {err}")) from None
        if not (isinstance(reply, dict) and reply.get("ok") is True):
            what = reply.get("description") if isinstance(reply, dict) else "unexpected reply"
            raise TelegramError(self.scrub(f"{method}: {what}"))
        return reply.get("result")


def private_chat_ids(updates: object) -> list[int]:
    """Ids of the private chats in a getUpdates result, first seen first."""
    ids: list[int] = []
    for update in updates if isinstance(updates, list) else []:
        for key in ("message", "edited_message", "my_chat_member"):
            chat = (update.get(key) or {}).get("chat") or {}
            cid = chat.get("id")
            if chat.get("type") == "private" and isinstance(cid, int) and cid not in ids:
                ids.append(cid)
    return ids


@dataclass(frozen=True)
class Notifier:
    """Sends plain-text messages to one chat: the owner's."""

    bot: Bot
    chat_id: str

    def send(self, text: str) -> None:
        payload = {"chat_id": self.chat_id, "text": text[:MAX_TEXT]}
        self.bot.call("sendMessage", payload | {"disable_web_page_preview": True})


def bot_from_settings(settings: Settings | None = None) -> Bot | None:
    s = settings if settings is not None else Settings()
    token = s.telegram_bot_token
    return Bot(token) if token is not None and token.get_secret_value().strip() else None


def notifier_from_settings(settings: Settings | None = None) -> Notifier | None:
    """The owner's notifier, or None unless both TELEGRAM_BOT_TOKEN and
    TELEGRAM_CHAT_ID are set."""
    s = settings if settings is not None else Settings()
    bot, chat = bot_from_settings(s), s.telegram_chat_id
    if bot is None or chat is None or not chat.get_secret_value().strip():
        return None
    return Notifier(bot, chat.get_secret_value().strip())
