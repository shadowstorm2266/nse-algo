"""nsealgo.notify against a fake Telegram Bot API (a local HTTP server): sendMessage goes
only to the configured chat, getUpdates yields only private chat ids, and no error text
ever carries the token."""

import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
from pydantic import SecretStr

from nsealgo.notify import (
    Bot,
    Notifier,
    TelegramError,
    notifier_from_settings,
    private_chat_ids,
)
from nsealgo.settings import Settings

TOKEN = "123456:FAKE-token-for-tests"


class FakeTelegram:
    """Serves /bot<token>/<method>; records (path, payload); replies from `replies`."""

    def __init__(self) -> None:
        self.requests: list[tuple[str, dict]] = []
        self.replies: dict[str, tuple[int, dict]] = {}
        fake = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self) -> None:
                body = self.rfile.read(int(self.headers["Content-Length"]))
                fake.requests.append((self.path, json.loads(body)))
                method = self.path.rsplit("/", 1)[-1]
                if not self.path.startswith(f"/bot{TOKEN}/"):
                    code, reply = 401, {"ok": False, "description": "Unauthorized"}
                else:
                    code, reply = fake.replies.get(method, (200, {"ok": True, "result": True}))
                data = json.dumps(reply).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args: object) -> None:
                pass

        self.server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        threading.Thread(target=self.server.serve_forever, daemon=True).start()


@pytest.fixture
def api():
    fake = FakeTelegram()
    yield fake
    fake.server.shutdown()
    fake.server.server_close()


def test_send_posts_plain_text_to_the_configured_chat(api):
    Notifier(Bot(SecretStr(TOKEN), api=api.url), "42").send("hello ₹")
    ((path, payload),) = api.requests
    assert path == f"/bot{TOKEN}/sendMessage"
    assert payload == {"chat_id": "42", "text": "hello ₹", "disable_web_page_preview": True}


def test_long_messages_are_cut_to_telegrams_limit(api):
    Notifier(Bot(SecretStr(TOKEN), api=api.url), "42").send("x" * 5000)
    assert len(api.requests[0][1]["text"]) == 4000


def test_an_api_error_is_raised_without_the_token(api):
    api.replies["sendMessage"] = (400, {"ok": False, "description": "Bad Request: chat not found"})
    with pytest.raises(TelegramError) as err:
        Notifier(Bot(SecretStr(TOKEN), api=api.url), "42").send("hi")
    assert "chat not found" in str(err.value) and TOKEN not in str(err.value)
    with pytest.raises(TelegramError) as err:
        Notifier(Bot(SecretStr("999:wrong"), api=api.url), "42").send("hi")
    assert "Unauthorized" in str(err.value) and "999:wrong" not in str(err.value)


def test_a_network_error_carrying_the_url_is_scrubbed():
    def post(url: str, body: bytes) -> bytes:
        raise OSError(f"cannot reach {url}")

    with pytest.raises(TelegramError) as err:
        Bot(SecretStr(TOKEN), post=post).call("sendMessage", {})
    text = str(err.value)
    assert TOKEN not in text and "<token>" in text
    assert err.value.__cause__ is None and err.value.__suppress_context__


def test_an_unreachable_api_is_a_telegram_error():
    bot = Bot(SecretStr(TOKEN), api="http://127.0.0.1:9")  # discard port: refused
    with pytest.raises(TelegramError) as err:
        bot.call("sendMessage", {})
    assert TOKEN not in str(err.value)


def test_get_updates_yields_only_private_chat_ids(api):
    api.replies["getUpdates"] = (
        200,
        {
            "ok": True,
            "result": [
                {"update_id": 1, "message": {"chat": {"id": 42, "type": "private",
                                                      "first_name": "Owner"}, "text": "/start"}},
                {"update_id": 2, "message": {"chat": {"id": -100, "type": "group"}}},
                {"update_id": 3, "message": {"chat": {"id": 42, "type": "private"}}},
            ],
        },
    )  # fmt: skip
    updates = Bot(SecretStr(TOKEN), api=api.url).call("getUpdates", {})
    assert private_chat_ids(updates) == [42]
    assert private_chat_ids(None) == [] and private_chat_ids([{"update_id": 9}]) == []


def test_the_notifier_needs_both_token_and_chat_id(monkeypatch):
    for var in ("TELEGRAM_BOT_TOKEN", "TELEGRAM_CHAT_ID"):
        monkeypatch.delenv(var, raising=False)
    assert notifier_from_settings(Settings(_env_file=None)) is None
    assert notifier_from_settings(Settings(_env_file=None, telegram_bot_token=TOKEN)) is None
    assert notifier_from_settings(Settings(_env_file=None, telegram_chat_id="42")) is None
    n = notifier_from_settings(
        Settings(_env_file=None, telegram_bot_token=TOKEN, telegram_chat_id=" 42 ")
    )
    assert n is not None and n.chat_id == "42"
    assert TOKEN not in repr(n)
