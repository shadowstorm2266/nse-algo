# Phase 2 literature: small-capital candidates in Indian markets

Research phase 2 starts here. **This is a literature and data-source report only. No backtest
was run and no trial was logged.** `research/trials.jsonl` was not touched. The DSR trial count
continues from 21 (7 ORB, 6 swing, 4 pullback, 4 sector_rotation); the next logged run would be
trial 22. Numbers only. The owner decides.

- **Compiled:** 2026-10-31, from seven research-note files, committed under
  `research/phase2_notes/` (parsed allotment tables and per-event arithmetic kept). Every source
  below is the original URL, not a notes file.
- **Question:** which edges in Indian markets can a resident individual with Rs 20,000 capture
  after all costs and taxes, specifically where being small helps?
- **Tags.** PRIMARY: SEBI, NSE, BSE, RBI, AMFI, niftyindices.com, statute or gazette text,
  offer documents (letters of offer, post-offer announcements, basis-of-allotment adverts),
  peer-reviewed papers, SSRN/IIM/ISB/NSE working papers. UNVERIFIED: everything else (brokers,
  aggregators, news, law-firm notes, blogs). A figure is UNVERIFIED unless its own source is
  PRIMARY.
- **Arithmetic.** Every computed figure shows its formula and inputs, or points to where they
  are. Arithmetic is on published figures only; no price series was processed.
- **Tax assumption behind every "after tax" figure:** adult resident individual, new regime,
  tax year 2026-27, other slab-rate income of Rs 3 lakh or less. Under those conditions tax on
  every candidate here is nil at Rs 20,000 of capital (section 7). If the account holder is a
  minor or has more other income, section 7 gives the rates.
- **Holdout.** `config/research.yaml` sets holdout_start 2025-04-08. Several published figures
  below cover dates on or after it (2025-2026 IPO listings, factor-fund NAVs to 30 Oct 2026,
  the 2025-2026 index reviews). No backtest touched those dates, but the owner has now seen
  them; a rule designed after reading them is not blind to the holdout period.
- **Holdout for the IPO track (owner's decision, 2026-10-31).** Published IPO figures dated after
  2025-04-08 have now been seen, so the holdout is contaminated for IPOs. For the IPO track, the
  true out-of-sample test is paper-tracking every new mainboard IPO from 1 Nov 2026 onward.
- **Scope (owner's decision, 2026-10-31).** The trading bot stays NSE equity cash only. IPO
  applications are manual (UPI) and will never be automated; researching and simulating them in
  this repo is allowed (hard rule 1 in `CLAUDE.md`).

## 0. What the four failed strategies say about where to look

All four phase-1 strategies ran on dev 2016-01-01 .. 2023-12-31 with Rs 20,000. Validation and
holdout were never touched. Sources: `research/track_comparison.md`, `orb_v1_result.md`,
`swing_v1_result.md`, `strategy3_result.md`, `strategy4_result.md`.

| Strategy | Trials | Base net bps/trade | Reference tier (no brokerage, 0 bps) | vs buy-and-hold, base | Failure as recorded |
|---|---|---|---|---|---|
| ORB v1, MIS, 5m | 1-7 | -12.7 (trial 7) | +0.1 (trial 2) | not long-only | fails Gate A: gross 3.6 bps/trade vs 16.3 bps costs |
| Swing momentum v2, CNC | 12-13 | +327.7 (trial 12) | +373.8 (v1, trial 9) | +87.8% vs +345.6% (EW 40); ahead 1 of 8 years | loses to buy-and-hold |
| Pullback v1, CNC | 14-17 | -51.7 (trial 15) | -7.6 (trial 14) | -71.5% vs +345.6%; ahead 0 of 8 | fails Gate A; reference tier already negative |
| Sector rotation v1, CNC on ETF proxies | 18-21 | +500.8 (trial 19) | +540.8 (trial 18) | +118.0% vs +222.6% (EW 11) and +201.2% (PX_NIFTY50); ahead 2 of 8 | fails first-pass checks 2 and 3 |

What phase 2 looks for, given those failures:

- **Two strategies died on costs.** ORB's gross edge was 3.6 bps against 16.3 bps of costs.
  Pullback's was 22.2 bps against 73.9, and its fixed DP charge (Rs 10.62 per sale) rose from
  24 to 85 bps of the median notional as the account shrank (`strategy3_result.md` section 3).
  Phase 2 looks for payoffs of several percent per event with a few transactions a year, where
  the round trip on Rs 20,000 (about 27.5 bps statutory plus DP, 33.5 bps with 3 bps slippage
  each side; "Arithmetic conventions" below the ranked table) is a small share of the payoff.
- **Two strategies died against buy-and-hold.** Swing and sector rotation had positive net
  expectancy, but their returns were market exposure with timing that lost to holding the same
  universe. Phase 2 looks for payoffs set by a rule or contract (an allotment lottery, a
  reserved acceptance ratio, a fixed offer price, forced index-fund flows) rather than by market
  direction. For factor funds, the comparison is made directly against a Nifty 50 index fund.
- **Survivorship.** The 40-symbol universe was today's large caps. Event candidates are defined
  by dated public documents (offer documents, allotment adverts, press releases), which are
  point-in-time by construction. Aggregator samples can still drop delisted names (section 1).
- **Size.** Rs 20,000 hurt in phase 1: the fixed DP charge, whole-share rounding, and 30%
  position-cap skips (MARUTI, ULTRACEMCO). Phase 2 asks where size is neutral or helps:
  per-PAN lotteries, reservations keyed to holdings of Rs 2 lakh or less, and tax thresholds.
- **Scope.** IPO bids go through the exchange bidding platform with a UPI mandate, and tenders
  through the exchange acquisition window. Neither is a CNC or MIS order in the current engine,
  and broker-API support for either was not researched. Whether they fit hard rule 1 is the
  owner's call. (IPOs decided 2026-10-31: manual applications only; see the header.)

## Read this first

- **Rules that favour small holders exist in three places:** the mainboard IPO retail lottery
  (one ticket per PAN; a one-lot bid of about Rs 13,500-15,000 has the same allotment chance as
  a Rs 2 lakh bid), the buyback small-shareholder reservation (holding worth Rs 2 lakh or less on
  the record date), and the tax shortfall rule (unused basic exemption absorbs STCG). **SME IPOs
  exclude Rs 20,000** (minimum application above Rs 2 lakh). Open offers, delisting offers,
  index changes and factor funds have no size-based rule.
- **Mainboard IPO lottery:** Rs 94-371 per application after costs at nil tax, Rs 1,880-18,550
  a year at 20-50 applications (section 1; an independence upper bound of Rs 1,648 per
  application is shown there and not used). Inputs are in-sample (listing returns 2018-2026,
  subscription buckets Apr 2021-Dec 2023) and the allotment chance per bucket is partly assumed.
  2025 and 2026 listing medians are below 2021-2024.
- **Factor funds vs a Nifty 50 index fund:** median +0.9 pp a year (range -0.3 to +7.0) for the
  12 funds with at least 4 years of NAV, about Rs 185 a year on Rs 20,000 (-Rs 58 to +Rs 1,406).
  10 of those 12 windows start in 2021-2022 (section 6).
- **Sign not established from published data:** buybacks (no primary post-offer price data;
  per event -5.2% to +6.6% at assumed post-offer moves), delisting offers (-9.7% to +7.6% per
  event; 37.5-56% success in law-firm samples), index inclusion (+2.3% to +3.3% net per review
  in 2010-2018, N=27; -5.2% in 2020-2024, N=13).
- **Tax:** the new-regime rebate (s.156, up to Rs 60,000) does not reduce tax on STCG (s.196)
  or equity LTCG (s.198) in tax year 2026-27, but the basic-exemption shortfall does: with no
  other income, STCG up to Rs 4 lakh and equity LTCG up to Rs 5.25 lakh pay nil.

## Corrections to the brief and to common beliefs

| # | Brief or common belief | What the sources say | Tag and source |
|---|---|---|---|
| 1 | FY 2026-27 under the 1961 Act; "section 111A" | The Income-tax Act, 2025 is in force from 1 Apr 2026 (s.1(3)). The year is "tax year 2026-27" (s.3). 111A is now **s.196**, 112A **s.198**, 112 **s.197**, 87A **s.156**, 115BAC **s.202**, 2(22)(f) **s.2(40)(f)**, 46A **s.69**. The old-to-new mapping is inferred from matching wording; the content is primary. | PRIMARY: [Income-tax Act 2025, e-Gazette, 21 Aug 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf) |
| 2 | Buybacks are taxed as deemed dividends (rule from 1 Oct 2024) | **Reversed from 1 Apr 2026.** Finance Act 2026 (No. 4 of 2026, assent 30 Mar 2026) s.35 omits s.2(40)(f); s.69(1) taxes consideration less cost as capital gains. A new s.69(2)-(3) adds tax for **promoters only**: 2% (STCG) / 9.5% (LTCG) for domestic-company promoters, 10% / 17.5% for others. The deemed-dividend regime ran 1 Oct 2024 to 31 Mar 2026. | PRIMARY: [Finance Act 2026, e-Gazette No. 9](https://egazette.gov.in/WriteReadData/2026/271439.pdf); [Memorandum, 1 Feb 2026](https://www.indiabudget.gov.in/doc/memo.pdf); [Wipro letter of offer, Jun 2026](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf) for the 1 Oct 2024 start |
| 3 | NSE SME listing-day cap from March 2024 | The +90% pre-open cap over issue price started **4 Jul 2024** (NSE/SME/62757). A -20% floor followed from **4 Aug 2025**. The BSE date was not found. | PRIMARY: recital in [NSE/CMTR/69388, 30 Jul 2025](https://nsearchives.nseindia.com/content/circulars/CMTR69388.pdf) |
| 4 | SME minimum application "around Rs 2 lakh since about March 2025" | ICDR Reg 267(2): **two lots, and above Rs 2 lakh**, in force **8 Mar 2025** (GN/2025/233; notified 3-4 Mar 2025; Board 18 Dec 2024). The word "retail" was deleted from the SME chapter. A pending SEBI paper (14 Oct 2026, comments by 4 Nov 2026) would cut it to Rs 1 lakh (4 lots x Rs 25,000) and the trading lot to one share. | PRIMARY: [consolidated ICDR, amended to 21 Mar 2026, pp.198-199](https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1774592300989.pdf); [SEBI consultation, 14 Oct 2026](https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791972839578.pdf) |
| 5 | The Rs 60,000 rebate (old 87A) covers STCG for a low-income investor | **Not in tax year 2026-27.** s.156(3) caps the new-regime rebate at slab-rate tax; s.198(7) bars it against LTCG. Taxpayer ITAT wins for AY 2024-25 and AY 2025-26 rested on the absence of an express bar, so they do not carry over. The **unused basic exemption does** reduce STCG (s.196(2)) and LTCG (s.198(3)) for residents. | PRIMARY: [Income-tax Act 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf); [ITAT Agra order, 3 Sep 2025](https://itat.gov.in/public/files/upload/1756901560-YJpjWc-1-TO.pdf) |
| 6 | Mainboard retail quota to be cut from 35% to 25% for IPOs above Rs 5,000 crore | Proposed 31 Jul 2025, then **dropped**: the Sept 2025 board memo says it is "no longer required to be pursued". A 5paisa article updated 14 Jan 2026 still calls it live (UNVERIFIED, contradicted). | PRIMARY: [SEBI board memo, Sept 2025, paras 2.5-2.6](https://www.sebi.gov.in/sebi_data/meetingfiles/sep-2025/1758535137982_1.pdf); UNVERIFIED: [5paisa](https://www.5paisa.com/news/sebi-proposes-cutting-retail-quota-in-large-ipos-seven-upcoming-offers-face-the-change) |
| 7 | Open-market buybacks were abolished in 2025 | Phased out by 1 Apr 2025 under the 2023 amendment, then **reinstated from 1 Aug 2026** (notified 1 Jul 2026; reported as GN/2026/306). That route has **no small-shareholder reservation**. | UNVERIFIED: [AZB, 27 Oct 2026](https://www.azbpartners.com/bank/sebi-notifies-amendments-to-buyback-of-securities-regulations-2018/), [Cyril Amarchand, Jun 2026](https://corporate.cyrilamarchandblogs.com/2026/06/reintroduction-of-open-market-buyback-through-the-stock-exchange-and-other-changes-to-buyback-regime/) |
| 8 | Finance Act 2026 raised STT | **F&O only.** Cash equity is unchanged: delivery 0.1% on buy and on sell, intraday sell 0.025%, ETF (equity-oriented fund unit) delivery sale 0.001%. | PRIMARY: [NSE/FATAX/73524, 31 Mar 2026](https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf) |
| 9 | Index-fund rebalance trades hit the continuous-market close | F&O stocks now close through a **closing auction session** (SEBI circular of 16 Jan 2026; NSE SOP of 18 Mar 2026), with a reference price set by the 15:00-15:15 VWAP and a ±3% band. Go-live is reported as 3 Aug 2026 (UNVERIFIED). | PRIMARY: [NSE/CMTR/73362](https://nsearchives.nseindia.com/content/circulars/CMTR73362.pdf); UNVERIFIED: [Angel One](https://www.angelone.in/news/market-updates/sebi-closing-auction-session-from-august-3-2026-new-timings-and-rules-for-f-o-stocks) |
| 10 | Factor-index factsheet returns show how the factor did | Factsheet "since inception" figures start at the **base date**, so they contain 3.5-20 years of back-calculated history. Live results start at the launch date (section 6). | PRIMARY: e.g. [Nifty200 Momentum 30 factsheet, 30 Sep 2026](https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf) |
| 11 | The Sensex is run by Asia Index (S&P DJI joint venture) | Methodology documents are now issued by **BSE Index Services Pvt Ltd**. BSE reportedly completed the purchase of S&P DJI's stake around 31 May 2024 (UNVERIFIED). | PRIMARY: [BSE Indices methodology, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf) |

## Ranked table of candidates

**Ranking rule (mechanical, not a recommendation):** rows are ordered by the lower end of the
stated annual range on Rs 20,000. Rows with no estimable range come last. The ranges come from
different methods with different confidence, so the order changes if the assumptions change.
Every figure is after statutory charges, DP charge and slippage, at **nil tax** (the tax
assumption in the header; section 7).

| Rank | Candidate | Small an advantage? | Evidence quality | Net expected annual return on Rs 20,000, after costs and tax (assumptions) | Data available to backtest | Biggest risk |
|---|---|---|---|---|---|---|
| 1 | Mainboard IPO, retail category, one lot, sold at the listing open | **Yes.** One lottery ticket per PAN; a 1-lot bid and a Rs 2 lakh bid have the same chance. The rupee EV does not grow with capital. | Medium. PRIMARY allotment adverts (n=29, biased to large issues) and SEBI aggregates (144 IPOs, Apr 2021-Dec 2023). Yearly listing returns UNVERIFIED. All in-sample and gross. | **Rs 1,880 to Rs 18,550 (9% to 93%).** N = 20-50 applications a year (not counted; one live bid at a time), lot Rs 14,800, 10 bps slippage, about Rs 27 of charges per allotment. Low end: 2018-20 medians at median P (Rs 94 per application). High end: SEBI subscription buckets with allotment-advert P (Rs 371). Section 1.4. | Allotment adverts 2019 onward (free PDF, no index); bhavcopy (free). Nothing found before 2019. | Allotment chance is lowest where listing gains are highest. 2025 and 2026 medians are 4.2% and 6.7%. N is capped by overlapping bid windows. |
| 2 | Factor ETF or index fund instead of a Nifty 50 index fund (excess only) | **Neutral.** No size rule; the same TER at any size. | Data: PRIMARY (official TRI, AMFI NAV and TER), live, after fund costs. Inference: weak (12 fund windows, 10 starting 2021-22; overlapping holdings). | **Median +Rs 185 a year (-Rs 58 to +Rs 1,406)**, i.e. +0.9 pp (-0.3 to +7.0) of excess over the UTI Nifty 50 index fund (direct), on NAV. ETF premium to NAV and the Rs 10.62 DP charge per sale are not included. Section 6.3. | niftyindices TRI (free; undocumented POST, 1 year per request); AMFI NAV and TER (free). | Tracking error against Nifty 50 (about 5-10% a year, inferred) swamps a 1 pp premium. Results depend on the regime and the end date. |
| 3 | Nifty 50 additions, long only, from the AD+1 close to the effective-date close | **Neutral.** | Low. Two small in-sample event studies with opposite signs, gross of costs. | **-Rs 2,120 to +Rs 1,330.** 2 reviews a year with all Rs 20,000 in each review's additions; round trip 33.5-47.5 bps. High end: 2010-18 means (N=27). Low end: 2020-24 (N=13). One-sigma market move per review is ±Rs 780-1,040. Section 5.4. | NSE press releases (free PDF, URL pattern); bhavcopy (free). Sensex notices not located. | Unhedged raw return is dominated by the market. The effect has decayed and may be negative after 2020. The closing auction applies from Aug 2026. |
| 4 | Voluntary delisting (reverse book building), buy after announcement and tender | **Neutral.** No proration on success, for any holder. | Low. SEBI 2018 lists 15 successes only. Law-firm samples UNVERIFIED. Post-failure drops from news. | **-Rs 4,800 to +Rs 3,800.** 2.5 sequential events a year (145-day average lock), each -9.7% to +7.6%: success 37.5-56%, premium 0-35.9% over the floor, failure move 0 to -20%, entry at the floor (optimistic). Section 4.4. | SEBI, BSE and NSE PDFs (free, scattered); no consolidated event table. | Failure (44-63% of attempts) with 10-24% one-day drops. An entrant near the indicative price earns about 0% on success. |
| 5 | Buyback tender offer, small-shareholder category | **Yes for holdings up to Rs 2 lakh.** At Rs 20,000, rounding gives zero proportional entitlement in stocks above about Rs 3,000-5,000. | Medium-low. 3 PRIMARY acceptance ratios; broker tables (53 offers) UNVERIFIED; no post-offer prices. | **Not estimable.** Per event -Rs 1,044 to +Rs 1,318 (-5.2% to +6.6%) at assumed post-settlement moves of 0, -5% and -10%. At 10 events a year: -Rs 10,440 to +Rs 13,180. Broker period medians: -6.35% and +19.1% annualised (pre-cost, pre-tax, different entry). Section 3.4. | SEBI filings (1,403 records, free, pagination blocked to scripts); post-buyback adverts scattered; bhavcopy. | Price of the 45-80% of shares not accepted. Crowding in publicised offers. The open-market route (no reservation) is back. |
| 6 | Open offer (SAST), buy and tender | **Neutral.** Proportionate acceptance, 1-share marketable lot, no reservation. | Very low. Anecdotes; base rate "under 5% fully subscribed" UNVERIFIED. | **Not estimable** (no published spreads). Illustration only: +1.5% to +8.2% gross per event at assumed 5-10% spreads and 86-91% acceptance, less 0.31-0.78% costs. Section 4.4. | SEBI monthly offer tables (no acceptances); post-offer reports (PDF). | Offer price below market at tendering. 3.5-6 months of lock. Micro-cap illiquidity. |
| 7 | SME IPO | **No: excluded.** Minimum application above Rs 2 lakh; trading lots Rs 1.0-1.6 lakh at issue price. | Refereed studies (2012-2018, gross, issue level); 2024-2026 UNVERIFIED. | **Not accessible at Rs 20,000.** Even the pending Rs 1 lakh minimum is 5x the capital. Section 2. | No free machine-readable dataset found. | Rules are in flux (Oct 2026 consultation). |

Cross-cutting item 7, tax: nil drag at this size under the header assumption, whether gains are
realised monthly or held. Not a candidate on its own; section 7.

Arithmetic conventions used in all sections:

- **Delivery round trip on Rs 20,000** (rates from `config/costs.yaml`, STT re-verified against
  [NSE/FATAX/73524](https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf)): buy
  Rs 23.72 (STT 0.1%, stamp 0.015%, NSE 0.00297%, SEBI Rs 10 per crore, GST 18% on the last
  two); sell Rs 31.34 (STT 0.1%, NSE, SEBI, GST, DP Rs 9 + 18% GST = Rs 10.62). Total Rs 55.07
  (27.53 bps); with 3 bps per side Rs 67.07 (33.53 bps); with 10 bps Rs 95.07 (47.53 bps). At
  Rs 10,000 the statutory part is 32.84 bps, because the DP charge is fixed per scrip.
- Stamp duty, the NSE transaction charge, the SEBI fee and the DP charge were not re-verified
  against primary sources (the NSE 0.00297% rate from 1 Oct 2024 is confirmed only by a
  [Zerodha bulletin, 28 Sep 2024](https://zerodha.com/marketintel/bulletin/391488/revision-in-transactions-charges-from-1st-october-2024),
  UNVERIFIED). Whether the transaction charge and DP charge apply to tender-window sales was not
  verified; they are assumed to apply.
- "%" of Rs 20,000 is simple, not compounded. Per-event figures are not annualised unless stated.

## 1. Mainboard IPO retail quota, 2016-2026

**Is small an advantage? Yes, structurally.** When the retail book is oversubscribed, each valid
retail application gets one minimum lot by draw, whatever its size. In Bajaj Housing Finance
(Sep 2024) the 1-lot bucket was allotted 496:2125 and every bucket from 2 to 13 lots 197:844,
both 23.34% ([allotment advert](https://nsearchives.nseindia.com/corporate/ADV_INE377Y01014_13SEP2024.pdf),
PRIMARY). The rupee EV is per PAN, so as a share of capital it is largest for the smallest account
that can fund one lot. Limits: Rs 20,000 funds one live bid at a time (lots in the sample were
Rs 13,527-14,980), and duplicate applications under one PAN are rejected.

### 1.1 Rules and dated changes

| Item | Value | Tag and source |
|---|---|---|
| Minimum application value | Rs 10,000-15,000, set by the issuer | UNVERIFIED reproduction of ICDR: [TaxTMI](https://www.taxtmi.com/tmi_blog_details?id=548568) |
| Retail individual investor (RII) | bids of not more than Rs 2 lakh | PRIMARY: [SEBI IPO study, 2 Sep 2024, p.2](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1725270963087.pdf) |
| Retail quota | at least 35% for Reg 6(1) issues; at most 10% for Reg 6(2) (non-profitability route); 101 and 43 of 144 IPOs in Apr 2021-Dec 2023 | PRIMARY: same study, p.11 |
| Allotment | at least one minimum lot per RII subject to availability, rest proportionate; lottery in practice | PRIMARY: allotment adverts ([Bajaj HFL](https://nsearchives.nseindia.com/corporate/ADV_INE377Y01014_13SEP2024.pdf), [Hyundai](https://nsearchives.nseindia.com/corporate/ADV_INE0V6F01027_21OCT2024.pdf)) |
| One application per PAN (mainboard) | duplicates "will not be considered for allotment" | UNVERIFIED: broker pages ([Groww](https://groww.in/help/stocks/sx-ipo/can-i-apply-for-an-ipo-on-multiple-platforms)); primary circular not found |
| ASBA mandatory | issues opening from 1 Jan 2016 | PRIMARY: [NSE ASBA page](https://www.nseindia.com/static/products-services/initial-public-offerings-asba-procedures) |
| UPI the only retail route through intermediaries | Phase II from 1 Jul 2019 | PRIMARY: [SEBI circular, 28 Jun 2019](https://www.sebi.gov.in/sebi_data/attachdocs/jun-2019/1561723926195.pdf) |
| UPI limit Rs 5 lakh | issues opening from 1 May 2022 (circular of 5 Apr 2022) | UNVERIFIED reproduction: [TaxGuru](https://taxguru.in/sebi/revision-upi-limits-public-issue-equity-shares-convertibles.html) |
| NII lottery and split; anchor lock-in 50% at 30 days, 50% at 90 days; RBI cap of Rs 1 crore on NBFC IPO loans | from 1 Apr 2022. NII oversubscription fell from 37.5x to 17.2x; retail lottery unchanged | PRIMARY: [SEBI IPO study, pp.2-3, 20-23](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1725270963087.pdf) |
| T+3 listing | voluntary for issues opening from 1 Sep 2023, mandatory from 1 Dec 2023; unblocking completed by 4 pm on T+2; trading on T+3 | PRIMARY: [SEBI circular, 9 Aug 2023](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2023/1691580430610.pdf) |
| Anchor book 33% to 40% (MFs one third, 7% insurers and pension funds) | Sept 2025 board memo; retail 35%/10% unchanged | PRIMARY: [board memo](https://www.sebi.gov.in/sebi_data/meetingfiles/sep-2025/1758535137982_1.pdf); approval on 12 Sep 2025 UNVERIFIED |
| Listing-day price discovery | 1-hour call auction; then a 5% band for issues up to Rs 250 crore, 20% above | UNVERIFIED reproduction of the 2012 circular: [TaxGuru](https://taxguru.in/sebi/formulation-price-bands-day-trading-pursuant-ipo-re-listing.html) |

Capital lock per application since Dec 2023: bid on closing day T, unblocked by 4 pm on T+2 if
not allotted; if allotted, sold on T+3 with proceeds around T+4 (inference from the T+3
timetable and T+1 settlement). Bank ASBA pages say blocked money keeps earning savings interest
(UNVERIFIED: [SBI ASBA](https://sbi.co.in/portal/web/personal-banking/asba)). No 2026 change to
the mainboard retail quota or minimum was found.

### 1.2 Listing-day returns

**PRIMARY (SEBI study, published 2 Sep 2024; 144 mainboard IPOs listed Apr 2021-Dec 2023;
in-sample; no costs or taxes; return to open or close not stated):** 75% (108) delivered positive
returns and 26 listed more than 50% up. Median listing-day return by overall subscription:
above 100x (17 IPOs) **82%**; 10-100x (75) **22%**; 5-10x (10) **10%**; 1-5x (40) **-2%**;
undersubscribed (2) **2%** ([study, pp.5, 18](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1725270963087.pdf)).

**Yearly series, UNVERIFIED** (aggregators; in-sample; gross; pages read 2026-10-31). No primary
yearly series was found; 2016 and 2017 are missing everywhere.

| Year | Tapetide: n, mean, median, % opened below issue | Trendlyne: mean to close, % closed in loss | Prime Database mean to close (via news) |
|---|---|---|---|
| 2018 | 24, +5.26%, +1.35%, 45.8% | 7.94%, 43.8% (n=16) | not found |
| 2019 | 17, +14.58%, +3.93%, 29.4% | 19.20%, 31.3% (n=16) | 19% |
| 2020 | 16, +38.72%, +18.41%, 25.0% | 47.24%, 30.8% (n=13) | 44% |
| 2021 | 66, +30.28%, +11.19%, 28.8% | 31.26%, 29.2% | 32% (63 IPOs) |
| 2022 | 39, +10.25%, +3.75%, 25.6% | 10.51%, 34.9% | 11% (40 IPOs) |
| 2023 | 61, +26.56%, +16.43%, 13.1% | 28.02%, 13.3% | 29% (57 IPOs) |
| 2024 | 93, +28.17%, +15.94%, 19.4% | 29.76%, 20.7% | 30% (91 IPOs) |
| 2025 | 108, +9.08%, +4.22%, 22.2% | 9.45%, 32.7% | 10% (103 IPOs) |
| 2026 to date | 111, +13.68%, +6.67%, 20.9% | 14.02%, 29.6% | n/a |

Sources: [Tapetide](https://tapetide.com/insight/reports/ipo-listing-gains/2024) (one page per
year, open vs issue price; % below computed from its counts),
[Trendlyne](https://trendlyne.com/ipo/screener/year-2024/mainline/) (same URL pattern per year),
Prime via [Industrial Economist, 30 Dec 2025](https://industrialeconomist.com/?p=18170) and
[Business Standard, 3 Jan 2024](https://www.business-standard.com/finance/personal-finance/ipo-fundraising-drops-17-in-2023-40-gave-a-return-of-over-10-on-listing-124010300366_1.html).
Period summaries (Tapetide, open): count-weighted mean 17.4% for 2018-20 and 19.1% for 2021-26;
average of yearly medians 7.9% and 9.7% (an average of medians is not a pooled median).
Could be overstated: means are set by a few hot issues; Trendlyne's lower 2018-2020 counts fit a
survivorship filter; counts differ by source (2024: NSE 90, Prime 91, Trendlyne 92, Tapetide 93).

### 1.3 Retail subscription and allotment probability

P(allot) = successful retail allottees / valid retail applications, read from NSE allotment
adverts (PRIMARY; URL pattern `nsearchives.nseindia.com/corporate/ADV_<ISIN>_<DDMONYYYY>.pdf`;
29 issues 2019-2025 with P computable). Range **2.5%** (Happiest Minds 2020: 46,988 of 1,862,370;
[advert](https://nsearchives.nseindia.com/corporate/ADV_INE419U01012_16SEP2020.pdf)) to **100%**
where the retail book was undersubscribed or small enough for every applicant to get one lot
(Hyundai 0.44x, Hexaware 0.10x, LIC 1.61x, Tata Capital 1.06x). Sample medians: 8.4% (2019-20,
n=6) and 50.4% (2021-25, n=23).

- **The sample is biased upward:** issues were chosen by known ISIN, mostly very large, and
  several had undersubscribed retail books. Small and mid issues above 100x subscribed show
  2.5-3.8% (Happiest Minds, [Burger King](https://nsearchives.nseindia.com/corporate/ADV_INE07T201019_11DEC2020.pdf),
  Ujjivan SFB, Devyani).
- **Identity:** P ≈ L̄ / x_RII, with L̄ the average lots per retail application (measured
  1.57-2.27) and x_RII the retail multiple. Bajaj HFL: 1.76 / 7.537 = 0.233, matching its
  measured P.
- **Retail multiples:** SEBI amount-weighted retail oversubscription 8.9x (FY22) and 7.9x (Apr
  2022-Dec 2023) (PRIMARY, study Chart 17). Prime average retail subscription 33.71x in 2024
  and 26.99x for the first 75 IPOs of 2025 (UNVERIFIED,
  [Financial Express via Magzter](https://www.magzter.com/en/stories/newspaper/Financial-Express-Ahmedabad/RETAIL-PARTICIPATION-IN-IPOS-SEES-SHARP-DIP)).
  At 33.7x and L̄ = 1.7, P ≈ 5%.
- **Aggregate P implied by Prime averages** (rough, ratio of averages): 19.3% (2021), 38.8%
  (2022, LIC-inflated), 9.7% (2023), 13.8% (2024), 16.9% (2025).
- **Rejections:** Paytm had 1,062,314 retail applications before technical rejection and 993,792
  after, -6.5% ([advert](https://nsearchives.nseindia.com/corporate/ADV_INE982J01020_17NOV2021.pdf)).
- No allotment adverts were found on NSE for 2016-2018 (0 of 10 probed).

### 1.4 Expected value per minimum application and per year

Formula: EV = P x [(V - L) - (STT + NSE + SEBI + GST + DP)], V = L x (1 + r) x (1 - s).
L = Rs 14,800, s = 10 bps, sale at the listing open. Check at r = 10%: V = 16,263.7; charges
Rs 27.47 plus Rs 16.28 slippage. Tax nil (header assumption); the 20% column applies only above
the shortfall (section 7).

| Case (P and r treated as independent unless stated) | r | P | EV per application, tax nil / 20% |
|---|---|---|---|
| 2018-20 medians | 7.90% | 8.35% | Rs 94 / 75 |
| 2021-26 medians, Prime-implied P | 9.70% | 15% | Rs 209 / 167 |
| 2025 median, Prime-implied 2025 P (this report's arithmetic, same formula) | 4.22% | 16.9% | Rs 98 / 78 |
| SEBI buckets, P link kept, low P (2%, 8%, 25%, 60%, 100%) | bucket medians | by bucket | Rs 135 / 96 |
| SEBI buckets, high P (4%, 15%, 35%, 70%, 100%) | bucket medians | by bucket | Rs 281 / 211 |
| SEBI buckets, allotment-advert P (3.2%, 21.9%, 35%*, 85%*, 100%) | bucket medians | by bucket | Rs 371 / 280 |
| Upper bound: 2021-26 means x sample-mean P (independence) | 19.12% | 59.2% | Rs 1,648 / 1,316 |

\* assumed; no allotment-advert data in those buckets. In the advert-P bucket model, the 1-5x
bucket contributes **-Rs 79** at 20% tax: the issues most likely to be allotted had a -2%
median. Keeping the P-return link cuts the EV by 50-85% against independence.

Per year at nil tax (N = applications; % of Rs 20,000):

| Case | N = 20 | N = 50 |
|---|---|---|
| 2018-20 medians | Rs 1,880 (9.4%) | Rs 4,700 (23.5%) |
| 2025 median, Prime P | Rs 1,969 (9.8%) | Rs 4,923 (24.6%) |
| SEBI buckets, low P | Rs 2,700 (13.5%) | Rs 6,750 (33.8%) |
| 2021-26 medians, Prime P | Rs 4,180 (20.9%) | Rs 10,450 (52.3%) |
| SEBI buckets, high P | Rs 5,620 (28.1%) | Rs 14,050 (70.3%) |
| SEBI buckets, advert P | Rs 7,420 (37.1%) | Rs 18,550 (92.8%) |

N was not counted. 2018-2020 had 16-24 mainboard IPOs a year; 2021-2026 had 39-111, many closing
in the same week, and one lot cannot be blocked twice. Counting distinct non-overlapping bid
windows needs the IPO calendar (section 8). Idle cash between bids is not counted.

### 1.5 Why these figures could be overstated or decayed

- Medians times medians is not an expected value; no per-IPO joint (P, r) data exist here, so
  E[P x r] was not computed. The bucket model rests on Apr 2021-Dec 2023, a strong regime.
- 2025 and 2026 yearly medians (4.2%, 6.7%) are well below 2023-24 (16.4%, 15.9%). Prime's MD
  is quoted saying a strong year "has typically been followed by a lull of two to three years"
  (UNVERIFIED, Industrial Economist above).
- Participation rose: average retail applications per IPO 4.05 lakh (2019) to 18.87 lakh (2024),
  14.99 lakh (2025) (Prime, UNVERIFIED); almost half the allotted demat accounts in the SEBI
  study were opened in 2021-23 (PRIMARY).
- Open vs close: in weak years more IPOs closed in loss than opened in loss (Trendlyne 2025: 22
  opened in loss, 35 closed in loss). Small issues trade in a 5% band after the auction.
- Allottees compete to sell: individuals were 54.3% of listing-day gross selling and sold 50.2%
  of allotted value within a week (SEBI study, pp.13-19, PRIMARY).
- Grey-market premium has no primary record; a filter on it cannot be tested historically.
- Literature: lottery allotment is used as a natural experiment by Anagol, Balasubramaniam and
  Ramadorai, *Review of Economic Studies* 85(4), 2018 ([EconPapers](https://econpapers.repec.org/RePEc:oup:restud:v:85:y:2018:i:4:p:1971-2004.),
  abstract only). No peer-reviewed study of post-2021 Indian IPO underpricing was confirmed.

## 2. SME IPOs (NSE Emerge, BSE SME)

**Is small an advantage? No: Rs 20,000 is excluded** from both the IPO and, in general, the
secondary market.

### 2.1 Current minimum and access (PRIMARY unless marked)

- **Reg 267(2):** "The minimum application size shall be two lots per application: Provided that
  the minimum application size shall be above 2 lakhs", in force 8 Mar 2025, measured at the
  issue price, not the amount paid on application
  ([consolidated ICDR, amended to 21 Mar 2026, pp.198-199](https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1774592300989.pdf)).
  SEBI's agenda memo puts two lots at Rs 2,00,200-3,20,000
  ([agenda memo, pp.3-5](https://www.sebi.gov.in/sebi_data/meetingfiles/jan-2025/1735725342588_1.pdf)).
  Rs 20,000 is 6.25%-9.99% of that.
- **Category:** "individual investors who applies for minimum application size", at least 35%
  (book built) or 50% (fixed price), by draw of lots (Reg 253, Reg 268(3)). Minimum allottees
  200 (was 50).
- **Secondary market:** trading lot = IPO lot under SEBI circular CIR/MRD/DSA/06/2012 (21 Feb
  2012), Rs 1.0-1.6 lakh at the issue price, and lots are not cut below the initial size while
  the price is below issue. One lot costs Rs 20,000 or less only after a fall of about 81-83%
  (issue Rs 100, lot 1,200: affordable at P ≤ 20,000 / 1,200 = Rs 16.67, a fall of 83.3%; issue
  Rs 1,050, lot 100: P ≤ Rs 200, 81.0%). Whether exchanges have since raised lot sizes was not
  verified. Circular quoted in the
  [SEBI consultation of 14 Oct 2026, para 5.5.3.6](https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791972839578.pdf).
- **Pending (comments by 4 Nov 2026):** 4 lots of at least Rs 25,000 (Rs 1 lakh, 5x Rs 20,000);
  "Retail Individual Investors" restored at 35%; trading lot of one share; compulsory market
  making removed; 500 minimum allottees. The paper's dates (31 Dec 2026, 15 Feb 2027) are
  illustrations only (same paper, paras 5.1-5.9, 7.1).

### 2.2 SEBI and exchange changes, 2024-2026

| Date | Change | Tag and source |
|---|---|---|
| 4 Jul 2024 | NSE: +90% cap over issue price in the listing-day pre-open (NSE/SME/62757) | PRIMARY recital in [NSE/CMTR/69388](https://nsearchives.nseindia.com/content/circulars/CMTR69388.pdf); press: [Business Standard, 4 Jul 2024](https://www.business-standard.com/markets/ipo/sme-ipo-opening-price-to-be-capped-at-90-in-pre-open-on-listing-day-nse-124070400429_1.html) (UNVERIFIED) |
| 28 Aug 2024 | SEBI investor advisory on SME stocks (tips, social media) | PRIMARY: date and content in the [agenda memo, para 2.5](https://www.sebi.gov.in/sebi_data/meetingfiles/jan-2025/1735725342588_1.pdf) |
| 1 Sep 2024 | NSE Emerge: positive free cash flow to equity in 2 of 3 years | PRIMARY recital in [NSE/SME/73818](https://nsearchives.nseindia.com/content/circulars/SME73818.pdf) |
| 18 Dec 2024 | SEBI Board (PR 36/2024): EBITDA Rs 1 crore in 2 of 3 years; OFS ≤ 20% of issue and ≤ 50% of a seller's holding; GCP ≤ 15% or Rs 10 crore; staged promoter lock-in; no repaying promoter loans; 21-day DRHP comments | PRIMARY: [PR 36/2024](https://www.sebi.gov.in/sebi_data/attachdocs/dec-2024/1734537931312.pdf); NSE applied it to DRHPs filed from 19 Dec 2024 ([NSE/SME/65701](https://nsearchives.nseindia.com/content/circulars/SME65701.pdf)) |
| 8 Mar 2025 | ICDR amendment GN/2025/233 in force: two-lot, above-Rs 2 lakh minimum; "retail" deleted; 200 allottees; monitoring agency above Rs 50 crore | PRIMARY: [consolidated ICDR](https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1774592300989.pdf) |
| 4 Aug 2025 | NSE: -20% floor below issue price in the pre-open | PRIMARY: [NSE/CMTR/69388](https://nsearchives.nseindia.com/content/circulars/CMTR69388.pdf) |
| 8 Oct 2025 | All pre-issue shares of promoters, KMP, QIBs and others must be demat before the DRHP | PRIMARY: consolidated ICDR, p.173 |
| 20 Apr 2026 | NSE: issue proceeds count in the FCFE test | PRIMARY: [NSE/SME/73818](https://nsearchives.nseindia.com/content/circulars/SME73818.pdf) |
| 21 May 2026 | SEBI consultation on pre-open price discovery (asks whether to apply flexing to SME IPOs); outcome not found | PRIMARY: [SEBI CP](https://www.sebi.gov.in/sebi_data/attachdocs/may-2026/1779362049037.pdf) |
| 14 Oct 2026 | SEBI consultation to partly reverse the 2025 tightening (section 2.1) | PRIMARY: [SEBI CP](https://www.sebi.gov.in/sebi_data/attachdocs/oct-2026/1791972839578.pdf); [Working Group report, Aug 2026](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/WG%20Report%20for%20Review%20of%20SME%20Provisions_p.pdf) |

SEBI's stated reason for the higher minimum was to "protect the interest of smaller retail
investors" and "attract investors with risk taking appetite", citing fund diversion and circular
trading (agenda memo, Annexure III). In Oct 2026 it says the Rs 2 lakh minimum "may
unnecessarily restrict access". No SEBI statistics on SME listing gains were found in these
documents.

### 2.3 Performance evidence (for reference; not accessible at Rs 20,000)

| Claim | Tag, source, date | Period, n | Live/OOS | Costs, taxes | Could be overstated because |
|---|---|---|---|---|---|
| Raw mean listing-day return +8.66%; 5% trimmed mean 5.77%; 33% negative vs Nifty | PRIMARY (refereed college journal): [Singh & Anand, *Business Analyst* 41(2)](https://www.srcc.edu/system/files/5.pdf), 2020 or later | Feb 2012-Mar 2017, 176 BSE SME IPOs, about 98% fixed price | in-sample | none | assumes full allotment; Rs 1 lakh minimum, no pre-open cap |
| 12-month BHAR overperformance; issue size and oversubscription relate negatively to BHAR | PRIMARY (abstract only): [Arora & Singh, *J. Asia Business Studies* 15(1), 2021](https://www.emerald.com/insight/content/doi/10.1108/JABS-10-2019-0305/full/html) | Feb 2012-May 2018, 375 IPOs (regressions on 104 with price data) | in-sample | none | data availability, illiquid prices, hot-market sample |
| CY2024 mean +56.91%, median +37.50% (n=248); CY2025 mean +11.15%, median +2.95% (n=269); 2026 to 25 Oct mean +12.18%, median +1.46% (n=183) | UNVERIFIED: [Tapetide 2024](https://tapetide.com/insight/reports/ipo-listing-gains/2024), [2025](https://tapetide.com/insight/reports/ipo-listing-gains/2025), [2026](https://tapetide.com/insight/reports/ipo-listing-gains/2026) | as stated | in-sample | none | method undocumented; no allotment adjustment; the 2024 cap and 2025 rules break comparability |
| "nearly 74%" of FY26 SME listings below their debut price | UNVERIFIED: [Multibagg citing Prime](https://www.multibagg.ai/market-pulse/articles/fy26-ipos-trading-below-listing-cmotq9cwyinsno50jb94fx6x5) | FY26 | snapshot | none | snapshot date and base unclear |

Median change CY2024 to CY2025: 2.95 - 37.50 = -34.55 pp (Tapetide). The data cannot separate
the July 2024 cap, the March 2025 rules and market conditions.

## 3. Tender-offer buybacks

**Is small an advantage? Yes for any holding worth Rs 2 lakh or less, with a rounding problem
at Rs 20,000.** The small-shareholder category got 2.5-9.1x the general category's acceptance in
the three primary cases (34.81/13.88, 55.17/10.65, 53.49/5.88). Rs 20,000 has no edge over
Rs 2 lakh inside the category, and in high-priced stocks its proportional entitlement rounds to
zero.

### 3.1 Rules

- **Small shareholder:** market value of not more than Rs 2 lakh at the record-date close on the
  exchange with the highest volume (Reg 2(i)(n)). TCS 2023: NSE close Rs 3,457.10, so up to 57
  shares ([TCS letter of offer, Nov 2023, para 19.7](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf)).
  Wipro 2026: Rs 198.37, up to 1,008 shares ([Wipro letter of offer, Jun 2026, para 20.5.8](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf)). PRIMARY.
- **Reservation:** the higher of 15% of the offer or the category's proportional entitlement
  (Reg 6). TCS 2023: 61,44,579 (15%) against 4,09,657 (proportional). PRIMARY, TCS letter of
  offer paras 19.9-19.11.
- **Rounding:** fractional entitlement "shall be ignored"; holders of 3 or fewer shares get
  "zero entitlement" but "will be given preference in the Acceptance of one Equity Share" from
  additional shares tendered. PRIMARY:
  [Bajaj Auto letter of offer, Mar 2024, paras 19.13-19.14](https://www.sebi.gov.in/sebi_data/commondocs/mar-2024/Bajaj_Auto_Limited_LOO_p.pdf).
- **One PAN:** holdings under one PAN are clubbed to decide small-shareholder status.
  UNVERIFIED (search summary of the [SIS Ltd PA, Jun 2025](https://www.sebi.gov.in/sebi_data/commondocs/jun-2025/SIS%20Limited_PN_p.pdf); not opened).
- **Mechanics:** 5 working days of tendering through the exchange mechanism; "Securities
  Transaction Tax at 0.1% ... will be applicable" (TCS letter of offer para 21.5, PRIMARY).
  Record date to settlement: TCS 2023, 25 Nov to 12 Dec
  ([post-buyback advert](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf));
  Infosys 2025, 14 Nov to 3 Dec ([post-buyback advert](https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/05122025/72F11864-D6DF-41CC-807A-289037B9E42B-152644.pdf));
  Wipro 2026, 5 Jun to 24 Jun. About 18-20 days. Before 2023, 5-9 weeks (UNVERIFIED, HDFC
  Securities notes below).
- **Last buy day** under T+1: the trading day before the record date (UNVERIFIED:
  [Zerodha support](https://support.zerodha.com/category/console/corporate-actions/ca-others/articles/what-does-ex-date-and-record-date-mean)).
- **Open-market route:** limit cut to 10% (Apr 2023), 5% (Apr 2024), zero from 1 Apr 2025
  ([Nishith Desai](https://nishithdesai.com/research-and-articles/hotline/capital-markets-hotline/capital-markets-hotline-sebi-buy-back-of-securities-amendment-regulations-2023-8507),
  UNVERIFIED); back from 1 Aug 2026 below 15% of capital and free reserves (correction 7). The
  open-market route has no small-shareholder reservation
  ([SEBI consultation addendum, Jul 2026](https://www.sebi.gov.in/sebi_data/commondocs/jul-2026/1%20list_p.pdf), search snippet only, so UNVERIFIED).

### 3.2 Acceptance ratios and premiums

Primary cases (AR = accepted / validly tendered in the category; premium = buyback price /
record-date close - 1):

| Offer | Record date | Buyback price | Premium | Small entitlement | Small AR | General AR | Tag, source |
|---|---|---|---|---|---|---|---|
| TCS 2023 | 25 Nov 2023 | 4,150 | 20.04% | 1 per 6 (16.67%) | **34.81%** | 13.88% | PRIMARY: letter of offer, post-buyback advert |
| Infosys 2025 | 14 Nov 2025 | 1,800 | not extracted | 2 per 11 (18.18%) | **55.17%** | 10.65% | PRIMARY: post-buyback advert |
| Wipro 2019 | 21 Jun 2019 | 325 | n/a | n/a | **53.49%** | 5.88% | PRIMARY: [Wipro post-buyback advert](https://www.wipro.com/content/dam/nexus/en/investor/buy-back/buyback2019/post-buyback-public-announcement-for-buy-back-of-equity-shares.pdf) |
| Wipro 2023 | 16 Jun 2023 | 445 | 16.71% | 62 per 265 (23.40%) | 77-78% UNVERIFIED | n/a | PRIMARY [letter of offer](https://www.sebi.gov.in/sebi_data/commondocs/jun-2023/Wipro_LTD_LOO_p.pdf); AR UNVERIFIED: [Business Today](https://www.businesstoday.in/markets/stocks/story/wipro-share-buyback-check-offer-opening-date-last-date-entitlement-ratio-for-reserved-and-general-category-535693-2026-06-09) |
| Bajaj Auto 2024 | 29 Feb 2024 | 10,000 | 26.43% | 7 per 27 (25.93%) | about 26% UNVERIFIED | n/a | PRIMARY letter of offer; AR UNVERIFIED: [Upstox](https://upstox.com/news/market-news/stocks/bajaj-auto-buyback-know-about-acceptance-ratio-return-and-retail-quota-ahead-of-june-24-record-date/article-195782/) |
| Wipro 2026 | 5 Jun 2026 | 250 | 26.03% | 11 per 56 (19.64%) | not found | n/a | PRIMARY letter of offer |

In TCS 2023, 37.4% of small shareholders bid (8,41,551 of 22,48,078) and small holders held
89.33% of the offer size.

Broker-compiled tables (UNVERIFIED: HDFC Securities retail-research notes of
[29 Aug 2019](https://www.hdfcsec.com/hsl.docs//BSE%20Ltd%20-%20Buyback%20update-201908291228149800252.pdf) and
[8 Mar 2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf);
in-sample; pre-cost; pre-tax; entry at the day-after-board price; unaccepted shares sold at
payout; annualised):

| Period | Offers | Median small AR | Offers at 100% | Median AR / entitlement | Median annualised return | Negative | Median payout price vs buyback price |
|---|---|---|---|---|---|---|---|
| Dec 2018-Aug 2019 | 22 | 33.85% | 6 | 2.59x | **-6.35%** | 12 of 22 | -28.5% |
| Dec 2020-Feb 2022 | 23 | 46.6% | 5 | 3.3x | **+19.1%** | 5 of 23 | -20.3% |

Could be overstated: the notes cover only offers completed in the year before each note and
were written to promote a live offer; annualising short holds assumes immediate redeployment
and no overlap. Earlier HDFC notes report TCS at 100% small AR in 2017, 2018 and 2020
([HDFC, 3 Sep 2018](https://www.hdfcsec.com/hsl.docs//TCS%20-%20Buyback%20Opportunity%20Note%20update%20-%20030918-201809031748079081979.pdf)).

Literature: Suresha B. et al., *Investment Management and Financial Innovations* 21(3), 5 Aug
2024 ([PDF](https://businessperspectives.org/images/pdf/applications/publishing/templates/article/assets/20528/IMFI_2024_03_Suresha%20B.pdf),
PRIMARY, peer-reviewed): NSE tender offers, 75 firms Apr 2016-Feb 2020 and 43 firms Mar
2020-Mar 2022; market-model event study, -21 to +21 days; in-sample; no costs. Pre-COVID
pre-event CAAR 3.61 (t 8.45), post-event -5.44 (t -12.75), event day 0.30 (t 0.71). **The
abstract calls the event-day result significant; its own table does not.** No study measures the
record-date path or the post-settlement price of unaccepted shares.

### 3.3 Tax, and the effect of the deemed-dividend rule and its reversal

| Buyback date | Shareholder tax | Tag, source |
|---|---|---|
| before 5 Jul 2019 | capital gains | UNVERIFIED (background; statute not read) |
| 5 Jul 2019 - 30 Sep 2024 | company paid buyback tax (s.115QA); shareholder exempt (s.10(34A)) | UNVERIFIED (background; statute not read) |
| 1 Oct 2024 - 31 Mar 2026 | whole consideration a deemed dividend at slab rates; cost of the shares a capital loss | PRIMARY: [Memorandum, 1 Feb 2026](https://www.indiabudget.gov.in/doc/memo.pdf); Wipro letter of offer 2026 |
| from 1 Apr 2026 | consideration less cost = capital gains (s.69(1)): s.196 STCG at 20% if held 12 months or less; promoters pay extra (correction 2); no TDS for residents | PRIMARY: [Finance Act 2026](https://egazette.gov.in/WriteReadData/2026/271439.pdf); Wipro letter of offer 2026 |

Illustration on Rs 20,000 at TCS 2023 inputs (AR 34.81%, premium 20.04%; arithmetic in this
report): accepted consideration = 20,000 x 0.3481 x 1.2004 = Rs 8,357; cost of accepted shares
Rs 6,962; gain Rs 1,395.

- **This owner (header assumption): nil tax in both regimes.** Deemed dividend: Rs 8,357 of slab
  income sits inside the nil band and the rebate; the Rs 6,962 capital loss carries forward 8
  years against capital gains only, which are untaxed anyway. Capital gains: Rs 1,395 of STCG
  is absorbed by the s.196(2) shortfall.
- **A holder at the 30% slab, for comparison:** deemed dividend 8,357 x 31.2% = Rs 2,607, plus a
  capital loss whose value depends on future gains (at most 6,962 x 20.8% = Rs 1,448);
  capital gains 1,395 x 20.8% = Rs 290. The reversal matters for higher-income holders, not
  for this owner.
- Dividend TDS (10%) applied only above Rs 10,000 per company per year. Finance Act 2025 s.57
  raised the threshold from Rs 5,000 (PRIMARY, [Finance Act 2025](https://thc.nic.in/Central%20Governmental%20Acts/Finance%20Act,%202025.pdf));
  the 1 Apr 2025 start is from the Act's general commencement, not checked clause by clause.
  Refundable through a return.
- Conflict: a 12% surcharge on the promoter tax appears in the e-Gazette rates chapter as read
  by the buyback researcher, but the tax researcher did not find it in a third-party copy and
  marks it unconfirmed (UNVERIFIED report: [Business Today, 25 Mar 2026](https://www.businesstoday.in/personal-finance/tax/story/finance-bill-amendments-propose-flat-12-surcharge-on-capital-gains-from-buybacks-522368-2026-03-25)).
  Promoters only; no effect on this owner.

### 3.4 Expected value on Rs 20,000

Per event: R = AR x (Pb/Pe - 1) + (1 - AR) x (Pu/Pe - 1) - c, with Pe the entry price (proxy:
record-date close), Pb the buyback price, Pu the sale price of unaccepted shares after
settlement, c the round-trip cost. c = Rs 77.69 (0.388%) at 3 bps with two sell days, Rs 105.69
(0.528%) at 10 bps, Rs 67.07 with one sell day. Breakeven Pu* = [Pe(1 + c) - AR x Pb] / (1 - AR).
The Pu moves are assumptions; no primary Pu was collected.

| Event (AR used) | AR x premium | R if Pu/Pe = 0% | -5% | -10% | Breakeven move |
|---|---|---|---|---|---|
| TCS 2023 (34.81%, primary) | 6.98% | +6.59% (Rs 1,318) | +3.33% | +0.07% | -10.10% |
| Wipro 2023 (23.40%, entitlement floor) | 3.91% | +3.52% | -0.31% | -4.14% | -4.59% |
| Bajaj Auto 2024 (26%, UNVERIFIED) | 6.87% | +6.48% | +2.78% | -0.92% | -8.76% |
| Wipro 2026 (19.64%, entitlement floor) | 5.11% | +4.72% | +0.70% | -3.32% | -5.88% |
| TCS 2022 (14.29%, entitlement floor) | 3.75% | +3.36% | -0.93% | -5.22% (-Rs 1,044) | -3.92% |

- **Rounding at Rs 20,000:** TCS 2023 buys 5 shares, entitlement 5 x 1/6 = 0; Bajaj 2024 buys 2
  shares, 2 x 7/27 = 0. Acceptance then comes only from the additional pool and the one-share
  preference, so the holder's AR is 0, 1 of 2 or 2 of 2, not the category AR. Wipro 2026 buys
  100 shares, entitlement 19. Proportional entitlement is zero above a price of about
  Rs 20,000 x entitlement ratio, roughly Rs 3,000-5,000 at 15-25% entitlements.
- **Per year:** sum of 20,000 x R_i, simple. At 18-20 days per event, one Rs 20,000 position
  can cycle through at most 15-18 non-overlapping events. Supply: about 19 tender offers a year
  (75 in Apr 2016-Feb 2020) and 21 (43 in Mar 2020-Mar 2022) per Suresha et al.; 25 companies
  filed buyback documents with SEBI between 29 Apr and 28 Oct 2026, route not checked
  ([SEBI filings list](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=22&smid=17)).

### 3.5 Why the figures could be overstated or decayed

- **Crowding:** TCS small AR went from 100% (2017, 2018, 2020) to 24-26% (2022, Chittorgarh
  shows both on one [page](https://www.chittorgarh.com/buyback/tcs-buyback/55/), UNVERIFIED) and
  34.81% (2023, PRIMARY). The largest premiums draw the most small bids.
- **Unaccepted shares fall:** median payout prices 20-28% below the buyback price and below the
  day-after-board price in 14 of 23 and 18 of 22 offers (broker tables). HEG, Savita Oil and
  eClerx lost money in 2019 despite premiums.
- **Route switch:** from 1 Aug 2026 a company can choose the open-market route, which has no
  reservation. No post-August route data was compiled.
- **Selection:** news covers large IT offers with high ARs; projected ARs are often quoted as
  outcomes.

## 4. Open offers and delisting offers

**Is small an advantage? No rule favours small holders in either.** Open offers prorate every
tendering holder alike, with a marketable lot of 1 share. A successful delisting accepts every
share bid at or below the final price, for any holder. A Rs 20,000 order has less market impact
than a large holder's in an illiquid target; no source measures this (inference).

### 4.1 Open offers: rules (SAST Regulations, consolidated to 5 Dec 2025, PRIMARY)

Source: [SEBI consolidated SAST text](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf).

- **Triggers:** crossing 25% of voting rights (Reg 3(1)); a 25%+ holder buying more than 5% in a
  financial year (Reg 3(2)); control (Reg 4). Minimum size 26% (Reg 7(1)).
- **Price (Reg 8(2)):** the highest of the negotiated price, the acquirer's 52-week VWAP and
  26-week high, and the 60-trading-day VWAP before the announcement (frequently traded shares);
  an independent registered valuer for infrequently traded shares from 3 Jan 2026.
- **Timeline:** tendering opens within 12 working days of SEBI comments and lasts 10 working
  days; tendered shares cannot be withdrawn (Reg 18(9)); payment within 10 working days.
  Delays can carry 10% a year interest (RGF Capital Markets, SEBI letter of 16 Jun 2026:
  [letter of offer, Oct 2026](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf)).
- **Acceptance:** proportionate when oversubscribed, "not less than the minimum marketable lot",
  which "shall be 1 (One)" (RGF letter of offer). The clause comes from the offer-letter format;
  it was not found in the Regulations themselves. **No small-shareholder provision** in the
  consolidated text (negative text search).
- **Costs and tax:** tenders go through the exchange acquisition window (SEBI circular of 13 Apr
  2015), so 0.1% delivery STT applies. Gains are STCG under s.196 (held 12 months or less).
  The RGF letter of offer (2026) still says LTCG on STT-paid shares is exempt, which has been
  wrong since 2018: offer-document tax text cannot be relied on.

### 4.2 Open offers: evidence

| Claim | Tag, source, date | Period, n | Live/OOS | Costs, taxes | Could be overstated because |
|---|---|---|---|---|---|
| "less than 5% open offers launched since 2015 ... have been fully subscribed" | UNVERIFIED: ET compilation via [blog repost, Jan 2025](https://gagashare1.blogspot.com/2025/01/ultratech-cement-ultratechs-open-offer.html) | 2015-Jan 2025, n not given | in-sample | none | definition and denominator unknown; ET original not seen |
| India Cements (Rs 390, Jan 2025) about 110% subscribed: implied AR 1/1.10 = 90.9% | UNVERIFIED, same repost | n=1 | in-sample | none | post-offer report not retrieved |
| Mindtree (Rs 980, Jun 2019) "oversubscribed by 116%": implied AR about 86% if 1.16x | UNVERIFIED: [Business Today](https://businesstoday.in/amp/bt-buzz/news/story/bt-buzz-taking-over-mindtree-what-lies-ahead-for-the-new-ceo-and-the-company-211809-2019-07-03) | n=1 | in-sample | none | "116%" could mean 1.16x or 2.16x |
| Offer below market: ACC about 8% of target tendered, Ambuja 0.14-1.35% (Sep 2022); NDTV 31.79% tendered at an offer about 25% below market (Dec 2022) | UNVERIFIED: [Business Standard, 10 Sep 2022](https://www.business-standard.com/article/companies/ambuja-cements-acc-receive-lukewarm-response-from-public-shareholders-122091000362_1.html); [Business Today, 5 Dec 2022](https://www.businesstoday.in/latest/corporate/story/adani-group-becomes-single-largest-shareholder-in-ndtv-with-375-355298-2022-12-05) | n=3 | in-sample | none | anecdotes |
| Many targets are sub-Rs 10 illiquid micro-caps (Senthil Infotek Rs 8; RGF Rs 1.10) | PRIMARY: [Senthil pre-offer advert, Jun 2026](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Senthil%20Infotek%20Limited%20-%20POA_p.pdf); RGF letter of offer | n=2 | n/a | n/a | examples only |
| Positive target abnormal returns at announcement | PRIMARY (abstract only): [Vemula, Gupta & Kashiramka 2020](https://www.inderscienceonline.com/doi/abs/10.1504/IJFSM.2020.113165) | 2011-2017, 96 offers | in-sample | none | numbers paywalled; announcement window, not a tender trade |

SEBI's monthly open-offer tables list target, dates, size and price but **not acceptances**
([example, May 2024](https://www.sebi.gov.in/statistics/open-offers/may2024.html)). No systematic
2016-2026 table of open-offer spreads or acceptance ratios was found.

### 4.3 Delisting: rules (Delisting Regulations 2021, consolidated to 3 Sep 2025, PRIMARY)

Source: [SEBI consolidated Delisting Regulations](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).

- **Reverse book building (RBB):** succeeds if the acquirer reaches 90% at the discovered price
  (the price that takes it to 90%). The acquirer may reject a discovered price above its
  indicative price.
- **Fixed price** (from 25 Sep 2024, frequently traded shares only): at least 15% above the floor;
  succeeds at 90%; no counter offer.
- **Floor (Reg 19A, from 25 Sep 2024):** highest of the acquirer's 52-week VWAP and 26-week high,
  adjusted book value (not for PSUs), and the 60-day VWAP; reference date = announcement date.
- **Counter offer** (RBB only, from 25 Sep 2024): allowed if acquirer plus tenders reach 75% and
  at least half the public shareholding tendered.
- **Small holders on success:** "All the public shareholders, whose bids are accepted, shall be
  paid the discovered price or a higher price ... or fixed price" (Reg 24(1)); bids at or below it are accepted, **no proration**.
  Non-tendering holders can sell at the same price for at least one year (Reg 26).
- **Timeline:** bidding 5 working days; payment within 5 working days of the outcome
  announcement; a 6-month bar after a failure. PSU fixed-price route added from 3 Sep 2025.

### 4.4 Delisting: evidence and expected value

| Claim | Tag, source, date | Period, n | Live/OOS | Costs, taxes | Could be overstated because |
|---|---|---|---|---|---|
| 15 successful RBB delistings: 7 at the floor (0%), 8 at 7.69%-242.02% over it; median 7.69%, mean 35.91% (this report's arithmetic) | PRIMARY: [SEBI discussion paper, 26 Jul 2018](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2018/1532603980878.pdf) | FY16-FY18, n=15 | in-sample | none | successes only; premium over the floor, not over the post-announcement price; mean set by Fulford, Panasonic, Essar Oil |
| 5 of 9 resolved offers succeeded; 4 of 5 at 0% premium; average 145 days from launch to completion | UNVERIFIED (law firm): [Cyril Amarchand, 11 Nov 2020](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report) | Oct 2019-Oct 2020, n=13 | in-sample | none | small-company route excluded |
| 6 of 16 succeeded (37.5%) | UNVERIFIED: [Cyril Amarchand blog, 12 Jul 2022](https://corporate.cyrilamarchandblogs.com/2022/07/analysis-of-recently-attempted-voluntary-delistings-india/) | about Jul 2021-Jul 2022, n=16 | in-sample | none | window may overlap the next row |
| 9 of 16 succeeded (56%); RBB price = indicative price in 6 of 8 that reached 90%; median RBB price 14.12% over floor (chart values) | UNVERIFIED: [Khaitan & Co, Aug 2024](https://khaitanco.com/sites/default/files/2024-08/Voluntary%20Delisting%20Snapshot.pdf) | FY23-FY24, n=16 | in-sample | none | values read from charts; includes rejected prices |
| Failures then fell: Vedanta 10-24% (Oct 2020), Linde India 20% (Jan 2019), INEOS Styrolution 20% (Jul 2020) | Vedanta failure PRIMARY ([post-offer announcement](https://vedantaresources.com/uploads/investor-sec-filings/Post-Offer-Public-Announcement-for-Delisting.pdf)); drops UNVERIFIED ([Business Standard, Vedanta](https://www.business-standard.com/amp/article/markets/vedanta-tanks-10-on-failure-of-delisting-offer-120101200164_1.html); [Linde](https://www.business-standard.com/amp/article/markets/linde-india-slips-20-on-failure-of-delisting-plan-119012500239_1.html); [INEOS](https://www.business-standard.com/article/markets/ineos-styrolution-tanks-20-on-failure-of-delisting-offer-120072400412_1.html)) | n=3 | in-sample | none | one- or two-day moves from a price that already held the run-up |
| 16 delisting offers in 2022; 11-12 in FY25 | UNVERIFIED (Prime via press): [Business Today, Nov 2023](https://www.businesstoday.in/amp/markets/market-commentary/story/sebi-set-to-amend-delisting-norms-soon-406045-2023-11-17); [Business Standard, 21 May 2025](https://www.business-standard.com/industry/news/fy25-marks-among-the-least-ever-spends-on-taking-companies-private-125052101883_1.html) | as stated | n/a | n/a | counts differ by source |

No SSRN, IIM, ISB or NSE paper on Indian RBB outcomes was found; the only delisting event study
found ([Manchanda 2012, *Indian Journal of Finance*](https://www.indianjournaloffinance.co.in/index.php/IJF/article/view/72421),
41 delistings, -12.01% wealth effect for NSE/BSE delistings; snippet only) predates 2016.

**EV per event:** EV = p x (g - c_win) + (1 - p) x (L - c_lose), tax nil; p success
probability, g premium of exit over entry, L failure move, c costs (success path 0.305% at 3
bps, 0.775% at 50 bps; failure path 0.309% and 1.155%). Entry at the floor is assumed, which is
optimistic: the price usually rises above the floor after the announcement.

| p, g, L | 3 bps | 50 bps |
|---|---|---|
| 0.50, 7.69% (SEBI median), 0% | +3.52% | +2.82% |
| 0.50, 7.69%, -10% | -1.47% | -2.15% |
| 0.50, 7.69%, -20% | -6.47% | -7.12% |
| 0.50, 35.91% (SEBI mean), -20% | +7.63% | +6.97% |
| 0.375 (CAM 2022), 14.12% (Khaitan median), -20% | -7.52% | -8.22% |
| 0.5625 (Khaitan), 14.12%, -20% | -1.12% | -1.76% |
| 0.5625, 0% (entry at the indicative price), -20% | -9.06% | -9.69% |

Breakeven p at 3 bps: 0.734 (g 7.69%, L -20%), 0.595 (14.12%, -20%), 0.363 (35.91%, -20%),
0.413 (fixed-price 15% minimum, L -10%). Per year: 2.5 sequential events at the 145-day average
lock (365 / 145) gives -Rs 4,800 to +Rs 3,800 on Rs 20,000 over the table's range. No success
rate has been published for the fixed-price route.

**Open offers, illustration only** (no published spreads): gross = a x s + (1 - a) x d, with a
the acceptance ratio, s the spread of offer over entry price, d the move in returned shares.
At a = 0.86-0.91: s = 5%, d = -10% gives +2.90% to +3.65%; s = 10%, d = -10% gives +7.20% to
+8.20%; s = 5%, d = -20% gives +1.50% to +2.75%; less 0.31-0.78% costs. Lock: about 3.5 months
(Mindtree) to 5.5 months (India Cements) from agreement to tendering.

Could be overstated or decayed (both offer types): every figure is in-sample and gross; premiums
are measured from a floor a post-announcement buyer cannot get; SEBI's 2018 list holds only
successes; the rules changed in 2018, 2021, 2024 and 2025; SEBI's own 2018 paper records
arbitrageurs who "disproportionately influence the price discovery".

## 5. Index inclusion and exclusion (Nifty 50, Nifty Next 50, Nifty 100, Sensex)

**Is small an advantage? Neutral.** No rule depends on size, and a Rs 20,000 order is negligible
next to passive flows. The fixed DP charge makes a split position slightly dearer (32.84 bps
statutory at Rs 10,000 against 27.53 at Rs 20,000). No F&O means no market hedge, so the
realised P&L is the raw stock return, not the abnormal return the studies report.

### 5.1 How the reviews work (PRIMARY)

- **Nifty 50, Nifty Next 50, Nifty 100:** semi-annual, on six-month averages to 31 January and
  31 July; changes effective after the last trading day of March and September, with at least
  four weeks' notice. A Nifty 50 entrant must be a Nifty 100 stock in F&O, with average
  free-float market cap at least 1.5x the smallest constituent's; at most five additions a
  calendar year ([NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)).
- **Sensex:** BSE 100 constituents with a derivative contract; a committee decides additions
  ("at the discretion of index committee"); reviewed on data to the end of April and October;
  effective at the open on the Monday after the third Friday of June and December; four weeks'
  notice ([BSE Indices methodology, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf)).
- **Recent Nifty reviews** (calendar days from announcement to the last pre-effective close, this
  report's count; NSE announces after trading hours, so AD+1 is the first tradable day):

| Announced | Effective close | Days | Nifty 50 changes | Source |
|---|---|---|---|---|
| 23 Aug 2024 | 27 Sep 2024 | 35 | Trent, BEL in; Divi's, LTIMindtree out | [press release](https://niftyindices.com/Press_Release/ind_prs23082024.pdf) |
| 21 Feb 2025 | 27 Mar 2025 | 34 | Zomato, Jio Financial in; BPCL, Britannia out | [press release](https://niftyindices.com/Press_Release/ind_prs21022025.pdf) |
| 22 Aug 2025 | 29 Sep 2025 | 38 | InterGlobe, Max Healthcare in; Hero MotoCorp, IndusInd out | [press release](https://niftyindices.com/Press_Release/ind_prs22082025.pdf) |
| 23 Feb 2026 | 27 Mar 2026 | 32 | none (Nifty 100 and Next 50: 6 in, 6 out) | [press release](https://niftyindices.com/Press_Release/ind_prs23022026.pdf) |
| 10 Aug 2026 | 29 Sep 2026 | 50 | BSE Ltd in; Wipro out (to Next 50) | [press release](https://niftyindices.com/Press_Release/ind_prs10082026.pdf) |

The cut-off-to-announcement gap was 10-23 days. Each release prints the near-misses for the next
review (InterGlobe missed in Feb 2025 and entered in Aug 2025). Brokers publish predicted changes
before NSE does (UNVERIFIED as to accuracy; e.g.
[Business Standard, 8 Feb 2026](https://www.business-standard.com/markets/news/tata-motors-cv-and-hdfc-amc-seen-entering-nifty-next-50-shows-data-126020800360_1.html)
named both later Nifty Next 50 entrants).

### 5.2 Evidence on abnormal returns

| Claim | Tag, source, date | Period, n | Live/OOS | Costs, taxes | Could be overstated because |
|---|---|---|---|---|---|
| Nifty additions, mean market-adjusted CAR: AD+1 +1.24%**; AD+2..ED-2 +1.21% (n.s.); ED-1..ED +1.56%**; ED+1..ED+3 -0.78% (n.s.); AD+1..AD+60 +2.43% vs +6.28% in 2000-09. No drift in AD-10..AD. | PRIMARY (peer-reviewed): [Parthasarathy, *Asian J. Finance & Accounting* 11(1), 1 Jun 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123) | 2010-2018, N=27 (full 2000-2018, N=50 on 30 dates) | in-sample | none | 21 of 71 additions dropped; clustered dates; run-up not significant; AD+1 jump arrives before a post-announcement buyer can act |
| Additions CAAR(-20..ED): -0.72% (2010-14, N=15), +1.39% (2015-19, N=16), **-4.84% (2020-24, N=13, p=0.036)**. Deletions: effective-day AAR +1.44% (2020-24, p=0.009) | PRIMARY (SSRN, weak journal): [Marisetty 2025, SSRN 5642110](https://doi.org/10.2139/ssrn.5642110); [journal PDF](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf) | 2010-2024, 81 of 92 events | in-sample | none | benchmark is the Nifty 50 itself; a 252-day estimation window can absorb the run-up and bias toward zero or negative |
| Nifty effective-day effect about +1.47%, reversed by the ninth day; no Jr Nifty effect | PRIMARY (NSE working paper): [Kumar](https://nsearchives.nseindia.com/content/research/comppaper90.pdf) | 1996-2003, 36 Nifty changes | in-sample | none | announcement dates inferred from circulars |
| Inclusion gains reverse within 60 days; excluded stocks earn about +4% to +7% abnormal over 60-240 days | PRIMARY (abstract only): [Chhatwani 2020, *J. Commerce & Accounting Research* 9(4)](https://publishingindia.com/archive/jcar/price-and-volume-effects-of-nifty-50-index-reorganization) | 2000-2016, n not read | in-sample | none | full text paywalled |
| US background: S&P 500 deletion effect over [-20,-1] fell from -14.7% (1990s) to -2.4% (2010s) | PRIMARY (SSRN; snippet): [Greenwood & Sammon](https://www.hbs.edu/ris/download.aspx?name=ssrn-4294297.pdf) | US | in-sample | none | different market |

\*\* = significant at 5%. No post-2016 study was found for the Nifty Next 50, the Nifty 100 or the
Sensex. Selvam et al. (2012) report announcement-day MCARs of -26% to -81%, which are not
plausible; not used.

### 5.3 Passive money

Nifty 50 passive assets: about Rs 84,081 crore in Sep 2019 (ETFs Rs 79,566 crore, index funds
Rs 4,515 crore; [NSE Indices, Jan 2022](https://nsearchives.nseindia.com/content/indices/25_Years_Journey_of_Nifty50_2022-01.pdf))
and about **Rs 4,98,576 crore in May 2026** (this report's sum of 21 ETFs and 26 index funds in
[Nifty Passive Insights, Jun 2026](https://niftyindices.com/Nifty_Passive_Insights/NiftyPassiveFundReport-June2026.pdf)),
5.9x. Nifty Next 50 passive is about Rs 32,844 crore, roughly 1/15 of that; the two largest
Sensex ETFs hold Rs 1,68,739 crore. Passive money grew 6x while the published effect did not
grow. A broker estimate of about $741M of passive buying in BSE Ltd for Sep 2026
([5paisa citing Nuvama](https://www.5paisa.com/news/nifty-rejig-bse-to-replace-wipro-in-nifty-50-as-per-a-nuvama-report),
UNVERIFIED) is about 4.6% of its Rs 1,40,879 crore average free float at Rs 88 per USD (assumed
rate).

### 5.4 What is left for a Rs 20,000 long-only CNC trader

Buy at the AD+1 close, sell at the effective-date close; net = gross - cost, tax nil.

| Model (Parthasarathy 2010-18) | Gross AD+2..ED | Net at 33.5 bps | Net at 47.5 bps | Rs on 20,000 |
|---|---|---|---|---|
| Market-adjusted (MCAR) | 1.21 + 1.56 = 2.77% | 2.43% | 2.29% | 487 / 459 |
| Control sample (CCAR) | 2.10 + 1.55 = 3.65% | 3.31% | 3.17% | 663 / 635 |
| Market model, adjusted (OCAR) | 1.52 + 1.60 = 3.12% | 2.78% | 2.64% | 557 / 529 |
| Marisetty 2020-24, CAAR(-20..ED) | -4.84% | -5.18% | -5.32% | -1,035 / -1,063 |

The Marisetty window starts 20 trading days before the effective date, which is later than AD+1
(22-35 trading days before it in recent reviews), so the two kinds of row are not the same window.

- **Market risk is larger than the mean:** Nifty 50 1-year standard deviation 13.88%
  ([factsheet, 30 Oct 2026](https://www.niftyindices.com/Factsheet/ind_nifty50.pdf)), so about
  3.9% over 20 trading days and 5.2% over 35 (x √(days/250)): ±Rs 780-1,040 one-sigma on
  Rs 20,000.
- **Events:** Nifty 50 additions per year 6, 4, 2, 4, 1, 2 in 2017-2022 (UNVERIFIED,
  [Angel One, 12 Jul 2023](https://www.angelone.in/news/share-market/analysis-of-nifty50-rebalancing-since-2017));
  2, 2, 2, 0 and 1 in the five reviews from Sep 2024 (PRIMARY, releases above). All additions in
  a review share one effective date, so one Rs 20,000 pool covers at most 2 reviews a year:
  2 x (-Rs 1,063 to +Rs 663) = **-Rs 2,120 to +Rs 1,330** a year. (Counting Rs 20,000 per
  addition instead, as the source notes do, gives Rs 900-2,600 but needs more capital.)
- **Nifty 100 / Next 50 additions** add 10-12 events a year, with about 1/15 of the Nifty 50's
  passive money and no post-2016 return evidence.
- **Deletions:** the forced selling executes in the closing auction after 15:15; an MIS short
  must be flat by 14:50 and there is no F&O, so it cannot be held through the auction. The
  long-only use in the literature is buying excluded stocks afterwards (Chhatwani, abstract only).

### 5.5 Why the effect could be overstated or decayed

- No Indian study nets costs or taxes; none is out-of-sample.
- Samples are small (N=13-27 per sub-period) with clustered dates, so none of the post-2015
  estimates can establish whether an effect exists.
- Decline across sub-periods in both studies; the US effect also shrank as passive share rose.
- Rules are mechanical and inputs public 10-23 days before the announcement, and brokers publish
  predictions, so early positioning can absorb the effect. Marisetty's 2020-24 additions show
  CAAR(-20..AD) of +4.86% (p=0.12) before announcement and -4.84% into the effective date,
  consistent with that (a hypothesis only).
- Since Aug 2026 (go-live date UNVERIFIED) the close of F&O stocks is set in an auction with a
  ±3% band around the 15:00-15:15 VWAP (correction 9). No study covers a closing-auction rebalance.
- Overlapping memberships: a Nifty 50 drop-down is also a Nifty Next 50 addition; net passive
  flow depends on all memberships, and no study nets them.

## 6. NSE factor indices: live results, and funds against a Nifty 50 index fund

**Is small an advantage? Neutral.** Every investor pays the same TER and tracking difference. Size
matters only through the fixed DP charge on ETF sales (Rs 10.62, about 0.05% of Rs 20,000).

Definitions: back-calculated = base date to launch date (rules applied to past data); live =
launch date (each index's factsheet, 30 Sep 2026) to the 30 Oct 2026 close. Index levels are
official TRI closes from [niftyindices historical data](https://www.niftyindices.com/reports/historical-data)
(PRIMARY); fund NAVs and TERs are from AMFI ([NAVAll](https://www.amfiindia.com/spages/NAVAll.txt),
[TER disclosure](https://www.amfiindia.com/ter-of-mf-schemes), PRIMARY). The only computation is
CAGR between published levels (this report's arithmetic). Index figures exclude fees, taxes and
trading costs; fund figures are after TER and tracking difference but before the investor's own
charges and taxes.

### 6.1 Coverage

29 NSE factor or strategy indices had at least one live ETF or index fund on 30 Oct 2026.
Direct-plan factor index-fund TERs run 0.37-1.09% (median about 0.59%) against **0.25% for the
UTI Nifty 50 index fund (direct)**. Seven factor indices have no fund, among them Alpha Quality
Low-Volatility 30 and Quality Low-Volatility 30. More than half the funds launched in 2021 or
later, after the indices' strong records.

### 6.2 Index level, live vs back-calculated (gross, against Nifty 50 TRI)

For the 21 indices with at least 3.5 years live, the **median excess was +5.29 pp a year
back-calculated and +1.53 pp a year live**; live was lower for 15 of 21 (median change -3.1 pp).
Indices launched before 2018 (9-16 years live):

| Index (launch) | Live yrs | Live excess pp/yr | Back-calc excess pp/yr | Fund exists |
|---|---|---|---|---|
| Dividend Opportunities 50 (2011) | 15.6 | +1.03 | +9.36 | yes |
| Alpha 50 (2012) | 13.9 | +8.23 | +4.97 | yes |
| High Beta 50 (2012) | 13.9 | -3.71 | -8.63 | no |
| Low Volatility 50 (2012) | 13.9 | +2.32 | +5.29 | no |
| Nifty100 Equal Weight (2013) | 13.4 | +1.69 | +3.30 | yes |
| Nifty50 Value 20 (2014) | 12.6 | +1.53 | +8.42 | yes |
| Growth Sectors 15 (2014) | 12.4 | -0.54 | +11.31 | yes |
| Nifty100 Quality 30 (2015) | 11.6 | -0.54 | +6.07 | yes |
| Nifty100 Low Volatility 30 (2016) | 10.3 | +0.72 | +5.68 | yes |
| Nifty50 Equal Weight (2017) | 9.5 | +1.10 | n/a | yes |
| Alpha Quality Value Low-Vol 30 (2017) | 9.3 | +3.67 | +3.49 | no |
| Alpha Low-Volatility 30 (2017) | 9.3 | +1.14 | +6.99 | yes |
| Alpha Quality Low-Vol 30 (2017) | 9.3 | +1.49 | +5.47 | no |
| Quality Low-Vol 30 (2017) | 9.3 | -0.76 | +4.67 | no |

Median live excess of these 14: +1.12 pp a year; 4 negative. Later launches depend on the end
date: Nifty200 Momentum 30 (2020) shows +9.86 pp a year to 27 Sep 2024, +3.06 to 31 Oct 2025 and
+2.65 to 30 Oct 2026; Nifty200 Alpha 30 (2022) +28.07, +11.51 and +10.53. Indices launched in
2023-2025 with back-calculated excesses of +6 to +10 pp a year show -7.3 to +1.2 live (1.7-2.9
years).

### 6.3 Funds after costs against the UTI Nifty 50 index fund (direct)

Fund window from its first AMFI NAV to 30 Oct 2026; the benchmark fund's NAV over the same dates.
Excess = fund CAGR minus UTI Nifty 50 CAGR. Rs a year = excess x Rs 20,000 (simple). TD = fund
CAGR minus its own TRI CAGR. The UTI fund's own TD was -0.24 to -0.30 pp a year.

| Index | Fund (AMFI code) | Start | Yrs | Fund CAGR | UTI Nifty 50 CAGR | Excess pp/yr | Rs/yr on 20,000 | TD pp/yr |
|---|---|---|---|---|---|---|---|---|
| Dividend Opp 50 | Nippon India ETF (128639) | 2014-04-21 | 12.5 | 12.26% | 11.28% | +0.98 | +196 | -0.27 |
| Nifty50 Equal Weight | DSP IF Dir (141877) | 2017-10-23 | 9.0 | 11.24% | 10.53% | +0.71 | +142 | -0.80 |
| Nifty50 Value 20 | Nippon India IF Dir (148721) | 2021-02-23 | 5.7 | 9.99% | 9.28% | +0.71 | +142 | -0.53 |
| Nifty200 Momentum 30 | UTI IF Dir (148703) | 2021-03-12 | 5.6 | 13.04% | 8.94% | +4.11 | +822 | -0.48 |
| Nifty100 Quality 30 | Edelweiss IF Dir (149254) | 2021-10-07 | 5.1 | 6.96% | 6.26% | +0.70 | +140 | -0.27 |
| Alpha 50 | Kotak ETF (149397) | 2021-12-29 | 4.8 | 8.13% | 7.26% | +0.87 | +174 | -1.91 |
| Nifty100 Equal Weight | Sundaram Dir (149483) | 2022-01-03 | 4.8 | 10.27% | 6.75% | +3.52 | +704 | -0.56 |
| Midcap150 Quality 50 | DSP IF Dir (150428) | 2022-08-04 | 4.2 | 7.57% | 7.86% | -0.29 | -58 | -0.24 |
| Nifty200 Quality 30 | ABSL ETF (150497) | 2022-08-19 | 4.2 | 7.35% | 7.35% | -0.00 | 0 | -0.34 |
| Alpha Low-Vol 30 | Nippon India IF Dir (150487) | 2022-08-22 | 4.2 | 10.58% | 7.75% | +2.82 | +564 | -0.70 |
| Nifty100 Low Vol 30 | Bandhan IF Dir (150636) | 2022-10-07 | 4.1 | 10.57% | 8.28% | +2.29 | +458 | -0.70 |
| Midcap150 Momentum 50 | Tata IF Dir (150738) | 2022-10-31 | 4.0 | 14.36% | 7.33% | +7.03 | +1,406 | -1.38 |

- **Median excess +0.93 pp a year (Rs 185 on Rs 20,000); range -0.29 to +7.03; 10 of 12
  positive.** Ten of the twelve windows start between Feb 2021 and Oct 2022, one market path, so
  they are not independent confirmations.
- The two longest windows (12.5 and 9.0 years) show +0.98 and +0.71 pp a year.
- Funds started late 2023 or later (1-3 years) range from -6.59 pp a year (Nifty500 Multicap
  Momentum Quality 50) and -5.65 (Nifty500 Momentum 50) to +15.22 (Nifty500 Value 50, 3.5 years).
- Fund TD ran a median 0.56 pp a year (0.24-1.91), largest in high-turnover indices: Alpha 50's
  +8.23 pp live index lead became +0.87 pp over the Kotak ETF's window, partly the window and
  partly its 1.91 pp TD.
- Pre-2018 indices, gross live median +1.1 pp a year, less the TD gap to a Nifty 50 fund (0 to
  1.7 pp): about -0.5 to +1.1 pp a year, or -Rs 110 to +Rs 220 on Rs 20,000 (this report's
  arithmetic).

### 6.4 Decay literature

| Claim | Tag, source, date | Period, n | Live/OOS | Costs, taxes | Could be overstated because |
|---|---|---|---|---|---|
| 7 of 9 NSE strategy indices had lower returns after launch; about 4 of 9 had significant four-factor alpha before launch and none after; differences not significant (t -0.16 to -1.68) | PRIMARY (peer-reviewed): [Lalwani, *Applied Finance Letters* 11, 2022](https://ojs.aut.ac.nz/applied-finance-letters/1/article/download/604/159) | base date to Aug 2022, 9 indices | out-of-sample split at launch | none | 9 overlapping indices; low power |
| Long-short WML 12.00% a year (1995-2013) vs 12.68% (2014-2025); HML 5.30% vs 8.58% (this report's geometric means) | PRIMARY (IIMA working-paper data): [IIMA factor library, release 2025-12](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/), [yearly CSV](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/DATA/2025-12_FourFactors_and_Market_Returns_Yearly_SurvivorshipBiasAdjusted.csv) | Oct 1993-Dec 2025 | paper portfolios | none | long-short, gross, broad universe: not investable at Rs 20,000 |
| Momentum indices beat parents by "300-600 bps" over most 10-15 year periods | vendor (NSE Indices licenses these indices): [momentum whitepaper, Feb 2026](https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf) | from Apr 2005, mostly back-calculated | no | none | conflict of interest; does not separate live from back-calculated |

The IIMA and index results do not conflict: the long-short premia did not fall; the long-only,
capped index versions' excess over Nifty 50 did. Phase 1's swing momentum on 40 large caps lost
to buy-and-hold while WML earned 12.68% a year gross in 2016-2023; different universe, long-only
and costs.

### 6.5 Implementation at Rs 20,000

- **ETF round trip** (rates from `config/costs.yaml`; ETF sale STT 0.001% PRIMARY via
  NSE/FATAX/73524): buy about Rs 3.7, sell about Rs 11.5 including DP, about Rs 15 (0.077%)
  before spread; the repo models 10 bps of ETF slippage per side.
- **ETF price vs NAV:** last trade 0.12-1.38% above stated NAV for factor ETFs in a 30 Oct 2026
  snapshot ([ETF.json](https://liveindexsa.niftyindices.com/jsonfiles/ETF.json), field meanings
  undocumented; the Nifty 50 rose about 0.5% that day, so part may be stale NAV). Indicative
  only; no iNAV history was found. Several factor ETFs trade thinly.
- **Direct index fund:** transacts at NAV, about Rs 1.2 per round trip (stamp 0.005%, redemption
  STT 0.001%; both UNVERIFIED), no DP charge if held as a statement of account. Index funds are
  mutual funds, not exchange-traded; whether they fit hard rule 1 is the owner's call.
- **Tax:** held over 12 months, gains are s.198 LTCG inside the Rs 1.25 lakh exemption; nil
  either way under the header assumption.

### 6.6 Why live results could still be overstated

12 of 36 indices have under 2.5 years live; NSE launched multi-factor indices after strong
back-tests; results swing with the end date; closed or merged factor funds are absent from
AMFI's live-scheme file, so fund survivorship could not be checked; Lalwani finds market beta
rose after launch for 7 of 9 indices (about +0.09), so part of a live lead in a rising market is
beta. Tracking error against Nifty 50 of about 5-10% a year (inferred from factsheet
correlations of 0.84-0.95, not computed) means ten years of live data cannot separate a 1-2 pp
premium from zero.

## 7. Tax drag for a resident individual with little or no other income, tax year 2026-27

**Is small an advantage? Yes, through thresholds.** At Rs 20,000 of capital, any plausible annual
gain sits inside the basic-exemption shortfall, so tax drag is nil for an adult resident. A larger
account with the same percentage return crosses the thresholds. This does not scale and depends
on the holder's other income and age.

Sources for this section, all PRIMARY: [Income-tax Act 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf);
[Finance Act 2026, e-Gazette](https://egazette.gov.in/WriteReadData/2026/271439.pdf) (the tax
researcher read a [third-party gazette copy](https://a2ztaxcorp.net/wp-content/uploads/2026/03/THE-FINANCE-ACT-2026.pdf)
and the [22 Apr 2026 corrigendum](https://egazette.gov.in/WriteReadData/2026/271980.pdf));
[Memorandum, 1 Feb 2026](https://www.indiabudget.gov.in/doc/memo.pdf). Period, sample and cost
fields do not apply to statute text. The tables are this report's arithmetic on the provisions,
not an official calculator, and were not cross-checked against the incometaxindia.gov.in
calculator.

### 7.1 Rates for tax year 2026-27 (unchanged by the Finance Act 2026)

| Item | Provision | Value |
|---|---|---|
| New regime (default) slabs | s.202(1) | nil to Rs 4 lakh; 5% to 8 lakh; 10% to 12 lakh; 15% to 16 lakh; 20% to 20 lakh; 25% to 24 lakh; 30% above |
| Old regime (opt-out), under 60 | First Schedule Part I-B | nil to Rs 2.5 lakh; 5% to 5 lakh; 20% to 10 lakh; 30% above |
| STCG on STT-paid listed equity and equity-fund units | s.196(1) (old 111A) | 20% |
| Equity LTCG | s.198(2) (old 112A) | 12.5% above Rs 1,25,000 |
| Holding period for LTCG | s.2(101)(b) | more than 12 months |
| Cess; surcharge | Finance Act 2026 s.3(15)-(16) | 4% of tax; surcharge only above Rs 50 lakh of income |
| STT | s.72(3)(b); s.32(k) | not deductible from capital gains; deductible from intraday (business) income |
| Rebate, new regime | s.156(2)-(3) | 100% of tax up to Rs 60,000 if income ≤ Rs 12 lakh, **capped at slab-rate tax**, so not against s.196 or s.198 tax |
| Rebate, old regime | s.156(1) | up to Rs 12,500 if income ≤ Rs 5 lakh; no slab-rate cap in the text, so on the plain text it can reduce s.196 tax but not s.198 tax (s.198(7)); inference |

### 7.2 Can s.196 (old 111A) gains use the unused basic exemption? Yes

s.196(2): for "an individual or a Hindu undivided family, being a resident", where total income
as reduced by the STCG is below "the maximum amount which is not chargeable to income-tax", the
STCG "shall be reduced by the amount by which the total income as so reduced falls short", and
the balance is taxed at 20%. s.198(3) does the same for equity LTCG, after the Rs 1.25 lakh
exemption.

- The limit follows the regime: Rs 4 lakh new, Rs 2.5 lakh old (under 60).
- **Slab income uses the exemption first.** Interest, dividends and intraday profit come before
  STCG. With Rs 3 lakh of other income, only Rs 1 lakh of shortfall is left for STCG.
- Non-residents get no shortfall. Whether STCG or LTCG absorbs the shortfall first is not stated
  in the Act; the tables assume STCG first.
- Formula (new regime): tax = 1.04 x [20% x max(0, STCG - max(0, 4,00,000 - O)) + slab(O) -
  rebate on slab(O)], O = other slab-rate income.
- The rebate history: ITAT Ahmedabad (12 Aug 2025) and Agra (3 Sep 2025) allowed the 87A rebate
  against 111A STCG for AY 2024-25 because the 1961 Act had no express bar (PRIMARY,
  [ITAT Agra order](https://itat.gov.in/public/files/upload/1756901560-YJpjWc-1-TO.pdf)); ITAT
  Bangalore reportedly did the same for AY 2025-26 (UNVERIFIED,
  [Taxmann, 18 Jun 2026](https://www.taxmann.com/post/blog/section-87a-rebate-restriction-on-special-rate-income-is-prospective-itat/)).
  The Finance Act 2025 added an express bar from AY 2026-27
  ([Finance Act 2025](https://thc.nic.in/Central%20Governmental%20Acts/Finance%20Act,%202025.pdf)),
  and s.156(3) carries it into the 2025 Act. No challenge to s.156(3) was found.

### 7.3 Monthly STCG vs buy-and-hold vs intraday, new regime, resident adult under 60

**Rs 20,000 of capital, annual gains Rs 2,000-50,000 (10%-250% of capital), other income 0 or
Rs 3 lakh: tax nil in every cell** (realised monthly as STCG, held over 12 months as LTCG, or
intraday). Drag 0% of gains and of capital. Realising monthly instead of yearly does not change
the tax by itself; what matters is the year's total, the 12-month test, and deferral of unsold
gains (s.67(1) taxes only on transfer).

First rupee of tax (search in Rs 100 steps):

| Gain type | Other income 0 | Other income Rs 3 lakh |
|---|---|---|
| STCG (s.196) | above Rs 4,00,000 | above Rs 1,00,000 |
| Equity LTCG (s.198) | above Rs 5,25,000 | above Rs 2,25,000 |
| Intraday (speculative business, slab rates) | above Rs 12,00,000 (marginal relief to about Rs 12,70,588) | above Rs 9,00,000 |

Larger gains, for scale (tax in Rs including cess / % of gain):

| Annual gain | Other income | STCG | LTCG | Intraday |
|---|---|---|---|---|
| 5,00,000 | 0 | 20,800 / 4.16% | 0 | 0 |
| 10,00,000 | 0 | 1,24,800 / 12.48% | 61,750 / 6.18% | 0 |
| 2,00,000 | 3,00,000 | 20,800 / 10.40% | 0 | 0 |
| 5,00,000 | 3,00,000 | 83,200 / 16.64% | 35,750 / 7.15% | 0 |
| 10,00,000 | 3,00,000 | 1,87,200 / 18.72% | 1,00,750 / 10.08% | 78,000 / 7.80% |

Worked lines: STCG 5 lakh, O = 0: (5,00,000 - 4,00,000) x 20% = 20,000, plus cess = 20,800.
LTCG 10 lakh, O = 0: (10L - 1.25L - 4L) x 12.5% = 59,375, plus cess = 61,750. Old-regime tax was
equal or higher in every case checked (e.g. STCG 5 lakh, O = 0: Rs 39,000).

### 7.4 Losses, filing and timing

- Short-term capital loss offsets STCG and LTCG and carries forward 8 tax years; long-term loss
  only LTCG (s.108, s.111). Capital losses cannot reduce other heads (s.109(2)).
- Intraday (MIS) round trips are speculative transactions (s.66(31)), a separate business
  (s.26(3)); losses offset only speculation profit, 4 years (s.113).
- Carry-forward needs an on-time return (s.121). Filing is compulsory above Rs 4 lakh of total
  income even when tax is nil. Due dates for tax year 2026-27: 31 Jul 2027, or 31 Aug 2027 with
  business (intraday) income and no audit (Finance Act 2026 s.66). Late fee Rs 1,000 at income up
  to Rs 5 lakh (s.428). Advance tax only if the year's tax is Rs 10,000 or more (s.404).
- Mixing MIS and CNC in one account: intraday slab income uses the exemption before STCG does.

### 7.5 Dividends, buyback proceeds, minors

- Dividends are slab income (nil band and rebate apply); TDS 10% only above Rs 10,000 per company
  per year paid electronically (s.393). The no-TDS declaration is reportedly Form 121 from
  1 Apr 2026 (UNVERIFIED, [Business Today, 1 Apr 2026](https://www.businesstoday.in/personal-finance/tax/story/income-tax-rules-2026-form-121-simplifies-tds-process-for-senior-citizens-523555-2026-04-01)).
- Buyback proceeds from 1 Apr 2026: section 3.3.
- **If the account holder is under 18**, the income is added to the higher-earning parent's
  (s.99(1)(c), s.99(2)(b)) and uses that parent's exemption, usually already used; the Rs 1,500
  per-child exclusion is not available in the new regime (s.202(2)(a)(i)). Brokers say minor
  accounts cannot trade intraday or F&O (UNVERIFIED,
  [Zerodha minor-account FAQ](https://support.zerodha.com/category/account-opening/online-account-opening/minor-account/articles/minor-account-faqs)).
  The nil-tax results in this report then do not hold.

## 8. Downloadable datasets by candidate

Common to every event study: daily prices from NSE bhavcopy, old format
`https://nsearchives.nseindia.com/content/historical/EQUITIES/YYYY/MON/cmDDMONYYYYbhav.csv.zip`
([2016-01-01 file verified](https://nsearchives.nseindia.com/content/historical/EQUITIES/2016/JAN/cm01JAN2016bhav.csv.zip))
and UDiFF format `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`
([2026-09-30 file verified](https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20260930_F_0000.csv.zip)).
CSV in ZIP, free, needs a browser-like User-Agent, not adjusted for corporate actions; the
format changeover date was not confirmed. The repo's own data (40 symbols, 1-minute, to
2026-04-07, per `docs/data.md`) cannot cover any event universe here. Any study built on these
would be a research run: logged in `research/trials.jsonl`, and stopped before 2025-04-08 unless
the owner types "run holdout".

### 8.1 Mainboard IPO

| Dataset | URL | Format | Coverage | Cost | Friction |
|---|---|---|---|---|---|
| NSE basis-of-allotment adverts (PRIMARY) | `https://nsearchives.nseindia.com/corporate/ADV_<ISIN>_<DDMONYYYY>.pdf`, e.g. [Bajaj HFL](https://nsearchives.nseindia.com/corporate/ADV_INE377Y01014_13SEP2024.pdf) | 1-page PDF, two-column | 26 of 26 probed issues 2019-2025; 0 of 10 for 2016-2018 | free | no index: needs ISIN and filing date (usually listing date minus 1-7 days); row order sometimes scrambled in extraction |
| SEBI offer documents (PRIMARY) | [SEBI public-issue filings](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=15&smid=11) | PDF, hundreds of pages | all issues | free | price band, lot, Reg 6(1)/6(2) must be parsed by hand (listing page not opened) |
| SEBI IPO study (PRIMARY) | [PDF, 2 Sep 2024](https://www.sebi.gov.in/sebi_data/attachdocs/sep-2024/1725270963087.pdf) | PDF tables | 144 IPOs, Apr 2021-Dec 2023 | free | aggregates only; PAN-level data not public |
| Tapetide, Trendlyne, Chittorgarh (UNVERIFIED) | [Tapetide](https://tapetide.com/insight/reports/ipo-listing-gains/2024); [Trendlyne](https://trendlyne.com/ipo/screener/year-2024/mainline/); [Chittorgarh allotment list](https://www.chittorgarh.com/report/ipo_basis_of_allotment_list/7/mainline/?year=2024) | HTML | 2018 onward | free tier | locate issues only; Chittorgarh tables load by JavaScript |
| Prime Database (UNVERIFIED) | primedatabase.com | unknown | source of most year-end figures | paid, price not checked | licence terms unknown |

Minimum fields per IPO: ISIN, issue price, lot, retail quota, valid retail applications,
allottees, retail and overall subscription, bid dates, listing-day open and close. With these,
E[P x r] can be computed per IPO instead of the bucket assumption in section 1.4. An IPO
calendar is also needed to count non-overlapping bid windows.

### 8.2 SME IPO

| Dataset | URL | Format | Coverage | Cost | Friction |
|---|---|---|---|---|---|
| Consolidated ICDR, board papers, consultations (PRIMARY) | [ICDR](https://www.sebi.gov.in/sebi_data/attachdocs/mar-2026/1774592300989.pdf); [WG report](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/WG%20Report%20for%20Review%20of%20SME%20Provisions_p.pdf) | PDF | rules; aggregate counts to 31 Jul 2026 | free | none |
| NSE Emerge circulars (PRIMARY) | e.g. [NSE/SME/73818](https://nsearchives.nseindia.com/content/circulars/SME73818.pdf) | PDF | per circular | free | browser headers needed; no CSV of past SME issues found |
| Aggregators (UNVERIFIED) | [Chittorgarh SME by year](https://chittorgarh.com/report/list-of-sme-ipo-by-year-fund-raised/153/all/?year=2022); [Trendlyne SME](https://trendlyne.com/ipo/screener/year-2024/sme/); [InvestorGain](https://www.investorgain.com/report/current-ipo/394/sme/) | HTML | varies | free | methods undocumented |
| Prime Database, CMIE Prowess (UNVERIFIED) | not checked | unknown | used by academic studies | paid | price not checked |

### 8.3 Buybacks

| Dataset | URL | Format | Coverage | Cost | Friction |
|---|---|---|---|---|---|
| SEBI buyback filings: PA, letter of offer, some post-buyback adverts (PRIMARY) | [SEBI listing](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=22&smid=17) | HTML list with PDFs | 1,403 records, back to about 2010 | free | page 1 loads; scripted pagination returned "Unauthorized Request Blocked"; browse manually |
| Post-buyback adverts (PRIMARY; the AR source) | BSE/NSE filings and company sites, e.g. [TCS](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf), [Infosys](https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/05122025/72F11864-D6DF-41CC-807A-289037B9E42B-152644.pdf) | PDF | per offer | free | scattered; anti-bot headers on exchange archives |
| HDFC Securities buyback notes (UNVERIFIED) | links in section 3.2 | PDF tables | 53 offers, 2016-2022 | free | `pdftotext -raw` works; layout mode garbles |
| Chittorgarh buyback pages (UNVERIFIED) | [example](https://www.chittorgarh.com/buyback/tcs-buyback/55/) | HTML with JSON | about 220 offers | free | robots.txt disallows AI crawlers; internally inconsistent |

Minimum fields per event: ISIN, board and PA dates, record date and last cum date, buyback
price, offer size, reserved shares, small and general entitlements, small shares validly
tendered, tender window, settlement date, route, tax regime by date, and a per-holder rounding
rule (fractions ignored; one-share preference for zero-entitlement holders).

### 8.4 Open offers and delisting

| Dataset | URL | Format | Coverage | Cost | Friction |
|---|---|---|---|---|---|
| SEBI open-offer statistics (PRIMARY) | [monthly page, e.g. May 2024](https://www.sebi.gov.in/statistics/open-offers/may2024.html) | HTML table | per month | free | no acceptance data |
| SEBI takeover filings (PRIMARY) | `https://www.sebi.gov.in/sebi_data/commondocs/<mon-yyyy>/...`; index at [serveall](https://www.sebi.gov.in/takeover/serveall.html) (not opened) | PDF | per offer | free | one PDF per document; post-offer reports hold tendered and accepted counts |
| BSE and NSE corporate announcements (PRIMARY) | bseindia.com corporate filings; nsearchives.nseindia.com/corporate | PDF | all listed | free | session cookies; per-company search |
| Exchange delisted-company lists | BSE and NSE | not retrieved | not checked | free | URLs not tested |
| Law-firm summaries (UNVERIFIED) | [CAM 2020](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report); [Khaitan 2024](https://khaitanco.com/sites/default/files/2024-08/Voluntary%20Delisting%20Snapshot.pdf) | PDF/HTML | n=13 and n=16 | free | values in charts and images |

Minimum fields: event type; announcement (with time of day, for the first tradable bar), offer
opening and closing, outcome and payment dates; floor, indicative, offer, discovered and final
prices; promoter holding before and after; shares tendered and accepted; failure reason;
frequently-traded flag; daily prices from 90 sessions before to 60 after.

### 8.5 Index inclusion

| Dataset | URL | Format | Coverage | Cost | Friction |
|---|---|---|---|---|---|
| NSE Indices press releases (PRIMARY) | `https://niftyindices.com/Press_Release/ind_prsDDMMYYYY.pdf`, e.g. [10 Aug 2026](https://niftyindices.com/Press_Release/ind_prs10082026.pdf) | PDF | verified for the five reviews Sep 2024-Sep 2026; earlier by the same pattern (not verified) | free | must be parsed; no consolidated change history with announcement dates |
| Current constituents (PRIMARY) | [Nifty 50](https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv), [Next 50](https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv), [Nifty 100](https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv) | CSV | current only | free | no point-in-time history |
| Methodology documents (PRIMARY) | [NSE, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf); [BSE, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf) | PDF | current versions | free | older versions needed for rule changes since 2016 |
| Passive AUM (PRIMARY) | [Nifty Passive Insights, Jun 2026](https://niftyindices.com/Nifty_Passive_Insights/NiftyPassiveFundReport-June2026.pdf); [AMFI monthly note, Sep 2026](https://www.amfiindia.com/uploads/AMFI_Monthly_Note_September2026_554f6604b6.pdf) | PDF | monthly, 2026 issues seen | free | guessed URLs for later months returned HTML |
| Sensex change notices | BSE | not located | n/a | n/a | URL pattern unknown |

Not found: free point-in-time constituent history for any of the four indices, historical
free-float (IWF) files needed to rebuild rankings before announcements.

### 8.6 Factor indices and funds

| Dataset | URL | Format | Coverage | Cost | Friction |
|---|---|---|---|---|---|
| NSE Indices TRI history (PRIMARY) | [historical data](https://www.niftyindices.com/reports/historical-data); POST `/BackPage/getTotalReturnIndexString` | JSON | from each base date | free | undocumented; 365 days per request; session cookie; names via [IndexMapping.json](https://liveindexsa.niftyindices.com/assets/json/IndexMapping.json) |
| Factsheets (PRIMARY) | `https://www.niftyindices.com/Factsheet/<file>.pdf` | PDF | current month | free | base and launch dates, rebalancing frequency |
| AMFI NAV (PRIMARY) | [NAVAll.txt](https://www.amfiindia.com/spages/NAVAll.txt); history `https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=DD-Mon-YYYY&todt=DD-Mon-YYYY` | semicolon text | all schemes | free | history is per date range, about 1.2 MB a day |
| AMFI TER (PRIMARY) | [TER page](https://www.amfiindia.com/ter-of-mf-schemes); internal API `populate-te-rdata-revised` | XLSX | daily TER components | free | API undocumented |
| ETF snapshot (PRIMARY host, undocumented fields) | [ETF.json](https://liveindexsa.niftyindices.com/jsonfiles/ETF.json) | JSON | current only, 146 ETFs | free | no iNAV or bid-ask history |
| IIMA factor library (PRIMARY) | [IIMA](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/) | CSV | Oct 1993-Dec 2025 | free | cite Agarwalla, Jacob & Varma (2013) |
| api.mfapi.in (UNVERIFIED mirror) | `https://api.mfapi.in/mf/<code>` | JSON | full NAV history | free | slow; 3 of about 45 responses truncated; verify against AMFI |

### 8.7 Tax

Statute and gazette texts (PRIMARY, free PDF): [Income-tax Act 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf),
[Finance Act 2026](https://egazette.gov.in/WriteReadData/2026/271439.pdf),
[Memorandum](https://www.indiabudget.gov.in/doc/memo.pdf),
[NSE/FATAX/73524](https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf).
incometaxindia.gov.in returned HTTP 403 to scripted requests; e-Gazette worked.

## 9. Conflicts between sources, and how they were handled

Rule: on tax the tax research wins; otherwise the more primary source wins. Each conflict is
listed whether or not it changes a number.

| # | Conflict | Handling |
|---|---|---|
| 1 | The IPO research applied 20% STCG as one case; the tax research finds STCG up to Rs 4 lakh nil for a resident with no other income (s.196(2)) | Tax research used: nil-tax figures lead; 20% shown for reference only |
| 2 | 12% surcharge on the promoter buyback tax: read in the e-Gazette rates chapter by the buyback research, not found in a third-party copy by the tax research | Reported as unconfirmed (tax research); promoters only, no effect on this owner |
| 3 | Finance Act 2026 text: the tax research read a third-party gazette copy plus the e-Gazette corrigendum; the buyback research cites the e-Gazette PDF | Both cited; the clauses relied on agree |
| 4 | Dividend TDS threshold: buyback research marks Rs 5,000 to Rs 10,000 UNVERIFIED; tax research reads it in Finance Act 2025 s.57 | Tax research used (PRIMARY) |
| 5 | SME pre-open lower band: NSE floor -20% from 4 Aug 2025; SEBI's May 2026 paper describes a -90% to +90% dummy band | Unresolved; possibly BSE or the generic band |
| 6 | SME amendment notified 3 Mar (secondary) or 4 Mar 2025 (SEBI Oct 2026 paper); in force 8 Mar 2025 | In-force date used |
| 7 | SEBI press release number 36/2024 (PDF, NSE circular) vs 37/2024 (HTML header) | 36/2024 used |
| 8 | Retail quota cut 35% to 25%: dropped (SEBI memo) vs live (5paisa, Jan 2026) | SEBI memo used |
| 9 | Mainboard IPO counts: 2024 NSE 90, Prime 91, Trendlyne 92, Tapetide 93; 2018 Trendlyne 16 vs Tapetide 24 | Reported side by side; possible survivorship filter |
| 10 | TCS 2022 small AR 24% and 26% on one Chittorgarh page | Both shown, UNVERIFIED |
| 11 | Mindtree open offer "oversubscribed by 116%": 1.16x or 2.16x | 1.16x assumed, flagged |
| 12 | Vedanta post-failure fall reported as 10%, 20% and 24% | Range shown |
| 13 | Suresha et al. (2024): abstract says event-day CAAR significant; table shows t = 0.71 | Table used |
| 14 | Parthasarathy (2019): notice period "six weeks" and "four weeks" in different places; CCAR/OCAR column labels inconsistent | Table 1 values used as printed |
| 15 | PSU delisting amendment dated 1 Sep (secondary) or 3 Sep 2025 (SEBI consolidated text) | SEBI date used |
| 16 | Index-inclusion annual figure: the source notes multiply Rs 20,000 by each addition (Rs 900-2,600); additions in one review share a date | Recomputed per review (section 5.4); both shown |

## 10. What is unverified or missing, by candidate

**Mainboard IPO**
- No primary yearly listing-return series; 2016 and 2017 missing everywhere; yearly table is
  aggregator data.
- No per-IPO joint (P, r) for any period, so no true E[P x r]; the bucket P for two buckets is
  assumed; no allotment data for 2016-2018.
- The number of non-overlapping bid windows per year (N) was not counted.
- ICDR text for the Rs 10,000-15,000 minimum and the RII definition read only as reproductions;
  the mainboard one-PAN rejection circular, the UPI Rs 5 lakh circular and the 2012 call-auction
  circular number (01 or 02/2012) not confirmed.
- No data on listing-day auction depth or failures; no verifiable grey-market history.
- Broker-API support for IPO bids not researched; not needed, since applications stay manual
  (owner's decision, 2026-10-31).

**SME IPO**
- e-Gazette copy of GN/2025/233 not opened; Board minutes not checked.
- BSE's date for the +90% cap and whether BSE adopted the -20% floor.
- Whether exchanges ever raise SME lot sizes after price falls; lot size of migrated companies.
- Outcome of the 21 May 2026 and 14 Oct 2026 consultations (the latter closes 4 Nov 2026).
- No primary summary of SME listing returns after 2017; no peer-reviewed study after 2020;
  Arora & Singh magnitudes paywalled.

**Buybacks**
- The consolidated Buy-back Regulations and the 2023 and 2026 amendment gazettes were not read;
  open-market phase-out and reinstatement details are secondary.
- PAN clubbing for small-shareholder status not confirmed from an opened document.
- **No post-settlement price (Pu) for any primary-sourced event**, which decides the sign of the
  per-event result; no record-date-eve prices; Infosys 2025 record-date close not extracted.
- Small ARs for TCS 2017-2022, Wipro 2017, 2020, 2023 and 2026, Infosys 2017, Bajaj Auto 2024
  and 2026 and all small caps are secondary or missing; no complete 2022-2026 list.
- The AR a zero-entitlement holder actually receives is not published (category totals only).
- Whether the exchange transaction charge and DP charge apply to tender settlements, and broker
  tender fees; route (tender or open market) of the 25 filers since Apr 2026.
- Finance (No. 2) Act 2024 text not read; the pre-Oct 2024 regimes (s.115QA, s.10(34A)) are
  background only.

**Open offers and delisting**
- Post-offer reports for Mindtree, India Cements, NDTV, Ambuja and ACC not retrieved; no
  systematic table of open-offer spreads or acceptance ratios.
- The 13 Apr 2015 acquisition-window circular and the 16 Feb 2023 SAST master circular not read;
  the proration clause is from an offer letter, not the Regulations.
- No success rate for fixed-price (from 25 Sep 2024) or PSU delistings; failure drops are
  news-only; no complete list of 2016-2026 attempts with floor, indicative, discovered and
  pre-announcement prices; Apr 2024-Oct 2026 is thin.
- Vemula et al. CARs paywalled; no SSRN/IIM/ISB/NSE paper on RBB or open-offer outcomes found.

**Index inclusion**
- Sensex changes for Jun 2025, Dec 2025 and Jun 2026 rest on secondary sources; BSE notice URL
  pattern unknown.
- The closing-auction go-live date (3 Aug 2026) is secondary; no study of a closing-auction
  rebalance.
- No post-2016 study for the Nifty Next 50, Nifty 100 or Sensex; three papers read as abstracts
  only; Nifty 50 additions per year for 2017-2022 from a broker list.
- No point-in-time constituent history or historical free-float files; broker flow estimates and
  EPFO allocations unverified.

**Factor indices and funds**
- Fund survivorship: closed or merged factor funds are not in AMFI's live-scheme file.
- Exact fund inception dates (first AMFI NAV used); older ETF histories split-affected or
  truncated (ICICI Low Vol 30, ICICI Alpha Low-Vol 30, DSP Midcap150 Quality 50 ETF, Nippon and
  Kotak NV20).
- AMFI's disclosed tracking-difference file not found (TD here is this report's arithmetic);
  historical TERs over each window not collected; regular plans not covered.
- MF stamp duty (0.005%) and redemption STT (0.001%) unverified; no ETF iNAV or bid-ask history;
  ETF.json field meanings undocumented.
- Methodology changes after launch not checked; cross-index correlation not estimated; the
  literature search hit a usage limit; BSE factor indices not covered.

**Tax**
- CBDT Circular 13/2025 and the 3 Sep 2025 corrigenda to the Income-tax Act 2025 not read; ITR
  forms for tax year 2026-27 not located.
- Shortfall order between STCG and LTCG, and the old-regime rebate against s.196 tax, are
  readings of the text, not rulings.
- Primary SEBI or depository text on minor-account restrictions not located.
- Whether frequent CNC trading could be treated as business income, and whether CBDT Circular
  6/2016 continues under the 2025 Act, not researched.
- Advance-tax instalment and interest rules under the 2025 Act not read.

**Cross-cutting**
- Stamp duty, NSE transaction charge, SEBI fee and DP charge come from `config/costs.yaml` and
  were not re-verified this phase (STT was).
- The age of the account holder is not known to this report; every nil-tax figure assumes an
  adult.

Status: literature only. No decision recorded; the owner decides what, if anything, to
pre-register as strategy 5 or later.
