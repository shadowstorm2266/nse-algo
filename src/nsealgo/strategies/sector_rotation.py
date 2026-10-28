"""Strategy 4: sector rotation over NSE sector-ETF proxies, swing (CNC delivery, daily
bars). Pre-registered in research/strategy4_plan.md (version 1).

The rules are strategy 2's (swing_momentum.py, version 2), unchanged: after the last
tradeable session of each month, keep the series whose close is above their 200-session
average, rank them by 6-month return skipping the latest month, and hold the top 4
(holdings still in the top 4 are kept as they are); orders fill at the next tradeable
open. Only the name, the version and the instrument differ: every fill is an equity-ETF
unit (instrument "ETF"), and the backtest reads the ETF proxy dataset and its universe
(config/etf_proxy.yaml, the 11 sector series).

Parameters come from config/strategies/sector_rotation.yaml; nothing here has a
default. Equal weight, whole units, the position cap and max_positions belong to the
RiskGovernor (config/risk.yaml, swing block).
"""

from nsealgo.strategies.swing_momentum import SwingMomentumStrategy


class SectorRotationStrategy(SwingMomentumStrategy):
    name = "sector_rotation"
    # bump on any logic change here or in SwingMomentumStrategy, or a change of a
    # default in sector_rotation.yaml
    version = "1"
    instrument = "ETF"
