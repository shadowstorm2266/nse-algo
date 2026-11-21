"""The recorder's Telegram messages (scripts/ipo_live_notify.py), end to end through
record_ipo_live.run_once on a fake network with a fake notifier: decisions, alerts,
the 19:30 heartbeat, nothing about listings, and failed sends as warnings only."""

import json
import sys
from datetime import date, datetime

import pytest

from nsealgo.data.calendar import IST
from nsealgo.notify import TelegramError
from nsealgo.settings import REPO_ROOT
from tests.ipo_live_helpers import current_rows, detail, udiff_zip

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import ipo_live_notify
import ipo_live_steps
import ipo_v2_decisions
import record_ipo_live
from download_bhavcopy import bhavcopy_url

HOL = {date(2026, 12, 25)}
CURRENT = record_ipo_live.CURRENT_URL
DETAIL = ipo_live_steps.DETAIL_URL.format(symbol="BCSSL")


def ist(*args: int) -> datetime:
    return datetime(*args, tzinfo=IST)


class FakeNotifier:
    def __init__(self) -> None:
        self.sent: list[str] = []

    def send(self, text: str) -> None:
        self.sent.append(text)


class FailingNotifier:
    def send(self, text: str) -> None:
        raise TelegramError("sendMessage: Bad Gateway")


@pytest.fixture
def rec(tmp_path, monkeypatch):
    monkeypatch.setattr(ipo_live_steps, "pdf_text", lambda path, table, exe: "")
    cfg = ipo_v2_decisions.load_v2_config(REPO_ROOT / "config" / "ipo_v2.yaml")
    stamped = detail(stamp="Updated as on 02-Nov-2026 15:24:00")
    bodies = {CURRENT: json.dumps(current_rows()).encode(), DETAIL: json.dumps(stamped).encode()}
    archive: dict[str, bytes | Exception] = {}

    def get_archive(url: str) -> bytes | None:
        body = archive.get(url)
        if isinstance(body, Exception):
            raise body
        return body

    net = ipo_live_steps.Net(nse=lambda u, r: bodies[u], archive=get_archive, ready=lambda: True)
    root, tg = tmp_path / "live", FakeNotifier()

    def run(at: datetime, scheduled: bool = True, holidays: set[date] = HOL, notifier=None):
        n = tg if notifier is None else notifier
        clock = lambda: at  # noqa: E731
        return record_ipo_live.run_once(net, root, holidays, scheduled, clock, {}, None, cfg, n)

    return run, tg, bodies, archive, root


def test_a_decision_is_sent_with_subscription_and_application_amount(rec):
    run, tg, *_ = rec
    run(ist(2026, 11, 2, 12, 0, 3))
    assert tg.sent == []
    r = run(ist(2026, 11, 2, 15, 30, 4))
    (msg,) = tg.sent
    assert msg.splitlines() == [
        "IPO v2 decision: BCSSL_20261029: APPLY",
        "Total subscription: 10.73x",
        "Snapshot: 02 Nov 15:30 IST (scheduled_1530)",
        "Application: ₹14,924",  # 182 shares x ₹82
        "Rule: apply if total >= 5.0x",
    ]
    assert r.log["telegram_sent"] == ["decision BCSSL_20261029"] and not r.warnings


def test_the_1930_run_sends_one_heartbeat(rec):
    run, tg, *_ = rec
    for hm in ((12, 0, 3), (15, 30, 4)):
        run(ist(2026, 11, 2, *hm))
    tg.sent.clear()
    run(ist(2026, 11, 2, 19, 30, 2))
    (msg,) = tg.sent
    assert msg.splitlines() == [
        "✅ IPO recorder: all OK (Mon 02 Nov)",
        "Runs today: 3, 3 ok, 0 missed slot(s)",
        "Decisions today: 1",
        "Open for bidding: BCSSL_20261029",
    ]


def test_a_failed_run_and_its_missed_slot_are_alerted_once(rec):
    run, tg, bodies, _, _ = rec
    run(ist(2026, 11, 2, 12, 0, 3))
    del bodies[CURRENT]  # the current-issue call now fails
    run(ist(2026, 11, 2, 19, 30, 2))  # 15:30 was missed
    decision, alert, heartbeat = tg.sent  # 12:00's snapshot predates the plan commit
    assert decision.startswith("IPO v2 decision: BCSSL_20261029: BEFORE PLAN")
    assert alert.splitlines()[0] == "⚠ IPO recorder: scheduled Mon 02 Nov 19:30 run"
    assert "- current issues: KeyError(" in alert
    assert "Missed scheduled run(s): Mon 02 Nov 15:30" in alert
    assert heartbeat.startswith("⚠ IPO recorder: problems today (see alerts) (Mon 02 Nov)")
    assert "Runs today: 2, 1 ok, 1 missed slot(s)" in heartbeat
    tg.sent.clear()
    bodies[CURRENT] = json.dumps(current_rows()).encode()
    run(ist(2026, 11, 2, 20, 0), scheduled=False)  # the same missed slot: no new alert
    assert tg.sent == []


def test_a_failed_send_is_a_warning_and_the_run_stays_ok(rec):
    run, _, _, _, root = rec
    run(ist(2026, 11, 2, 12, 0, 3))
    r = run(ist(2026, 11, 2, 15, 30, 4), notifier=FailingNotifier())
    assert not r.errors and r.warnings == [
        "telegram decision BCSSL_20261029 not sent: TelegramError: sendMessage: Bad Gateway"
    ]
    last = json.loads((root / "run_log.jsonl").read_text("utf-8").splitlines()[-1])
    assert last["ok"] and last["telegram"] is True and "not sent" in last["warnings"][0]


def test_a_holiday_still_gets_a_heartbeat_at_1930(rec):
    run, tg, *_ = rec
    run(ist(2026, 11, 3, 12, 0), holidays={date(2026, 11, 3)} | HOL)
    assert tg.sent == []
    run(ist(2026, 11, 3, 19, 30, 1), holidays={date(2026, 11, 3)} | HOL)
    (msg,) = tg.sent
    assert "Not an NSE trading day" in msg and "Runs today: 2, 2 ok" in msg


def test_nothing_about_the_listing_is_sent(rec):
    run, tg, bodies, archive, _ = rec
    run(ist(2026, 11, 2, 15, 30, 4))
    bodies[CURRENT] = b"[]"
    other = ("OTHER", "EQ", "INE0OT001010", 10.0, 11.0, 10.0)
    for n in (2, 3, 4):
        archive[bhavcopy_url(date(2026, 11, n))] = udiff_zip(date(2026, 11, n), [other])
    listing_day = bhavcopy_url(date(2026, 11, 5))
    archive[listing_day] = ValueError("row BCSSL 96.25 97.55")  # an error quoting prices
    tg.sent.clear()
    r = run(ist(2026, 11, 5, 19, 30, 4))
    assert any(" listing: " in e for e in r.errors)
    listed = ("BCSSL", "EQ", "INE0BC001010", 96.25, 97.55, 82.0)
    archive[listing_day] = udiff_zip(date(2026, 11, 5), [other, listed])
    r = run(ist(2026, 11, 6, 19, 30, 1))
    assert "listing" in [a["kind"] for a in r.actions] and not r.errors
    text = "\n".join(tg.sent)
    assert "listing: failed (text in run_log.jsonl, not sent: v2 is blind)" in text
    assert sum(m.startswith("✅") or "problems today" in m for m in tg.sent) == 2  # heartbeats
    for secret in ("96.25", "97.55", "96.2", "97.5", "97.6"):
        assert secret not in text


def test_error_text_is_sent_only_for_steps_before_the_listing():
    line = ipo_live_notify.error_line
    assert line("current issues: KeyError('x')") == "current issues: KeyError('x')"
    assert line("BCSSL_20261029 snapshot: OSError()") == "BCSSL_20261029 snapshot: OSError()"
    assert line("backup: git push failed: denied") == "backup: git push failed: denied"
    for blind in (
        "BCSSL_20261029 listing: ValueError('97.5')",
        "BCSSL_20261029 advert: ValueError('allotted 1 in 3')",
        "backfill: KeyError('close')",
        "run: TypeError('x')",
    ):
        got = line(blind)
        assert got.endswith("not sent: v2 is blind)") and "97.5" not in got and "1 in 3" not in got


def test_an_unpushed_backup_is_alerted():
    at = ist(2026, 11, 2, 19, 30)
    log = {"slot": at.isoformat(), "backup": {"pushed": False, "note": "no remote"}}
    run = ipo_live_steps.Run(clock=lambda: at, started_at=at, scheduled=True, log=log)
    text = ipo_live_notify.alert_text(run, [])
    assert text is not None and "Backup not pushed: no remote" in text
