"""Partitioned parquet under data/clean and DuckDB views over it.

Layout (hive partitions; partition columns are not stored inside the files):
    {1m,5m,15m}/symbol=X/year=YYYY/part-0.parquet
    daily/features/symbol=X/part-0.parquet
    daily/rvol/symbol=X/part-0.parquet
    calendar/calendar.parquet
    etf_proxy/bars.parquet  (scripts/build_etf_proxy.py; daily, one file)

Views: bars_1m, bars_5m, bars_15m, daily_features, rvol_profile, calendar,
bars_5m_rvol (5m bars joined to their prior-20-session bucket average), and
etf_proxy_1d when the ETF proxy dataset has been built.
Timestamps are TIMESTAMPTZ; the connection's TimeZone is Asia/Kolkata.
"""

from pathlib import Path

import duckdb
import pandas as pd

from nsealgo.settings import REPO_ROOT

CLEAN_DIR = REPO_ROOT / "data" / "clean"
TIMEFRAMES = ("1m", "5m", "15m")
PART = "part-0.parquet"
ETF_PROXY_FILE = Path("etf_proxy") / "bars.parquet"


def write_bars(bars: pd.DataFrame, clean_dir: Path, timeframe: str) -> None:
    """Write one symbol's bars, one file per year (overwrites existing files)."""
    if timeframe not in TIMEFRAMES:
        raise ValueError(f"unknown timeframe {timeframe!r}")
    (symbol,) = bars["symbol"].unique()
    years = pd.to_datetime(bars["session_date"]).dt.year
    for year, part in bars.groupby(years.to_numpy()):
        out = clean_dir / timeframe / f"symbol={symbol}" / f"year={year}"
        out.mkdir(parents=True, exist_ok=True)
        part.drop(columns="symbol").to_parquet(out / PART, index=False)


def write_symbol_table(df: pd.DataFrame, clean_dir: Path, name: str) -> None:
    """Write one symbol's rows of a daily table (`features` or `rvol`)."""
    (symbol,) = df["symbol"].unique()
    out = clean_dir / "daily" / name / f"symbol={symbol}"
    out.mkdir(parents=True, exist_ok=True)
    df.drop(columns="symbol").to_parquet(out / PART, index=False)


def write_calendar(calendar: pd.DataFrame, clean_dir: Path) -> None:
    out = clean_dir / "calendar"
    out.mkdir(parents=True, exist_ok=True)
    calendar.to_parquet(out / "calendar.parquet", index=False)


def write_etf_proxy(bars: pd.DataFrame, clean_dir: Path) -> Path:
    """Write the ETF proxy bars (overwrites); returns the file written."""
    out = clean_dir / ETF_PROXY_FILE
    out.parent.mkdir(parents=True, exist_ok=True)
    bars.to_parquet(out, index=False)
    return out


def _glob(clean_dir: Path, sub: str, depth: int) -> str:
    return (clean_dir / sub).as_posix() + "/*" * depth + "/*.parquet"


def connect(clean_dir: Path = CLEAN_DIR) -> duckdb.DuckDBPyConnection:
    """In-memory DuckDB connection with read-only views over data/clean."""
    if not (clean_dir / "calendar" / "calendar.parquet").is_file():
        raise FileNotFoundError(f"{clean_dir} not built; run scripts/build_data.py")
    con = duckdb.connect(":memory:")
    con.execute("SET TimeZone = 'Asia/Kolkata'")
    for tf in TIMEFRAMES:
        src = _glob(clean_dir, tf, 2)
        con.execute(
            f"CREATE VIEW bars_{tf} AS SELECT * EXCLUDE (year) "
            f"FROM read_parquet('{src}', hive_partitioning = true)"
        )
    for view, sub in (("daily_features", "daily/features"), ("rvol_profile", "daily/rvol")):
        src = _glob(clean_dir, sub, 1)
        con.execute(
            f"CREATE VIEW {view} AS SELECT * FROM read_parquet('{src}', hive_partitioning = true)"
        )
    cal = (clean_dir / "calendar" / "calendar.parquet").as_posix()
    con.execute(f"CREATE VIEW calendar AS SELECT * FROM read_parquet('{cal}')")
    con.execute(
        "CREATE VIEW bars_5m_rvol AS "
        "SELECT b.*, r.avg_volume_20d, b.volume / NULLIF(r.avg_volume_20d, 0) AS rvol "
        "FROM bars_5m b LEFT JOIN rvol_profile r ON b.symbol = r.symbol AND b.ts = r.ts"
    )
    etf = clean_dir / ETF_PROXY_FILE
    if etf.is_file():
        con.execute(f"CREATE VIEW etf_proxy_1d AS SELECT * FROM read_parquet('{etf.as_posix()}')")
    return con
