"""Daily-bar indicators shared by the swing strategies. Pure functions, no state."""

from datetime import date

import numpy as np

from nsealgo.engine.context import BarView


def has_bar_on(bars: BarView, day: date) -> bool:
    """True when the symbol's last visible bar is from `day`."""
    return bool(len(bars)) and bars.ts[-1].date() == day


def above_average(bars: BarView, sessions: int) -> bool:
    """The last close is strictly above the simple average of the last `sessions` closes
    (the last one included). False with fewer closes."""
    c = bars.close
    return len(c) >= sessions and float(c[-1]) > float(c[-sessions:].mean())


def wilder_rsi(close: np.ndarray, n: int) -> float | None:
    """Wilder's RSI(n) at the last close of `close`.

    Changes of consecutive closes; gain = max(change, 0), loss = max(-change, 0). The
    averages start as the simple mean of the first n gains and losses, then
    avg = (avg x (n - 1) + new) / n. RSI = 100 x avg gain / (avg gain + avg loss).
    None with fewer than n changes, or when both averages are zero.
    """
    change = np.diff(np.asarray(close, dtype="float64"))
    if len(change) < n:
        return None
    gains, losses = np.maximum(change, 0.0), np.maximum(-change, 0.0)
    gain, loss = float(gains[:n].mean()), float(losses[:n].mean())
    for g, lo in zip(gains[n:].tolist(), losses[n:].tolist(), strict=True):
        gain = (gain * (n - 1) + g) / n
        loss = (loss * (n - 1) + lo) / n
    total = gain + loss
    return 100 * gain / total if total > 0 else None
