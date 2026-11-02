# IPO v2: apply only when the book is at least 5x subscribed at 15:30 on the last day: pre-registration (forward test)

Written, committed and pushed before any decision under it. Strategy name `ipo`, version 2.
**Forward test only, no backtest:** the decision input (the 15:30 book on the last bid day)
was never recorded for past IPOs. NSE keeps one overwritten book per issue (step 1b,
`research/ipo_data_check_1b.md`). The rules in section 1 are the owner's and fixed. Any
change to them, or to the details this plan fixes, is v3 and restarts the count.

IPO applications are manual (UPI) and will never be automated (hard rule 1). Nothing here
places an order. A decision is a record of what the rule says. The simulation is the
evaluation.

## 1. Owner's rules (fixed)

> - Universe: every NSE mainboard IPO whose decision snapshot is taken after this plan's
>   commit time.
> - Decision snapshot: the scheduled 15:30 snapshot on the last bid day. If it is missing,
>   use the latest snapshot taken before 17:00 that day; if there is none, the issue is
>   "no decision data", excluded and counted in the report.
> - Apply for 1 lot at the top of the band if the total (consolidated) subscription at the
>   decision snapshot is at least 5.0x. If several qualify the same day and cash covers
>   fewer, take the highest total subscription at the snapshot.
> - Capital, blocking, costs, slippage tiers and the Monte Carlo method: exactly as IPO v1
>   (research/ipo_strategy_plan.md), Rs 20,000 virtual capital. Allotment uses each
>   issue's real 1-lot chance from its basis-of-allotment advert.
> - Sell at the NSE listing-day close.

## 2. Owner's decision rule (fixed)

> "If v2 passes checks 1-3 after at least 20 decisions, the owner may, once 18 and with an
> account open, apply with real money following v2 exactly. If it fails any of 1-3, the
> IPO track is parked."

## 3. Data

All from the live recorder, `scripts/record_ipo_live.py` (IPO track step 3; layout in
`docs/data.md`, "Live IPO recorder"), under `data/live/ipo/`, backed up to the private repo
nse-algo-live-data after every scheduled 19:30 run:

- per-issue JSON snapshots `<issue_id>/<YYYYMMDDTHHMMSS+0530>.json` (fetch time, IST) with
  the consolidated category-wise book and NSE's "Updated as on" stamp;
- `run_log.jsonl` (which run was scheduled, for which slot, which files it saved);
- the listing day's row from NSE's bhavcopy, `<issue_id>/listing_<YYYYMMDD>.json`;
- the basis-of-allotment advert, `<issue_id>/ADV_<ISIN>_<DDMONYYYY>.pdf`.

The benchmark is the Nifty 50 TRI from niftyindices.com
(`scripts/download_indices.py --only nifty50`), downloaded at evaluation time. Trading
days are weekdays not listed in `config/holidays.csv`, which is filled from each year's
NSE circular.

## 4. Universe and decision snapshot (details this plan fixes where section 1 is silent)

- **Mainboard:** the recorder's definition. A row of NSE's `/api/ipo-current-issue` with
  series `EQ` that is not an FPO and not a partly-paid line. SME issues are not in the
  universe. REITs and InvITs are not in that list.
- **Plan commit time:** the committer timestamp of the commit that adds this file. The
  next commit records it in `config/ipo_v2.yaml`. An issue is in the universe if the fetch
  time of its decision snapshot is later than this timestamp. An issue whose decision
  snapshot is earlier is recorded as `before_plan` and is not counted.
- **Last bid day D:** the bid-period end in the issue's latest per-issue JSON on disk when
  the decision is made.
- **Scheduled 15:30 snapshot:** the issue's per-issue JSON saved by the run that
  `run_log.jsonl` records as scheduled, for slot D 15:30 IST. It counts only if its fetch
  time is before 17:00:00 IST on D. A scheduled run that Task Scheduler starts after the
  17:00 UPI cutoff is too late to act on.
- **Fallback:** the issue's per-issue JSON with the latest fetch time on D before 17:00:00
  IST, from any run, scheduled or manual.
- **No decision data:** no per-issue JSON fetched on D before 17:00. Also when the chosen
  snapshot's consolidated "Total" row is missing or unreadable.
- **Total subscription:** the "Total" row of NSE's consolidated book (`activeCat`), times
  subscribed as NSE reports it (`noOfTotalMeant`; if absent, shares bid / shares offered),
  read by `nsealgo.data.ipo.category_bids(detail, "Total")`. Apply if it is >= 5.0. The
  value is compared as read, with no rounding.
- **One decision per issue,** appended once to `data/live/ipo/decisions.jsonl` and never
  changed. The decision written by the scheduled 15:30 run is final. If no decision has
  been written by 17:00 on D, the first run at or after 17:00 writes one by the rules
  above. If NSE extends the bid period after a decision, the decision stands and the
  evaluation report flags the issue.
- **No look-ahead:** the decision reads only the decision snapshot. Allotment chance,
  listing prices and later snapshots are never inputs.

## 5. Simulation (as IPO v1, `research/ipo_strategy_plan.md` at bb1946c, sections 5-7)

- **Capital:** Rs 20,000 virtual, compounding. Free cash on D = cash - everything still
  blocked on D (v1 5.1).
- **Application:** 1 lot at the top of the band. Blocked amount A = lot x (band high -
  retail discount); the discount counts only if the advert states one (v1 5.1).
- **Same-day choice (v2 rule, replaces v1's random order):** the issues that qualify on D
  are taken in order of total subscription at their decision snapshot, highest first
  (ties by issue_id). Each is applied for if free cash still covers its A; otherwise it is
  skipped, and counted as in v1 5.1.
- **Blocking:** v1 5.2. Not allotted: through the allotment date +1. Allotted: through the
  listing date +2. Withdrawn: through D. The allotment date comes from the advert; if the
  advert gives none, listing date -1 (v1).
- **Allotment:** one draw per application, allotted with probability p, the issue's 1-lot
  chance read from its advert. The advert is parsed by `nsealgo.data.ipo_boa`; p follows
  the dataset's 1-lot rule (`nsealgo.data.ipo_build`), including p = 1 for an
  undersubscribed retail book. If the advert is not found or its 1-lot row cannot be read,
  p is v1's estimate (v1 5.3): p = min(1, k / x), with these inputs.
  - x is the retail multiple in the issue's final book (`final_*.json`).
  - k is the median, over the evaluation set's issues with a parsed advert, of the average
    lots per valid application (advert TOTAL row).

  Such issues are flagged and counted. Withdrawn issues have p = 0.
- **Sale (v2 rule):** at the NSE listing-day close, the bhavcopy close in
  `listing_<date>.json`. Sale price = close x (1 - s).
- **P&L of an allotment:** lot x close x (1 - s) - sale charges - lot x (issue price -
  retail discount) - allotment charges. Issue price = the listing day's bhavcopy base
  price (previous close), which for an IPO is the issue price. P&L is credited when the
  money is free again. The refund of band high minus issue price comes back at the same
  time (v1 5.5).
- **Costs:** as v1 section 6. Allotment charges are nil, stamp duty included (allotments
  after 1 Jul 2020). The sale is a delivery sell, `costs.fill_charges("CNC", "SELL", ...)`
  with `config/costs.yaml` as it stands at the evaluation commit. Tax is nil (v1's main
  variant).
- **Slippage tiers on the sale:** none 0 (reference), base 0.25%, stress1 0.5%,
  stress2 1.0% (`config/costs.yaml` `ipo_listing_slippage_pct`, as v1).
- **Monte Carlo:** 10,000 runs per tier, seed 20261101 (numpy PCG64), common random
  numbers: one uniform per (run, issue) for allotment, shared by every tier and by the v1
  comparison (v1 section 7). Each run walks the decision days in order. On each day it
  first releases the blocks that are due, then applies, then draws the allotments.
- **Final equity** is counted after every block has been released.

## 6. Evaluation set and when the evaluation may run

- **A decision** is `apply` or `skip`. `no_decision_data` and `before_plan` are not
  decisions; they are counted.
- **Evaluation set:** decisions sorted by D (ties by issue_id). D20 is the D of the 20th
  decision. The set is every decision with D <= D20, so it has 20 or more issues if several
  close on D20. Decisions after D20 are not evaluated.
- **Ready:** the set exists, and every issue in it is resolved: its listing file is saved,
  or NSE marks it withdrawn. An issue neither listed nor marked withdrawn 45 days after D
  is reported to the owner and holds the evaluation until it is resolved.
- **Before ready:** `scripts/evaluate_ipo_v2.py` shows counts only: decisions, applies,
  skips, no decision data, before plan, listed, pending. No performance number of any kind
  (no subscription-vs-listing table, no P&L) is computed or shown before ready.
- **Once ready:** a single evaluation on a clean commit, logged as **one trial** in
  `research/trials.jsonl`: strategy `ipo`, version 2, period label `ipo_v2_forward`, from
  the first D to the evaluation end date, holding every tier's metrics. The script refuses
  a second evaluation of version 2. The DSR trial count rises by one.

## 7. Comparisons

- **v1's rules on the same issues (check 2):** the evaluation set, with every issue
  applied for and no threshold. Same-day order is uniformly random, using one more uniform
  per (run, issue) from the same seed (v1 5.1). Sale is at the listing-day open
  (`listing_<date>.json` open, the pre-open auction price), at base slippage, with the same
  allotment draws as v2.
- **Benchmark (check 3):** Rs 20,000 in the Nifty 50 TRI less 0.05% a year (v1 section 8).
  It is bought at the close of the last session before the first D in the set and valued
  at the close of the evaluation end date E, with no charges. E = the latest listing date
  in the set +2 trading days, the last possible release day. If E is not yet in the TRI
  file, the last session on or before E is used and flagged.

## 8. Checks (owner's; "greater" is strict, a tie fails)

Statistics are the MEAN over the 10,000 runs. With about 20 issues the median is mostly
lottery luck.

| # | Check | Tier | PASS when |
|---|---|---|---|
| 1 | Mean net profit > 0 | stress2 | mean over runs of (final equity - 20,000) > 0 |
| 2 | v2 beats v1's rules on the same issues | base | mean v2 final equity > mean v1-rules final equity |
| 3 | v2 beats the Nifty 50 TRI | base | mean v2 final equity > benchmark value at E |
| 4 | Distribution | base | REPORTED: median, 5th percentile of net profit, P(loss) = share of runs with final equity < 20,000 |

Also reported: every tier's mean, median and 5th percentile; applications, allotments and
skips per run (mean); the estimated-p issues; the flagged issues (extended bid periods,
benchmark end date); and the no-decision-data and before-plan issues with reasons.

## 9. Code (built after this commit, before any evaluation)

- A step in `scripts/record_ipo_live.py`: the scheduled 15:30 run writes the decision for
  each issue whose last bid day is today, and later runs write the section 4 fallback.
  `decisions.jsonl` is append-only and backed up.
- `scripts/evaluate_ipo_v2.py`: counts until ready (section 6), then the single
  evaluation.
- Tests for both: snapshot choice and fallback, threshold, one decision per issue, the
  refusal before ready, the evaluation-set cut at D20, and the same-day order by
  subscription.

## 10. Known limits

- The laptop must be awake at 15:30 on each last bid day. Missed snapshots fall back or
  become "no decision data", and are counted.
- NSE's stamp trails the fetch. The 15:30 run sees the book as last updated by NSE,
  roughly every hour (for example "Updated as on 02-Nov-2026 12:33:00" fetched at 12:38).
- About 20 issues, with allotment by lottery. A few large listing-day moves dominate the
  mean.
- `config/holidays.csv` must be refilled for 2027 from NSE's circular before 2027 last bid
  days.
