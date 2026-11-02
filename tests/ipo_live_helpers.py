"""NSE-shaped inputs for the live IPO recorder tests, copied from NSE's responses of
2026-11-02 (/api/ipo-current-issue and /api/ipo-detail for BCSSL), trimmed."""

import io
import zipfile
from datetime import date


def current_rows() -> list[dict]:
    return [
        {
            "companyName": "Bombay Coated and Special Steels Limited",
            "issueEndDate": "02-Nov-2026",
            "issuePrice": "Rs.78 to Rs.82",
            "issueStartDate": "29-Oct-2026",
            "series": "EQ",
            "status": "Active",
            "symbol": "BCSSL",
            "noOfTime": "5.31490692682011",
        },
        {
            "companyName": "Vedant Poly Fabs Limited",
            "isBse": "1",
            "issueEndDate": "04-Nov-2026",
            "issueStartDate": "02-Nov-2026",
            "series": "SME",
            "status": "Active",
            "symbol": "VPFL",
        },
    ]


def detail(
    period: str = "29-Oct-2026 to 02-Nov-2026",
    stamp: str = "Updated as on 02-Nov-2026 11:24:00",
    isin: str | None = None,
) -> dict:
    head = {
        "category": "Category",
        "noOfShareOffered": "No.of shares offered/reserved",
        "noOfSharesBid": "No. of shares bid for",
        "noOfTotalMeant": "No. of times of total meant for the category",
        "srNo": "Sr.No.",
    }
    rows = [
        head,
        {
            "category": "Retail Individual Investors(RIIs)",
            "noOfShareOffered": "8214097",
            "noOfSharesBid": "73582418",
            "noOfTotalMeant": "8.958065384423875",
            "srNo": "3",
        },
        {
            "category": "Cut Off",
            "noOfShareOffered": "",
            "noOfSharesBid": "67622646",
            "srNo": "3(a)",
        },
        {
            "category": "Total",
            "noOfShareOffered": "1.6533012E7",
            "noOfSharesBid": "1.77421972E8",
            "noOfTotalMeant": "10.731376230779968",
            "srNo": None,
        },
    ]
    info = [
        {"title": "Symbol", "value": "BCSSL"},
        {"title": "Issue Period", "value": period},
        {"title": "Price Range", "value": "Rs. 78/- to Rs. 82/- per Equity Share"},
        {"title": "Bid Lot", "value": "182 Equity Shares and in multiples thereof"},
    ]
    return {
        "companyName": "BCSSL",
        "metaInfo": {"isin": isin} if isin else {},
        "issueInfo": {"dataList": info},
        "activeCat": {"dataList": rows, "symbol": "BCSSL", "updateTime": stamp},
    }


def udiff_zip(day: date, rows: list[tuple[str, str, str, float, float, float]]) -> bytes:
    """A UDiFF bhavcopy zip with rows (symbol, series, isin, open, close, prev_close)."""
    head = "TradDt,Sgmt,TckrSymb,SctySrs,ISIN,OpnPric,HghPric,LwPric,ClsPric,PrvsClsgPric"
    lines = [head] + [
        f"{day:%Y-%m-%d},CM,{s},{ser},{isin},{o},{max(o, c) + 1},{min(o, c) - 1},{c},{p}"
        for s, ser, isin, o, c, p in rows
    ]
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        name = f"BhavCopy_NSE_CM_0_0_0_{day:%Y%m%d}_F_0000.csv"
        zf.writestr(name, "\n".join(lines) + "\n")
    return buf.getvalue()
