# Index inclusion and exclusion effects in India (Nifty 50, Nifty Next 50, Nifty 100, BSE Sensex), 2016-2026

Scope note: literature and documents only. No backtests, event studies or statistics on raw prices were run. All arithmetic is on published figures, with formula and inputs shown. "UNVERIFIED" marks any figure whose only source is a broker, news site, blog or other non-primary source. Downloads used for these notes are in `C:/Users/Advik/AppData/Local/Temp/claude/C--Users-Advik-desktop-nse-algo/505a1726-172d-483b-ba01-281b0a6c0ca7/scratchpad/r5_index/`.

## 1. How the indices are reviewed, when changes are announced and when they take effect

### Takeaway
The Nifty 50, Nifty Next 50 and Nifty 100 are reviewed twice a year on six-month average data to 31 January and 31 July. Changes take effect after the close of the last trading day before the end of March or September, with at least four weeks' notice. Over the last five reviews (Sep 2024 to Sep 2026), the gap from announcement to the last pre-effective close was 32 to 50 calendar days. The Sensex, now run by BSE Index Services Pvt Ltd (formerly Asia Index Pvt Ltd), is reviewed every six months on data to the end of April and October. Its changes take effect at the open on the Monday after the third Friday of June and December, also with four weeks' notice.

### Cited Findings
**NSE Indices methodology document** (source: "Methodology Document for Equity Indices", September 2026, version stamp 20260821)
- Broad market indices are "reviewed semi-annually based on data for six months ending January and July." — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- Nifty 50: "The replacement of stocks in Nifty 50 (if any) is implemented from the last trading day of March and September. In case of any replacement in the index, a four weeks' prior notice is given to the market participants." — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- Nifty 50 eligibility:
  - The stock must be a Nifty 100 constituent that is "available for trading in NSE's Futures & Options segment".
  - Trading frequency must be 100% over the last six months.
  - Average impact cost must be ≤0.50% for 90% of observations, for a Rs 10 crore portfolio.
  - Average free-float market cap must be "at least 1.5 times the average free-float market capitalization of the smallest constituent".
  - At most five companies may be added in a calendar year. This cap does not apply to exclusions for loss of eligibility (F&O, impact cost, trading frequency, mergers or demergers, delisting, BZ series, suspension, adverse regulatory orders). — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- Replacements outside the review cycle: an "additional index reconstitution" can be triggered by any of these.
  - Merger, demerger, delisting, or specific cases of capital restructuring. For capital restructuring or voluntary delisting, shareholder approval is the trigger.
  - Move to the BZ series, withdrawal of F&O trading permission, or suspension from trading.
  - Adverse regulatory findings. — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- Nifty 100 entry rules:
  - The stock must be in the Nifty 500, with an investible weight factor ≥0.10 (or the alternative float-cap test).
  - It is included if its average full market cap ranks in the top 90 AND it is in F&O (or its average daily turnover exceeds that of the 90th Nifty 100 stock).
  - It is excluded if its rank falls below 110.
  - The replacement pool is ranks 91-110, with non-F&O stocks excluded first.
  - From now on, non-F&O stocks are eligible only if they hit price bands on fewer than 20% of trading days. — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- Nifty Next 50 is "the balance 50 companies from Nifty 100 after excluding the Nifty 50 companies". Non-F&O stocks are capped at 10% combined and 4.5% each, rebalanced quarterly. Child indices use the latest parent (Nifty 100) composition, "whether announced or yet to be announced". — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- The Nifty 50 covers about 66% of NSE's float-adjusted market cap. It has been float-adjusted since 26 June 2009. — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- The Nifty 50 factsheet (dated 30 Oct 2026) restates three rules: cut-off dates of 31 January and 31 July, a minimum listing history of one month, and four weeks' prior notice. It quotes the impact-cost basket as Rs 100 million (= Rs 10 crore). — [Nifty 50 factsheet, Oct 2026](https://www.niftyindices.com/Factsheet/ind_nifty50.pdf)

**NSE Indices press releases** (announcement date → stated effective date; arithmetic is my own count of calendar days from announcement to the last pre-effective close, which is when index funds trade)
- 23 Aug 2024 → "effective from September 30, 2024 (close of September 27, 2024)": 35 days. Nifty 50: Trent and Bharat Electronics in; Divi's Labs and LTIMindtree out. Nifty 100: 5 in, 5 out. — [NSE Indices press release 23 Aug 2024](https://niftyindices.com/Press_Release/ind_prs23082024.pdf)
- 21 Feb 2025 → effective 28 Mar 2025 (close of 27 Mar 2025): 34 days. Nifty 50: Zomato and Jio Financial in; BPCL and Britannia out. Nifty Next 50: 7 in, 7 out. — [NSE Indices press release 21 Feb 2025](https://niftyindices.com/Press_Release/ind_prs21022025.pdf)
- 22 Aug 2025 → effective 30 Sep 2025 (close of 29 Sep 2025): 38 days. Nifty 50: InterGlobe Aviation and Max Healthcare in; Hero MotoCorp and IndusInd Bank out. Nifty 100: 5 in, 5 out. Nifty Next 50: 4 in, 4 out. — [NSE Indices press release 22 Aug 2025](https://niftyindices.com/Press_Release/ind_prs22082025.pdf)
- 23 Feb 2026 → effective 30 Mar 2026 (close of 27 Mar 2026): 32 days. Nifty 50: no change. Nifty 100 and Nifty Next 50: 6 in, 6 out each. — [NSE Indices press release 23 Feb 2026](https://niftyindices.com/Press_Release/ind_prs23022026.pdf)
- 10 Aug 2026 → effective 30 Sep 2026 (close of 29 Sep 2026): 50 days. Nifty 50: BSE Ltd in, Wipro out (Wipro moves to the Nifty Next 50). Nifty 100: 5 in, 5 out. Nifty Next 50: 5 in, 5 out. — [NSE Indices press release 10 Aug 2026](https://niftyindices.com/Press_Release/ind_prs10082026.pdf)
- Gap from cut-off to announcement (my count): 23, 21, 22, 23 and 10 days for the five reviews above. Inputs are the 31 Jan / 31 Jul cut-offs from the [methodology](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf) and the press-release dates above.
- Each press release prints the 6-month average free-float market cap of included stocks, excluded stocks and the "next two eligible companies" that missed the 1.5x test. For example, BSE Ltd was Rs 1,40,879 cr against Wipro's Rs 55,930 cr; the misses were TVS Motor (Rs 84,566 cr) and Divi's (Rs 82,930 cr). — [NSE Indices press release 10 Aug 2026](https://niftyindices.com/Press_Release/ind_prs10082026.pdf)
- NSE's F&O department re-circulates index changes shortly before they take effect. Circular NSE/FAOP/76591, dated 28 Sep 2026, refers back to the 10 Aug 2026 press release "w.e.f. September 30, 2026 (close of September 29, 2026)". — [NSE circular FAOP76591](https://nsearchives.nseindia.com/content/circulars/FAOP76591.pdf)
- Historical lead times:
  - For 2000-2018, Parthasarathy (2019) reports 7 to 33 days (mean about 25) between announcement and inclusion. NSE "normally announces ... after trading hours", so AD+1 is the first tradable day. — [Parthasarathy 2019, AJFA](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
  - Kumar (NSE working paper, data 1996-2003) states each revision then took "around six weeks". — [Kumar, NSE research paper](https://nsearchives.nseindia.com/content/research/comppaper90.pdf)

**BSE Sensex** (source: "BSE Indices Methodology", October 2026, BSE Index Services Pvt Ltd)
- Eligible universe:
  - Constituents of the BSE 100 with at least six months' listing at BSE.
  - The stock must have traded every day of the six-month reference period, and "Stock must have a derivative contract."
- Selection steps:
  1. Take the top 75 by average six-month float cap and the top 75 by total market cap.
  2. Drop stocks beyond 98% of cumulative annualized traded value.
  3. Drop stocks with less than 0.5% weight.
  4. The top 21 enter automatically. Existing constituents ranked 22-39 are kept first. Non-constituents ranked 22-30 are then preferred by sector under-representation.
- "All additions and deletions are made at the discretion of index committee." — [BSE Indices methodology, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf)
- Sensex, BSE 100, Sensex 50 and Sensex Next 50 are reviewed every six months. Changes take effect on the "Monday following the third Friday of June and December". The reference date is the last trading day of April and October. "Effective dates are at the market open and Reference dates are after the market close." — [BSE Indices methodology, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf)
- "To comply with SEBI regulations for indices with derivative contracts, index composition changes due to scheduled rebalancings are announced four weeks in advance." This applies to the BSE SENSEX, BSE 100, SENSEX 50, SENSEX Next 50, BANKEX and Focused IT. Pro-forma files are provided daily ahead of each rebalancing. Corporate-event changes are "typically announced one to five business days prior to the implementation date." — [BSE Indices methodology, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf)
- Maintainer: current methodology documents are issued by "BSE Index Services Pvt. Ltd."; April 2024 versions were issued by "Asia Index Private Limited". — [BSE Indices methodology, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf); [April 2024 Asia Index BSE AllCap methodology](https://www.bseindices.com/Downloads/Methodology_Doc/BSE_Allcap_Methodology.pdf)
- BSE completed its purchase of S&P Dow Jones Indices' entire stake in Asia Index Pvt Ltd around 31 May 2024 (UNVERIFIED, news). — [Business Standard, 31 May 2024](https://www.business-standard.com/markets/news/bse-completes-acquisition-of-s-p-dow-jones-indices-entire-stake-in-asia-index-124053101907_1.html)
- Recent Sensex changes (all UNVERIFIED, secondary):
  - June 2025: Trent and Bharat Electronics in; Nestle India and IndusInd Bank out. — [NiftyTrader](https://www.niftytrader.in/markets/?p=10694)
  - December 2025: IndiGo replaced Tata Motors Passenger Vehicles from 22 Dec 2025. — [Wikipedia mirror, List of BSE SENSEX companies](https://wiki.krisyotam.com/content/wikipedia_en_all_nopic_2026-03/List_of_BSE_SENSEX_companies)
  - June 2026: core Sensex reported unchanged. — [Indian Masterminds](https://indianmasterminds.com/news/bse-index-reconstitution-2026-ashok-leyland-paytm-cg-power-205863/)
  - Calendar check: the methodology rule gives effective dates of Monday 23 Jun 2025, 22 Dec 2025 and 22 Jun 2026.

### Inferences
- The NSE's "four weeks" is a minimum, not the typical gap. Recent gaps were about 4.5 to 7 weeks, or 24-36 weekdays before holidays.
- The Sep 2026 review was announced unusually early: 10 days after cut-off and 50 days before taking effect. That gives a longer window for both arbitrage and noise.
- Nifty 50 additions must be F&O stocks, and Sensex constituents need a derivative contract. Since the closing auction exists only for F&O stocks, nearly every event in scope is priced at the close through that auction. See section 6.
- For the Nifty, every rule input is published (cut-off dates, the 1.5x rule, F&O status). For the Sensex, a discretionary committee and a sector-preference step make outcomes less mechanical.

### Gaps
- I did not find a single machine-readable NSE archive of all index changes with announcement and effective dates. They have to be rebuilt from individual press-release PDFs (URL pattern in section 7).
- I did not read primary BSE index-change notices for June 2025, December 2025 or June 2026. Those Sensex changes rest on secondary sources.
- I did not locate the SEBI circular behind BSE's "four weeks in advance" rule.
- I did not extract the NSE methodology's cap on Nifty 100 replacements per review. The extracted table was garbled, and Mar 2026 had 6 changes.

## 2. Published evidence on abnormal returns for added and deleted stocks

### Takeaway
The Indian evidence is thin, all in-sample, and none of it nets out costs or taxes. The best-documented study, Parthasarathy (2019), finds a mean market-adjusted abnormal return of about +2.8% for Nifty 50 additions in 2010-2018 (N=27), measured from AD+2 to the effective date. About 0.8% of that reverses within three days. That is down from about +5.5% in 2000-2009 (N=23). The only study covering 2020-2024 (Marisetty 2025; N=13 additions; weaker journal and benchmark) reports a significantly negative abnormal return over the 20 days before the effective date. I found no post-2016 study of the Nifty Next 50, the Nifty 100 or the Sensex on its own.

### Cited Findings
For every study below: event study, in-sample, no out-of-sample test, no transaction costs or taxes unless stated.

**Parthasarathy (2019), "Does Nifty Index Inclusion (still) Convey Information?"**
- Publication: Asian Journal of Finance & Accounting 11(1):307-, published 1 Jun 2019.
- Sample: Nifty additions only, Apr 2000 to Mar 2018. Of 71 additions, 50 form the "clean" sample after dropping spin-offs, M&A, name changes, IPOs with less than one year of history, and cases with fewer than 3 days between AD and ED.
- Sub-periods: N=23 (2000-2009) and N=27 (2010-2018). There are 30 unique announcement dates.
- Benchmark: three abnormal-return models against the CNX 500. MCAR (market-adjusted), OCAR (market model adjusted for high pre-event alpha), and CCAR (control sample of three eligible stocks that were not added).
- No mention of transaction costs. — [Parthasarathy 2019](https://ajfa.macrothink.org/index.php/ajfa/article/view/14866); [PDF](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
- Mean MCAR, Table 1. Brackets give the 2000-2009 / 2010-2018 sub-periods.

  | Window | Full sample (N=50) | 2000-09 / 2010-18 |
  |---|---|---|
  | Anticipation, AD-10..AD | -0.70% (not significant) | -0.90% / -0.51% |
  | AD+1 | +1.49%** | +2.32%** / +1.24%** |
  | Run-up, AD+2..ED-2 | +2.30%* | +3.66%* / +1.21% (n.s.) |
  | ED window, ED-1..ED | +1.67%** | +1.81%** / +1.56%** |
  | Pressure release, ED+1..ED+3 | -1.50%** | -2.03%* / -0.78% (n.s.) |
  | AD+1..AD+40 | +3.50%* | +5.06%** / +2.18% |
  | AD+1..AD+60 | +4.19%** | +6.28%** / +2.43% |

  Control-sample CCAR for 2010-2018: run-up +2.10%, ED window +1.55%, release -1.11%.
  ** = significant at 5%, * = at 10%, n.s. = not significant. — [Parthasarathy 2019, PDF p.316](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
- Author's conclusion: "the index effect has diminished in the second period." Abnormal volume is largely insignificant except in the ED window (mean volume ratio 2.30). Evidence for the price-pressure hypothesis is called "limited at best." — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
- Internal inconsistencies to note:
  - The paper says NSE gives "a notice period of six weeks" in one place and "four weeks" in another.
  - The text calls the 2010-2018 AD40/AD60 values (2.57% and 3.64%) CCARs, but in Table 1 those numbers sit in the OCAR column. — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)

**Marisetty (2025), "Market reaction to index reconstitutions: Evidence from NSE NIFTY additions and deletions"**
- Publication: SSRN, posted Oct 2025; also International Journal of Research in Finance and Management 8(2):712-721, 2025.
- Sample: Nifty 50, 2010-2024. Of 92 events (46 additions, 46 deletions), 81 were analysed. Sub-periods are 2010-14, 2015-19 and 2020-24.
- Method: market model against the Nifty 50, with a 252-day estimation window and a -20..+20 event window. No costs. — [SSRN 5642110](https://doi.org/10.2139/ssrn.5642110); [journal PDF](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf)
- The reported "event-day CAAR" is cumulative from day -20 to day 0 (confirmed by Table 6).
- Additions, CAAR(-20..ED) on the effective date:

  | Period | N | CAAR | p |
  |---|---|---|---|
  | 2010-14 | 15 | -0.72% | 0.70 |
  | 2015-19 | 16 | +1.39% | 0.55 |
  | 2020-24 | 13 | -4.84% | 0.036 |

- Additions, CAAR(-20..AD) on the announcement date:

  | Period | CAAR | p |
  |---|---|---|
  | 2010-14 | -0.57% | n.s. |
  | 2015-19 | -0.37% | n.s. |
  | 2020-24 | +4.86% | 0.12 |

- Deletions:
  - CAAR(-20..ED): -1.32% (2010-14), +2.66% (2015-19), +2.62% (2020-24, p=0.11).
  - Effective-day AAR: +1.18% (2015-19, p=0.09) and +1.44% (2020-24, p=0.009). — [Marisetty 2025, Tables 4-5](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf)

**Kumar, "Price and Volume Effects of S&P CNX Nifty Index Reorganizations"** (NSE research paper, IIM Kozhikode author; data 1996-2003; publication year not printed in the extracted text)
- Sample: 36 Nifty and 62 Jr Nifty changes initially, fewer in the final samples.
- Method: market model; announcement dates inferred from circular dates.
- Findings:
  - No significant announcement-day effect.
  - Nifty effective-day effect "averaging around 1.47% which is subsequently reversed by ninth day".
  - Similar results for deletions.
  - No effect for the Jr Nifty, and no abnormal volume. — [Kumar, NSE](https://nsearchives.nseindia.com/content/research/comppaper90.pdf)

**Joshipura & Janakiramanan (2015)** (Afro-Asian Journal of Finance and Accounting 5(1):21-36; sample period not given in the abstract)
- Inclusions: "no significant abnormal positive returns ... surrounding announcement day". Positive abnormal returns appear on the effective day "but fails to sustain".
- Exclusions: a significant negative effect through the announcement window, plus a non-sustained negative effect near the effective day.
- Volume rises on the effective day, attributed to index funds and ETFs. — [IDEAS/RePEc abstract](https://ideas.repec.org/a/ids/afasfa/v5y2015i1p21-36.html)

**Chhatwani (2020), "Price and Volume Effects of NIFTY 50 Index Reorganization"** (Journal of Commerce & Accounting Research 9(4); Nifty 50, 2000-2016; abstract only, full text paywalled)
- Positive abnormal returns after inclusion and negative after exclusion.
- "abnormal returns get reversed for index included stocks in 60 days after the inclusion, while the excluded stocks yield negative returns only in the first ten days".
- After 60 to 240 days, excluded stocks "yield around 4% to 7% positive abnormal returns". — [Publishing India abstract](https://publishingindia.com/archive/jcar/price-and-volume-effects-of-nifty-50-index-reorganization)
- A search-engine summary attributed "+1.8% over 10 days for inclusions, -1.9% over two days for exclusions" to this paper. I could not confirm it against the paper (UNVERIFIED).

**Ahluwalia, Mishra & Tripathy (2020)** (Journal of Multinational Financial Management vol. 55; Nifty 50 and Nifty Next 50, 2002-2016)
- Institutional ownership rises for additions and falls for deletions, which "exhibit positive (negative) stock returns on an average".
- Foreign institutional investors react faster than mutual funds and banks.
- The authors read index rebalancing as "an information event". No magnitudes in the abstract. — [IDEAS/RePEc](https://ideas.repec.org/a/eee/mulfin/v55y2020ics1042444x20300049.html); [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S1042444X20300049)

**Selvam, Indhumathi & Lydia (2012)** (Global Business Review 13(1):39-50; CNX Nifty, Jan 2005 to Dec 2009)
- Sample: 24 additions and 24 deletions, of which 28 companies were used.
- Method: market model against the Nifty itself.
- Conclusion: "no permanent effects", and that it is "impossible to earn any excess returns".
- The reported figures are not plausible. Announcement-day MCAR is -26.2% for inclusions and the ranges run to -81%. They should not be used. — [PDF copy](https://smartjournalbms.org/docs/scopus/Impact%20on%20Stock%20Price%20by%20the%20Inclusion%20to%20and%20Exclusion%20from%20CNX%20nifty%20Index.pdf)

**Other studies, cited only inside the papers above (originals not read)**
- Parthasarathy (2010): Nifty additions 1999-2010, permanent abnormal return of about 4.90%.
- Rahman & Rajib (2014): Nifty 2008-2010, short-term effects only.
- Chakrabarti et al. (2005): MSCI India additions 1998-2000, about +4.17% permanent.
- All three are as cited by [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123).
- Vijaya (2002), the only Sensex study found: "weak permanent price effect for deletions", but with "assumed announcement dates as BSE did not maintain a record". — as cited by [Kumar, NSE](https://nsearchives.nseindia.com/content/research/comppaper90.pdf)

**Firm performance rather than prices**
- An IUP Journal of Applied Finance study of CNX Nifty revisions, 1998-2011, reports lower EPS/ROA/ROE changes for inclusions than for matched peers, and the reverse for exclusions. — [IUP abstract](https://www.iupindia.in/1707/Applied%20Finance/CNX_NIFTY_Index_Reorganizations.html)

**Low-quality source to avoid**
- Ray (2025), IJAR 13(10): a CAGR comparison of 44 Nifty 50 additions 2010-2024, with no event study.
- Its reference list misattributes known papers. For example, it credits Parthasarathy's AJFA 2019 paper to "Mehta, D., & Singh, R." and the Selvam et al. paper to "Kumar, P., & Rao, S. K.".
- Excluded from the evidence. — [IJAR PDF](https://www.journalijar.com/uploads/2025/10/690dc3421f326_IJAR-54563.pdf)

**US background**
- Greenwood & Sammon, "The Disappearing Index Effect" (SSRN 4294297): S&P 500 deletion abnormal returns over [-20,-1] fell from -14.7% in the 1990s to -2.4% in the 2010s. Figure taken from a search snippet; full paper not read. — [HBS/SSRN PDF](https://www.hbs.edu/ris/download.aspx?name=ssrn-4294297.pdf)

### Inferences
- Parthasarathy is the only Indian source that breaks out windows a trader could actually use. Its gross 2010-2018 mean from AD+2 to ED is 1.21% + 1.56% = 2.77% (MCAR), 3.65% (CCAR) or 3.12% (OCAR).
  - The run-up component alone is not significant.
  - Only the two-day ED window is significant at 5%.
- Marisetty's 2020-2024 additions run the other way: -4.84% over the 20 days before the effective date. Two reasons to treat this cautiously:
  - The benchmark is the Nifty 50, which contains the stock after inclusion.
  - The 252-day estimation window can absorb the pre-addition run-up, which biases abnormal returns downward. That is the Lynch-Mendenhall issue Parthasarathy corrects for.
- With N=10-16 per sub-period, none of the post-2015 estimates can establish whether an effect exists.
- On reversal after the effective date, every source agrees there is at least a partial reversal for additions:
  - Kumar: full reversal by day 9.
  - Parthasarathy: -1.5% within ED+1..ED+3 for the full sample.
  - Chhatwani: reversal within 60 days.
- Deletions show an initial negative reaction, then a recovery around or after the effective date (Chhatwani; Marisetty 2015-2024).

### Gaps
- No peer-reviewed or working-paper study found for:
  - The Nifty Next 50 or Nifty 100 as separate event sets after 2016. Ahluwalia et al. cover the Nifty Next 50 only through 2016.
  - Sensex additions or deletions after 2002.
- No Indian study reports net-of-cost or after-tax results, or uses out-of-sample validation.
- Full texts not read: Joshipura & Janakiramanan (paywalled), Chhatwani (paywalled), Ahluwalia et al. (paywalled), and Rahman & Rajib.

## 3. Growth of passive AUM and whether it has changed the size of the effect

### Takeaway
Passive money tracking the Nifty 50 grew from about Rs 400 crore in 2003 to about Rs 84,000 crore in September 2019, and to about Rs 5 lakh crore by May 2026 (my sum of NSE scheme-level figures). Over the same period, the measured Indian inclusion effect shrank in the only like-for-like comparison (Parthasarathy, 2000-09 vs 2010-18). I found no Indian study that tests whether passive AUM drives the size of inclusion effects.

### Cited Findings
- **2003:** passive funds "amounting to approximately Rs 400 Cr. tracking Nifty in 2003". — [Kumar, NSE research paper](https://nsearchives.nseindia.com/content/research/comppaper90.pdf)
- **Sep 2019 to Nov 2021** (source: "Nifty50 Journey of 25 Years", NSE Indices, Jan 2022; data from CMOTS):
  - ETFs on the Nifty 50 held Rs 1,63,287 cr at 30 Nov 2021, up from Rs 79,566 cr at 30 Sep 2019 ("~39% CAGR").
  - Nifty 50 index funds held Rs 16,105 cr, up from Rs 4,515 cr ("~80% CAGR").
  - 16 Nifty 50 ETFs made up 52% of domestic equity ETF AUM. — [NSE Indices, 25 Years of Nifty50](https://nsearchives.nseindia.com/content/indices/25_Years_Journey_of_Nifty50_2022-01.pdf)
- **May 2026** (source: "Nifty Passive Insights", June 2026 issue, data as of May 2026):
  - Total Indian passive AUM was Rs 14.77 lakh crore, with net outflows of Rs 402 cr that month.
  - Equity ETF assets were Rs 7.81 lakh crore. — [NSE Nifty Passive Insights, June 2026](https://niftyindices.com/Nifty_Passive_Insights/NiftyPassiveFundReport-June2026.pdf)
  - Largest equity ETFs:

    | ETF | AUM (Rs cr) |
    |---|---|
    | SBI Nifty 50 ETF | 2,05,278 |
    | SBI BSE Sensex ETF | 1,15,687 |
    | UTI Nifty 50 ETF | 68,963 |
    | Nippon India ETF Nifty 50 BeES | 62,890 |
    | UTI BSE Sensex ETF | 53,052 |

  - Nifty Next 50 ETFs totalled Rs 8,044 cr. Nifty 50 index funds include UTI (Rs 27,827 cr), HDFC (Rs 23,155 cr), ICICI Pru (Rs 16,443 cr) and SBI (Rs 13,283 cr). — [NSE Nifty Passive Insights, June 2026, pp.23, 47-48, 54](https://niftyindices.com/Nifty_Passive_Insights/NiftyPassiveFundReport-June2026.pdf)
- **My arithmetic on those May 2026 scheme-level figures** (the group-total rows did not extract cleanly):

  | Group | How computed | Total (Rs cr) |
  |---|---|---|
  | Nifty 50 ETFs | sum of 21 listed schemes | 3,98,376 |
  | Nifty 50 index funds | sum of 26 listed schemes | 1,00,200 |
  | **Nifty 50 passive** | ETFs + index funds | **≈4,98,576 (≈Rs 5.0 lakh cr)** |
  | Nifty Next 50 | 8,044 ETF + 24,800 index funds (sum of 11 listed schemes) | ≈32,844 |
  | Sensex, two largest ETFs only | 1,15,687 + 53,052 | 1,68,739 |

  Growth of Nifty 50 passive AUM, Sep 2019 to May 2026: 4,98,576 / (79,566 + 4,515) = 5.9x. Inputs: [NSE Passive Insights June 2026](https://niftyindices.com/Nifty_Passive_Insights/NiftyPassiveFundReport-June2026.pdf); [NSE 25 Years of Nifty50](https://nsearchives.nseindia.com/content/indices/25_Years_Journey_of_Nifty50_2022-01.pdf).
- **September 2026:** passive AUM "declined 4.6% on-month to Rs 14.70 lakh crore". Equity ETFs took net inflows of Rs 9,960 cr. — [AMFI Monthly Note, Sep 2026](https://www.amfiindia.com/uploads/AMFI_Monthly_Note_September2026_554f6604b6.pdf)
- **EPFO (all UNVERIFIED, secondary):**
  - In August 2015 it decided to put 5% of incremental deposits into Nifty and Sensex ETFs, later raised to up to 15%. — [Business Standard, Aug 2015](https://www.business-standard.com/amp/article/markets/epfo-makes-stock-market-debut-through-sbi-mf-115080600584_1.html)
  - It moved from a 75:25 Nifty:Sensex split to an equal split in 2019. — [Business Standard, Aug 2019](https://www.business-standard.com/article/economy-policy/epfo-to-allocate-equity-investments-equally-in-nifty-and-sensex-firms-119082201471_1.html)
  - This is consistent with SBI and UTI Sensex ETFs ranking among the largest equity ETFs (primary data above).
- **Broker flow estimates per event (all UNVERIFIED, secondary):**
  - Sep 2026: Nuvama estimated about $741M passive inflow into BSE Ltd and about $246M outflow from Wipro. — [5paisa, citing Nuvama](https://www.5paisa.com/news/nifty-rejig-bse-to-replace-wipro-in-nifty-50-as-per-a-nuvama-report); [Swastika](https://www.swastika.co.in/blog/wipro-share-price-and-nifty-50-reconstitution-bse-flows-free-float-shifts-and-re)
  - Feb 2024: $271M for Shriram Finance. — [Business Today, 29 Feb 2024](https://www.businesstoday.in/markets/stocks/story/shriram-finance-niftys-latest-entry-to-attract-271-million-inflows-jio-financial-adani-power-shares-to-gain-big-419415-2024-02-29)
  - Feb 2025: about $910M for Zomato and JFS combined. — [Equentis](https://www.equentis.com/blog/zomato-jfs-to-enter-nifty-910m-inflows/)
  - Feb 2025 Nifty 50 / Nifty Next 50 rebalance: "cumulative churn of over Rs 22,000 crore". — [Business Standard, 23 Feb 2025](https://www.business-standard.com/amp/markets/news/epicentre-of-change-nifty-indices-rebalance-to-set-the-ground-moving-125022300427_1.html)
- **My arithmetic on the UNVERIFIED Nuvama BSE figure:** $741M × 88 INR/USD (my assumed rate) / Rs 1,40,879 cr average free-float market cap ([NSE press release](https://niftyindices.com/Press_Release/ind_prs10082026.pdf)) ≈ 4.6% of BSE's free float traded by passives at one close.
- **Decay within India:** Parthasarathy's 2010-18 abnormal returns are about half the 2000-09 values (AD+1..AD+60 MCAR 2.43% vs 6.28%). The author reads this as a diminished effect, with the 2010-18 period supporting downward-sloping demand curves rather than information. — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
- **MSCI 2024 (UNVERIFIED, secondary):** seven Indian MSCI additions rose 3.6% between announcement and effective date, against 4.1% for the MSCI India index. — [Advisor Perspectives, Sep 2024](https://www.advisorperspectives.com/commentaries/2024/09/19/msci-index-rebalances-chinas-weight-decline)

### Inferences
- Passive Nifty 50 AUM grew about 6x from 2019 to 2026, while the published abnormal returns did not grow. Parthasarathy's numbers fell between sub-periods, and Marisetty's 2020-24 additions are negative into the effective date.
- Two explanations fit, and the data cannot separate them:
  - Faster arbitrage and broker front-running absorb the forced demand before the passive trade.
  - The samples are too small to detect any trend (N=13-27).
- In the US, the effect also shrank as passive share rose (Greenwood & Sammon), so a larger passive base is not evidence of a larger tradable effect.
- Flow per event is skewed toward the Nifty 50, which has about Rs 5 lakh cr passive against about Rs 0.33 lakh cr for the Nifty Next 50.
  - A stock moving from the Nifty Next 50 into the Nifty 50 gets large net buying.
  - A stock dropping from the Nifty 50 into the Nifty Next 50 (e.g. Wipro, Sep 2026) gets net selling even though it is "added" to the Nifty Next 50.

### Gaps
- No primary 2016 baseline for Nifty 50, Sensex or Nifty Next 50 passive AUM was found. The NSE series in hand starts Sep 2019.
- No primary figure for the Nifty 50's total free-float market cap, so passive ownership as a share of free float could not be computed from primary data.
- No Indian study regresses inclusion-effect size on passive AUM or passive share.
- EPFO allocations and broker flow estimates are unverified.

## 4. Predictability before the announcement, and pre-announcement drift

### Takeaway
Nifty changes follow published rules: six-month average free-float market cap to a known cut-off date, a 1.5x threshold, and F&O eligibility. Brokers routinely publish the likely changes before NSE announces them. The cut-off-to-announcement gap was 10-23 days in recent reviews. The only Indian test of drift before the announcement (AD-10..AD) finds none, but no study measures returns from the cut-off date, or from the first broker prediction, to the announcement.

### Cited Findings
- **Rules are mechanical.** Inclusion requires an average free-float market cap "at least 1.5 times" the smallest constituent's, over six months to the January/July cut-off, plus F&O availability. — [NSE Indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf)
- **Press releases reveal near-misses.** Each one publishes the average free-float market cap of the next two eligible stocks that missed the 1.5x test. That tells the market who sits close to the line for the next review. Example: InterGlobe Aviation and HAL missed in Feb 2025, and InterGlobe was included in Aug 2025. — [NSE press release 21 Feb 2025](https://niftyindices.com/Press_Release/ind_prs21022025.pdf); [NSE press release 22 Aug 2025](https://niftyindices.com/Press_Release/ind_prs22082025.pdf)
- **Brokers predict ahead of announcements (UNVERIFIED as to timing and accuracy, secondary; outcomes checked against NSE releases):**
  - On announcement day, 22 Aug 2025, a news report said IndiGo and Max Healthcare were "set for Nifty entry; announcement due post-market". Both were included. — [Business Standard, 22 Aug 2025](https://www.business-standard.com/amp/markets/news/nse-nifty-rejig-indigo-max-healthcare-set-for-nifty-entry-announcement-due-post-market-125082200518_1.html); [NSE press release 22 Aug 2025](https://niftyindices.com/Press_Release/ind_prs22082025.pdf)
  - On 8 Feb 2026, a report said "Tata Motors CV and HDFC AMC seen entering Nifty Next 50". Both (TMCV, HDFCAMC) were in the 23 Feb 2026 release. — [Business Standard, 8 Feb 2026](https://www.business-standard.com/markets/news/tata-motors-cv-and-hdfc-amc-seen-entering-nifty-next-50-shows-data-126020800360_1.html); [NSE press release 23 Feb 2026](https://niftyindices.com/Press_Release/ind_prs23022026.pdf)
  - Nuvama also publishes Sensex predictions, e.g. "Hindalco or Shriram Finance may enter Sensex in June". — [Kotak Neo](https://www.kotakneo.com/news/market-news/hindalco-shriram-finance-sensex-june-rejig-trent-exclusion-2026/)
- **No drift before the announcement in 2000-2018.** The anticipation window AD-10..AD has a mean MCAR of -0.70% for the full sample and -0.51% for 2010-18, both insignificant. 48-52% of stocks are positive. — [Parthasarathy 2019, Table 1](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
- **Signs of a priced-in announcement in 2020-24 (weak):** additions' CAAR over (-20..AD) was +4.86% (N=13, p=0.12). — [Marisetty 2025](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf)

### Inferences
- The data that decides a Nifty review is fixed at the cut-off date, 10-23 days before NSE announces. Brokers publish lists from public data.
  - Much of the "announcement" news can be known in advance.
  - For anyone trading after the announcement, that should shrink the AD+1 jump. It may also shrink the AD→ED run-up if arbitrageurs are already positioned.
- The rising (-20..AD) CAAR for 2020-24 and the falling (-20..ED) CAAR are what you would expect if early positioning were absorbing the effect. The samples are too small to show this; it is a hypothesis only.
- The Sensex's committee discretion and sector preference make it less mechanical to predict than the Nifty.

### Gaps
- No study measures returns from the cut-off date (or the first broker prediction) to the announcement, for any of the four indices.
- The accuracy record of broker predictions is not documented in any primary source.
- NSE does not appear to publish a ranked list of 6-month average free-float market caps. Reconstructing one needs free-float (IWF) and share data; see section 7.

## 5. What is left for a Rs 20,000 long-only delivery (CNC) trader after costs and tax

### Takeaway
A Rs 20,000 delivery round trip costs about 27.5 bps in statutory and DP charges. Adding 3-10 bps of slippage per side brings it to 33.5-47.5 bps. Published 2010-2018 mean abnormal returns for Nifty 50 additions from AD+2 to ED (2.8-3.7%) would be about 2.3-3.3% after those costs, or about 1.8-2.7% after 20% STCG. That is only a paper figure: it is in-sample, from 27 events, mostly not significant, and contradicted for 2020-2024. A long-only trader also earns the raw return, not the abnormal return. The market risk over the holding period (about 4-5% one-sigma over 4-7 weeks) is larger than the mean effect. There are roughly 2-4 Nifty 50 additions a year.

### Cited Findings
**Rates used**
- Delivery STT is 0.1% on purchase and 0.1% on sale, "No Change" from 1 Apr 2026. — [NSE circular NSE/FATAX/73524, 31 Mar 2026](https://nsearchives.nseindia.com/content/circulars/FATAX73524.pdf)
- From the repo's `config/costs.yaml` (statutory "as of Oct 2026", shoonya preset):
  - Stamp duty 0.015% on buy.
  - NSE transaction charge 0.00297% on both legs.
  - SEBI fee Rs 10 per crore on both legs.
  - GST 18% on transaction charge, SEBI fee and DP charge.
  - DP charge Rs 9 per scrip per sell day, before GST.
  - Zero delivery brokerage.
  - Slippage tiers of 3/6/10 bps per side. — [costs.yaml in repo](file:///C:/Users/Advik/desktop/nse-algo/config/costs.yaml)
- Not re-verified against a primary source in this pass: stamp duty, transaction charge, SEBI fee and DP charge.

**Round-trip cost formula, buying and selling at the same value V**
- Buy = V × (0.001 + 0.00015 + 0.0000297 + 0.000001) + 0.18 × V × (0.0000297 + 0.000001)
- Sell = V × (0.001 + 0.0000297 + 0.000001) + 9 + 0.18 × (V × (0.0000297 + 0.000001) + 9)
- Slippage = 2 × V × s

| V (Rs) | Statutory + DP | +3 bps/side | +6 bps/side | +10 bps/side |
|---|---|---|---|---|
| 20,000 | Rs 55.07 (27.53 bps) | Rs 67.07 (33.53 bps) | Rs 79.07 (39.53 bps) | Rs 95.07 (47.53 bps) |
| 10,000 | Rs 32.84 (32.84 bps) | 38.84 bps | 44.84 bps | 52.84 bps |

- At V = Rs 20,000: buy-side charges are Rs 23.72 and sell-side Rs 31.34.
- The Rs 10,000 row covers splitting capital across two simultaneous additions. The DP charge, Rs 10.62 including GST, is fixed per scrip.

**Net of published mean abnormal returns** (Parthasarathy 2019, 2010-2018 additions, N=27)
- Strategy assumed: buy at the close of AD+1, sell at the close of ED. This captures run-up AD+2..ED-2 plus ED window ED-1..ED. Net = gross − cost; after tax = net × (1 − 0.20).

| Model | Gross | Net at 33.5 bps | Net at 47.5 bps | After 20% STCG | Net Rs on 20k |
|---|---|---|---|---|---|
| MCAR | 1.21 + 1.56 = 2.77% | 2.43% | 2.29% | 1.95% / 1.84% | 487 / 459 |
| CCAR | 2.10 + 1.55 = 3.65% | 3.31% | 3.17% | 2.65% / 2.54% | 663 / 635 |
| OCAR | 1.52 + 1.60 = 3.12% | 2.78% | 2.64% | 2.23% / 2.12% | 557 / 529 |

- Inputs come from [Parthasarathy 2019, Table 1](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123).
- Holding through ED+3 instead drops the gross 2010-18 MCAR to 2.77 − 0.78 = 1.99%.
- Full-sample (2000-2018, N=50) gross AD+2..ED is 2.30 + 1.67 = 3.97% (MCAR).
- **Marisetty 2020-2024 additions** (N=13): CAAR(-20..ED) is -4.84%. Net of 33.5-47.5 bps, that is about -5.2% to -5.3%. — [Marisetty 2025](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf)

**Market risk over the hold**
- The Nifty 50's 1-year annualised standard deviation is 13.88%. — [Nifty 50 factsheet, Oct 2026](https://www.niftyindices.com/Factsheet/ind_nifty50.pdf)
- Scaled by √(days/250): about 3.9% over 20 trading days and about 5.2% over 35 trading days.

**Tax (UNVERIFIED, secondary)**
- Section 87A rebate is not available against STCG under s.111A from FY 2025-26.
- A resident can still set unused basic exemption against s.111A STCG. The new-regime basic exemption is Rs 4 lakh for FY 2025-26. — [TaxGuru](https://taxguru.in/income-tax/section-87a-rebate-stcg-111a-tax-planning-fy-2025-26.html)
- The 20% STCG rate is taken from the brief and was not re-verified here.

**Events per year**
- Nifty 50 additions per calendar year (scheduled and ad hoc):
  - From an UNVERIFIED secondary list: 2017: 6; 2018: 4; 2019: 2; 2020: 4 (incl. ad hoc Shree Cement in Mar 2020 and HDFC Life in Jul 2020); 2021: 1; 2022: 2. — [Angel One, 12 Jul 2023](https://www.angelone.in/news/share-market/analysis-of-nifty50-rebalancing-since-2017)
  - From NSE releases (primary): Sep 2024: 2; Mar 2025: 2; Sep 2025: 2; Mar 2026: 0; Sep 2026: 1. — [NSE PR Aug 2024](https://niftyindices.com/Press_Release/ind_prs23082024.pdf); [Feb 2025](https://niftyindices.com/Press_Release/ind_prs21022025.pdf); [Aug 2025](https://niftyindices.com/Press_Release/ind_prs22082025.pdf); [Feb 2026](https://niftyindices.com/Press_Release/ind_prs23022026.pdf); [Aug 2026](https://niftyindices.com/Press_Release/ind_prs10082026.pdf)
- Nifty 100 additions per review: 5 (Sep 2024), 5 (Sep 2025), 6 (Mar 2026), 5 (Sep 2026).
- Nifty Next 50 additions per review: 7 (Mar 2025), 4 (Sep 2025), 6 (Mar 2026), 5 (Sep 2026). They overlap almost fully with Nifty 100 entrants, plus Nifty 50 drop-downs.
- Sensex: about 1-2 additions per review (UNVERIFIED, secondary; see section 1).

**Short side**
- Intraday MIS short selling is the only short available. The project rules require MIS positions to be flat by 14:50 IST.
- The closing auction for F&O stocks starts after 15:15. — [repo CLAUDE.md market facts](file:///C:/Users/Advik/desktop/nse-algo/CLAUDE.md); [NSE SOP CMTR73362](https://nsearchives.nseindia.com/content/circulars/CMTR73362.pdf)

### Inferences
- The abnormal return in these studies is relative to the CNX 500 or the Nifty. A cash-only, long-only trader cannot hedge the market (no F&O), so the realised P&L is the raw stock return.
  - The ~4-5% one-sigma market move over the hold is bigger than the 2.8-3.7% mean.
  - Results per event will be dominated by market direction.
  - At roughly 2-4 Nifty 50 additions a year, a sample large enough to judge the effect would take many years.
- Illustrative upper bound only: 2-4 events × about Rs 460-660 net each (2010-18 means, before tax) ≈ Rs 900-2,600 a year on Rs 20,000.
  - It rests on in-sample means whose run-up part is not significant.
  - Marisetty's 2020-24 estimate has the opposite sign.
- Moving down to Nifty 100 / Nifty Next 50 additions adds about 10-12 events a year. But Nifty Next 50 passive AUM is about 1/15 of Nifty 50 passive, and no post-2016 return evidence exists for those events.
- Deletion side:
  - The selling pressure is executed in the closing auction after 15:15. An MIS short that must be flat by 14:50 cannot hold through it.
  - The only long-only use of deletions in the literature is buying after exclusion: Chhatwani's +4-7% over 60-240 days (abstract only, 2000-2016), and Marisetty's positive effective-day AARs for deletions in 2015-2024.
- Holding period and tax treatment:
  - All holds here run a few weeks, so gains are short-term.
  - If total income stays within the basic exemption, the after-tax figures equal the net figures.
  - If not, multiply the net by 0.8. Whether transfer expenses (DP charge, GST) can be deducted, and STT cannot, needs re-verification.

### Gaps
- Sensex event-level return evidence is missing, so no net-of-cost estimate is possible for Sensex events.
- No study reports the distribution of event returns (percentiles), only means and medians. Medians for 2010-18 are AD+1 1.53%, run-up 1.90% and ED window 1.24% (MCAR).
- Delivery tax rules under the new Income-tax Act effective 1 Apr 2026 were not checked against primary text.

## 6. Why the published effect could be overstated or may have decayed

### Takeaway
The Indian figures come from small in-sample event studies that ignore costs, have few independent event dates, and sometimes use benchmarks that contain the event stock. The market structure has also changed since 2016: much larger passive AUM, published broker predictions, earlier announcements, and since Aug 2026 a closing auction for F&O stocks. All of these could shrink the tradable part of the effect, or move it to the close.

### Cited Findings
- **No costs in any study.**
  - Kumar flags "hidden transaction costs" for index funds but reports gross returns. — [Kumar, NSE](https://nsearchives.nseindia.com/content/research/comppaper90.pdf)
  - Parthasarathy and Marisetty report gross abnormal returns only. — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123); [Marisetty 2025](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf)
- **Small samples and clustering.** Parthasarathy has 50 additions on only 30 unique announcement dates. That means correlated events, which the author argues are a minor issue because fewer than two stocks were added per review. — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
- **Sample selection.** 21 of 71 Nifty additions in 2000-2018 were dropped (corporate events, short gaps, IPO history). — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
- **Model sensitivity.**
  - Parthasarathy shows that a market model estimated near the announcement dampens abnormal returns for high-alpha (run-up) stocks. The author says earlier Indian studies' lack of permanent effects may come from "choice of market model ... choice of market index and the estimation period close to AD". — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
  - Marisetty and Selvam et al. use the Nifty itself as the benchmark. — [Marisetty 2025](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf); [Selvam et al. 2012](https://smartjournalbms.org/docs/scopus/Impact%20on%20Stock%20Price%20by%20the%20Inclusion%20to%20and%20Exclusion%20from%20CNX%20nifty%20Index.pdf)
- **Announcement dates are uncertain in older work.**
  - Kumar infers them from circular dates, and ten early Nifty changes have no announcement date. — [Kumar, NSE](https://nsearchives.nseindia.com/content/research/comppaper90.pdf)
  - The only Sensex study used "assumed announcement dates". — as cited by [Kumar, NSE](https://nsearchives.nseindia.com/content/research/comppaper90.pdf)
- **Decline across sub-periods.**
  - 2000-09 vs 2010-18: AD+1 2.32% vs 1.24%; AD+1..AD+60 6.28% vs 2.43%. — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123)
  - Additions' CAAR into the effective date: 2020-24 at -4.84%, against +1.39% in 2015-19. — [Marisetty 2025](https://www.allfinancejournal.com/archives/2025/vol8issue2/PartH/8-2-82-601.pdf)
  - US background: S&P 500 deletion effects fell from -14.7% to -2.4% between the 1990s and 2010s. — [Greenwood & Sammon](https://www.hbs.edu/ris/download.aspx?name=ssrn-4294297.pdf)
- **Closing auction session (CAS).**
  - Introduced by SEBI circular SEBI/HO/47/11/11(3)2025-MRD-POD2/I/2765/2026 dated 16 Jan 2026. Initially the closing price of "stocks in the cash segment on which derivative contracts are available shall be determined based on CAS".
  - The reference price is the VWAP from 3:00 to 3:15 p.m., and the CAS price band is ±3% around it.
  - Only limit and market orders are allowed; stop-loss orders are not. — [NSE circular NSE/CMTR/73362, 18 Mar 2026](https://nsearchives.nseindia.com/content/circulars/CMTR73362.pdf)
  - Go-live on 3 Aug 2026, with continuous trading in F&O stocks ending at 15:15 (UNVERIFIED, secondary). — [Angel One](https://www.angelone.in/news/market-updates/sebi-closing-auction-session-from-august-3-2026-new-timings-and-rules-for-f-o-stocks)
- **Closing auction on MSCI day (UNVERIFIED, secondary):** about $4.2 billion of closing-auction turnover on the September MSCI rebalance day. — [5paisa](https://www.5paisa.com/blog/msci-rejig-cas-turnover)
- **Earlier and longer lead times.** The Sep 2026 Nifty review was announced 50 days before the effective close, against 32-38 days in the four prior reviews. — [NSE press releases, section 1](https://niftyindices.com/Press_Release/ind_prs10082026.pdf)
- **Effective-day volume.** Parthasarathy's only significant abnormal volume is in the ED window (mean volume ratio 2.30). Joshipura & Janakiramanan attribute effective-day volume to index funds and ETFs. — [Parthasarathy 2019](https://www.macrothink.org/journal/index.php/ajfa/article/download/14866/12123); [IDEAS abstract](https://ideas.repec.org/a/ids/afasfa/v5y2015i1p21-36.html)

### Inferences
- The Sep 2026 review (BSE Ltd in, Wipro out; both F&O stocks) appears to be the first semi-annual Nifty rebalance after CAS went live. If the go-live date is right, passive trades on 29 Sep 2026 would have been matched in the auction. No published study covers any CAS-era rebalance.
- With the close set in an auction, a seller can submit into the same auction where passive demand executes. The ±3% band around the 15:00-15:15 VWAP caps how far the close can move from the late-session price in one auction.
- Cumulative selection effects plausibly overstate the tradable effect: no costs, survivor-like "clean" samples, model choices that raise abnormal returns, and the AD+1 jump that arrives before a post-announcement buyer can act. None of the studies quantifies this.
- Overlapping events push in the same direction. Nifty 50, Nifty 100 and Nifty Next 50 changes share one effective date, and Nifty 50 drop-downs are simultaneously Nifty Next 50 additions. Net passive flow for a stock depends on all its index memberships, and none of the studies nets these out.

### Gaps
- No primary source in hand for the CAS go-live date.
- No study of index events under CAS, or of how far the closing price moved from the pre-auction VWAP on rebalance days.
- No Indian study quantifies arbitrageur positioning (for example, delivery-percentage or institutional-flow changes between announcement and effective date) after 2016.

## 7. Downloadable datasets

### Takeaway
All the primary inputs are free: NSE Indices press releases, NSE and BSE methodology documents, NSE daily bhavcopy archives in both formats, current constituent CSVs, and monthly passive-AUM reports. Point-in-time constituent lists and a consolidated change history with announcement dates are not available as free downloads. They have to be rebuilt from press releases.

### Cited Findings
**NSE Indices press releases (index changes)**
- PDF per announcement, at the pattern `https://niftyindices.com/Press_Release/ind_prsDDMMYYYY.pdf`. Verified for 23 Aug 2024, 21 Feb 2025, 22 Aug 2025, 23 Feb 2026 and 10 Aug 2026.
- Each gives the announcement date, the effective date with the "close of" date, inclusions and exclusions per index, and average free-float market caps. Free; PDF only, so it needs parsing. — [example](https://niftyindices.com/Press_Release/ind_prs10082026.pdf)
- Newer releases are also on NSE's archive, e.g. `https://nsearchives.nseindia.com//web/pressrelease/2026-09/ind_prs25092026_20260925205643.pdf` (from search results; not opened).

**NSE F&O circulars restating index changes**
- PDF circulars. — [FAOP76591](https://nsearchives.nseindia.com/content/circulars/FAOP76591.pdf)

**Current constituents**
- CSVs: [Nifty 50](https://www.niftyindices.com/IndexConstituent/ind_nifty50list.csv), [Nifty Next 50](https://www.niftyindices.com/IndexConstituent/ind_niftynext50list.csv), [Nifty 100](https://www.niftyindices.com/IndexConstituent/ind_nifty100list.csv). All returned HTTP 200 on 31 Oct 2026.
- Current composition only, no history. Free.

**NSE equity bhavcopy (daily prices for all NSE stocks)**
- Old format: `https://nsearchives.nseindia.com/content/historical/EQUITIES/YYYY/MON/cmDDMONYYYYbhav.csv.zip`. The 2016-01-01 file is verified (zip). — [example](https://nsearchives.nseindia.com/content/historical/EQUITIES/2016/JAN/cm01JAN2016bhav.csv.zip)
- New UDiFF format: `https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_YYYYMMDD_F_0000.csv.zip`. The 2026-09-30 file is verified (zip). — [example](https://nsearchives.nseindia.com/content/cm/BhavCopy_NSE_CM_0_0_0_20260930_F_0000.csv.zip)
- Free. Access friction:
  - A browser-like User-Agent was used.
  - Prices are not adjusted for corporate actions.
  - The format changes partway through the history. The changeover date was not confirmed here.

**Methodology documents**
- [NSE equity indices methodology, Sep 2026](https://www.niftyindices.com/Methodology/Method_NIFTY_Equity_Indices.pdf) (PDF, 345 pages).
- [BSE Indices methodology, Oct 2026](https://www.bseindices.com/Downloads/BSE_Indices_Methodology.pdf) (PDF, 104 pages).
- Older versions would be needed to check rule changes since 2016. Not collected.

**Passive AUM**
- NSE "Nifty Passive Insights" monthly PDFs, e.g. [June 2026](https://niftyindices.com/Nifty_Passive_Insights/NiftyPassiveFundReport-June2026.pdf). Search results also show March, April and May 2026 issues.
  - Scheme-level AUM by tracked index. Free.
  - Guessed URLs for Jul-Oct 2026 returned HTML, not PDF.
- [AMFI monthly note](https://www.amfiindia.com/uploads/AMFI_Monthly_Note_September2026_554f6604b6.pdf) (PDF, industry aggregates). Also the [AMFI monthly index page](https://www.amfiindia.com/research-information/amfi-monthly).
- [NSE 25 Years of Nifty50 (Jan 2022)](https://nsearchives.nseindia.com/content/indices/25_Years_Journey_of_Nifty50_2022-01.pdf) for the Sep 2019 to Nov 2021 Nifty 50 passive AUM series.

**What the repo already has**
- Kaggle NSE 1-minute CSVs for 40 symbols, 2015-02-02 to 2026-04-08, plus index TRI files from `scripts/download_indices.py`. — [docs/data.md in repo](file:///C:/Users/Advik/desktop/nse-algo/docs/data.md)

### Inferences
- An Indian index-event dataset for 2016-2026 is buildable at zero cost:
  1. Parse NSE press releases into a table of (announcement date, effective close, index, symbol, in/out).
  2. Join daily bhavcopy prices, adjusting for corporate actions.
  3. For the Sensex, add BSE notices.
- The repo's 40-symbol minute data cannot cover the event universe, so a daily bhavcopy layer would be needed.
- Building and testing such a dataset would count as a new research run. Per CLAUDE.md, it would have to be logged and respect the holdout.

### Gaps
Not found or not verified:
- A free point-in-time constituent history for the Nifty 50, Nifty Next 50, Nifty 100 or Sensex.
- An NSE Indices or BSE page listing all historical index changes with announcement dates.
- The URL pattern and archive depth for BSE index-change notices and BSE bhavcopy.
- Whether NSE Indices sells historical constituent data, and at what price.
- Historical IWF (free-float) files, needed to rebuild rankings before announcements.

