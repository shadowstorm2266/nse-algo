# IPO v1: apply for one lot of every affordable mainboard IPO: pre-registration

Written and committed before any run of this strategy. The rules and parameters below are
the owner's, fixed, and not tuned on any result. Strategy name `ipo`, version 1. If a code
bug is found after the run, the fix bumps the version and the rerun is a new trial. Earlier
trial lines stay in `research/trials.jsonl`.

IPO applications are manual (UPI) and will never be automated (hard rule 1). This is a
simulation only. Nothing here places an order, so the RiskGovernor is not involved: the
only limit is the owner's rule that free cash must cover each application.

## 1. What is tested

Apply for one lot, at the top of the price band, on the last bid day, to every mainboard
IPO that free cash can cover. Sell any allotment at the NSE listing-day open. The question
is whether this beats Rs 20,000 in the Nifty 50 total-return index after costs, with
allotment drawn at each issue's 1-lot chance.

## 2. Owner's decision rule (fixed before the run)

> "If IPO v1 fails any first-pass check, the IPO strategy is parked. If it passes, the next
> step is live paper-tracking of every mainboard IPO from 1 Nov 2026 for at least 20
> issues; real money only after that and after the owner turns 18."

## 3. Data

- **Issues:** `data/clean/ipo/ipos.parquet`, built by `scripts/build_ipo.py` at ec52ba6
  (rules in `docs/data.md`, report in `research/ipo_dataset.md`; owner's decisions in its
  section 7 and in `research/ipo_data_check_1b.md` section 9).
- **Trading days:** the NSE bhavcopy sessions in `data/raw/ipo/bhavcopy` (2016-01-01 to
  2026-10-30). "Working day" = NSE trading day (owner's decision 4 of step 1b). Bank
  holidays can differ. If a day past 2026-10-30 is ever needed, weekdays are used and the
  run records a warning.
- **Benchmark:** Nifty 50 TRI from niftyindices.com, `data/raw/ipo/benchmark/nifty50_tri.csv`
  (`scripts/download_indices.py --only nifty50 --out data/raw/ipo/benchmark`, downloaded
  2026-11-01, to 2026-10-30; its 2,929 rows overlapping `data/raw/indices` are identical).
- **Holdout.** The period runs past `holdout_start` (2025-04-08). For IPOs the holdout is
  already contaminated (owner's decision of 2026-10-31, `research/phase2_literature.md`),
  and the out-of-sample test is paper-tracking from 1 Nov 2026. Hard rule 8 still applies:
  the run starts only after the owner types "run holdout" in the session. `scripts/run_ipo.py`
  refuses without `--run-holdout`, logs every trial with `holdout: true`, and refuses a
  second holdout run of `ipo` version 1.

## 4. Universe

Issues in the table with bid close from 2019-01-01 to 2026-10-31: 496.

| Group | Issues | Treatment |
|---|---|---|
| Listed on NSE, with lot and a 1-lot chance (parsed or estimable) | 479 | choices |
| Withdrawn after bidding opened: Antony Waste (first attempt, Mar 2020), PKH Ventures (Jul 2023) | 2 | choices: blocked through the bid window, zero return |
| BSE-only listings: CAMS 2020, Protean 2023, NSDL 2025, NSE 2026 | 4 | excluded (no BSE prices); listed in the report |
| Already listed before bidding (Ruchi Soya 2022, an unlabelled FPO) | 1 | excluded (not an IPO) |
| K.P.R. Agrochem 2019: no NSE bids or listing; news reports it was withdrawn a day before opening (UNVERIFIED) | 1 | excluded (could not be applied for) |
| Pending at 31 Oct 2026 (closed 28-29 Oct, not yet listed): EAAA India Alternatives, BLS Polymers, SFC Environmental | 3 | excluded (outcome unknown). No other issue closes on or after 28 Oct, so no choice depends on them |
| Listed, data gap: no lot (Vishwaraj 2019, Archean 2022, HMA Agro 2023, Platinum 2024), or no 1-lot chance and no exchange multiple (MTAR 2021, IREDA 2023) | 6 | excluded; listed in the report |

**Choices: 481 issues on 362 application days (up to 6 closing on one day).** Of the 479
listed, 50 use an estimated 1-lot chance (section 5.3). Their counts by bid-close year:
2019 1, 2020 2, 2021 4, 2022 2, 2023 14, 2024 10, 2025 13, 2026 4.

## 5. Rules (ipo v1)

Parameters live in `config/strategies/ipo_v1.yaml`; costs in `config/costs.yaml`.

### 5.1 Application (decision inputs: dates, band, lot, free cash only)

- **Capital:** Rs 20,000 at the start, compounding. There is no limit on concurrent
  applications as long as free cash covers each one.
- **When:** on the issue's last bid day D (`issue_close`), before the 17:00 cutoff (owner's
  decision 1 of step 1b).
- **What:** exactly 1 lot at the top of the band. Blocked amount A = lot x (band high -
  retail discount), where the discount counts only if the advert states one (4 listed
  issues).
- **Free cash** on D = cash - every amount still blocked on D.
- **Same-day choice:** issues closing on D are taken in a uniformly random order (drawn
  inside the simulation). Each is applied for if free cash still covers its A; otherwise
  it is skipped and the next is tried. If free cash covers all of them, all are applied.
- **Skipped:** an issue whose A exceeds free cash on D is skipped. It is counted as
  "skipped, cash blocked" when total cash would cover it, and as "skipped, capital below
  one lot" when even total cash would not.
- **No look-ahead:** subscription, allotment chance, listing prices and withdrawal are not
  inputs to the choice. Excluding BSE-only listings uses information in the offer
  document; the data-gap and pending exclusions are recorded as such.

### 5.2 Blocking (owner's decision 3, `research/ipo_dataset.md` section 7)

Money is blocked from D through the release day R inclusive, and is free again from the
first trading day after R. "+n" means n NSE trading days later.

| Outcome | Release day R |
|---|---|
| Not allotted | allotment date +1 (the first trading day after the allotment date) |
| Allotted | listing date +2 (the listing-day sale settles and the money is back in the bank) |
| Withdrawn | D (blocked through the bid window only) |

Where the advert gives no allotment date (41 listed choices), it is estimated as the
listing date -1. None of the 438 known allotment dates from 2019 on is later than that
(6 equal it; 306 are 2 trading days before listing, 121 are 3, 5 are 4), so the estimate
keeps non-allotted money blocked at least as long as the real date would.

### 5.3 Allotment

A random draw per application: allotted with probability p, the issue's 1-lot chance.

- **Parsed** (`p_1lot`, 429 choices): the advert's value as built.
- **Estimated** (50 choices, flagged): p = min(1, k_y / x). Here x = `retail_sub_exch`, and
  k_y is the median over year y's parsed issues of `retail_shares_applied` / lot /
  `retail_valid_applications` (average lots per valid application, advert TOTAL row). y is
  the bid-close year, and the parsed issues are listed issues of that year with all three
  fields. The mix of after-rejection (k) and before-rejection (x) figures is accepted by
  the owner (decision 5 of step 1b). The k values used are printed in the report.
- Withdrawn issues: p = 0.

### 5.4 Sale

At the NSE listing-day open (`list_open`, the pre-open call-auction price), less slippage:
sale price = open x (1 - s), with s from the tier (section 6). The listing-day close is
reported only as a secondary figure (section 9). It is never a decision input.

### 5.5 Net profit of an allotted application

P&L = lot x open x (1 - s) - sale charges - lot x (issue price - retail discount) -
allotment charges. It is credited when the money is free again (the day after R). An
issue priced below the band's top gets its refund of the difference at the same time
(conservative).

## 6. Costs

| Item | Value | Source |
|---|---|---|
| Allotment: brokerage, STT | nil | owner |
| Allotment: stamp duty, allotments from 1 Jul 2020 | nil to the allottee | stamp duty on an issue of securities is collected from the issuer (rule 6(1); from the offeror for an offer for sale, rule 6(4)): Indian Stamp (Collection of Stamp-Duty through Stock Exchanges, Clearing Corporations and Depositories) Rules, 2019, G.S.R. 901(E), 10 Dec 2019, Gazette of India (read in the original). The rules say they come into force on 9 Jan 2020; the deferral of the Finance Act 2019 stamp provisions to 1 Jul 2020 is from secondary sources (not read in the original) |
| Allotment: stamp duty, allotments before 1 Jul 2020 | 0.015% of the allotment value | owner's default (no official source read for the earlier regime). Date = allotment date, else the estimate in 5.2. 16 choices |
| Sale (delivery sell, `costs.fill_charges("CNC", "SELL", ...)`) | STT 0.1%; NSE transaction charge 0.00297%; SEBI Rs 10 per crore; GST 18% on (transaction + SEBI + DP); shoonya DP charge Rs 9 + GST; brokerage nil (shoonya delivery) | `config/costs.yaml` (rates as of Oct 2026, applied to every year) |
| Slippage on the listing-open sale | none 0 (reference tier), base 0.25%, stress1 0.5%, stress2 1.0% | owner; new table `ipo_listing_slippage_pct` in `config/costs.yaml` |
| Tax | nil for the owner (owner's statement: adult, no other income). Sensitivity: 20% STCG (cess not included) | owner |

**Tax sensitivity** (base tier only): 20% of each financial year's net realised P&L
(April-March, by listing date) when positive, no loss carry-forward, deducted from cash on
the first trading day on or after 31 July following the year (the return due date). The
partial year 2026-27 is deducted at the end of the run. A deduction counts against the
calendar year in which it is paid.

## 7. Simulation method

- 10,000 Monte Carlo runs per tier, seed 20261101 (numpy PCG64). Every tier and variant uses
  the same draws (common random numbers): one uniform per (run, issue) for allotment, and
  one uniform per (run, issue) that orders same-day issues.
- Each run walks the 362 application days in order. On each day it first releases every
  block whose free day has come, then applies (section 5.1), then draws the allotments.
- Variants inside each tier's trial:
  1. main: all 481 choices;
  2. without estimated issues: the 50 estimated issues removed from the universe (not
     applied for, so they block nothing).
- Base tier only: (3) tax sensitivity and (4) sale at the listing-day close (secondary),
  both on all 481 choices.

**Per-run quantities.**

- Net profit of calendar year y = the P&L of sales with listing date in y, less any tax
  paid in y (variant 3 only).
- Equity at the end of y = Rs 20,000 + the net profits of all years up to y.
- In-year return = the year's net profit / equity at the end of y-1 (Rs 20,000 for 2019).
- Total return = (final equity - 20,000) / 20,000. Final equity is after every block has
  been released; the last release is in Oct 2026.
- Applications, allotments and skips count by bid-close year.

## 8. Benchmark (reporting, not a trial)

Rs 20,000 in the Nifty 50 TRI less 0.05% a year: value = 20,000 x TRI_t / TRI_0 x (1 -
0.05%/365)^days (as `nsealgo.data.etf_proxy.accrual_factor`). It is bought at the close of
31 Dec 2018, the last session before the period, with no charges. It is valued at each
year's last session close, and 2026 ends at the close of 30 Oct 2026. In-year return =
year-end value / previous year-end value - 1. Total return = 30 Oct 2026 value / 20,000 - 1.

## 9. Runs and trials

One invocation, after the owner types "run holdout":

    uv run python scripts/run_ipo.py --run-holdout

It runs four tiers and logs **one trial per tier: trials 22-25** (the DSR trial count goes
from 21 to 25), in this order: none (`reference_tier: true`), base, stress1, stress2. Each
trial record holds the tier's main metrics, the without-estimated metrics, and for base
the tax and listing-close variants. Period label `ipo_2019_2026`, 2019-01-01 to
2026-10-31, `holdout: true`. All four run on one clean commit containing this plan and the
code. No other runs, no parameter variants.

## 10. First-pass checks (fixed before the run)

Each is reported as PASS or FAIL with its number. "Beats" means strictly greater; a tie is
a FAIL. All checks use the main variant (481 choices).

| # | Check | Tier | PASS when |
|---|---|---|---|
| 1 | Mean net profit > 0 at stress2 | stress2 (1.0%) | the mean over the 10,000 runs of final equity - Rs 20,000 is > 0 |
| 2 | The median run beats the benchmark overall and in at least 5 of the 8 years | base (0.25%) | the median over runs of total return > the benchmark's total return, **and** the median over runs of the in-year return > the benchmark's in-year return in at least 5 of 2019, ..., 2025, 2026 (to 31 Oct) |
| 3 | P(losing year) at base | base | reported as a number: the share of runs with at least one calendar year 2019-2026 of negative net profit. The owner set no threshold, so it cannot pass or fail. It is shown as REPORTED |

Check 2 compares per-year medians across runs. The year-by-year record of the single run
with the median total return (rank 5,000 of 10,000, ties by run index) is also shown, as
information only. The tier for check 2 was not named by the owner; base is used, the same
tier as check 3.

## 11. Reported (numbers only, no verdict)

For each tier, for each calendar year 2019-2026 and overall:

- median, 5th and 95th percentile of net profit in Rs and in % (in-year return; overall:
  total return);
- applications made, allotments won, skipped (cash blocked), skipped (capital below one
  lot): median and mean per run;
- the share of runs with a losing year (overall: any year; per year: that year).

Also shown:

- the same for the without-estimated variant;
- the benchmark by year and overall, next to the base-tier medians;
- the k values by year;
- the excluded issues with reasons;
- the tax sensitivity and listing-close lines at base;
- the mean net profit per tier (check 1's statistic at every tier).

Tables go to the run directory (`research/runs/`, gitignored), and the write-up is
`research/ipo_v1_result.md`.

## 12. Code (built and tested before the run)

- `config/strategies/ipo_v1.yaml`: every parameter above; `config/costs.yaml`: an `ipo`
  section (allotment stamp rates and switch date, listing-sale slippage tiers), loaded by
  `costs.load_ipo_costs`.
- `src/nsealgo/strategies/ipo_v1.py`: universe and exclusions, k and the estimated p,
  blocking days, per-issue P&L by tier.
- `src/nsealgo/engine/ipo_sim.py`: the Monte Carlo cash and blocking simulation,
  vectorised over runs.
- `src/nsealgo/reporting/ipo_report.py`: statistics, benchmark, checks and tables.
- `scripts/run_ipo.py`: holdout lock, the four tiers, trial records, run directory.
- Tests first, on synthetic issues:
  - release-day conventions (blocked through R, free from R+1);
  - same-day random choice (about even over many runs);
  - skip counting;
  - withdrawn issues;
  - compounding (a win funds two applications at once);
  - P&L and costs on a hand-worked issue;
  - tax deduction timing;
  - year attribution;
  - the estimated p and k;
  - no look-ahead (changing an issue's p, P&L or later issues does not change the choices
    made on or before its day);
  - the benchmark on a toy TRI.
