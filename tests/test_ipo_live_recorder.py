"""Live IPO recorder: the run schedule (slots, late and missed runs) and
scripts/record_ipo_live.py end to end on a fake network, through one issue's life: bid
days, final book, listing day, advert. Nothing here touches NSE."""

import json
import sys
from datetime import date, datetime, timedelta

import pytest

from nsealgo.data.calendar import IST
from nsealgo.data.ipo_live import Tracked
from nsealgo.data.live_schedule import (
    check_schedule,
    missed_in_window,
    slot_for,
    slots_between,
)
from nsealgo.settings import REPO_ROOT
from tests.ipo_live_helpers import current_rows, detail, udiff_zip

sys.path.insert(0, str(REPO_ROOT / "scripts"))
import ipo_live_steps
import record_ipo_live
from download_bhavcopy import bhavcopy_url
from download_ipo_boa import URL as ADVERT_URL


def ist(*args: int) -> datetime:
    return datetime(*args, tzinfo=IST)


# 2026: Thu 29 Oct, Fri 30 Oct, Sat 31 Oct, Mon 2 Nov, Tue 3 Nov, Wed 4 Nov, Thu 5 Nov
NO_HOLIDAYS: set[date] = set()


# --- schedule -----------------------------------------------------------------------------


def test_a_run_counts_for_the_latest_slot_at_or_before_it():
    assert slot_for(ist(2026, 11, 2, 12, 0, 0), NO_HOLIDAYS) == ist(2026, 11, 2, 12, 0)
    assert slot_for(ist(2026, 11, 2, 11, 56), NO_HOLIDAYS) == ist(2026, 11, 2, 12, 0)  # early
    assert slot_for(ist(2026, 11, 2, 11, 50), NO_HOLIDAYS) == ist(2026, 10, 30, 19, 30)
    assert slot_for(ist(2026, 11, 2, 17, 0), NO_HOLIDAYS) == ist(2026, 11, 2, 15, 30)
    assert slot_for(ist(2026, 10, 31, 12, 0), NO_HOLIDAYS) is None  # Saturday
    holiday = {date(2026, 11, 3)}
    assert slot_for(ist(2026, 11, 3, 12, 0), holiday) is None
    assert slot_for(ist(2026, 11, 4, 9, 0), holiday) == ist(2026, 11, 2, 19, 30)


def test_slots_between_skips_weekends_and_holidays():
    got = slots_between(ist(2026, 10, 30, 19, 30), ist(2026, 11, 3, 15, 30), {date(2026, 11, 2)})
    assert got == [ist(2026, 11, 3, 12, 0)]
    got = slots_between(ist(2026, 10, 30, 15, 30), ist(2026, 11, 2, 12, 0), NO_HOLIDAYS)
    assert got == [ist(2026, 10, 30, 19, 30)]


def test_check_schedule_reports_missed_late_and_duplicate_runs():
    mon_noon = ist(2026, 11, 2, 12, 0)
    c = check_schedule([mon_noon], ist(2026, 11, 2, 19, 30, 5), True, NO_HOLIDAYS)
    assert (c.slot, c.missed, c.duplicate) == (
        ist(2026, 11, 2, 19, 30),
        [ist(2026, 11, 2, 15, 30)],
        False,
    )
    assert c.late == timedelta(seconds=5)
    late = check_schedule([ist(2026, 10, 30, 19, 30)], ist(2026, 11, 2, 14, 0), True, NO_HOLIDAYS)
    assert (late.slot, late.late, late.missed) == (mon_noon, timedelta(hours=2), [])
    assert check_schedule([mon_noon], ist(2026, 11, 2, 12, 10), True, NO_HOLIDAYS).duplicate
    first = check_schedule([], ist(2026, 11, 2, 19, 30), True, NO_HOLIDAYS)
    assert first.missed == []  # nothing is missed before the first scheduled run


def test_a_manual_run_counts_for_no_slot_and_waits_an_hour_before_calling_a_miss():
    mon_noon = ist(2026, 11, 2, 12, 0)
    c = check_schedule([mon_noon], ist(2026, 11, 2, 16, 0), False, NO_HOLIDAYS)
    assert (c.slot, c.late, c.missed) == (None, None, [])
    c = check_schedule([mon_noon], ist(2026, 11, 2, 16, 31), False, NO_HOLIDAYS)
    assert c.missed == [ist(2026, 11, 2, 15, 30)]


def test_missed_in_window_starts_at_the_first_scheduled_run():
    covered = [ist(2026, 11, 2, 12, 0), ist(2026, 11, 2, 19, 30)]
    got = missed_in_window(covered, ist(2026, 10, 20, 0, 0), ist(2026, 11, 3, 13, 5), NO_HOLIDAYS)
    assert got == [ist(2026, 11, 2, 15, 30), ist(2026, 11, 3, 12, 0)]
    assert missed_in_window([], ist(2026, 10, 20, 0, 0), ist(2026, 11, 3, 13, 5), NO_HOLIDAYS) == []


# --- the recorder on a fake network -------------------------------------------------------


class FakeNet:
    def __init__(self) -> None:
        self.nse_bodies: dict[str, bytes] = {}
        self.archive_bodies: dict[str, bytes] = {}
        self.calls: list[str] = []

    def nse(self, url: str, referer: str) -> bytes:
        self.calls.append(url)
        return self.nse_bodies[url]

    def archive(self, url: str) -> bytes | None:
        self.calls.append(url)
        return self.archive_bodies.get(url)

    def net(self) -> ipo_live_steps.Net:
        return ipo_live_steps.Net(nse=self.nse, archive=self.archive, ready=lambda: True)


CURRENT = record_ipo_live.CURRENT_URL
DETAIL = ipo_live_steps.DETAIL_URL.format(symbol="BCSSL")
HOLIDAYS_2026 = {date(2026, 12, 25)}  # any 2026 date: no empty-calendar warning
OTHER = ("OTHER", "EQ", "INE0OT001010", 10.0, 11.0, 10.0)


@pytest.fixture
def recorder(tmp_path, monkeypatch):
    monkeypatch.setattr(ipo_live_steps, "pdf_text", lambda path, table: "")  # no pdftotext
    fake, root = FakeNet(), tmp_path / "live"

    def run(at: datetime, scheduled: bool = True, holidays: set[date] = HOLIDAYS_2026):
        return record_ipo_live.run_once(fake.net(), root, holidays, scheduled, lambda: at, {})

    return fake, root, run


def test_one_issue_from_bid_days_to_its_advert(recorder):
    fake, root, run = recorder
    d = root / "BCSSL_20261029"
    fake.nse_bodies[CURRENT] = json.dumps(current_rows()).encode()
    fake.nse_bodies[DETAIL] = json.dumps(
        detail(stamp="Updated as on 29-Oct-2026 11:00:00")
    ).encode()
    r1 = run(ist(2026, 10, 29, 12, 0, 3))
    assert not r1.errors and r1.log["open_mainboard"] == ["BCSSL_20261029"]
    assert [p.name for p in d.iterdir()] == ["20261029T120003+0530.json"]
    assert (root / "current_issue" / "20261029T120003+0530.json").exists()

    # close day, 19:30: NSE has dropped the issue from the list; it is still recorded
    fake.nse_bodies[CURRENT] = b"[]"
    fake.nse_bodies[DETAIL] = json.dumps(
        detail(stamp="Updated as on 02-Nov-2026 19:00:00")
    ).encode()
    r2 = run(ist(2026, 11, 2, 19, 30, 2))
    assert [a["kind"] for a in r2.actions] == ["snapshot"]
    assert r2.actions[0]["stamp"] == "2026-11-02T19:00:00+05:30"
    assert len(r2.log["missed_slots"]) == 7 and "missed scheduled run" in r2.warnings[0]

    # next day: final book; the close day's bhavcopy lacks the symbol; 3 Nov's is not out
    fake.archive_bodies[bhavcopy_url(date(2026, 11, 2))] = udiff_zip(date(2026, 11, 2), [OTHER])
    r3 = run(ist(2026, 11, 3, 12, 0, 1))
    assert [a["kind"] for a in r3.actions] == ["final", "listing_wait"] and not r3.warnings
    assert (d / "final_20261103T120001+0530.json").exists()

    # listing day, 19:30: the bhavcopy is out and the advert was filed the day before
    for n in (3, 4):
        fake.archive_bodies[bhavcopy_url(date(2026, 11, n))] = udiff_zip(date(2026, 11, n), [OTHER])
    listed = ("BCSSL", "EQ", "INE0BC001010", 96.0, 97.5, 82.0)
    fake.archive_bodies[bhavcopy_url(date(2026, 11, 5))] = udiff_zip(
        date(2026, 11, 5), [OTHER, listed]
    )
    fake.archive_bodies[ADVERT_URL.format(name="ADV_INE0BC001010_04NOV2026.pdf")] = b"%PDF-1.7 x"
    r4 = run(ist(2026, 11, 5, 19, 30, 4))
    assert [a["kind"] for a in r4.actions] == ["listing", "advert"] and not r4.errors
    listing = json.loads((d / "listing_20261105.json").read_text("utf-8"))
    assert (listing["open"], listing["close"], listing["prev_close"]) == (96, 97.5, 82)
    assert (listing["listing_date"], listing["match"], listing["isin"]) == (
        "2026-11-05",
        "symbol",
        "INE0BC001010",
    )
    assert (d / "ADV_INE0BC001010_04NOV2026.pdf").read_bytes() == b"%PDF-1.7 x"
    assert r4.actions[1]["readable"] is False

    # afterwards nothing is fetched for the issue
    fake.calls.clear()
    r5 = run(ist(2026, 11, 6, 12, 0, 0))
    assert r5.actions == [] and fake.calls == [CURRENT]

    log = [json.loads(x) for x in (root / "run_log.jsonl").read_text("utf-8").splitlines()]
    assert [x["slot"][:16] for x in log] == [
        "2026-10-29T12:00",
        "2026-11-02T19:30",
        "2026-11-03T12:00",
        "2026-11-05T19:30",
        "2026-11-06T12:00",
    ]
    assert all(x["ok"] for x in log)


def test_a_scheduled_run_on_a_holiday_fetches_nothing_but_is_logged(recorder):
    fake, root, run = recorder
    r = run(ist(2026, 11, 3, 12, 0), holidays={date(2026, 11, 3)})
    assert fake.calls == [] and r.log["skipped"] and r.log["slot"] is None
    assert len((root / "run_log.jsonl").read_text("utf-8").splitlines()) == 1


def test_an_empty_holiday_calendar_is_warned_about(recorder):
    fake, _, run = recorder
    fake.nse_bodies[CURRENT] = b"[]"
    r = run(ist(2026, 11, 3, 12, 0), holidays=set())
    assert any("holidays.csv" in w for w in r.warnings) and not r.errors


def test_a_failed_run_is_still_logged(recorder):
    _, root, run = recorder  # no bodies: every NSE call raises KeyError
    r = run(ist(2026, 11, 3, 12, 0))
    log = json.loads((root / "run_log.jsonl").read_text("utf-8"))
    assert r.errors and log["ok"] is False and "current issues" in log["errors"][0]


def test_another_bid_periods_json_is_not_saved(recorder):
    fake, root, run = recorder
    fake.nse_bodies[CURRENT] = json.dumps(current_rows()).encode()
    fake.nse_bodies[DETAIL] = json.dumps(detail(period="29-Dec-2026 to 31-Dec-2026")).encode()
    r = run(ist(2026, 10, 29, 12, 0))
    assert r.errors and not (root / "BCSSL_20261029").exists()


def tracked_issue() -> Tracked:
    return Tracked(
        issue_id="BCSSL_20261029",
        symbol="BCSSL",
        issue_open=date(2026, 10, 29),
        issue_close=date(2026, 11, 2),
        lot=182,
        isin=None,
        band=(78.0, 82.0),
        snapshots=3,
        final=True,
        listing=None,
        advert=None,
    )


def test_a_bhavcopy_still_missing_at_18h_next_day_counts_as_no_session(tmp_path):
    fake, root = FakeNet(), tmp_path / "live"
    fake.archive_bodies[bhavcopy_url(date(2026, 11, 2))] = udiff_zip(date(2026, 11, 2), [OTHER])
    listed = ("BCSSL", "EQ", "INE0BC001010", 96.0, 97.5, 82.0)
    fake.archive_bodies[bhavcopy_url(date(2026, 11, 4))] = udiff_zip(date(2026, 11, 4), [listed])

    def find(at: datetime) -> dict | None:
        run = ipo_live_steps.Run(clock=lambda: at, started_at=at, scheduled=False)
        return ipo_live_steps.find_listing(fake.net(), run, root, tracked_issue(), at.date(), set())

    assert find(ist(2026, 11, 4, 17, 59)) is None  # 3 Nov's file may still come
    got = find(ist(2026, 11, 4, 18, 0))
    assert got is not None and got["listing_date"] == "2026-11-04"
    misses = (root / "bhavcopy" / "misses.jsonl").read_text("utf-8")
    assert json.loads(misses)["day"] == "2026-11-03"


def test_a_symbol_already_trading_on_the_close_day_is_not_a_listing(tmp_path):
    fake, root = FakeNet(), tmp_path / "live"
    old = ("BCSSL", "EQ", "INE0OLD01010", 50.0, 51.0, 50.0)
    fake.archive_bodies[bhavcopy_url(date(2026, 11, 2))] = udiff_zip(date(2026, 11, 2), [old])
    at = ist(2026, 11, 3, 12, 0)
    run = ipo_live_steps.Run(clock=lambda: at, started_at=at, scheduled=False)
    assert (
        ipo_live_steps.find_listing(fake.net(), run, root, tracked_issue(), at.date(), set())
        is None
    )
    assert "already trades" in run.warnings[0]


def test_the_task_definition_wakes_the_pc_three_times_a_weekday():
    import xml.etree.ElementTree as ET

    import make_ipo_task_xml

    xml = make_ipo_task_xml.task_xml(date(2026, 11, 2), r"C:\uv\uv.exe", REPO_ROOT, r"PC\me")
    ns = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}
    root = ET.fromstring(xml.encode("utf-16"))
    starts = [e.text for e in root.findall(".//t:CalendarTrigger/t:StartBoundary", ns)]
    assert starts == [
        "2026-11-02T12:00:00+05:30",
        "2026-11-02T15:30:00+05:30",
        "2026-11-02T19:30:00+05:30",
    ]
    days = root.findall(".//t:CalendarTrigger[1]//t:DaysOfWeek/*", ns)
    assert [d.tag.split("}")[1] for d in days] == [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
    ]
    settings = {e.tag.split("}")[1]: e.text for e in root.find("t:Settings", ns)}
    assert settings["WakeToRun"] == "true" and settings["StartWhenAvailable"] == "true"
    assert settings["DisallowStartIfOnBatteries"] == "false"
    assert root.find(".//t:Arguments", ns).text.endswith("record_ipo_live.py --scheduled")
