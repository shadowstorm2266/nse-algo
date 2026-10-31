"""Retail basis of allotment from an IPO's basis-of-allotment (BoA) advertisement.

Input is the advert's text from xpdf's pdftotext 4.x, twice: reading order (no flag) for
the prose, and `-table` for the category table (scripts/build_ipo.py runs pdftotext).
Only the retail section is read: from the heading "Allotment to [the] Retail Individual"
to the next "Allotment to" heading.

A table row is accepted only if category shares x applications = shares applied and both
'% of total' cells look like percentages; that also tells which numbers on the line are
which. The 1-lot row is the accepted row with the smallest category; its category is the
minimum bid (the lot). `-table` text can put another category's table on the same lines,
so rows are not summed; the TOTAL row is read only when the next number is 100. The build
checks the 1-lot row against NSE's lot and the lottery identity. Every field the advert
does not give in a recognised form is None, never inferred.
"""

import re
from dataclasses import asdict, dataclass
from datetime import date, timedelta

from nsealgo.data.ipo import parse_long_date

_RATIO = re.compile(r"(\d+)\s*:\s*(\d+)")
_NUMTOK = re.compile(r"\d[\d,]*(?:\.\d+)?")
_RETAIL_HEAD = re.compile(r"Allotment\s+to\s+(?:the\s+)?Retail\s+Individual", re.I)
# a heading starts its line, optionally labelled "B." / "(B)" / "2)"
_NEXT_HEAD = re.compile(
    r"^[ \t]*(?:[A-Ha-h][.)]|\([A-Ha-h]\)|\d[.)])?[ \t]*Allotment\s+to\s+"
    r"(?!(?:the\s+)?Retail\s+Individual)",
    re.I | re.M,
)


@dataclass(frozen=True)
class BoaRow:
    category_shares: int
    applications: int
    shares_applied: int
    allotted_per_applicant: int | None
    ratio_num: int | None
    ratio_den: int | None


@dataclass(frozen=True)
class RetailBoa:
    retail_sub_boa: float | None
    retail_shares_allotted: int | None
    retail_allottees: int | None
    retail_valid_applications: int | None  # the table's TOTAL row
    min_bid_shares: int | None
    min_bid_applications: int | None
    min_bid_ratio_num: int | None
    min_bid_ratio_den: int | None
    min_bid_allotted_shares: int | None
    retail_offer_price: float | None
    retail_discount: float | None
    allotment_date: date | None
    allotment_date_src: str | None  # 'finalized' or 'taken_on_record' (see _allotment_date)
    designated_exchange: str | None

    def as_dict(self) -> dict:
        return asdict(self)


def _int(tok: str) -> int:
    return int(tok.replace(",", "").split(".")[0])


def _share_count(tok: str) -> int | None:
    """A share count: '5,31,14,865' -> 53114865; '616.107' (a typo for 616,107; share
    counts are whole numbers) -> 616107; any other decimal -> None."""
    s = tok.replace(",", "").rstrip(".")
    if "." not in s:
        return int(s)
    whole, frac = s.split(".", 1)
    return int(whole + frac) if len(frac) == 3 and frac.isdigit() else None


def _is_pct(tok: str) -> bool:
    """A '% of total' cell: 0-100, no thousands separator."""
    return "," not in tok and float(tok) <= 100


def retail_section(text: str) -> str | None:
    """Text from the retail heading to the next 'Allotment to' heading (or the end)."""
    head = _RETAIL_HEAD.search(text)
    if head is None:
        return None
    nxt = _NEXT_HEAD.search(text, head.end())
    return text[head.start() : nxt.start() if nxt else len(text)]


def parse_row(line: str) -> BoaRow | None:
    """A category row of the retail table, or None (header, note, additional-share line)."""
    ratio = _RATIO.search(line)
    nums = _NUMTOK.findall(line[: ratio.start()] if ratio else line)
    for i in range(len(nums) - 4):
        if "." in nums[i] or "." in nums[i + 1] or "." in nums[i + 3]:
            continue
        if not (_is_pct(nums[i + 2]) and _is_pct(nums[i + 4])):
            continue
        cat, apps, applied = _int(nums[i]), _int(nums[i + 1]), _int(nums[i + 3])
        if cat > 0 and apps > 0 and cat * apps == applied:
            per = _int(nums[i + 5]) if len(nums) > i + 5 and "." not in nums[i + 5] else None
            num, den = (int(ratio[1]), int(ratio[2])) if ratio else (None, None)
            if num is None or not 0 < num <= den:  # 59:24 or 0:0 is not a draw ratio
                num, den = None, None
            return BoaRow(cat, apps, applied, per, num, den)
    return None


def one_lot_row(rows: list[BoaRow], lot: int | None = None) -> BoaRow | None:
    """The 1-lot retail row: the row with the most applications among those whose category
    is `lot` (NSE's bid lot, when known), else among those with the smallest category.
    Another table on the same lines can share the category (an employee or shareholder
    reservation), and a retail row can fail to parse; the retail 1-lot bucket is far the
    largest. None if no row has category `lot`."""
    if not rows:
        return None
    target = lot if lot else min(r.category_shares for r in rows)
    same = [r for r in rows if r.category_shares == target]
    return max(same, key=lambda r: r.applications) if same else None


def table_rows(
    section: str, lot: int | None = None, smallest_total: bool = False
) -> tuple[list[BoaRow], int | None]:
    """Accepted rows and the retail TOTAL row's application count (None if not found).
    A TOTAL line counts only if it reads 'applications, 100, shares applied' and fits the
    accepted rows: at least the 1-lot row's applications, and at least one lot per
    application (other tables in the section have TOTAL lines too). The first such line
    is taken, or with `smallest_total` (a whole-advert search, where a grand total of all
    categories also fits) the one with the fewest applications."""
    rows: list[BoaRow] = []
    totals: list[tuple[int, int]] = []
    for line in section.splitlines():
        if re.match(r"\s*(?:Grand\s+)?Total\b", line, re.I):
            nums = _NUMTOK.findall(line)
            if len(nums) >= 3 and nums[1] in ("100", "100.0", "100.00") and "." not in nums[2]:
                totals.append((_int(nums[0]), _int(nums[2])))
            continue
        row = parse_row(line)
        if row is not None:
            rows.append(row)
    if not rows:
        return rows, None
    first = one_lot_row(rows, lot)
    if first is None:
        return rows, None
    fits = [
        apps
        for apps, applied in totals
        if apps >= first.applications and applied >= apps * first.category_shares
    ]
    if not fits:
        return rows, None
    return rows, min(fits) if smallest_total else fits[0]


def text_is_readable(text: str) -> bool:
    """False for scanned adverts (no text layer, or only a newspaper page's running heads)
    and fonts without a character map, whose text comes out as U+FFFD characters. A
    readable advert has well over 3,000 letters."""
    letters = sum(ch.isalpha() for ch in text)
    return letters >= 3000 and text.count("\ufffd") < 0.05 * letters


_EXCH = r"(NSE|BSE|National\s+Stock\s+Exchange|BSE\s+Limited)\b"
_DATE = r"((?:\w+,?\s+){1,4}\d{4})"
_FINALIZED = re.compile(
    r"Basis\s+of\s+Allotment\s+(?:\([^)]*\)\s+)?was\s+finali[sz]ed\s+in\s+consultation\s+"
    r"with\s+(?:the\s+)?(?:\w+\s+and\s+the\s+)?Designated\s+Stock\s+Exchange,?\s+being\s+"
    r"(?:the\s+)?" + _EXCH + r"[^.]{0,40}?\bon\s+" + _DATE,
    re.I,
)
_ON_RECORD = re.compile(
    r"\bon\s+" + _DATE + r",?\s+(?:has|have)\s+taken\s+on\s+record\s+the\s+Basis\s+of\s+"
    r"Allotment[^.]{0,120}?Designated\s+Stock\s+Exchange,?\s+being\s+(?:the\s+)?" + _EXCH,
    re.I,
)


def _allotment_date(flat_all: str) -> tuple[date | None, str | None, str | None]:
    """(date, source, designated exchange). 'finalized': the date the advert says the basis
    of allotment was finalised with the designated exchange. Else 'taken_on_record': the
    date the board or IPO committee took it on record and allotted the shares."""

    def exch(name: str) -> str:
        return "NSE" if name.upper().startswith(("NSE", "NATIONAL")) else "BSE"

    if (m := _FINALIZED.search(flat_all)) and (day := parse_long_date(m[2])):
        return day, "finalized", exch(m[1])
    if (m := _ON_RECORD.search(flat_all)) and (day := parse_long_date(m[1])):
        return day, "taken_on_record", exch(m[2])
    return None, None, None


def _prose_fields(flat_section: str, flat_all: str) -> dict:
    sub = re.search(
        r"subscribed\s+(?:to\s+the\s+extent\s+of\s+|by\s+)?([\d,]+(?:\.\d+)?)\s*times",
        flat_section,
        re.I,
    )
    # "... 2,133,480 Equity Shares (undersubscribed portion ... spilled over ...) to 11,476
    # successful ..."; one advert has no space before "successful"
    allot = re.search(
        r"(\d[\d,.]*)\s+Equity\s+Shares\s*(?:\([^)]*\)\s*)?to\s+([\d,]+)\s*successful",
        flat_section,
        re.I,
    )
    price = re.search(r"Offer\s+Price\s+of\s+\D{0,3}?([\d,]+(?:\.\d+)?)", flat_section, re.I)
    # "(Retail Discount of Rs 10", "(less Retail Discount of Rs 5/-", "(a discount of Rs 45 per
    # Equity Share was offered to Retail ...", "(less discount of Rs 0.50"
    disc = re.search(
        r"\(\s*(?:less\s+|a\s+)?(?:Retail\s+)?Discount\s+of\s+\D{0,3}?([\d,]*\d(?:\.\d+)?)",
        flat_section,
        re.I,
    )
    day, src, exch = _allotment_date(flat_all)
    return {
        "retail_sub_boa": float(sub[1].replace(",", "")) if sub else None,
        "retail_shares_allotted": _share_count(allot[1]) if allot else None,
        "retail_allottees": _int(allot[2]) if allot else None,
        "retail_offer_price": float(price[1].replace(",", "")) if price else None,
        "retail_discount": float(disc[1].replace(",", "")) if disc else None,
        "allotment_date": day,
        "allotment_date_src": src,
        "designated_exchange": exch,
    }


def parse_retail_boa(prose_text: str, table_text: str, lot: int | None = None) -> RetailBoa | None:
    """Retail fields of one advert, or None if neither text has a retail section. `lot` is
    NSE's bid lot for the issue, used to find the 1-lot row (one_lot_row)."""
    prose, table = retail_section(prose_text), retail_section(table_text)
    if prose is None and table is None:
        return None
    flat = re.sub(r"\s+", " ", prose or table or "")
    fields = _prose_fields(flat, re.sub(r"\s+", " ", prose_text))
    rows, total = table_rows(table or "", lot)
    first = one_lot_row(rows, lot)
    if first is None and lot:
        # the -table text can drop the retail heading, or break the 1-lot row inside the
        # section: look for NSE's lot in the whole advert (most applications wins)
        rows, total = table_rows(table_text, lot, smallest_total=True)
        first = one_lot_row(rows, lot)
    return RetailBoa(
        **fields,
        retail_valid_applications=total,
        min_bid_shares=first.category_shares if first else None,
        min_bid_applications=first.applications if first else None,
        min_bid_ratio_num=first.ratio_num if first else None,
        min_bid_ratio_den=first.ratio_den if first else None,
        min_bid_allotted_shares=first.allotted_per_applicant if first else None,
    )


def boa_probe_dates(issue_close: date, listing_date: date) -> list[date]:
    """Dates to try for NSE's advert file ADV_<ISIN>_<DDMONYYYY>.pdf, most likely first:
    the advert is usually filed the day before listing. Then the other days between the
    bid close and listing, and the day after listing."""
    first = [listing_date - timedelta(days=k) for k in (1, 2, 3)] + [listing_date]
    rest, day = [], listing_date - timedelta(days=4)
    while day > issue_close:
        rest.append(day)
        day -= timedelta(days=1)
    seen: list[date] = []
    for d in [*first, *rest, listing_date + timedelta(days=1)]:
        if d > issue_close and d not in seen:
            seen.append(d)
    return seen
