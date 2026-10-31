# IPO v1: result of the one authorised run

IPO v1 was pre-registered in `research/ipo_strategy_plan.md` (bb1946c) and built in
f3851b7. Both were committed and pushed before the run. The rules, parameters, costs,
benchmark and checks are exactly as written in the plan. This is a simulation of manual
UPI applications (hard rule 1). Nothing here places an order.

## Run facts

- **Authorisation:** on 2026-11-01 the owner typed "run holdout" in the session. They
  authorised one run of `scripts/run_ipo.py --run-holdout`, exactly as pre-registered,
  and approved the choices made where the spec was silent: check 2 at the base tier;
  check 3 REPORTED with no threshold; the listing-close variant at base slippage; and
  K.P.R. Agrochem excluded (plan sections 4 and 10).
- **Code:** `ipo` version 1 at f3851b7, run on a clean tree. All four trial lines record
  `git_dirty: false`.
- **Before the run:** 468 tests passed (`uv run python -m pytest -q`; the
  `uv run pytest` launcher is blocked by Windows Application Control on this machine).
  `ruff check` and `ruff format --check` were clean. `scripts/run_ipo.py --check` printed
  481 choices (479 listed, 2 withdrawn), 50 estimated 1-lot chances, 15 exclusions, 362
  application days and 41 estimated allotment dates. Those match plan sections 4 and 5.2.
- **Run:** one invocation at 2026-11-01 04:13 IST. It did 10,000 Monte Carlo runs per
  tier with seed 20261101, and every tier and variant used the same draws.
- **Trials:** 22 (none, reference tier), 23 (base), 24 (stress1) and 25 (stress2). All
  four have `holdout: true` and period `ipo_2019_2026` (bid close 2019-01-01 to
  2026-10-31). The DSR trial count is now 25: 7 ORB, 6 swing, 4 pullback,
  4 sector_rotation and 4 ipo. The runner will refuse a second holdout run of ipo v1.
- **Benchmark:** Rs 20,000 in the Nifty 50 TRI less 0.05% a year, bought at the close of
  2018-12-31. It was worth Rs 46,390 at the close of 2026-10-30 (+132.0%).
- **Warning printed by the run:** "weekdays used past the last session: 2026-11-02".
  This is the free day for the allotted case of JPL_20261021 and PARASHLTH_20261021
  (listed 2026-10-28, released 2026-10-30, the last bhavcopy session). The last
  application day in the universe is 2026-10-23, so this date changes no choice. P&L is
  attributed to the listing year, so it changes no year's number either.

## 1. First-pass checks (plan section 10)

All three checks use the main variant (481 choices).

| # | Check | Run | Number | Result |
|---|---|---|---|---|
| 1 | Mean net profit > 0 at stress2 | trial 25 (stress2, 1.0% listing slippage) | Mean over 10,000 runs of final equity - Rs 20,000 = Rs 33,859 | **PASS** |
| 2 | The median run beats the benchmark overall **and** in at least 5 of the 8 years | trial 23 (base, 0.25%) | Overall: median total return 321.5% vs benchmark 132.0% (ahead). Years: the per-year median is ahead in 3 of 8 (2023, 2024, 2026); 5 needed. | **FAIL** |
| 3 | P(losing year) at base | trial 23 (base) | 0.939: 9,389 of 10,000 runs have at least one calendar year 2019-2026 with negative net profit | **REPORTED** (no threshold) |

The owner's decision rule, fixed before the run (plan section 2):

> "If IPO v1 fails any first-pass check, the IPO strategy is parked. If it passes, the
> next step is live paper-tracking of every mainboard IPO from 1 Nov 2026 for at least 20
> issues; real money only after that and after the owner turns 18."

### Check 2, year by year (base, trial 23)

Base column: the median over the 10,000 runs of that year's in-year return. This is the
pre-registered statistic. "Ahead" means strictly greater.

| Year | Base median % | Benchmark % | Difference (pp) | Ahead |
|---|---|---|---|---|
| 2019 | -9.2% | 13.4% | -22.6 | no |
| 2020 | -3.1% | 16.1% | -19.1 | no |
| 2021 | 7.0% | 25.5% | -18.5 | no |
| 2022 | 0.0% | 5.6% | -5.6 | no |
| 2023 | 28.7% | 21.2% | +7.4 | yes |
| 2024 | 39.6% | 10.0% | +29.5 | yes |
| 2025 | 10.7% | 11.8% | -1.2 | no |
| 2026 | 3.1% | -10.9% | +14.0 | yes |

### The median run (information only, not the check)

The plan (section 10) also shows the year-by-year record of the single run with the
median total return. It is information only; check 2 uses the per-year medians above.

| Year | Run 4476 % | Benchmark % | Difference (pp) | Ahead |
|---|---|---|---|---|
| 2019 | 9.8% | 13.4% | -3.6 | no |
| 2020 | -3.3% | 16.1% | -19.4 | no |
| 2021 | -24.4% | 25.5% | -50.0 | no |
| 2022 | 10.3% | 5.6% | +4.7 | yes |
| 2023 | 59.7% | 21.2% | +38.4 | yes |
| 2024 | 54.5% | 10.0% | +44.4 | yes |
| 2025 | 41.2% | 11.8% | +29.4 | yes |
| 2026 | 36.7% | -10.9% | +47.6 | yes |
| **Total** | 321.5% | 132.0% | +189.5 | - |

## 2. Tiers, all 481 choices (trials 22-25)

Amounts are per run: the mean, median and 5th/95th percentiles over 10,000 runs of final
equity - Rs 20,000. Counts are the mean per run. The `none` tier (0% slippage) is the
reference tier and is not a tradeable result.

| Tier | Slippage | Mean Rs | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | P(losing year) | Applications | Allotments | Skipped, blocked | Skipped, capital |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 0% | 59,219 | 68,632 | -7,984 | 132,768 | 343.2% | -39.9% | 663.8% | 0.927 | 274.0 | 95.2 | 84.4 | 122.6 |
| base | 0.25% | 56,435 | 64,300 | -7,808 | 126,473 | 321.5% | -39.0% | 632.4% | 0.939 | 274.8 | 95.4 | 89.7 | 116.5 |
| stress1 | 0.5% | 48,555 | 55,188 | -7,903 | 119,321 | 275.9% | -39.5% | 596.6% | 0.953 | 252.9 | 88.0 | 85.9 | 142.2 |
| stress2 | 1% | 33,859 | 29,615 | -8,323 | 105,800 | 148.1% | -41.6% | 529.0% | 0.973 | 209.5 | 73.3 | 79.3 | 192.2 |

Mean net profit per tier (check 1's statistic): none Rs 59,219; base Rs 56,435;
stress1 Rs 48,555; stress2 Rs 33,859.

## 3. By year, base (trial 23)

Per year: the median, p5 and p95 of net profit; counts are the median per run; P(loss)
is the share of runs losing in that year. "All" is total return.

| Year | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | Applications | Allotments | Skipped, blocked | Skipped, capital | P(loss) | Benchmark % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | -1,841 | -4,018 | 10,702 | -9.2% | -20.1% | 53.5% | 11 | 4 | 4 | 0 | 0.663 | 13.4% |
| 2020 | -729 | -1,843 | 15,709 | -3.1% | -11.5% | 77.8% | 9 | 3 | 5 | 0 | 0.591 | 16.1% |
| 2021 | 1,600 | -5,803 | 24,365 | 7.0% | -29.3% | 103.8% | 21 | 8 | 30 | 0 | 0.451 | 25.5% |
| 2022 | 0 | -2,115 | 10,387 | 0.0% | -7.7% | 35.0% | 17 | 9 | 13 | 0 | 0.298 | 5.6% |
| 2023 | 9,594 | 0 | 35,292 | 28.7% | 0.0% | 108.6% | 36 | 8 | 10 | 0 | 0.001 | 21.2% |
| 2024 | 20,802 | 0 | 54,818 | 39.6% | 0.0% | 132.5% | 76 | 18 | 4 | 0 | 0.015 | 10.0% |
| 2025 | 6,425 | -847 | 22,359 | 10.7% | -1.2% | 32.9% | 85 | 32 | 7 | 0 | 0.064 | 11.8% |
| 2026 | 2,473 | -3,430 | 19,636 | 3.1% | -14.0% | 24.1% | 88 | 34 | 8 | 0 | 0.340 | -10.9% |
| **All** | 64,300 | -7,808 | 126,473 | 321.5% | -39.0% | 632.4% | 344 | 119 | 86 | 0 | 0.939 (any) | 132.0% |

## 4. By year, the other tiers

### none (0%, reference tier, trial 22)

| Year | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | Applications | Allotments | Skipped, blocked | Skipped, capital | P(loss) | Benchmark % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | -1,709 | -3,895 | 10,892 | -8.5% | -19.5% | 54.5% | 11 | 4 | 4 | 0 | 0.663 | 13.4% |
| 2020 | -620 | -1,812 | 15,896 | -2.6% | -11.3% | 78.8% | 9 | 3 | 5 | 0 | 0.590 | 16.1% |
| 2021 | 1,276 | -5,673 | 25,129 | 5.2% | -29.6% | 102.6% | 21 | 8 | 30 | 0 | 0.467 | 25.5% |
| 2022 | 0 | -1,696 | 11,213 | 0.0% | -6.6% | 36.1% | 17 | 9 | 13 | 0 | 0.266 | 5.6% |
| 2023 | 9,957 | 0 | 35,840 | 28.7% | 0.0% | 108.3% | 36 | 8 | 9 | 0 | 0.000 | 21.2% |
| 2024 | 21,322 | 0 | 55,580 | 39.2% | 0.0% | 130.8% | 77 | 18 | 3 | 0 | 0.013 | 10.0% |
| 2025 | 7,447 | 108 | 23,597 | 11.1% | 0.5% | 34.2% | 87 | 32 | 6 | 0 | 0.045 | 11.8% |
| 2026 | 3,496 | -2,907 | 21,238 | 4.0% | -7.0% | 25.3% | 89 | 34 | 7 | 0 | 0.233 | -10.9% |
| **All** | 68,632 | -7,984 | 132,768 | 343.2% | -39.9% | 663.8% | 349 | 120 | 80 | 0 | 0.927 (any) | 132.0% |

### stress1 (0.5%, trial 24)

| Year | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | Applications | Allotments | Skipped, blocked | Skipped, capital | P(loss) | Benchmark % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | -1,972 | -4,141 | 10,534 | -9.9% | -20.7% | 52.7% | 11 | 4 | 4 | 0 | 0.679 | 13.4% |
| 2020 | -838 | -2,825 | 15,521 | -3.8% | -15.9% | 76.2% | 9 | 3 | 5 | 0 | 0.615 | 16.1% |
| 2021 | 216 | -5,932 | 23,683 | 0.8% | -30.2% | 100.4% | 20 | 7 | 27 | 0 | 0.494 | 25.5% |
| 2022 | 0 | -2,420 | 9,518 | 0.0% | -8.5% | 32.3% | 16 | 8 | 13 | 0 | 0.283 | 5.6% |
| 2023 | 8,065 | 0 | 33,691 | 24.5% | 0.0% | 103.6% | 34 | 7 | 9 | 0 | 0.001 | 21.2% |
| 2024 | 17,781 | 0 | 53,282 | 34.6% | 0.0% | 129.7% | 73 | 18 | 4 | 0 | 0.012 | 10.0% |
| 2025 | 4,073 | -1,621 | 20,700 | 7.8% | -2.2% | 30.7% | 83 | 30 | 6 | 0 | 0.077 | 11.8% |
| 2026 | 772 | -4,373 | 17,778 | 1.3% | -9.2% | 22.5% | 82 | 32 | 8 | 0 | 0.346 | -10.9% |
| **All** | 55,188 | -7,903 | 119,321 | 275.9% | -39.5% | 596.6% | 330 | 114 | 82 | 0 | 0.953 (any) | 132.0% |

### stress2 (1.0%, trial 25)

| Year | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | Applications | Allotments | Skipped, blocked | Skipped, capital | P(loss) | Benchmark % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | -2,235 | -4,387 | 10,198 | -11.2% | -21.9% | 51.0% | 11 | 4 | 4 | 0 | 0.709 | 13.4% |
| 2020 | -1,056 | -2,957 | 14,745 | -5.3% | -16.8% | 65.0% | 9 | 2 | 5 | 0 | 0.657 | 16.1% |
| 2021 | -1,340 | -6,191 | 20,894 | -9.6% | -28.8% | 90.1% | 19 | 6 | 23 | 3 | 0.587 | 25.5% |
| 2022 | 0 | -2,833 | 7,743 | 0.0% | -9.4% | 27.9% | 15 | 7 | 8 | 0 | 0.276 | 5.6% |
| 2023 | 4,493 | 0 | 30,668 | 15.3% | 0.0% | 93.5% | 23 | 5 | 5 | 0 | 0.001 | 21.2% |
| 2024 | 9,345 | 0 | 49,348 | 20.4% | 0.0% | 121.9% | 62 | 15 | 3 | 0 | 0.016 | 10.0% |
| 2025 | -4 | -3,331 | 17,440 | -0.0% | -5.1% | 26.4% | 63 | 23 | 5 | 0 | 0.513 | 11.8% |
| 2026 | 0 | -6,114 | 13,427 | 0.0% | -9.6% | 18.0% | 62 | 25 | 7 | 0 | 0.413 | -10.9% |
| **All** | 29,615 | -8,323 | 105,800 | 148.1% | -41.6% | 529.0% | 271.5 | 93 | 66 | 6 | 0.973 (any) | 132.0% |

## 5. Without the 50 estimated issues (431 choices)

| Tier | Slippage | Mean Rs | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | P(losing year) | Applications | Allotments | Skipped, blocked | Skipped, capital |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| none | 0% | 50,921 | 55,394 | -7,871 | 116,814 | 277.0% | -39.4% | 584.1% | 0.947 | 254.7 | 92.7 | 80.6 | 95.7 |
| base | 0.25% | 47,206 | 50,483 | -7,559 | 111,067 | 252.4% | -37.8% | 555.3% | 0.957 | 251.2 | 91.5 | 84.9 | 94.9 |
| stress1 | 0.5% | 40,863 | 42,985 | -7,614 | 104,783 | 214.9% | -38.1% | 523.9% | 0.966 | 234.6 | 85.6 | 83.7 | 112.8 |
| stress2 | 1% | 31,868 | 31,602 | -8,291 | 92,451 | 158.0% | -41.5% | 462.3% | 0.984 | 216.9 | 79.2 | 89.7 | 124.4 |

### By year, base, without the estimated issues

| Year | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | Applications | Allotments | Skipped, blocked | Skipped, capital | P(loss) | Benchmark % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | -1,163 | -1,491 | 11,376 | -5.8% | -7.5% | 56.9% | 11 | 4 | 3 | 0 | 0.575 | 13.4% |
| 2020 | -729 | -4,335 | 12,286 | -3.9% | -23.4% | 50.5% | 9 | 3 | 4 | 0 | 0.692 | 16.1% |
| 2021 | 2,101 | -5,803 | 25,270 | 9.3% | -31.5% | 109.9% | 21 | 8 | 27 | 0 | 0.431 | 25.5% |
| 2022 | 0 | -2,469 | 10,966 | 0.0% | -9.6% | 34.8% | 16 | 9 | 12 | 0 | 0.321 | 5.6% |
| 2023 | 7,564 | 0 | 29,904 | 24.1% | 0.0% | 90.8% | 30 | 8 | 6 | 0 | 0.001 | 21.2% |
| 2024 | 19,025 | 0 | 51,564 | 39.3% | 0.0% | 132.2% | 67 | 17 | 5 | 0 | 0.017 | 10.0% |
| 2025 | 1,736 | -7,878 | 13,697 | 2.4% | -11.8% | 21.1% | 76 | 27 | 5 | 0 | 0.295 | 11.8% |
| 2026 | 2,744 | -3,226 | 19,179 | 4.1% | -17.9% | 29.3% | 78 | 31 | 10 | 0 | 0.237 | -10.9% |
| **All** | 50,483 | -7,559 | 111,067 | 252.4% | -37.8% | 555.3% | 308 | 111 | 79 | 0 | 0.957 (any) | 132.0% |

## 6. Secondary lines at base (plan section 7, variants 3 and 4)

Neither variant feeds a check. The sale at the close is never a decision input; the rule
sells at the listing-day open.

### 20% STCG sensitivity

| Year | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | Applications | Allotments | Skipped, blocked | Skipped, capital | P(loss) | Benchmark % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | -1,841 | -4,018 | 10,702 | -9.2% | -20.1% | 53.5% | 11 | 4 | 4 | 0 | 0.663 | 13.4% |
| 2020 | -729 | -2,501 | 14,579 | -4.0% | -11.5% | 77.4% | 9 | 3 | 5 | 0 | 0.608 | 16.1% |
| 2021 | 423 | -6,108 | 21,830 | 1.6% | -29.3% | 99.2% | 20 | 8 | 31.5 | 0 | 0.488 | 25.5% |
| 2022 | 0 | -4,691 | 8,158 | 0.0% | -13.3% | 32.3% | 16 | 8 | 14 | 0 | 0.418 | 5.6% |
| 2023 | 8,126 | 0 | 32,942 | 26.8% | 0.0% | 109.8% | 34 | 7 | 14 | 0 | 0.003 | 21.2% |
| 2024 | 16,710 | 0 | 51,153 | 35.7% | 0.0% | 134.9% | 72 | 18 | 6 | 0 | 0.026 | 10.0% |
| 2025 | 2,608 | -6,440 | 17,543 | 4.6% | -8.9% | 28.9% | 78 | 29 | 12 | 0 | 0.200 | 11.8% |
| 2026 | 0 | -5,386 | 12,888 | 0.0% | -18.0% | 19.0% | 79 | 31 | 12 | 0 | 0.491 | -10.9% |
| **All** | 48,584 | -7,824 | 98,664 | 242.9% | -39.1% | 493.3% | 321 | 112 | 103 | 0 | 0.983 (any) | 132.0% |

### Sale at the listing-day close

| Year | Median Rs | p5 Rs | p95 Rs | Median % | p5 % | p95 % | Applications | Allotments | Skipped, blocked | Skipped, capital | P(loss) | Benchmark % |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2019 | -932 | -2,581 | 15,760 | -4.7% | -12.9% | 78.8% | 11 | 4 | 4 | 0 | 0.608 | 13.4% |
| 2020 | 1,511 | 1,511 | 20,131 | 8.6% | 4.0% | 101.6% | 9 | 3 | 6 | 0 | 0.038 | 16.1% |
| 2021 | 10,886 | -2,861 | 37,845 | 37.6% | -13.0% | 132.5% | 30 | 10 | 32 | 0 | 0.133 | 25.5% |
| 2022 | -243 | -7,755 | 10,342 | -0.8% | -18.5% | 29.1% | 25 | 13 | 13 | 0 | 0.532 | 5.6% |
| 2023 | 18,808 | 5,373 | 45,956 | 46.2% | 16.0% | 127.7% | 45 | 11 | 10 | 0 | 0.000 | 21.2% |
| 2024 | 35,849 | 10,821 | 64,920 | 58.1% | 16.9% | 144.9% | 85 | 21 | 3 | 0 | 0.006 | 10.0% |
| 2025 | 10,421 | -2,401 | 25,500 | 10.3% | -4.3% | 32.0% | 97 | 36 | 5 | 0 | 0.113 | 11.8% |
| 2026 | 855 | -10,277 | 17,859 | 0.9% | -9.9% | 17.7% | 96 | 37 | 7 | 0 | 0.437 | -10.9% |
| **All** | 92,330 | 35,647 | 152,168 | 461.7% | 178.2% | 760.8% | 397 | 136 | 82 | 0 | 0.921 (any) | 132.0% |

## 7. Inputs

### k by year (average lots per valid application, used for the 50 estimated chances)

2018 1.351, 2019 1.270, 2020 1.362, 2021 1.254, 2022 1.274, 2023 1.290, 2024 1.301, 2025 1.225, 2026 1.199

### Excluded issues (15)

| Issue | Company | Bid close | Reason |
|---|---|---|---|
| KPRAGRO_20190628 | K.P.R. Agrochem Limited | 2019-07-02 | status not_found_on_nse: withdrawn a day before bidding opened (news, UNVERIFIED) |
| VISHWARAJ_20190930 | Vishwaraj Sugar Industries Limited | 2019-10-04 | data gap: no lot |
| CAMS_20200921 | Computer Age Management Services Limited | 2020-09-23 | status not_listed_on_nse_at_ipo: BSE-only listing (config/ipo_dataset.yaml) |
| MTARTECH_20210303 | MTAR Technologies Limited | 2021-03-05 | data gap: no 1-lot chance and no exchange multiple |
| RUCHISOYA_20220324 | Ruchi Soya Industries Limited | 2022-03-28 | status already_listed: traded before bidding (an unlabelled FPO) |
| ACI_20221109 | Archean Chemical Industries Limited | 2022-11-11 | data gap: no lot |
| HMAAGRO_20230620 | HMA Agro Industries Limited | 2023-06-23 | data gap: no lot |
| PROTEAN_20231106 | Protean eGov Technologies Limited | 2023-11-08 | status not_found_on_nse: BSE-only listing (UNVERIFIED; research/ipo_dataset.md section 2) |
| IREDA_20231121 | Indian Renewable Energy Development Agency Limited | 2023-11-23 | data gap: no 1-lot chance and no exchange multiple |
| PLATIND_20240227 | Platinum Industries Limited | 2024-02-29 | data gap: no lot |
| NSDL_20250730 | National Securities Depository Limited | 2025-08-01 | status not_found_on_nse: BSE-only listing (UNVERIFIED; research/ipo_dataset.md section 2) |
| NSE_20260917 | National Stock Exchange of India Limited | 2026-09-21 | status not_found_on_nse: BSE-only listing (the issuer itself; research/ipo_dataset.md section 2) |
| EDELALTS_20261026 | EAAA India Alternatives Limited | 2026-10-28 | status pending |
| BLSPOLY_20261027 | BLS Polymers Limited | 2026-10-29 | status pending |
| SFCTECH_20261027 | SFC Environmental Technologies Limited | 2026-10-29 | status pending |

## Read with the tables

These are observations on the numbers above. None of them changes a check.

- **Per-year medians are not one run's path.** Check 2 compares, for each year, the
  median across runs. The single median run (above) is ahead of the benchmark in 5 of 8
  years (2022-2026), while the per-year medians are ahead in 3. The pre-registered check
  uses the per-year medians.
- **Runs that fall below one lot.** Lot values in the universe range from Rs 11,025 to
  Rs 15,000 (median Rs 14,841; 94% above Rs 14,000). A run with less
  than about Rs 14,000 can apply for very few issues. The share of each year's choices
  skipped as "capital below one lot", averaged over runs:

  | Tier | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
  |---|---|---|---|---|---|---|---|---|
  | none | 0.0% | 16.1% | 21.5% | 28.1% | 28.1% | 28.0% | 27.4% | 26.5% |
  | base | 0.0% | 16.2% | 20.5% | 26.6% | 26.7% | 26.6% | 26.1% | 25.0% |
  | stress1 | 0.0% | 18.8% | 27.5% | 32.0% | 32.0% | 31.9% | 31.4% | 30.6% |
  | stress2 | 0.0% | 23.5% | 38.1% | 42.8% | 42.7% | 42.7% | 42.2% | 42.2% |
  | Choices (bid-close year) | 15 | 15 | 62 | 38 | 56 | 89 | 103 | 103 |

  The per-run median of these skips is 0 in every year at none, base and stress1 (at
  stress2 it is 3 in 2021 and 0 in the other years). From 2022 on, the mean share holds
  steady at about a quarter (base) and two-fifths (stress2). **My reading** is that
  about that share of runs is below one lot from 2022 on and applies for almost nothing
  after that (only the cheapest few lots). Such runs mostly have exactly Rs 0 in later
  years. That would explain the 2022 base median of exactly Rs 0, the Rs 0 p5 in 2023
  and 2024, and the total-return p5 of -39.0% (equity near Rs 12,000). This is inferred
  from the saved counts. The share of runs is not measured directly, because per-run
  final equity was not saved.
- **Mean vs median.** At base the mean exceeds the median in every year. In 2019, 2020
  and 2022 the median is negative or zero while the mean is positive (means Rs 245,
  2,682 and 2,072; medians Rs -1,841, -729 and 0). Overall the mean (Rs 56,435) is
  below the median (Rs 64,300).
- **Application counts are not monotone in cost.** Mean applications per run are 274.0
  (none) and 274.8 (base), then 252.9 and 209.5. Mean net profit is monotone. With
  common draws, a slightly different balance changes which issue is affordable on a day
  and so changes the rest of the path. I did not trace individual runs.
- **Open vs close.** Selling at the close (secondary) gives a base median total of
  461.7% and a p5 of +178.2%, against 321.5% and -39.0% at the open (the rule).
- **Fixed assumptions (plan sections 5-6):** Oct 2026 charge rates for every year;
  allotment as an independent draw at each issue's 1-lot chance; 50 estimated chances;
  41 estimated allotment dates; tax nil per the owner (20% sensitivity above); stamp
  duty of 0.015% on allotments before 1 Jul 2020 (the owner's default; no official source
  was read for that regime).

## Reproduce

    uv run python scripts/run_ipo.py --check         # inputs only, no simulation, no trial
    uv run python scripts/run_ipo.py --run-holdout   # refuses now: holdout already run for ipo 1

Run directory (local, gitignored): `research/runs/20261101-041347_ipo_v1`
(results.json, tables.md, terms.csv, excluded.csv). The check-2 and median-run year
tables, the skip-share table and the lot values above were computed from that
directory's `results.json` and `terms.csv` (one-off script, not in the repo; no
simulation).

Status: check 1 PASS, check 2 FAIL, check 3 REPORTED. The plan's decision rule says a
FAIL on any first-pass check parks the IPO strategy. The owner has not yet recorded a
decision.
