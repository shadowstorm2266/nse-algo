# IPO track step 1b: what a selection rule could see before the UPI cutoff

**Data check only. No backtest, no trial.** `research/trials.jsonl` was not touched; the DSR
trial count stays at 21. The owner's rule: the selection rule may use only information
visible before the UPI cutoff on the last bid day. Questions: do NSE or BSE publish
historical day-wise (end of each bid day) category-wise subscription for past mainboard
IPOs from 2019 on, and which fields already in the table are known before bidding closes?

Universe for the counts below: the 485 listed mainboard issues with bid close in 2019-2026
(`data/clean/ipo/ipos.parquet`). For 463 of them the cached NSE per-issue JSON has issue
information for this attempt; 22 have an empty JSON, another date format (UTI AMC) or the
other attempt's (Antony Waste). Tags as in `research/ipo_dataset.md`: PRIMARY = exchange,
UNVERIFIED = aggregator or news. Checked 2026-10-31 to 2026-11-01.

## 1. Short answer

- **NSE:** no historical day-wise subscription was found. Its per-issue JSON keeps one
  category-wise bid book, overwritten during bidding; for a past issue it is the last one,
  stamped on the close day (454 of 463), almost always at or after the 17:00 close.
- **BSE:** its per-issue "Cumulative Demand Schedule" page is category-wise but also
  overwritten in place: after the close it shows the final book. No day-wise history was
  seen there. BSE's site answered 403 to my fetch, so I could not look for other BSE pages
  directly (not retried; see the BSE note in `research/ipo_dataset.md` section 5).
- **Archived copies of the BSE page** (Internet Archive, a third party) hold some true
  intraday snapshots: an estimated ~30 of the 485 issues (upper bound 97), none from
  2019-2020, rarely more than one bid day per issue, and biased towards issues people
  were watching. Too sparse for a backtest input.

## 2. The cutoff itself (NSE JSON field "Cut-off time for UPI Mandate Confirmation", PRIMARY)

| Bid close | Stated cutoff | Issues |
|---|---|---|
| 31 Jan 2019 - 26 Aug 2022 | 12:00 PM on a day after the close (next weekday for 84; 2-4 weekdays later for 17, holidays not removed) | 101 |
| 7 Oct 2020 (Likhitha) | 12:00 PM, dated two days *before* the close (NSE text error) | 1 |
| 25 Jan 2019 (Xelpmoc) | field absent | 1 |
| 7 Sep 2022 - 23 Oct 2026 | 5:00 PM on the last bid day | 359 |
| 23 Oct 2026 (JPL) | 7:00 PM on the last bid day | 1 |

No issue after 26 Aug 2022 states 12:00 PM, and none before 7 Sep 2022 states 5:00 PM.
"IPO Market Timings" reads "10.00 a.m. to 5.00 p.m." for 450 of 463 (JPL: 9 am-7 pm).

So from Sep 2022 the bid close and the mandate cutoff coincide at 17:00 on the last day.
Before that, bids closed at 17:00 on the last day but mandates could be approved until
noon on a later day. Strictly, an applicant then could see the close-of-bidding book
before approving. The owner's rule says "on the last bid day", which matches only the
newer regime; see question 1.

## 3. NSE

**Per-issue JSON (`/api/ipo-detail`, cached in `data/raw/ipo/nse_ipo_detail/`).** Keys:
issue information, NSE-only and consolidated category-wise bid books (`bidDetails`,
`activeCat`), demand graphs at price points, metadata. Each holds **one** snapshot. Stamp
(`activeCat.updateTime`) for the 463:

| Stamp | Issues |
|---|---|
| Close day: mostly 17:00 through Aug 2022 and 19:00 from Sep 2022; others from 16:42 to 23:15 (6 between 16:42 and 16:55, minutes before the close) | 454 |
| "Updated as on null" (bid book empty; `retail_sub_exch` missing, e.g. MTAR, Kalyan Jewellers, Paras Defence) | 8 |
| Four days *before* the close: Adani Wilmar, 27 Jan 2022 12:27 | 1 |

**Defect found in the step-1 table:** Adani Wilmar's `retail_sub_exch` (0.53) is a day-1
intraday figure, not the close-of-bidding figure the column claims. Its `retail_sub` uses
the advert's 3.32, so that column is unaffected. Not fixed in this step; see question 3.

**Archives and pages.** Web searches (nseindia.com and general) found only the live issue
pages, the bid-verification page and the basis-of-allotment adverts, and SEBI's
market-data link page points to the same pages; no day-wise file or past-issue archive. No endpoint names were guessed. The Internet
Archive has 5 captures of NSE's `/api/ipo-detail` from 2019 to 2026 (CDX query), which is
negligible.

## 4. BSE

**What the page shows.** `bseindia.com/markets/publicIssues/CummDemandSchedule.aspx?ID=<n>`:
the company name, "Last updated on <date> | <time>", then category rows (QIB with
sub-rows, NII, RII with cut-off and price bids, employee and shareholder reservations,
total) with shares offered, shares bid and times subscribed. Read from archived copies
only, because BSE returned 403 to a direct fetch. A search snippet of the live page
(Bharat Coking Coal, Jan 2026) adds: demand includes UPI and non-UPI bids, and "the final
demand display of UPI bids shall be updated upto 7:00 PM on last day of IPO".

**It is the consolidated book.** In all 10 archived copies taken after the issue closed
where NSE has a close figure, the page's retail multiple equals NSE's consolidated
`retail_sub_exch` to 2 decimals (RateGain 8.08, Ruchi Soya 0.90, Kalpataru 1.29, Sula 1.65,
Prudent 1.29, Glenmark Life 14.63, Standard Glass 64.99, MapmyIndia 15.20, Aptus 1.35,
Ethos 0.84).

**The stamp cannot be used to time a snapshot.** Aptus, Glenmark Life and Ethos show
figures equal to NSE's close figure under an 11:00 AM stamp on the last bid day (Paras
Defence too, in a copy taken two months after its close; no NSE figure to compare). Only the
archive's capture time bounds what was visible.

## 5. Archived BSE pages: coverage (Internet Archive)

Method: CDX listing of every capture of the page, 2019-2026 (576 captures; 313 with HTTP
200; 143 distinct BSE issue IDs, of any issue type). First captures by year: 2021: 26 IDs,
2022: 21, 2023: 9, 2024: 39, 2025: 48. None with an ID in 2019 or 2020.

- **Upper bound:** 97 IDs have a capture whose time (IST) falls inside some mainboard bid
  window from the table, before 17:00 on that window's last day.
- **Sample:** 25 of the 97 at random (seed 20261101). 6 could not be fetched (the archive
  was intermittently offline) and 1 had no table, leaving 18. All 18 are mainboard issues
  in the table, but only **6 were captured during their own bid window** before the
  cutoff. The other 12 are copies of a finished issue's page that happened to be taken
  during another issue's window. Evidence: `research/ipo_wayback_bse_sample.csv`.

| Issue | Bid window | Captured (IST) | Page stamp | Retail x on page | Retail x at close (NSE) | Bid days covered |
|---|---|---|---|---|---|---|
| Easy Trip Planners | 8-10 Mar 2021 | 10 Mar 15:40 | 10 Mar 3:30 PM | 68.18 | 70.40 | 1 |
| Delhivery | 11-13 May 2022 | 13 May 13:13 | 13 May 1:12 PM | 0.47 | 0.57 | 1 |
| Western Carriers | 13-19 Sep 2024 | 17 Sep 17:49 | 17 Sep 5:00 PM | 13.27 | (none) | 2 |
| Enviro Infra | 22-26 Nov 2024 | 22 Nov 11:17 | 22 Nov 11:15 AM | 0.53 | 24.48 | 2 |
| Quality Power | 14-18 Feb 2025 | 17 Feb 10:05 | 17 Feb 10:03 AM | 0.65 | 1.83 | 1 |
| Patel Retail | 19-21 Aug 2025 | 21 Aug 09:57 | 20 Aug 5:00 PM | 16.58 | 42.49 | 1 |

LIC, looked up by hand and not part of the sample, is another example: captured
4 May 2022 18:23 IST, stamp 6:21 PM on day 1, retail 0.58x against 1.99x at the close.

**Estimate:** 6 of 18 scaled to the 97 candidates gives about 30 issues (very rough; the
sample is small) out of 485, and almost never every bid day. Popular issues are archived
more often, so this subset is not random.

**Retail portion size is fixed during bidding**, at least in these cases: the retail
"shares offered/reserved" on all 7 intraday pages (the 6 above plus LIC) equals the
figure in NSE's close snapshot.

## 6. Sources outside NSE and BSE (not checked for coverage)

- News wires print end-of-day figures with a time, e.g. Business Standard's Capital Market
  items: "according to stock exchange data at 17:30 IST" (NSE's own IPO, Sep 2026).
  UNVERIFIED; how far back and how complete was not checked.
- Aggregators publish day-wise tables: Chittorgarh (not used: robots file), InvestorGain
  (declares ai-input=yes; not checked), broker blogs. UNVERIFIED. The cached Tapetide pages
  have no day-wise figures.

## 7. Fields already held that are known before bidding closes

| Field | In the clean table? | Source (tag) | Coverage, 485 listed 2019+ | Note |
|---|---|---|---|---|
| Bid open and close dates | yes: `issue_open`, `issue_close` | NSE past-issue list (PRIMARY) | 485 | |
| Price band | yes: `price_band_low/high` | NSE list (PRIMARY) | 485 | the list holds the final band; a band revised during bidding would not show |
| Lot size | yes: `lot_size` | NSE JSON "Bid Lot", else the advert's 1-lot category (PRIMARY) | 481 | the advert is published after allotment, but the lot it states was fixed before bidding |
| One lot's cost at the cap | yes: `lot_value_at_cap` | lot x upper band | 481 | |
| Registrar | yes: `registrar` | NSE JSON (PRIMARY) | 466 | |
| Retail discount | yes: `retail_discount` | advert (PRIMARY) | 5 | announced before bidding, but recorded only where an advert states it |
| Retail portion size (shares) | **no**: parsed as `retail_shares_offered_exch` in `nsealgo.data.ipo` but dropped from `CLEAN_COLS` | NSE JSON close snapshot, RII "shares offered/reserved" (PRIMARY) | 455 | equal to the intraday figure in 7 of 7 archived pages (section 5) |
| Issue size | **no** | NSE JSON "Issue Size" (PRIMARY): free text (fresh issue and OFS, in Rs million or shares) | 463 have the text; not parsed | |
| Anchor investment | **no** | NSE JSON links `ANCHOR_<SYMBOL>.zip` ("Anchor Allocation Report") and post-anchor parameters (PRIMARY) | 441 have the anchor link, 395 the post-anchor link; nothing downloaded | anchors are allotted before bidding opens (rule as recalled, not read in the ICDR text) |
| UPI cutoff, bid timings, categories, lead managers | **no** | NSE JSON text fields (PRIMARY) | 462 have a cutoff | section 2 |

**Not known before the cutoff, so not usable by the selection rule:** `retail_sub_exch` and
`total_sub_exch` (the close snapshot: mostly 17:00 through Aug 2022 and 19:00 from Sep 2022,
after the 17:00 cutoff), `retail_sub_boa` and `retail_sub`, every basis-of-allotment field,
`allotment_date`, listing-day fields and returns, and `status`.

## 8. Questions for the owner

1. **Cutoff for 2019 to Aug 2022.** Apply 17:00 on the last bid day to every issue, which
   is today's rule (my recommendation, since the paper and live tracks run under it). Or
   use each issue's own cutoff, noon on a later day, which would let 102 issues use NSE's
   17:00 close snapshot.
2. **Subscription as a selection input.** With no exchange day-wise history, the choices
   are: (a) use only the pre-bid fields in section 7 (my recommended default for a first
   test); (b) build an end-of-day snapshot table from news items, after a separate coverage
   check (UNVERIFIED source); (c) leave subscription out of the backtest and record NSE's
   snapshot at the end of each bid day in the paper track from 1 Nov 2026 (PRIMARY, but
   only from now on). (c) can be combined with (a).
3. **Adani Wilmar's `retail_sub_exch`.** Fix it in the build: drop the exchange figure when
   the JSON stamp is dated before the close, and flag the row. It is 1 issue; the fix needs
   a test and a rebuild. Or leave it as is and note it.

Status: data check only. No strategy, backtest or trial was run.
