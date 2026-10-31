# Open offers (SEBI SAST) and voluntary delisting offers in India as possible edges for a Rs 20,000 holder, 2016-2026

Prepared 2026-10-31. These are research notes only. No backtest was run and no statistic was computed from raw price data. Arithmetic on published figures is shown with its formula and inputs. Nothing here is a trading recommendation.

Tags used on each finding:
- **PRIMARY** means the source is SEBI, NSE, BSE, an Income Tax Department or e-Gazette page, a letter of offer or post-offer report, a peer-reviewed journal, or an SSRN/IIM/ISB/NSE working paper.
- **UNVERIFIED (secondary)** means a law-firm note, a news report, a blog or an aggregator.
- Each data finding carries: publication date; period covered; sample size (n); whether it is in-sample or live; whether costs and taxes are included; and why the figure could be overstated.

Local copies of the main documents are in `C:/Users/Advik/AppData/Local/Temp/claude/C--Users-Advik-desktop-nse-algo/505a1726-172d-483b-ba01-281b0a6c0ca7/scratchpad/r4_offers/dl/`. They are: the consolidated Delisting Regulations (`delisting_regs_consol.pdf/.txt`), the consolidated SAST Regulations (`sast_consol.pdf/.txt`), the SEBI 2018 RBB discussion paper (`sebi_rbb_dp_2018.*`), the Cyril Amarchand Mangaldas 2020 delisting report (`cam_delisting_trends_2020.*`), the Khaitan 2024 snapshot (`khaitan_snapshot_2024.*`), the Vedanta post-offer announcement (`vedanta_post_offer_pa.*`), the RGF Capital Markets letter of offer 2026 (`rgf_loo_2026.*`), the Senthil Infotek pre-offer advertisement 2026 (`senthil_poa_2026.*`) and the NSE STT circular (`nse_stt_73524.pdf`). The cost and EV arithmetic script is `.../r4_offers/scripts/ev_calc.py`.

## 1. Rules for open offers under the SEBI (SAST) Regulations, 2011, as of 2026-10-31

### Takeaway
An open offer is triggered in two ways: by crossing 25% of voting rights, or, for a holder already at 25% or more, by buying more than 5% in one financial year. It must be for at least 26% of the shares. It is priced off pre-announcement data under Reg 8, and it is tendered through the stock-exchange acquisition window, so the 0.1% delivery STT applies on the sale. When more shares are tendered than the offer size, acceptance is proportionate. The consolidated text has no small-shareholder reservation or preference. The only small-holder feature is that the minimum lot is 1 share.

### Cited Findings
- **Version in force.** SEBI's consolidated SAST text is marked "[Amended upto December 5, 2025]". The page is titled "last amended on December 5, 2025". The newest substantive change is Reg 8(2)(e), w.e.f. 03.01.2026: the price for infrequently traded shares must now be set by "an independent registered valuer" instead of by "the acquirer and the manager to the open offer". — PRIMARY [SEBI consolidated SAST Regulations](https://www.sebi.gov.in/legal/regulations/dec-2025/securities-and-exchange-board-of-india-substantial-acquisition-of-shares-and-takeovers-regulations-2011-last-amended-on-december-5-2025-_98643.html) (PDF: https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf). A secondary search snippet gives the notification as SEBI/LAD-NRO/GN/2025/283 dated 3 Dec 2025 — UNVERIFIED [MSEI circular 10 Dec 2025](https://www.msei.in/SX-Content/Company-Circulars/2025/December/EXCHANGE-10-DEC-2025-SEBI-(SUBSTANTIAL-ACQUISITION-OF-SHARES-AND-TAKEOVERS)-(AMENDMENT)-REGULATIONS--2025.pdf).
- **Triggers.**
  - Reg 3(1): acquiring shares that take the holding with persons acting in concert (PACs) to "twenty-five per cent or more of the voting rights" requires a public announcement of an open offer.
  - Reg 3(2): a holder at 25% or more but below the maximum permissible non-public shareholding may not acquire "more than five per cent of the voting rights" in a financial year without an open offer. For FY2020-21 only, the limit was 10% for promoters acquiring through a preferential issue.
  - Reg 4: an acquisition of control triggers an open offer.
  - Reg 5: indirect acquisitions.
  - Reg 6: voluntary offers.
  - Source — PRIMARY [SEBI SAST consolidated text](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf), Reg 3-6.
- **Minimum size.** Reg 7(1): an offer under Reg 3 or 4 must be "for at least twenty six per cent of total shares", measured as of the tenth working day after the tendering period closes. Reg 7(2): a voluntary offer under Reg 6 must be for at least an additional 10%. The Reg 7(4) proviso, w.e.f. 6-12-2021, lets an acquirer that has stated upfront it will keep the listing scale down the underlying agreement proportionately instead of exceeding the maximum non-public shareholding. — PRIMARY [SAST text](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf).
- **Offer price formula (Reg 8(2), direct acquisitions).** The price is the highest of:
  - (a) the highest negotiated price under the agreement that triggered the offer;
  - (b) the VWAP paid by the acquirer and PACs in the 52 weeks before the public announcement;
  - (c) the highest price paid by them in the 26 weeks before;
  - (d) the 60-trading-day VWAP before the public announcement on the exchange with the most volume, if the shares are frequently traded. A proviso added w.e.f. 9-11-2022 disapplies (d) for change-of-control PSU disinvestments;
  - (e) for infrequently traded shares, a value set by an independent registered valuer (from 03.01.2026);
  - (f) the Reg 8(5) value for indirect acquisitions.
  - "Frequently traded" (Reg 2(1)(j)) means turnover in the preceding 12 calendar months of at least 10% of the total shares.
  - Source — PRIMARY [SAST text](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf).
- **Timelines (Reg 16, 18, 21).**
  - Reg 16(1): the draft letter of offer is filed within 5 working days of the detailed public statement (DPS).
  - Reg 18(4): upward price revisions are allowed until 1 working day before the tendering period. This was 3 working days before 11-09-2018.
  - Reg 18(6) proviso: the acquirer may not buy or sell from 3 working days before the tendering period until it ends.
  - Reg 18(6A), w.e.f. 24-03-2015: tendering and settlement go "through the stock exchange mechanism as specified by the Board".
  - Reg 18(8): the tendering period starts within 12 working days of receiving SEBI's comments and stays open 10 working days.
  - Reg 18(9): tendered shares cannot be withdrawn during the tendering period.
  - Reg 18(10) and 21(2): payment is due within 10 working days of the close.
  - Source — PRIMARY [SAST text](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf).
- **Delay interest, example.** In the RGF Capital Markets offer (2026), SEBI's letter of 16 Jun 2026 granted an extension because statutory approvals were pending. It directed the acquirers to pay 10% p.a. interest under Reg 18(11)/(11A) for the delay. — PRIMARY [RGF Capital Markets letter of offer, Oct 2026](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf).
- **Proration when tenders exceed the offer size.** The standard letter-of-offer clause reads: "accepted on a proportionate basis in consultation with the Manager to the Offer, taking care to ensure that the basis of acceptance is decided in a fair and equitable manner and does not result in non-marketable lots, provided that the acquisition ... shall not be less than the minimum marketable lot, or the entire holding if it is less than the marketable lot. The marketable lot ... shall be 1 (One)". It adds: "there is no assurance that all Equity Shares tendered ... will be accepted". — PRIMARY [RGF Capital Markets LoF](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf). I did not find this proration rule in the consolidated SAST Regulations themselves (searched for "proportionate", "proportional", "fair and equitable"). It appears to come from the letter-of-offer format and SEBI's tender-offer circulars.
- **No small-shareholder reservation.** A text search of the consolidated SAST Regulations, amended to 5 Dec 2025, found no "small shareholder" provision. This matches your belief. Buybacks are different: they have a small-shareholder reservation, which I did not re-verify in this pass. — PRIMARY (negative search) [SAST text](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf).
- **Stock-exchange "acquisition window".** SEBI's circular CIR/CFD/POLICYCELL/1/2015 of 13 Apr 2015 created a separate acquisition window on exchanges with nationwide terminals for tender offers in takeovers, buybacks and delistings. One summary says it applies to public announcements from 1 Jul 2015. — PRIMARY page [SEBI circular 13 Apr 2015](https://www.sebi.gov.in/legal/circulars/apr-2015/mechanism-for-acquisition-of-shares-through-stock-exchange-pursuant-to-tender-offers-under-takeovers-buy-back-and-delisting_29579.html). I read only the listing, not the full text. The 1 Jul 2015 date and the carry-forward into SEBI's 16 Feb 2023 SAST master circular come from UNVERIFIED summaries [taxtmi](https://www.taxmanagementindia.com/web/tmi_blog_details.asp?id=545879) and [enterslice](https://enterslice.com/learning/sebis-master-circular-on-takeover-regulations/). A 2026 example is the BSE notice "Opening of Offer to Buy – Acquisition Window (Takeover) of Simandhar Impex Limited", 16 Apr 2026 — UNVERIFIED index [rhnvrm circulars mirror](https://rhnvrm.github.io/stock-market-circulars/circulars/bse/2026/bse-2026-04-16-f02361c9dc969cb3-opening-of-offer-to-buy-acquisition-window-takeover-of-simandhar-impex-limited/).
- **STT on tendered shares.** NSE circular NSE/FATAX/73524 of 31 Mar 2026 gives the rates from 1 Apr 2026. The Finance Act 2026 left delivery equity STT unchanged: 0.1% on purchase (purchaser) and 0.1% on sale (seller), where the trade is on a recognised exchange and settled by delivery. Only F&O rates changed. — PRIMARY [NSE circular 73524](https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf). A 2026 letter of offer confirms tenders go through the exchange and that "STT will be levied on and collected by a domestic stock exchange on which the Equity Shares are sold". — PRIMARY [RGF LoF](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf). Before 2015, open-offer sales were off-market and did not attract STT. — UNVERIFIED [Business Standard "Open offers are more taxing"](https://www.business-standard.com/amp/article/pf/open-offers-are-more-taxing-112111600020_1.html).
- **Stale tax text in letters of offer.** The same RGF letter of offer, dated 2026, still says gains on listed shares held more than 12 months "will not be subject to capital gains tax in India if STT has been paid". That has been wrong since 2018. Letter-of-offer tax sections cannot be relied on. — PRIMARY [RGF LoF](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf). The letter also says the consideration "could be net of such costs, applicable taxes, charges and expenses (including brokerage)" charged by the selling broker.
- **Tax under the Income-tax Act, 2025, in force from tax year 2026-27.**
  - s.196 (formerly s.111A): short-term gains on STT-paid listed equity at 20%. Resident individuals can set the unused basic exemption against these gains.
  - s.198 (formerly s.112A): long-term gains at 12.5% on the amount above Rs 1,25,000.
  - Source — official domain, seen only as search snippets; direct fetch was blocked (HTTP 403) [ITD s.196](https://www.incometaxindia.gov.in/w/section-196-76), [ITD s.198](https://www.incometaxindia.gov.in/w/section-198-76). The section mapping 111A→196 and 112A→198 is also in UNVERIFIED [studycafe](https://studycafe.in/overview-of-new-capital-gains-tax-structure-under-income-tax-act-2025-416536.html).
  - Open-offer and delisting proceeds are capital gains, not deemed dividend; the deemed-dividend treatment applied only to buybacks from 1 Oct 2024. This is from general knowledge and was not re-verified here.

### Inferences
- The Reg 8 price is anchored to the 60-day VWAP before the announcement and to the acquirer's own purchase prices. So whether an offer price is above or below the market at tendering depends on what happened between the announcement and tendering, often 3 to 6 months. That gap is where a gain or loss arises.
- With a marketable lot of 1, a Rs 20,000 holder is prorated exactly like a large holder. There is no small-holder benefit like the one in buybacks.

### Gaps
- I did not read the full text of the 13 Apr 2015 circular, its later revisions (9 Dec 2016; the lien-marking circular of 13 Aug 2021) or the 16 Feb 2023 SAST master circular. The proration clause should be confirmed in the master circular.
- I did not verify whether exchange transaction charges and the SEBI fee are levied on acquisition-window trades, or what tendering fee a broker charges. The cost model below assumes the normal delivery charges apply.
- I did not get the full gazette text of Income-tax Act 2025 ss.196/198, the current basic exemption limit, or the s.87A-equivalent rebate rules for special-rate gains.

## 2. Historical open offers 2016-2026: premiums, acceptance ratios and outcomes

### Takeaway
The published evidence is thin and mostly anecdotal. The only base-rate figure found is that "less than 5% of open offers launched since 2015" were fully subscribed, an ET compilation reported second-hand and UNVERIFIED. Large-cap cases fit the expected pattern. When the offer price was above market, offers were oversubscribed: Mindtree about 116%, India Cements about 110%, implying acceptance ratios of roughly 86-91%. When the offer price was below market, tenders were small: Ambuja about 0.14-1.35% of offer size, ACC about 8%. NDTV is the exception: 31.8% was tendered even though the offer was about 25% below market. I found no systematic table of premiums or acceptance ratios for 2016-2026.

### Cited Findings
- **Base rate.** "less than 5% open offers launched since 2015 in the country have been fully subscribed, data compiled by ET showed." Published Jan 2025; period 2015 to Jan 2025; n not given; in-sample; no costs or taxes. Overstatement risk: the definition of "fully subscribed" and the denominator are unknown, and the ET original was not seen. — UNVERIFIED (blog repost of ET) [gagashare repost](https://gagashare1.blogspot.com/2025/01/ultratech-cement-ultratechs-open-offer.html).
- **India Cements (UltraTech).**
  - Offer: Rs 390 per share, tendering 8-21 Jan 2025, reported subscription 110%, UltraTech's stake rising to 81.49%. Source as above — UNVERIFIED. UltraTech had bought 32.72% from the promoters at Rs 390, which triggered the offer — UNVERIFIED [Business Today 28 Jul 2024](https://www.businesstoday.in/amp/industry/infra/story/ultratech-to-purchase-3272-equity-in-india-cements-triggers-open-offer-at-rs-390-per-share-439145-2024-07-28).
  - Implied acceptance ratio = offer size / tendered = 1/1.10 ≈ 90.9%, if "110%" means tendered = 1.10 × offer size.
  - Time from the share purchase agreement (late Jul 2024) to tendering (Jan 2025) is about 5.5 months.
  - I did not obtain the post-offer report.
- **Mindtree (L&T).**
  - Offer: Rs 980 for up to 31%, tendering 17-28 Jun 2019 — UNVERIFIED [Business Standard 8 Jun 2019](https://www.business-standard.com/amp/article/companies/l-t-makes-rs-5-030-crore-open-offer-for-additional-31-stake-in-mindtree-119060800061_1.html).
  - Subscription was 108.09% on 27 Jun (5.54 crore shares) — UNVERIFIED [Business Standard 27 Jun 2019](https://www.business-standard.com/article/news-cm/mindtree-ends-higher-after-see-saw-trade-119062700920_1.html). It was "oversubscribed by 116%" at close, which is ambiguous: 1.16x or 2.16x — UNVERIFIED [Business Today](https://businesstoday.in/amp/bt-buzz/news/story/bt-buzz-taking-over-mindtree-what-lies-ahead-for-the-new-ceo-and-the-company-211809-2019-07-03).
  - Paid 2 Jul 2019; L&T stake 60.06% — UNVERIFIED [Business Standard](https://www.business-standard.com/amp/article/news-cm/l-t-rises-after-taking-control-of-mindtree-119070300411_1.html).
  - Implied acceptance ≈ 1/1.16 ≈ 86% if 1.16x. The pre-offer stake of 28.90% plus 31% is about 60%, which fits close to full use of the offer size.
  - This case is just before the 2016-2026 cut-off for the Mindtree-specific story but inside the period overall; kept as a large-cap reference.
- **Ambuja Cements and ACC (Adani, 2022), offer below market.**
  - Offer prices about Rs 385 (Ambuja) and Rs 2,300 (ACC). Ambuja closed around Rs 453-454 during the offer.
  - About 8% of the targeted ACC shares were tendered. Ambuja was about 1.35% by one count and about 0.14% by another.
  - Published Sep 2022; n=2; no costs. — UNVERIFIED [Business Standard 10 Sep 2022](https://www.business-standard.com/article/companies/ambuja-cements-acc-receive-lukewarm-response-from-public-shareholders-122091000362_1.html), [Outlook Business](https://www.outlookbusiness.com/news/adani-group-s-open-offer-for-acc-ambuja-cements-gets-lukewarm-response-from-investors-news-222413).
- **NDTV (Adani, closed 5 Dec 2022), offer below market but meaningful tender.**
  - Offer price Rs 294. The stock was at Rs 393.90 at close, about 34% above.
  - About 53.3 lakh shares were tendered against 1.67 crore sought, 31.79% of offer size. Of these, 39.3 lakh came from corporate investors and about 7 lakh from retail.
  - Source — UNVERIFIED [Business Today 5 Dec 2022](https://www.businesstoday.in/latest/corporate/story/adani-group-becomes-single-largest-shareholder-in-ndtv-with-375-355298-2022-12-05), [Free Press Journal](https://www.freepressjournal.in/business/adani-becomes-ndtvs-single-largest-stakeholder-despite-bagging-a-third-of-shares-targeted-through-open-offer).
  - Acceptance ratio for tenderers = 100%, since tenders were below offer size. Tenderers received less than the market price.
- **Micro-cap examples from 2026 (primary documents).**
  - Senthil Infotek: public announcement 8 Apr 2026, DPS 15 Apr 2026, letter of offer 8 Jun 2026. Offer Rs 8 against a negotiated price of Rs 5.50 and a valuer's fair value of Rs 7.48. The shares are infrequently traded on BSE. — PRIMARY [Senthil Infotek pre-offer advertisement](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Senthil%20Infotek%20Limited%20-%20POA_p.pdf).
  - RGF Capital Markets: offer price Rs 1.10, extension and interest ordered — PRIMARY [RGF LoF](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf).
  - These show that many offers are sub-Rs-10 illiquid micro-caps.
- **SEBI monthly table.** SEBI's monthly table of open offers lists, per offer: target, acquirers, offer schedule dates, offer size in shares, percentage, price, amount, objective (e.g. "Change in control", "Consolidation of holdings") and mode of payment. Example entries for Apr-May 2024: Ace Software Exports (consolidation), Pyxis Finvest (change in control), Cinerad Communications (change in control). It does not report acceptances. — PRIMARY [SEBI open-offer statistics, Apr-May 2024](https://www.sebi.gov.in/statistics/open-offers/may2024.html).
- **Event studies (sample sizes; returns not acceptance).** See section 5: Vemula, Gupta & Kashiramka (2020), n=96 offers 2011-2017; Nangia et al. (2011), n=187 offers 2007-10.

### Inferences
- Acceptance ratio, implied: when the offer price O is above the market price P, a ≈ offer size / shares tendered. In the two large-cap cases that is 0.86-0.91, if the subscription figures mean multiples. When O < P, rational holders sell in the market and tenders come mainly from holders with other motives, such as tax or corporate reasons (NDTV).
- If fewer than 5% of offers are fully subscribed (UNVERIFIED), the subset where O is meaningfully above P near tendering is small, probably a handful a year. This is an inference, not a count.

### Gaps
- I found no systematic, sourced dataset of open-offer premium against the pre-announcement price or against the market price at opening, or of acceptance ratios, for 2016-2026.
- Post-offer reports (Reg 18(12)) for Mindtree, India Cements, NDTV, Ambuja and ACC were not retrieved. Exact tendered and accepted figures should come from those reports on SEBI or BSE.
- Annual counts of open offers from SEBI annual reports or the Handbook of Statistics were not retrieved. The monthly SEBI pages exist but were not tallied.
- No source covered the Fortis Healthcare open offer (stalled by litigation since 2018), which would illustrate extreme lock-up risk.

## 3. Rules for delisting under the SEBI (Delisting of Equity Shares) Regulations, 2021, the Sept 2024 amendments and the Sept 2025 PSU amendment

### Takeaway
There are two routes. Reverse book building (RBB) succeeds if the acquirer reaches 90% at the discovered price. Fixed price, from 25 Sep 2024 and for frequently traded shares only, requires a price at least 15% above the floor and also needs 90%. A counter offer, RBB only, is allowed if the acquirer and tendered shares reach at least 75% and at least half the public shares are tendered. On success, every share tendered at or below the final price is paid that price: there is no proration. Holders who did not tender, or whose bids were not accepted, can tender at the same price for at least one year after delisting.

### Cited Findings
- **Notification dates.**
  - The 2021 Regulations were published in the Gazette on 10 Jun 2021 (No. SEBI/LAD-NRO/GN/2021-25).
  - Amended 3 Aug 2021 (Regulatory Sandbox); 25 Sep 2024 (Delisting Amendment, SEBI/LAD-NRO/GN/2024/206); 28 Nov 2024 (Attestation of Documents); and 3 Sep 2025 (Delisting Amendment 2025, SEBI/LAD-NRO/GN/2025/257).
  - Source — PRIMARY [SEBI consolidated Delisting Regulations, "Amended upto September 3, 2025"](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf), note on p.46; listing page [SEBI](https://www.sebi.gov.in/legal/regulations/sep-2025/securities-and-exchange-board-of-india-delisting-of-equity-shares-regulations-2021-last-amended-on-september-3-2025-_96540.html).
  - The 2024 changes apply to offers whose initial public announcement is on or after 25 Sep 2024 — UNVERIFIED [Nishith Desai](https://nishithdesai.com/NewsDetails/15146), [AZB](https://www.azbpartners.com/bank/amendments-to-sebi-delisting-of-equity-shares-regulations-2021/).
  - Earlier history: the 2009 Regulations were amended 24 Mar 2015 — PRIMARY [SEBI RBB discussion paper, Jul 2018](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2018/1532603980878.pdf). The counter-offer option came with the 24 Nov 2018 amendment — UNVERIFIED [CAM report 2020, fn 3](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report).
- **Floor price (Reg 19A, inserted w.e.f. 25.09.2024).** The floor is the highest of:
  - (i) the 52-week VWAP of the acquirer's and PACs' purchases;
  - (ii) the highest price they paid in 26 weeks;
  - (iii) the adjusted book value on consolidated financials, set by an independent registered valuer. This does not apply to PSUs. Formula: A+B+C+D−L, covering assets at book value, jewellery and art at market value, unquoted securities at fair value and quoted securities at exchange value, and immovable property at stamp-duty value, less liabilities;
  - (iv) the 60-trading-day VWAP, if frequently traded;
  - (v) a valuer's price, if infrequently traded.
  - Reference date (Reg 19A(2)): the date of the initial public announcement if made before market close, otherwise the next trading day. Before 2024, the floor came from SAST Reg 8, with the reference date being when the exchange had to be told of the board meeting (omitted Reg 20(2)-(3)).
  - Source — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
  - Note: the regulation text applies adjusted book value to all delistings except PSUs, not only to "certain companies".
- **Fixed price route (Reg 20A).** The fixed price must be "at least 15 percent more than the floor price calculated in terms of regulation 19A". It is available "only if the shares of the company are frequently traded". The acquirer must accept if its holding plus tendered shares "reaches 90 percent at the fixed delisting price". No counter offer exists on this route: Reg 22(4) is limited to RBB. — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
- **RBB discovered price (Schedule II cl.13-14).** The discovered price is "the price at which shares are accepted through eligible bids, that takes the shareholding of the acquirer ... to ninety per cent". The SEBI example: floor Rs 550, acquirer at 75%, 15 lakh shares needed; cumulative bids reach 15 lakh at Rs 600, so the discovered price is Rs 600. — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
  - Reg 21: success means reaching 90% of total issued shares. Shares are excluded from the base if held by DR custodians, employee benefit trusts or inactive holders (vanishing or struck-off companies, IEPF).
  - Reg 22(1)-(3): the acquirer is bound to accept if the discovered price equals the floor or the indicative price, or is below the indicative price. It may reject if the discovered price is above the indicative price.
  - Reg 20(4)-(6): an optional indicative price above the floor, which can be revised up before bidding. The acquirer may pay above the discovered price.
- **Counter offer (Reg 22(4)-(5), substituted w.e.f. 25.09.2024).** Allowed for RBB only if "(i) the post-offer shareholding of the acquirer, along with the shares tendered by public shareholders, is not less than seventy-five percent; and (ii) not less than fifty percent of the public shareholding has been tendered". It must be made within 2 working days of the bidding close. The price must be at least the higher of the VWAP of shares tendered in the RBB and the indicative price. The counter offer must still reach 90% (Reg 21). Before 2024, the counter-offer price had to be at least book value. — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf). That the earlier threshold was 90% comes from UNVERIFIED [Khaitan 2024 snapshot](https://khaitanco.com/sites/default/files/2024-08/Voluntary%20Delisting%20Snapshot.pdf).
- **Timelines and payment.**
  - Reg 17(1): bidding or tendering starts within 7 working days of the detailed public announcement and stays open 5 working days.
  - Reg 17(2): tendering goes through the stock exchange mechanism.
  - Reg 17(3)-(4): the outcome is announced within 2 hours of the close, and the public announcement within 2 working days.
  - Reg 24(1)(ii): when the price is above the floor or indicative price, payment is due within 5 working days of the public announcement. Reg 24(2) adds 10% p.a. interest if late.
  - Reg 25: the final application to the exchange is due within 5 working days of payment, and the exchange decides within 15 working days.
  - Shareholder approval needs public votes in favour of at least twice the votes against.
  - Reg 23(2)(c): after a failure, there is a 6-month bar on a new offer.
  - Schedule IV: the counter-offer timetable runs about 4-5 more weeks, with payment no later than 10 working days after the counter offer closes.
  - Source — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
- **On failure (Reg 23(2)).** Tendered shares are released on the outcome date, or on the date of the failure announcement if the acquirer rejected the price. The acquirer bears the costs. — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
- **Full acceptance for small holders on success.** Reg 24(1): "All the public shareholders, whose bids are accepted, shall be paid the discovered price or a higher price ... or fixed price". Bids at or below the discovered price are the eligible bids (Sch II cl.13). There is no proration, so a Rs 20,000 holder who bids at or below the final price is paid in full. — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
- **Exit window (Reg 26).** Remaining public shareholders "whose shares were either not accepted or were not tendered at all" can tender "for a minimum period of one year from the date of delisting" at "the same price at which the equity shares had been delisted". Payment comes from the escrow, which stays in place for at least one year. — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
- **Other routes added on 25.09.2024 and 03.09.2025.**
  - Delisting of investment holding companies by scheme of arrangement (Part E): the IHC distributes its listed shares in specie, pays cash for other assets, then reduces capital — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf); summary UNVERIFIED [Khaitan](https://khaitanco.com/sites/default/files/2024-08/Voluntary%20Delisting%20Snapshot.pdf).
  - PSUs (Part F, Reg 38B, w.e.f. 03.09.2025): for PSUs other than banks, NBFCs and insurers, where the acquirer plus other PSUs hold at least 90%. Delisting uses the fixed price process. The floor is the highest of the 52-week VWAP of purchases, the 26-week high and a joint valuation by two independent registered valuers. The delisting price must be "at least fifteen percent higher". — PRIMARY [Delisting Regs](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).
  - Secondary reports give the notification date as 1 Sep 2025, against the SEBI note's 3 Sep 2025 — UNVERIFIED [taxmann](https://www.taxmann.com/post/blog/analysis-sebi-psu-delisting-regulations-2025-fixed-price-framework-investor-protection).
- **No later amendment seen.** The SEBI-hosted consolidated PDF sits in an "aug-2026" upload folder but is still marked amended up to 3 Sep 2025. — PRIMARY [PDF](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf).

### Inferences
- Under RBB, the price a small holder receives is set by the marginal bidder at the 90% point, so holdouts and arbitrageurs drive the outcome, as SEBI itself noted in 2018. Under fixed price, the payoff on success is known in advance (at least 1.15 × floor). The only open question is whether 90% is reached, so the market price after the announcement should reflect the implied probability of success.
- The 2024 change moving the reference date to the announcement date removes the earlier gap, in which prices could rise between the board-meeting notice and the floor computation.

### Gaps
- I did not retrieve the SEBI circular giving the RBB and fixed-price operational procedure under the 2021 Regulations, for example on bid revision and withdrawal under the stock-exchange mechanism. Schedule II cl.12 disapplies cl.1-11 when the exchange mechanism is used.
- I did not verify the original pre-2024 counter-offer eligibility rule in primary text; the 90% figure is from Khaitan.

## 4. Historical delisting offers 2016-2026: attempts and successes, discovered price against floor, price falls after failures, time to payment

### Takeaway
Published success rates by sample:

| Sample | Period | Success |
|---|---|---|
| CAM 2020 | Oct 2019 to Oct 2020, resolved offers | 5 of 9 (≈56%) |
| CAM 2022 | about Jul 2021 to Jul 2022 | 6 of 16 (37.5%) |
| Khaitan 2024 | FY23-FY24 | 9 of 16 (56%) |

Among successes, the premium over the floor is often zero:
- SEBI 2018 (FY16-FY18, 15 successful delistings): 7 at 0%, 8 at 7.69-242.02%. Median 7.69%, mean 35.9% (my arithmetic).
- CAM 2020: 4 of 5 successes at 0%; Hexaware at 79.27%.

Failures were followed by reported one-day falls of about 10-24% (Vedanta, Linde India, INEOS Styrolution); these figures are from news only. Delisting took about 145 days on average from launch to completion (CAM 2020).

### Cited Findings
- **SEBI discussion paper, 26 Jul 2018.** FY2015-16 to FY2017-18; n=15 successful RBB delistings (failures not listed); in-sample; no costs or taxes. — PRIMARY [SEBI](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2018/1532603980878.pdf). Per-company floor → discovered price, with premium over floor:

  | Company | Floor (Rs) | Discovered (Rs) | Premium |
  |---|---|---|---|
  | Panasonic Appliances India | 167.65 | 380 | 126.66% |
  | Hella India Lighting | 52.39 | 52.39 | 0% |
  | Srinivasa Hatcheries | 110 | 130 | 18.18% |
  | Fulford (India) | 701.71 | 2,400 | 242.02% |
  | Regency Hospital | 48 | 52 | 8.33% |
  | Bombay Swadeshi Stores | 126 | 126 | 0% |
  | Essar Ports | 93.66 | 133 | 42.00% |
  | Essar Oil | 146.05 | 262.8 | 79.94% |
  | Arora Fibres | 10 | 10 | 0% |
  | Circuit Systems (India) | 13 | 14 | 7.69% |
  | Elf Trading & Chemicals | 2,500 | 2,500 | 0% |
  | Haryana Texprints (Overseas) | 3 | 3 | 0% |
  | Mewar Polytex | 56 | 56 | 0% |
  | Assam Petro-Chemicals | 76 | 76 | 0% |
  | Claris Lifesciences | 351.6 | 399.3 | 13.77% |

  - SEBI's summary: "Seven companies got delisted at the floor price (Premium being zero) and 8 companies got delisted at a premium ranging between 7.69% to 242.02%".
  - My arithmetic on these 15 values: median = 7.69%; mean = 538.59/15 = 35.91%. The mean is driven by Fulford, Panasonic and Essar Oil.
  - Overstatement risk: only successes are listed (survivorship); premiums are against the floor, not the post-announcement market price; many are tiny, illiquid companies.
- **Essar Oil follow-on payment.** Delisted at Rs 262.80. After the Rosneft sale, public shareholders received a further Rs 76.41 per share under an undertaking SEBI accepted. — UNVERIFIED [CAM 2020 report, citing a SEBI order of 6 Nov 2015 and ET](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report).
- **Cyril Amarchand Mangaldas report, updated 11 Nov 2020.** Offers announced from 1 Oct 2019 to 30 Oct 2020, small-company route excluded; n=13; in-sample; no costs. — UNVERIFIED (law firm) [CAM report](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report).
  - Outcomes: 5 successful, 3 unsuccessful, 1 rescinded, 4 ongoing.
  - Successes: Hexaware (promoter 62.08%, floor Rs 264.97, discovered Rs 475, +79.27%); Frontline Securities (floor = exit Rs 36.08); Vyapar Industries (Rs 43); Fomento Resorts (Rs 141); Ocean Agro (Rs 18.50).
  - Failures:
    - Brady & Morris: floor Rs 61.04, discovered Rs 750, +1,128.70%, rejected by the promoters.
    - Vedanta: promoter 50.13%, floor Rs 87.25, offer size about Rs 14,809 crore; insufficient shares tendered.
    - ABM International: rescinded.
    - UP Hotels: rejected by shareholders.
  - Ongoing at the time: Adani Power (floor Rs 33.82), Allcargo (Rs 92.58), Shyam Telecom (Rs 6.15), Xchanging (Rs 44.64). The table extraction was misaligned, so the floor-to-company mapping should be checked against the PDF.
  - Six of the 13 offers were below Rs 15 crore. "The average time taken for completing the delisting offers was 145 ... days from the launch of the delisting proposal", or "six to eight months" for large deals including preparation. No counter offer had been made by Oct 2020.
- **CAM blog, 12 Jul 2022.** About a one-year window; n=16 attempted; 6 successful. — UNVERIFIED [CAM blog](https://corporate.cyrilamarchandblogs.com/2022/07/analysis-of-recently-attempted-voluntary-delistings-india/).
  - Named successes: Amrit Corp, East India Securities, Genesis Exports, Solid Containers, Hexa Tradex.
  - Named failures:
    - Crimson Metal: board.
    - Allcargo Logistics: shareholder vote, Sep 2021.
    - Elcid Investments: shareholders.
    - Jindal Photo, Xchanging, Shyam Telecom: insufficient tender.
    - Universus Photo Imagings: discovered Rs 1,500 against indicative Rs 568, rejected.
- **Khaitan & Co snapshot, Aug 2024.** Offers attempted in FY2022-23 and FY2023-24 on BSE/NSE, excluding small-company, compulsory, scheme and winding-up cases; n=16; 9 successful, 7 failed. — UNVERIFIED (law firm) [Khaitan 2024](https://khaitanco.com/sites/default/files/2024-08/Voluntary%20Delisting%20Snapshot.pdf).
  - Failures: 4 below 90% in RBB; 1 RBB price rejected; 1 below 90% after a counter offer; 1 rejected by the board.
  - 3 cases had an unacceptable RBB price, and a counter offer was made in 2 of them.
  - "In 6 of the 8 delisting offers where 90% threshold was met during RBB, the RBB Price was equal to the Indicative Price."
  - 14 of 16 had promoter holdings of 70% or more.
  - Indicative price over floor (11 deals): 7 in 0-10%, 1 in 10-20%, 3 in 20-30%. Values read from the chart: 0.19, 1.21, 3.81, 24.43, 2.08, 1.44, 4.17, 3.23, 28.42, 23.61, 11.66.
  - RBB price over floor (11 deals): 3 in 0-10%, 3 in 10-20%, 2 in 20-30%, 3 above 30%. Values: 11.55, 99.01, 1.21, 3.81, 238.72, 24.43, 14.12, 2.08, 204.79, 11.66, 23.61. My arithmetic: median 14.12%. This includes RBB prices that were rejected.
  - Overstatement risk: values were read from charts; small sample; failures are mixed into the premium chart.
- **Vedanta, 2020.**
  - Bid period 5-9 Oct 2020 on BSE.
  - Post-offer public announcement of 10 Oct 2020: "The total number of Offer Shares validly tendered ... is 1,25,47,16,610", less than the minimum, so the offer "is deemed to have failed in terms of Regulation 19(1)" of the 2009 Regulations. Shares were returned and the listing continued. — PRIMARY (post-offer announcement, filed as Form 6-K) [Vedanta post-offer PA](https://vedantaresources.com/uploads/investor-sec-filings/Post-Offer-Public-Announcement-for-Delisting.pdf).
  - About 134.12 crore shares were needed; about 12.31 crore bids were unconfirmed; LIC (6.37%) bid at Rs 320 against a floor of about Rs 87.5. — UNVERIFIED [Moneylife](https://www.moneylife.in/article/vedanta-delisting-fails/61781.html), [Business Today](https://www.businesstoday.in/amp/latest/corporate/story/lic-upsets-vedanta-delisting-plans-shareholders-demand-unaffordable-275504-2020-10-12).
  - The stock fell 10% to Rs 109.90 in early trade on 12 Oct 2020; another headline says 20% — UNVERIFIED [Business Standard](https://www.business-standard.com/amp/article/markets/vedanta-tanks-10-on-failure-of-delisting-offer-120101200164_1.html), [Business Standard (20%)](https://www.business-standard.com/amp/article/markets/vedanta-s-failed-delisting-bid-comes-under-sebi-s-scanner-stock-falls-20-120101300057_1.html), [DT Next (24%)](https://www.dtnext.in/business/2020/10/12/vedanta-plummets-over-24-pc-after-delisting-fails).
- **Other failed delistings.**
  - Linde India, Jan 2019: hit the 20% lower circuit after the delisting failed — UNVERIFIED [Business Standard](https://www.business-standard.com/amp/article/markets/linde-india-slips-20-on-failure-of-delisting-plan-119012500239_1.html).
  - INEOS Styrolution India, Jul 2020: fell 20% after the promoter rejected the discovered price and made no counter offer — UNVERIFIED [Business Standard](https://www.business-standard.com/article/markets/ineos-styrolution-tanks-20-on-failure-of-delisting-offer-120072400412_1.html).
  - Ricoh India, Jun 2014, outside the period: down about 36% over two sessions — UNVERIFIED [Business Standard](https://www.business-standard.com/amp/article/markets/ricoh-india-dips-36-in-two-sessions-after-delisting-bid-fails-114061801168_1.html).
  - All are single-day or two-day moves from the pre-failure price, which usually already included an announcement run-up. None is measured against the pre-announcement price.
- **Counts per year (Prime Database via press).**
  - 16 delisting offers in 2022 and 8 to Oct 2023 — UNVERIFIED [Business Today, Nov 2023](https://www.businesstoday.in/amp/markets/market-commentary/story/sebi-set-to-amend-delisting-norms-soon-406045-2023-11-17).
  - 11 delisting offers in FY25, total spend Rs 70.98 crore, a five-year low — UNVERIFIED [Business Standard, 21 May 2025](https://www.business-standard.com/industry/news/fy25-marks-among-the-least-ever-spends-on-taking-companies-private-125052101883_1.html). Another source has 12 voluntary delistings in FY25, "lowest in over a decade" — UNVERIFIED [JSA](https://www.jsalaw.com/jsa_news/why-indian-promoters-are-no-longer-rushing-to-delist).
  - The value of delisting offers hit a record during the pandemic, 2020-21 — UNVERIFIED [Business Standard, Mar 2021](https://www.business-standard.com/article/markets/value-of-delisting-offers-at-record-high-amid-pandemic-surge-shows-data-121030500126_1.html).
  - Under the 2009 Regulations, 38 offers with 29 successful (76%); period unclear, pre-2015 — UNVERIFIED [Mondaq](https://mondaq.co.uk/india/securities/392770/delisting-made-easier-sebi-amends-the-delisting-norms).
- **Post-2024 fixed-price cases.** Elpro International: a fixed-price delisting at Rs 181.80 declared successful in 2026, with the promoter at 93.02% after the offer — UNVERIFIED [multibagg](https://www.multibagg.ai/market-pulse/articles/elpro-international-delisting-success-2026-cmssur0hf012n0zpjgiwr9zfw). I found no tally of fixed-price outcomes.
- **Fixing the RBB.** SEBI found that AstraZeneca Pharma India's promoter and Elliott-linked FIIs had pre-arranged the delisting price; SEBI order of 5 Jun 2020. In ECE Industries, the floor was miscomputed (simple average instead of VWAP) and was later topped up from Rs 204 to Rs 233.66. — UNVERIFIED summaries of SEBI orders [CAM 2020](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report).

### Inferences
- Rough pooled success rate across the three non-overlapping law-firm samples: (5+6+9)/(9+16+16) = 20/41 ≈ 49%. There may be some overlap between CAM 2022 and Khaitan around Apr-Jul 2022, and the samples define their universes differently. Treat this as a range of roughly 37-56%, not a point estimate.
- On success, a typical premium of 0-14% over the floor (medians) set against reported failure drops of 10-24% gives an asymmetric payoff. The mean premium is driven by a few outliers. See section 6.
- For a small holder, success means full acceptance at the final price (section 3). Failure means the shares come back at a lower market price.

### Gaps
- I found no complete, sourced list of every delisting attempt 2016-2026 with floor, indicative, discovered and pre-announcement prices and outcome. FY2018-19 and FY2019-20 (before Oct 2019) and Apr 2024 to Oct 2026 are particularly thin.
- Hexaware's pre-announcement market price and the Adani Power and Allcargo outcome prices were not retrieved.
- There is no primary source for the size of the price falls after failure; those are news only.

## 5. Academic and regulator studies

### Takeaway
I found no SSRN, IIM, ISB or NSE working paper on Indian reverse-book-building premiums. The regulator material, SEBI's 2018 discussion paper, is descriptive. The peer-reviewed open-offer work consists of event studies on announcement returns, not acceptance or premium outcomes. The only delisting event study found (Manchanda 2012) predates the period.

### Cited Findings
- **SEBI 2018 discussion paper, "Review of Reverse Book Building Process", 26 Jul 2018.** n=15 successful delistings FY16-18. It lists stakeholder concerns:
  - "arbitrageurs/speculators ... get into the company through the secondary market route and disproportionately influence the price discovery";
  - groups "bid at exorbitantly high prices", so "small shareholders are denied a chance to exit";
  - promoters may place stock with "friendly shareholders";
  - the floor ignores book value. One BSE case had a floor of Rs 510 against a book value of Rs 1,569.
  - It proposed a counter offer at not less than book value.
  - Source — PRIMARY [SEBI](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2018/1532603980878.pdf).
- **Vemula, Gupta & Kashiramka (2020), "Impact of open offer announcements on shareholders' wealth: evidence from India", International Journal of Financial Services Management (Inderscience).** 96 open offers, 2011-2017; event study; reports positive abnormal returns for targets, read as semi-strong inefficiency; splits the sample by motive and by success. The numeric CARs were not retrieved because the full text is paywalled (403). In-sample; no costs. — PRIMARY (peer-reviewed), abstract via search only [Inderscience](https://www.inderscienceonline.com/doi/abs/10.1504/IJFSM.2020.113165).
- **Nangia, Agrawal & Reddy (2011), "Open Offers and Shareholders Earnings – Evidence from India".** IIT Roorkee working paper on MPRA; 187 offers, 2007-10; significant negative post-announcement returns. Outside the period, and MPRA is not on the verified list. — UNVERIFIED [MPRA 60432](https://mpra.ub.uni-muenchen.de/60432/1/MPRA_paper_60432.pdf).
- **Manchanda (2012), "Price and Volume Effects of Voluntary Delisting in India", Indian Journal of Finance.** 41 voluntary delistings from NSE, BSE and CSE; NSE/BSE delistings reduced shareholder wealth by 12.01% over the event window. Snippet only; pre-2016. — PRIMARY (journal), not read in full [IJF](https://www.indianjournaloffinance.co.in/index.php/IJF/article/view/72421).
- **Verma & Mittal, International Journal of Applied Business and Economic Research.** The market takes time to absorb open-offer news. Date and sample not retrieved. — snippet only [serialsjournals](https://serialsjournals.com/abstract/22653_ch_12_f_-_paper_id_121_rajit.pdf).

### Inferences
- None of these studies reports net-of-cost returns to a buyer entering after the announcement and tendering, which is the quantity a Rs 20,000 holder needs.

### Gaps
- No SSRN, IIM, ISB or NSE paper on RBB outcomes, open-offer acceptance or merger-arbitrage returns in India was found with short queries. A targeted SSRN search ("delisting" "India" "reverse book building"; "open offer" "acceptance") is still needed.
- The CAR figures from Vemula et al. were not retrieved.

## 6. Expected value on Rs 20,000 from published figures, after costs and tax

### Takeaway
From published inputs only, the sign of the RBB delisting EV depends on two numbers: the premium you assume on success and the loss you assume on failure. With median premiums of 7.7-14% and a 20% failure loss, the net EV is about -1% to -9% at 37.5-56% success. With the outlier-driven mean premium of 35.9%, it is about +3.9% to +7.6%. A 20% failure loss needs about 60-73% success at median premiums to break even. Costs are small next to these swings: about 0.3% of capital per round trip at 3 bps slippage, about 0.8-1.2% at 50 bps. Tax at 20.8% matters only on gains. For open offers, the edge needs offer price above market and depends on the acceptance ratio. Only illustrative inputs are possible because no published spreads were found.

### Cited Findings (inputs)
- **Statutory delivery rates (re-verified).**
  - STT 0.1% buy and 0.1% sell, from 1 Apr 2026 — PRIMARY [NSE/FATAX/73524](https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf).
  - Stamp 0.015% on buy, NSE transaction charge 0.00297%, SEBI fee Rs 10 per crore and GST 18% are taken from the repo's `config/costs.yaml` (statutory block). They were not independently re-verified in this pass except STT.
  - DP Rs 9 + 18% GST = Rs 10.62 per scrip per sell day, from your broker assumption.
  - Slippage: 3 bps (the repo's base tier, meant for liquid stocks) and 50 bps (my stress assumption for illiquid small caps; not sourced).
- **Success rates.** 0.375 (CAM 2022), 0.556 (CAM 2020 resolved), 0.5625 (Khaitan 2024). Pooled about 0.49 — section 4.
- **Premium on success, over the floor.**
  - SEBI 2018: median 7.69%, mean 35.91%.
  - CAM 2020: median 0%, mean 15.85% = 79.27/5.
  - Khaitan RBB price: median 14.12%, including rejected prices.
  - Khaitan: in 6 of 8 offers that reached 90%, the RBB price equalled the indicative price.
- **Loss on failure.** 0%, -10% or -20%. The reported one-day falls after failure are 10-24% (news, section 4).
- **Tax.**
  - Zero, if the gain is within the unused basic exemption.
  - 20% short-term rate (s.196, formerly s.111A) plus 4% cess = 20.8%. Holding periods are below 12 months for these events.
  - Long-term gains at 12.5% apply only above Rs 1.25 lakh, so a Rs 20,000 position would pay none in practice.
  - The 4% cess is from general knowledge and was not re-verified.

### Formulas and arithmetic (script `scratchpad/r4_offers/scripts/ev_calc.py`)
- **Buy costs on value B.**
  - Formula: `0.001B + 0.00015B + 0.0000297B + B·10/1e7 + 0.18·(0.0000297B + B·10/1e7) + slip·B`.
  - For B = Rs 20,000 with no slippage: 20 + 3 + 0.594 + 0.02 + 0.11 = **Rs 23.72**.
- **Tender sell costs on value S.**
  - Formula: `0.001S + 0.0000297S + S·10/1e7 + GST + 9×1.18`.
  - For S = Rs 20,000: **Rs 31.34**. This assumes exchange charges apply in the acquisition window (unverified). There is no slippage because the price is fixed.
- **Round trip.**
  - Success path: **Rs 61.07 (0.305%)** at 3 bps entry slippage; **Rs 155.07 (0.775%)** at 50 bps.
  - Failure path, selling in the market 20% lower: **Rs 61.72 (0.309%)** at 3 bps per side; **Rs 230.92 (1.155%)** at 50 bps per side.
- **EV per rupee.**
  - Formula: `EV = p·[g − c_win]·(1−t if positive) + (1−p)·[L − c_lose]`.
  - Here p is the success probability, g the premium of the exit price over the entry price, L the failure move from entry, c the costs and t the tax.
  - Tax is applied only to positive outcomes, with no loss offset, which is conservative.
  - Entry is assumed at the floor price. That is optimistic, because the price usually moves above the floor after the announcement.

| Inputs (p, g, L) | slip 3 bps, tax 0 | slip 3 bps, tax 20.8% | slip 50 bps, tax 0 | slip 50 bps, tax 20.8% |
|---|---|---|---|---|
| 0.50, 7.69% (SEBI median), 0% | +3.52% | +2.75% | +2.82% | +2.10% |
| 0.50, 7.69%, -10% | -1.47% | -2.24% | -2.15% | -2.87% |
| 0.50, 7.69%, -20% | -6.47% | -7.23% | -7.12% | -7.84% |
| 0.50, 35.91% (SEBI mean), -20% | +7.63% | +3.93% | +6.97% | +3.32% |
| 0.375 (CAM22), 14.12% (Khaitan median), -20% | -7.52% | -8.59% | -8.22% | -9.26% |
| 0.5625 (Khaitan), 14.12%, -20% | -1.12% | -2.74% | -1.76% | -3.32% |
| 0.556 (CAM20), 15.85% (CAM20 mean), -20% | -0.38% | -2.18% | -1.02% | -2.76% |
| 0.5625, 0% (late entry at indicative price), -20% | -9.06% | -9.06% | -9.69% | -9.69% |

- **Break-even success probability** (3 bps slippage, no tax):

  | g | L | Break-even p |
  |---|---|---|
  | 7.69% | -20% | 0.734 |
  | 14.12% | -20% | 0.595 |
  | 35.91% | -20% | 0.363 |
  | 7.69% | -10% | 0.583 |
  | 15% (fixed-price minimum, if entry = floor) | -10% | 0.413 |
  | 15% | -20% | 0.580 |

- **Open offer with proration (illustrative; inputs are not published spreads).**
  - Formula: `gross = a·s + (1−a)·d`, where a is the acceptance ratio, s the spread `(O − P_entry)/P_entry` and d the move in unaccepted shares.
  - With a = 0.86 (Mindtree-implied) or 0.91 (India Cements-implied):
    - s = 5%, d = -10%: gross +2.90% or +3.65%.
    - s = 10%, d = -10%: +7.20% or +8.20%.
    - s = 5%, d = -20%: +1.50% or +2.75%.
  - Subtract about 0.31-0.78% costs, more if the unaccepted shares are sold in the market, then 20.8% tax on any positive net.
  - None of these spreads is a published figure.
- **Lock-up.**
  - Delisting: average 145 days from launch to completion (CAM 2020), and 6-8 months for large deals.
  - Open offers: Mindtree's agreement-to-payment period was about 3.5 months (public announcement in March 2019, paid 2 Jul 2019); India Cements was about 5.5 months to tendering. RGF Capital Markets was extended by SEBI.
  - Returns above are per event, not annualised.
- **Tradeable events per year (inference from published counts).**
  - About 8-16 delisting offers a year (Prime Database via press: 16 in 2022, 11-12 in FY25; Khaitan 16 over two years). At a 37-56% success rate, that is roughly 3-9 successes a year. Many are below Rs 15 crore in size and infrequently traded (CAM 2020: 6 of 13).
  - Open offers where the offer price is materially above market and acceptance is high look rare: "less than 5% fully subscribed" since 2015 (UNVERIFIED).

### Inferences
- **Entry at announcement versus later.**
  - Under RBB, the published premiums are measured against the floor (the undisturbed 60-day VWAP). A buyer after the announcement pays a price that already partly reflects the expected exit price. Khaitan's finding that in 6 of 8 successful cases the exit price equalled the indicative price suggests that a buyer near the indicative price earns about 0% on success. That buyer still carries the full loss on failure (the last row of the table).
  - Under fixed price, the payoff on success is fixed in advance. The relevant edge is whether the market's implied probability, `(P − P_fail)/(F − P_fail)`, understates the true success rate. No published fixed-price outcome sample exists to test that.
- **Costs are not the binding issue at Rs 20,000.** The DP charge of Rs 10.62 is about 0.05%. The swing between premium and failure-loss assumptions is 10-40 times larger than costs.

### Gaps
- No published figures for the market price on the day after the announcement, or at offer opening, relative to the final price. That is the quantity a late entrant earns, so a real EV needs price data, which this task did not allow.
- No published success rate for fixed-price delistings (from 25 Sep 2024) or PSU delistings (from 3 Sep 2025).
- Whether exchange charges apply in the acquisition window, and broker fees for tendering: not verified.
- Whether capital losses offset other gains for this holder: not modelled.

## 7. Why the published numbers could overstate a small holder's result

### Takeaway
Every published figure is in-sample, gross of costs and taxes, and measured from a reference price (floor or pre-announcement) that a buyer after the announcement cannot get. Several figures are survivorship-biased: SEBI 2018 lists only successful delistings. The rules have changed three times since 2018 (2018, 2021, 2024, plus the PSU route in 2025), so older base rates may not carry over.

### Cited Findings
- **Price jump on announcement.** The floor uses the undisturbed price (reference date = initial public announcement date, from 2024). Arbitrageurs buy after the announcement and influence price discovery — PRIMARY [SEBI 2018 DP](https://www.sebi.gov.in/sebi_data/attachdocs/jul-2018/1532603980878.pdf); reference date — PRIMARY [Delisting Regs Reg 19A(2)](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf). The RBB price often equals the indicative price (6 of 8) — UNVERIFIED [Khaitan](https://khaitanco.com/sites/default/files/2024-08/Voluntary%20Delisting%20Snapshot.pdf).
- **Failed delistings and sharp falls.** Vedanta, Linde, INEOS and Ricoh fell 10-36% after failure (section 4). Success rates in recent samples were 37.5-56%.
- **Holdouts and price rejection.** Brady & Morris was discovered at 1,128.7% over the floor and rejected; Universus Photo at Rs 1,500 against an indicative Rs 568, also rejected — UNVERIFIED [CAM 2020](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report), [CAM 2022](https://corporate.cyrilamarchandblogs.com/2022/07/analysis-of-recently-attempted-voluntary-delistings-india/).
- **Lock-up and approval delays.**
  - Delisting averages 145 days and can take 6-8 months (CAM).
  - Open offers can be extended by SEBI when approvals are pending (RGF 2026, 10% p.a. interest) — PRIMARY [RGF LoF](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf).
  - Prabhat Dairy's delisting was stalled by a SEBI-ordered forensic audit and SAT litigation (2019-2020) — UNVERIFIED [CAM 2020](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report).
  - Tendered open-offer shares cannot be withdrawn during the tendering period (Reg 18(9)) — PRIMARY [SAST](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf).
- **Proration.** Even oversubscribed open offers returned about 9-14% of tendered shares (India Cements, Mindtree implied), and those returned shares were exposed to the post-offer price.
- **Selection bias.** SEBI 2018 lists successes only. Law-firm samples exclude small-company routes and ongoing cases. News covers large or dramatic cases.
- **Liquidity and slippage.** Many targets are micro-caps: CAM 2020 found 6 of 13 delisting offers below Rs 15 crore; 2026 open-offer targets include sub-Rs-10 and infrequently traded shares (Senthil Rs 8, RGF Rs 1.10). The repo's 3 bps base slippage is meant for liquid F&O stocks and is likely too low for these.
- **Regulatory change and decay.**
  - Counter offers came in 2018. The 2021 Regulations replaced those of 2009.
  - In Sep 2024 SEBI added the fixed-price route, adjusted book value in the floor, the announcement-date reference date and the 75%/50% counter-offer rule.
  - In Sep 2025 it added PSU delisting. In Jan 2026 SAST valuations for infrequently traded shares moved to independent registered valuers.
  - Each change alters the payoff distribution. Pre-2024 RBB premium samples may not describe fixed-price outcomes.
- **Manipulation risk.** AstraZeneca pre-arrangement; ECE floor error; promoters funding third-party tenders in ECE — UNVERIFIED [CAM 2020](https://www.cyrilshroff.com/publications/voluntary-delisting-current-trends-a-detailed-report).
- **Tax text in offer documents can be wrong** (RGF 2026 LoF, section 1).

### Inferences
- Every figure here is in-sample and none is live; no source includes costs or taxes. The overstatement risk is highest for mean premiums (outlier-driven) and for any calculation that assumes entry at the floor price.

### Gaps
- No study measures the decay of delisting or open-offer spreads over 2016-2026.
- No data on how fully public-shareholder tenders participate under the fixed-price regime.

## 8. Downloadable datasets needed to backtest this

### Takeaway
Everything needed is public and free, but scattered. You would need announcement dates, offer, floor, indicative, discovered and fixed prices, outcomes, acceptance counts and daily prices. Building a clean event table means scraping SEBI and exchange PDFs. Paid databases (Prime, CMIE Prowess) would shorten the work but were not checked.

### Cited Findings
- **SEBI open-offer statistics.** Monthly HTML tables per financial year, e.g. `https://www.sebi.gov.in/statistics/open-offers/may2024.html`. They give target, acquirer, offer schedule dates, offer size, price, objective and payment mode. Free, but no acceptance data; scraping is moderate work. — PRIMARY [SEBI](https://www.sebi.gov.in/statistics/open-offers/may2024.html).
- **SEBI takeover filings** (public announcements, DPS, draft and final letters of offer, pre-offer and post-offer advertisements). PDFs under `https://www.sebi.gov.in/sebi_data/commondocs/<mon-yyyy>/...`, with an index at `https://www.sebi.gov.in/takeover/serveall.html` (seen in search, not opened). Free; high friction (one PDF per document, inconsistent formats); post-offer reports hold the tendered and accepted counts. — PRIMARY examples: [RGF LoF](https://www.sebi.gov.in/sebi_data/commondocs/oct-2026/RGF%20Capital%20Markets%20Limited_LOO_p.pdf), [Senthil pre-offer advertisement](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Senthil%20Infotek%20Limited%20-%20POA_p.pdf), [Hypersoft post-offer](https://www.sebi.gov.in/sebi_data/commondocs/oct-2025/Hypersoft%20Technologies%20Limited_POOA_p.pdf) (not opened).
- **BSE and NSE corporate announcements.** Delisting public announcements, outcome and post-offer announcements, and acquisition-window notices. BSE attachments are at `bseindia.com/xml-data/corpfiling/...`; NSE at `nsearchives.nseindia.com/corporate/...`. Free; PDF; announcement search UIs, with NSE's needing session cookies. — PRIMARY (example) [Vedanta post-offer PA](https://vedantaresources.com/uploads/investor-sec-filings/Post-Offer-Public-Announcement-for-Delisting.pdf).
- **NSE and BSE daily bhavcopy.** Daily OHLCV CSV/ZIP in the NSE archives (`nsearchives.nseindia.com`) and the BSE equivalent. Free; needed for pre-announcement, entry and post-failure prices; small caps may be on BSE only. — PRIMARY (domain); URLs not tested in this pass.
- **Exchange delisted-company lists** (BSE and NSE), with delisting reason and date. Free; used to find voluntary delistings. — not retrieved in this pass.
- **SEBI Delisting and SAST consolidated texts** (for rule-change dates): [Delisting](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1786948319926.pdf), [SAST](https://www.sebi.gov.in/sebi_data/attachdocs/aug-2026/1785911192198.pdf). Free PDFs.
- **Ready-made summaries** (secondary, cross-check only): SEBI 2018 DP table (n=15); CAM 2020 (n=13); CAM 2022 (n=16, case tables are images); Khaitan 2024 (n=16, values in charts). All free PDF or HTML. — links above.
- **Prime Database** (`primedatabase.com`), source of the press counts. Paid; coverage and format unverified.
- **CMIE Prowess.** Paid; not checked.
- **Unofficial circular mirror** (index only): [rhnvrm stock-market-circulars](https://rhnvrm.github.io/stock-market-circulars/tags/substantial-acquisition). Free HTML; UNVERIFIED.

### Inferences
- **Minimum fields for a backtest.**
  - Event id and type (open offer, RBB delisting, fixed-price delisting, PSU).
  - Dates: initial public announcement, DPS or detailed public announcement, letter of offer, tendering or bidding open and close, outcome, payment, final delisting.
  - Prices: floor, indicative, offer or fixed, discovered and final.
  - Holdings and counts: promoter holding before and after; offer size; shares tendered and accepted.
  - Outcome and failure reason; frequently-traded flag.
  - Daily prices from 90 trading days before the announcement to 60 after the outcome.
- **Look-ahead risk.** Trading-day timestamps of announcements must be used: whether before or after market close decides the first tradable bar, consistent with the repo's no-look-ahead rule. The Reg 19A(2) reference date makes the same distinction.

### Gaps
- Bhavcopy URL patterns and the delisted-company list URLs were not tested.
- Prime Database pricing and coverage were not checked.
- Whether SEBI's post-offer advertisements are complete for 2016-2026 is unknown.
