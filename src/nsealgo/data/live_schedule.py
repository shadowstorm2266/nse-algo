"""Run schedule of the live IPO recorder (scripts/record_ipo_live.py): which runs were due
and which were missed. Pure functions; every datetime is tz-aware Asia/Kolkata.

A slot is 12:00, 15:30 or 19:30 IST on an NSE trading day: a weekday not listed in
config/holidays.csv. A scheduled run counts for the latest slot at or before its start
(up to EARLY before a slot counts for that slot), so a run that Task Scheduler starts late
(computer off or asleep at the slot) still counts for its slot and is flagged late. A
manual run counts for no slot. A slot is missed when no scheduled run counted for it.
"""

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta

from nsealgo.data.calendar import IST

SLOT_TIMES = (time(12, 0), time(15, 30), time(19, 30))
EARLY = timedelta(minutes=5)
# a manual run reports a slot as missed only once this much time has passed since it
MANUAL_GRACE = timedelta(minutes=60)
LATE_WARN = timedelta(minutes=30)
MAX_LOOKBACK_DAYS = 31


def is_trading_day(day: date, holidays: set[date]) -> bool:
    return day.weekday() < 5 and day not in holidays


def day_slots(day: date) -> list[datetime]:
    return [datetime.combine(day, t, tzinfo=IST) for t in SLOT_TIMES]


def _ist(at: datetime) -> datetime:
    if at.tzinfo is None:
        raise ValueError(f"naive datetime {at!r}")
    return at.astimezone(IST)


def slots_between(since: datetime, until: datetime, holidays: set[date]) -> list[datetime]:
    """Slots s with since < s < until, in order."""
    since, until = _ist(since), _ist(until)
    out: list[datetime] = []
    day = since.date()
    while day <= until.date():
        if is_trading_day(day, holidays):
            out.extend(s for s in day_slots(day) if since < s < until)
        day += timedelta(days=1)
    return out


def slot_for(at: datetime, holidays: set[date]) -> datetime | None:
    """The slot a scheduled run starting at `at` counts for: the latest slot at or before
    at + EARLY, looking back at most MAX_LOOKBACK_DAYS days. None on a day that is not a
    trading day (the run has no slot to count for) or if there is no slot in reach."""
    t = _ist(at) + EARLY
    if not is_trading_day(t.date(), holidays):
        return None
    for back in range(MAX_LOOKBACK_DAYS + 1):
        day = t.date() - timedelta(days=back)
        if is_trading_day(day, holidays):
            due = [s for s in day_slots(day) if s <= t]
            if due:
                return due[-1]
    return None


@dataclass(frozen=True)
class ScheduleCheck:
    slot: datetime | None  # the slot this run counts for (scheduled runs only)
    late: timedelta | None  # start minus slot
    duplicate: bool  # an earlier scheduled run already counted for this slot
    missed: list[datetime] = field(default_factory=list)  # newly missed since the last one


def check_schedule(
    covered: Iterable[datetime], now: datetime, scheduled: bool, holidays: set[date]
) -> ScheduleCheck:
    """`covered`: slots that earlier scheduled runs counted for (from the run log). Missed
    slots are those after the latest covered slot and before this run's slot (scheduled)
    or before now - MANUAL_GRACE (manual) that no run covered. Nothing is missed before
    the first scheduled run on record."""
    done = {_ist(s) for s in covered}
    now = _ist(now)
    slot = slot_for(now, holidays) if scheduled else None
    late = now - slot if slot is not None else None
    missed: list[datetime] = []
    if done:
        until = slot if slot is not None else now - MANUAL_GRACE
        missed = [s for s in slots_between(max(done), until, holidays) if s not in done]
    return ScheduleCheck(slot, late, slot in done, missed)


def missed_in_window(
    covered: Iterable[datetime], start: datetime, now: datetime, holidays: set[date]
) -> list[datetime]:
    """Every slot from `start` (inclusive) to now - MANUAL_GRACE with no scheduled run,
    for the --status report. Starts no earlier than the first covered slot."""
    done = {_ist(s) for s in covered}
    if not done:
        return []
    since = max(_ist(start), min(done)) - timedelta(seconds=1)
    return [s for s in slots_between(since, _ist(now) - MANUAL_GRACE, holidays) if s not in done]
