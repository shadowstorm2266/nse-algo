# NSE factor / smart-beta indices: live (post-launch) results vs Nifty 50 TRI, and realised fund results after costs

Compiled 2026-10-31. All index levels are official NSE Indices TRI closes, downloaded from niftyindices.com. All fund NAVs are AMFI NAVs. The only computation is CAGR between two published levels; no rule was simulated and no backtest was run. Raw downloads and the small scripts that did the arithmetic are in `C:/Users/Advik/AppData/Local/Temp/claude/C--Users-Advik-desktop-nse-algo/505a1726-172d-483b-ba01-281b0a6c0ca7/scratchpad/r6_factor/` (`dl/` holds the data; `scripts/` holds the scripts; the result tables are `live_table.md`, `insample_table.md`, `alt_end_table.md` and `fund_table.md`). Every Python run used `python -I`.

Definitions used throughout:
- **Base date**: the first date of the index series. Values from the base date to the launch date are **back-calculated**: the methodology was applied to past data after the fact.
- **Launch date**: the date NSE Indices released the index. Values after it are **live**. The launch dates come from the "Launch Date" field of each NSE factsheet dated September 30, 2026.
- **Live CAGR**: the TRI close on the launch date (or the last trading day before it) to the TRI close on 30-Oct-2026, the latest close available on 2026-10-31. Nifty 50 TRI is measured over the same dates.
- None of the index-level figures include fund fees, taxes, spreads or impact cost. The fund-level figures (section 3) are net of TER and tracking error, but they exclude the investor's own taxes and exchange or transaction costs.

## 1. Which NSE factor indices have ETFs or index funds (as of 2026-10-31), with base date, launch date, funds and TER

### Takeaway
29 NSE factor or strategy indices have at least one live ETF or index fund in AMFI's NAV file for 30-Oct-2026. Most were launched in 2016 or later. More than half of the funds were launched in 2021 or later. Direct-plan TERs on factor index funds run about 0.37-1.09% a year (median about 0.59%), against 0.25% for the UTI Nifty 50 index fund (direct plan). At least 7 NSE factor indices have no fund at all, including the two candidates Nifty Alpha Quality Low-Volatility 30 and Nifty Quality Low-Volatility 30.

### Cited Findings
**Launch and base dates.** Each launch and base date below comes from that index's NSE factsheet, dated September 30, 2026. The factsheets are at `https://www.niftyindices.com/Factsheet/<file>.pdf`. Examples: [Nifty200 Momentum 30](https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf), [Nifty Alpha 50](https://www.niftyindices.com/Factsheet/Factsheet_Nifty_Alpha50.pdf), [Nifty50 Value 20](https://www.niftyindices.com/Factsheet/Nifty50_Value20.pdf), [Nifty100 Low Volatility 30](https://www.niftyindices.com/Factsheet/Nifty100_LowVolatility30.pdf). The factsheet links are on each index page under `https://www.niftyindices.com/indices/equity/strategy-indices/`. Every factsheet gives a base value of 1000. I checked the TRI equals 1000.00 on the base date for 6 indices.

**Funds.** Fund names and AMFI scheme codes are from [AMFI NAVAll.txt](https://www.amfiindia.com/spages/NAVAll.txt) (NAV date 30-Oct-2026). ETF symbols are cross-checked against the NSE Indices ETF list, [ETF.json](https://liveindexsa.niftyindices.com/jsonfiles/ETF.json). TER is the "Total TER (%)" for the latest day of October 2026 in AMFI's TER disclosure ([AMFI TER page](https://www.amfiindia.com/ter-of-mf-schemes)). It was exported through the page's own API, `https://www.amfiindia.com/api/populate-te-rdata-revised?MF_ID=All&Month=10-2026&strCat={50|52|101|104}&strType=-1&excel=true`. "Dir" means the direct-plan TER of an index fund. ETFs have a single TER. "(oldest)" marks the fund used in section 3. That fund is the oldest one with an unbroken, split-free AMFI NAV history; in a few cases an older ETF was skipped because of unit splits (see Gaps).

| Index | Base date | Launch date | Funds found in AMFI NAVAll 30-Oct-2026 (scheme code), TER Oct-2026 |
|---|---|---|---|
| Nifty Dividend Opportunities 50 | 2007-10-01 | 2011-03-22 | Nippon India ETF Nifty Dividend Opportunities 50 (128639) 0.39% (oldest) |
| Nifty Alpha 50 | 2003-12-31 | 2012-11-19 | Kotak Nifty Alpha 50 ETF (149397) 0.71% (oldest); Motilal Oswal Nifty Alpha 50 ETF (153724); Bandhan Nifty Alpha 50 IF (152177) Dir 0.75%; Kotak Nifty Alpha 50 IF (153781) Dir 1.09% |
| Nifty100 Equal Weight | 2003-01-01 | 2013-06-10 | Sundaram (formerly Principal) Nifty 100 Equal Weight Fund (149483) Dir 0.76% (oldest); HDFC NIFTY 100 EW IF (149870); Kotak Nifty 100 EW IF (153146) and ETF (153315) |
| Nifty50 Value 20 | 2009-01-01 | 2014-03-28 | Nippon India ETF Nifty 50 Value 20 (134782) 0.46%; Kotak Nifty 50 Value 20 ETF (135744) 0.35%; ICICI Pru Nifty50 Value 20 ETF (139455) and IF (152365); HDFC NIFTY50 Value 20 ETF (150619); Nippon India Nifty 50 Value 20 IF (148721) Dir 0.52% (oldest split-free) |
| Nifty Growth Sectors 15 | 2009-01-01 | 2014-05-22 | HDFC NIFTY Growth Sectors 15 ETF (150621) 0.32% |
| Nifty100 Quality 30 | 2009-10-01 | 2015-03-19 | Edelweiss Nifty 100 Quality 30 IF (149254) Dir 0.59% (oldest); HDFC NIFTY100 Quality 30 ETF (150620) and IF (153264) |
| Nifty100 Low Volatility 30 | 2005-04-01 | 2016-07-08 | ICICI Pru ETF (141596) 0.52%, plus FoF (148822); Kotak ETF (150000); Mirae ETF (151604); HDFC ETF (150658) and IF (152713); Bandhan IF (150636) Dir 0.50% (oldest split-free IF); Kotak IF (152663); SBI IF (153718) |
| Nifty50 Equal Weight | 1995-11-03 | 2017-04-13 | DSP Nifty 50 EW IF (141877) Dir 0.49% (oldest); DSP ETF (149286) 0.24%; ABSL (148962), HDFC (149107), ICICI (150639), UTI (151762), SBI (152370), Kotak (153150), Axis (154460) index funds; Mirae (153519), Motilal (153532), SBI (152749) ETFs |
| Nifty Alpha Low-Volatility 30 | 2005-04-01 | 2017-07-10 | ICICI Pru ETF (148456) 0.57%, plus FoF (149158); Nippon India IF (150487) Dir 0.56% (oldest split-free IF); Edelweiss (152616), UTI (153086), Bandhan (153213), Kotak (154388) IFs |
| Nifty200 Quality 30 | 2005-04-01 | 2018-04-17 | SBI Nifty 200 Quality 30 ETF (145648) 0.33%; ABSL ETF (150497) 0.33% (used); ICICI ETF (151907) and IF (153546); Kotak ETF (153657) and IF (153660); Bandhan IF (153114); UTI IF (152859); SBI IF (153555) |
| Nifty500 Value 50 | 2005-04-01 | 2018-10-24 | UTI IF (151739) Dir 0.73% (oldest); Axis IF (152949) and ETF (153414); Bandhan IF (152990); Mirae ETF (154299) |
| Nifty Midcap150 Quality 50 | 2005-04-01 | 2019-10-24 | DSP ETF (149403) 0.41%; DSP IF (150428) Dir 0.45% (used); UTI IF (150313) |
| Nifty200 Momentum 30 | 2005-04-01 | 2020-08-25 | UTI IF (148703) Dir 0.82% (oldest); Motilal ETF (149801) 0.84% and IF (149800) Dir 0.76%; ABSL ETF (150498); HDFC ETF (150657) and IF (152430); ICICI ETF (150455) and IF (150452); Bandhan IF (150591); Kotak IF (151781) and ETF (153904); Baroda BNP IF (152931); SBI IF (153662) |
| Nifty200 Alpha 30 | 2005-04-01 | 2022-07-21 | Mirae ETF (152134) 0.78% (oldest), plus FoF (152718); Tata IF (152836) |
| Nifty Midcap150 Momentum 50 | 2005-04-01 | 2022-08-16 | Tata IF (150738) Dir 0.77% (oldest); Edelweiss IF (150902); Kotak IF (152916); Motilal ETF (153694); SBI ETF (154237), plus FoF |
| Nifty Smallcap250 Quality 50 | 2005-04-01 | 2023-03-15 | DSP IF (152243) Dir 0.38% |
| Nifty Smallcap250 Momentum Quality 100 | 2005-04-01 | 2023-12-21 | Mirae ETF (152455) 0.73% (oldest), plus FoF; Navi IF (153362); Groww ETF (154384) and IF (154383) |
| Nifty MidSmallcap400 Momentum Quality 100 | 2005-04-01 | 2024-02-08 | Mirae ETF (152634), plus FoF (152645); UTI IF (153272) |
| Nifty500 Equal Weight | 2005-04-01 | 2024-05-31 | Nippon India IF (152842) Dir 0.55% |
| Nifty500 Momentum 50 | 2005-04-01 | 2024-06-04 | Motilal ETF (152874) 0.88% and IF (152875) Dir 0.79%; Nippon (152881), Bandhan (153003), Axis (153244), Kotak (154032) IFs; Groww ETF (153452), plus FoF |
| Nifty200 Value 30 | 2005-04-01 | 2024-06-12 | ICICI ETF (152932) 0.38% and IF (152936) Dir 0.59%; Kotak IF (154145); SBI ETF (154354), plus FoF |
| Nifty Top 10 Equal Weight | 2006-03-02 | 2024-06-24 | DSP ETF (152812) 0.23% and IF (152814) Dir 0.40%; Kotak IF (153461) |
| Nifty500 Multicap Momentum Quality 50 | 2005-04-01 | 2024-09-04 | Edelweiss ETF (152981) 0.73% and IF (152985) Dir 0.71% |
| Nifty Top 15 Equal Weight | 2006-03-02 | 2024-10-15 | ICICI ETF (153617) 0.38% and IF (153614) Dir 0.48% |
| Nifty Top 20 Equal Weight | 2006-03-02 | 2024-10-22 | HDFC IF (153405) Dir 0.37%; Mirae ETF (154060) |
| Nifty500 Quality 50 | 2005-04-01 | 2024-12-20 | Nippon India IF (153470) Dir 0.57%; Axis IF (153829) |
| Nifty500 Low Volatility 50 | 2005-04-01 | 2024-12-20 | Nippon India IF (153474) Dir 0.63%; Groww ETF (153583); Axis IF (154738) |
| Nifty500 Flexicap Quality 30 | 2009-10-01 | 2025-04-04 | DSP IF (153801) Dir 0.70% and ETF (153874) 0.60% |
| Nifty Total Market Momentum Quality 50 | 2005-04-01 | 2025-08-06 | Angel One IF (153956) Dir 0.66% and ETF (153957) 0.90% |

- Benchmark fund: the UTI Nifty 50 Index Fund has a direct-plan TER of 0.25% for Oct-2026 and a direct-plan NAV history from 02-Jan-2013 — [AMFI TER](https://www.amfiindia.com/ter-of-mf-schemes), [AMFI NAVAll](https://www.amfiindia.com/spages/NAVAll.txt).
- **Factor indices with no fund.** Searching scheme names in AMFI NAVAll for 30-Oct-2026 found no fund for: Nifty High Beta 50 and Nifty Low Volatility 50 (both launched 2012-11-19), Nifty100 Alpha 30 (2019-06-28), Nifty Alpha Quality Low-Volatility 30 (2017-07-10), Nifty Quality Low-Volatility 30 (2017-07-10), Nifty Alpha Quality Value Low-Volatility 30 (2017-07-03) and Nifty500 Multifactor MQVLv 50 (2025-02-06). Two new indices are too young to evaluate: Nifty500 Growth 50 (launched 2026-08-26) and Nifty High Dividend Yield 15 (launched 2026-09-30). Launch dates are from their [factsheets](https://www.niftyindices.com/indices/equity/strategy-indices); fund status is from [AMFI NAVAll](https://www.amfiindia.com/spages/NAVAll.txt).
- **Fund counts.** As of February 2026, 24 passive funds tracked the three Nifty momentum indices, with AUM above ₹17,000 crore. This is vendor research — [NSE Indices momentum whitepaper 2026](https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf). NSE Indices earns licence fees from these funds, so it has a conflict of interest.
- **BSE factor funds** are out of scope here, but they exist: ABSL BSE 500 Momentum 50 and Quality 50, Motilal Oswal BSE Low Volatility and BSE Quality, UTI BSE Low Volatility, Tata BSE Quality, and Mirae/Motilal BSE Midcap 150 Momentum 30 — [AMFI NAVAll](https://www.amfiindia.com/spages/NAVAll.txt).

### Inferences
- Product launches cluster after an index has a strong recent record. Momentum funds arrived in 2021-2022, after the 2020-21 rally; Smallcap/MidSmallcap momentum-quality funds arrived in 2024. Fund investors therefore started later than the index launch dates, and their live windows are shorter than the index windows in section 2.
- Direct-plan factor index fund TERs (median about 0.6%) are 2-4 times the Nifty 50 index fund TER. Any factor premium must clear that gap before it shows up for the investor.

### Gaps
- The no-fund list comes from name matching in a file of live schemes. A fund that closed or merged does not appear in NAVAll, so this list cannot show survivorship. I found no SEBI or AMFI list of closed factor funds.
- Exact fund inception dates come from SIDs and KIMs, which I did not open. I used the first NAV in AMFI's history as a proxy.
- Some older ETFs (ICICI Low Vol 30, ICICI Alpha Low-Vol 30, DSP Midcap150 Quality 50, Nippon NV20) had unit splits, so their raw NAV series cannot be compared across the split. The NAV downloads for the SBI Quality 30, Kotak NV20 and Nippon NV20 ETFs came back truncated. Section 3 therefore uses split-free index funds for those indices.
- Not checked: whether any index fund or ETF tracks the TRI or the PR variant as its benchmark. NAV-based tracking difference against the TRI is correct either way, because funds reinvest dividends.

## 2. Live-period returns: factor TRI vs Nifty 50 TRI from each launch date to 30-Oct-2026 (gross, index level)

### Takeaway
The factor CAGRs printed on factsheets start at the base date, so they include years of back-calculated history. The live record is weaker. For the 21 indices with at least 3.5 years live and a computable back-calculated period, the median excess over Nifty 50 TRI was +5.3 pp a year back-calculated and +1.5 pp a year live, before fees. Five of the 22 indices with at least 3.5 years live trailed Nifty 50 TRI over their live window: High Beta 50, Growth Sectors 15, Nifty100 Quality 30, Quality Low-Vol 30 and Nifty200 Quality 30. The largest live leads belong to indices launched in 2018-2022 that rode the 2020-2024 small/mid and momentum rally: Alpha 50, Nifty500 Value 50, Nifty200 Alpha 30 and Midcap150 Momentum 50. Those leads shrink sharply if the window ends in 2025 or 2026 rather than in September 2024.

### Cited Findings
**Sources and method.** TRI closes come from the niftyindices.com historical data page, [Total Returns Index tab](https://www.niftyindices.com/reports/historical-data), through the page's own POST endpoint `https://www.niftyindices.com/BackPage/getTotalReturnIndexString` (one-year range per request). The start close is on the launch date and the end close is 30-Oct-2026. Live periods only; no fees, taxes or trading costs are included. The table is reproduced in scratchpad `live_table.md`.

**Back-calculated factsheet figure.** The "SI" column is the factsheet's "Since Inception" TR CAGR as of 30-Sep-2026. **It starts at the base date, so it is mostly back-calculated.** Source: the NSE factsheets for September 30, 2026, at `https://www.niftyindices.com/Factsheet/...`. The Nifty 50 factsheet, dated 30-Oct-2026, shows a since-inception TR of 12.15%, a 5-year TR of 6.70% and a 1-year TR of -9.45% ([Nifty 50 factsheet](https://www.niftyindices.com/Factsheet/ind_nifty50.pdf)).

| Index | Launch | Factor TRI at launch → 30-Oct-2026 | Nifty 50 TRI at launch | Live yrs | Live CAGR factor | Live CAGR Nifty 50 | Live excess pp/yr | Factsheet SI TR (base→Sep-26, back-calc) |
|---|---|---|---|---|---|---|---|---|
| Dividend Opportunities 50 | 2011-03-22 | 1,495.31 → 8,899.15 | 6,799.80 | 15.6 | 12.11% | 11.08% | +1.03 | 12.05% |
| Alpha 50 | 2012-11-19 | 4,880.59 → 64,179.58 | 7,160.33 | 13.9 | 20.29% | 12.06% | +8.23 | 20.21% |
| High Beta 50 (no fund) | 2012-11-19 | 1,668.69 → 5,109.49 | 7,160.33 | 13.9 | 8.36% | 12.06% | -3.71 | 7.71% |
| Low Volatility 50 (no fund) | 2012-11-19 | 4,996.94 → 32,555.84 | 7,160.33 | 13.9 | 14.39% | 12.06% | +2.32 | 16.49% |
| Nifty100 Equal Weight | 2013-06-10 | 8,287.04 → 46,700.51 | 7,597.17 | 13.4 | 13.79% | 12.10% | +1.69 | 17.61% |
| Nifty50 Value 20 | 2014-03-28 | 3,363.20 → 16,026.91 | 8,729.05 | 12.6 | 13.20% | 11.67% | +1.53 | 16.77% |
| Growth Sectors 15 | 2014-05-22 | 4,153.29 → 14,429.25 | 9,490.91 | 12.4 | 10.53% | 11.07% | -0.54 | 15.87% |
| Nifty100 Quality 30 | 2015-03-19 | 2,413.48 → 7,016.20 | 11,380.91 | 11.6 | 9.62% | 10.17% | -0.54 | 12.01% |
| Nifty100 Low Volatility 30 | 2016-07-08 | 8,002.93 → 26,830.25 | 11,172.39 | 10.3 | 12.45% | 11.72% | +0.72 | 16.45% |
| Nifty50 Equal Weight | 2017-04-13 | 17,384.77 → 54,066.40 | 12,375.68 | 9.5 | 12.62% | 11.52% | +1.10 | 13.73% |
| Alpha Quality Value Low-Vol 30 (no fund) | 2017-07-03 | 7,829.23 → 28,432.42 | 13,060.15 | 9.3 | 14.83% | 11.17% | +3.67 | 16.90% |
| Alpha Low-Volatility 30 | 2017-07-10 | 11,381.66 → 33,029.52 | 13,278.81 | 9.3 | 12.13% | 10.99% | +1.14 | 17.71% |
| Alpha Quality Low-Vol 30 (no fund) | 2017-07-10 | 9,764.07 → 29,180.64 | 13,278.81 | 9.3 | 12.48% | 10.99% | +1.49 | 17.03% |
| Quality Low-Vol 30 (no fund) | 2017-07-10 | 8,996.78 → 22,281.71 | 13,278.81 | 9.3 | 10.24% | 10.99% | -0.76 | 15.46% |
| Nifty200 Quality 30 | 2018-04-17 | 11,646.94 → 27,454.47 | 14,461.97 | 8.5 | 10.57% | 10.92% | -0.36 | 16.64% |
| Nifty500 Value 50 | 2018-10-24 | 5,931.88 → 25,028.63 | 14,139.75 | 8.0 | 19.67% | 11.99% | +7.69 | 16.35% |
| Nifty100 Alpha 30 (no fund) | 2019-06-28 | 8,689.09 → 21,308.59 | 16,433.85 | 7.3 | 13.00% | 10.87% | +2.13 | 15.47% |
| Midcap150 Quality 50 | 2019-10-24 | 12,896.72 → 30,329.21 | 16,252.63 | 7.0 | 12.96% | 11.57% | +1.39 | 17.31% |
| Nifty200 Momentum 30 | 2020-08-25 | 14,443.10 → 35,987.03 | 16,226.20 | 6.2 | 15.92% | 13.27% | +2.65 | 18.30% |
| Nifty200 Alpha 30 | 2022-07-21 | 14,457.13 → 31,218.19 | 24,058.17 | 4.3 | 19.72% | 9.19% | +10.53 | 17.49% |
| Midcap150 Momentum 50 | 2022-08-16 | 39,987.03 → 73,370.68 | 25,863.24 | 4.2 | 15.53% | 7.49% | +8.04 | 22.22% |
| Smallcap250 Quality 50 | 2023-03-15 | 20,704.47 → 33,460.16 | 24,701.60 | 3.6 | 14.15% | 10.12% | +4.03 | 18.03% |
| Smallcap250 Momentum Quality 100 | 2023-12-21 | 53,059.64 → 61,436.40 | 31,233.93 | 2.9 | 5.26% | 4.11% | +1.15 | 21.37% |
| MidSmallcap400 Momentum Quality 100 | 2024-02-08 | 56,801.02 → 63,716.97 | 31,950.32 | 2.7 | 4.31% | 3.45% | +0.86 | 21.39% |
| Nifty500 Equal Weight | 2024-05-31 | 16,914.14 → 17,806.97 | 33,285.90 | 2.4 | 2.15% | 2.15% | -0.00 | 14.60% |
| Nifty500 Momentum 50 | 2024-06-04 | 64,048.34 → 62,672.74 | 32,353.50 | 2.4 | -0.90% | 3.38% | -4.28 | 21.35% |
| Nifty200 Value 30 | 2024-06-12 | 22,582.91 → 24,315.11 | 34,487.88 | 2.4 | 3.15% | 0.67% | +2.48 | 16.12% |
| Top 10 Equal Weight | 2024-06-24 | 11,535.01 → 11,254.03 | 34,834.33 | 2.4 | -1.04% | 0.26% | -1.30 | 12.22% |
| Nifty500 Multicap Momentum Quality 50 | 2024-09-04 | 63,024.03 → 49,924.14 | 37,406.55 | 2.2 | -10.26% | -2.99% | -7.28 | 20.17% |
| Top 15 Equal Weight | 2024-10-15 | 12,825.40 → 12,376.37 | 37,196.69 | 2.0 | -1.73% | -2.88% | +1.15 | 12.78% |
| Top 20 Equal Weight | 2024-10-22 | 11,717.14 → 11,426.81 | 36,335.46 | 2.0 | -1.23% | -1.78% | +0.54 | 12.35% |
| Nifty500 Low Volatility 50 | 2024-12-20 | 27,131.96 → 29,381.27 | 35,070.59 | 1.9 | 4.38% | -0.04% | +4.42 | 16.93% |
| Nifty500 Quality 50 | 2024-12-20 | 27,288.53 → 25,793.35 | 35,070.59 | 1.9 | -2.99% | -0.04% | -2.94 | 16.37% |
| Nifty500 Multifactor MQVLv 50 (no fund) | 2025-02-06 | 41,916.55 → 41,809.64 | 35,143.08 | 1.7 | -0.15% | -0.16% | +0.02 | 19.09% |
| Nifty500 Flexicap Quality 30 | 2025-04-04 | 12,092.91 → 12,141.15 | 34,137.61 | 1.6 | 0.25% | 1.68% | -1.43 | 15.74% |
| Total Market Momentum Quality 50 | 2025-08-06 | 53,987.82 → 53,058.18 | 36,880.81 | 1.2 | -1.40% | -4.06% | +2.66 | 20.47% |

Nifty 50 TRI on 30-Oct-2026: 35,043.45, from the same [niftyindices TRI download](https://www.niftyindices.com/reports/historical-data).

**Back-calculated vs live excess over Nifty 50 TRI.** The back-calculated CAGR runs from the base value of 1000 to the TRI at launch. The Nifty 50 TRI is measured over the same window: 2369.69 on 31-Mar-2005 for the 2005-04-01 base, 2139.93 on 31-Dec-2003, 6151.88 on 01-Oct-2007, 1219.01 on 01-Jan-2003, 3635.87 on 31-Dec-2008, 6301.54 on 01-Oct-2009, and the close on 02-Mar-2006 for the Top-N equal-weight bases. Source: [niftyindices TRI](https://www.niftyindices.com/reports/historical-data). Nifty50 Equal Weight is left out because its base date (1995) predates the Nifty 50 TRI series I downloaded. Full table in scratchpad `insample_table.md`.

| Index | Back-calc yrs | Back-calc excess pp/yr | Live yrs | Live excess pp/yr | Change |
|---|---|---|---|---|---|
| Alpha 50 | 8.9 | +4.97 | 13.9 | +8.23 | +3.26 |
| High Beta 50 | 8.9 | -8.63 | 13.9 | -3.71 | +4.92 |
| Low Volatility 50 | 8.9 | +5.29 | 13.9 | +2.32 | -2.96 |
| Dividend Opportunities 50 | 3.5 | +9.36 | 15.6 | +1.03 | -8.33 |
| Nifty100 Equal Weight | 10.4 | +3.30 | 13.4 | +1.69 | -1.61 |
| Nifty50 Value 20 | 5.2 | +8.42 | 12.6 | +1.53 | -6.89 |
| Growth Sectors 15 | 5.4 | +11.31 | 12.4 | -0.54 | -11.85 |
| Nifty100 Quality 30 | 5.5 | +6.07 | 11.6 | -0.54 | -6.62 |
| Nifty100 Low Volatility 30 | 11.3 | +5.68 | 10.3 | +0.72 | -4.95 |
| Alpha Quality Value Low-Vol 30 | 12.3 | +3.49 | 9.3 | +3.67 | +0.18 |
| Alpha Low-Volatility 30 | 12.3 | +6.99 | 9.3 | +1.14 | -5.85 |
| Alpha Quality Low-Vol 30 | 12.3 | +5.47 | 9.3 | +1.49 | -3.98 |
| Quality Low-Vol 30 | 12.3 | +4.67 | 9.3 | -0.76 | -5.43 |
| Nifty200 Quality 30 | 13.0 | +5.97 | 8.5 | -0.36 | -6.33 |
| Nifty500 Value 50 | 13.6 | +0.08 | 8.0 | +7.69 | +7.60 |
| Nifty100 Alpha 30 | 14.2 | +1.95 | 7.3 | +2.13 | +0.18 |
| Midcap150 Quality 50 | 14.6 | +5.18 | 7.0 | +1.39 | -3.79 |
| Nifty200 Momentum 30 | 15.4 | +5.74 | 6.2 | +2.65 | -3.09 |
| Nifty200 Alpha 30 | 17.3 | +2.46 | 4.3 | +10.53 | +8.07 |
| Midcap150 Momentum 50 | 17.4 | +9.01 | 4.2 | +8.04 | -0.97 |
| Smallcap250 Quality 50 | 18.0 | +4.54 | 3.6 | +4.03 | -0.51 |
| Smallcap250 Momentum Quality 100 | 18.7 | +8.96 | 2.9 | +1.15 | -7.80 |
| MidSmallcap400 Momentum Quality 100 | 18.9 | +9.19 | 2.7 | +0.86 | -8.34 |
| Nifty500 Momentum 50 | 19.2 | +9.71 | 2.4 | -4.28 | -13.99 |
| Nifty500 Multicap Momentum Quality 50 | 19.4 | +8.61 | 2.2 | -7.28 | -15.88 |
| Nifty500 Quality 50 | 19.7 | +3.70 | 1.9 | -2.94 | -6.65 |
| Nifty500 Multifactor MQVLv 50 | 19.9 | +6.24 | 1.7 | +0.02 | -6.23 |

- Summary of the first 21 rows (live window of at least 3.5 years). The live excess was lower than the back-calculated excess for 15 of the 21. The median back-calculated excess was +5.29 pp a year; the median live excess was +1.53 pp a year. The mean change was -2.3 pp a year and the median change -3.1 pp a year. My arithmetic, on the [niftyindices TRI](https://www.niftyindices.com/reports/historical-data) levels above.
- Indices launched after 2023 with multi-factor or momentum-quality tilts showed back-calculated excesses of +6 to +10 pp a year. Their live excess was between -7.3 and +1.2 pp a year. These windows are short (1.7-2.9 years) — same source.

**Endpoint sensitivity.** The table shows live CAGR from the launch date to three different end dates, as factor CAGR / Nifty 50 CAGR / difference in pp. 27-Sep-2024 is near the Nifty 50 TRI peak in this data. Full table in scratchpad `alt_end_table.md`.

| Index (launch) | to 27-Sep-2024 | to 31-Oct-2025 | to 30-Oct-2026 |
|---|---|---|---|
| Alpha 50 (2012) | 25.67 / 15.34 / +10.34 | 21.68 / 13.92 / +7.76 | 20.29 / 12.06 / +8.23 |
| Nifty50 Value 20 (2014) | 18.42 / 15.28 / +3.14 | 15.59 / 13.70 / +1.89 | 13.20 / 11.67 / +1.53 |
| Nifty100 Low Volatility 30 (2016) | 17.38 / 16.37 / +1.01 | 14.75 / 14.27 / +0.48 | 12.45 / 11.72 / +0.72 |
| Alpha Low-Volatility 30 (2017) | 19.39 / 16.04 / +3.34 | 14.54 / 13.74 / +0.80 | 12.13 / 10.99 / +1.14 |
| Nifty200 Quality 30 (2018) | 17.49 / 16.57 / +0.92 | 13.43 / 13.95 / -0.51 | 10.57 / 10.92 / -0.36 |
| Nifty500 Value 50 (2018) | 28.05 / 18.60 / +9.45 | 23.06 / 15.42 / +7.63 | 19.67 / 11.99 / +7.69 |
| Nifty100 Alpha 30 (2019) | 24.28 / 17.81 / +6.47 | 17.18 / 14.46 / +2.73 | 13.00 / 10.87 / +2.13 |
| Nifty200 Momentum 30 (2020) | 33.66 / 23.80 / +9.86 | 21.32 / 18.26 / +3.06 | 15.92 / 13.27 / +2.65 |
| Nifty200 Alpha 30 (2022) | 52.58 / 24.51 / +28.07 | 27.10 / 15.60 / +11.51 | 19.72 / 9.19 / +10.53 |
| Midcap150 Momentum 50 (2022) | 40.76 / 21.22 / +19.54 | 22.13 / 13.38 / +8.75 | 15.53 / 7.49 / +8.04 |
| Smallcap250 Quality 50 (2023) | 61.22 / 34.25 / +26.97 | 26.03 / 18.61 / +7.42 | 14.15 / 10.12 / +4.03 |

### Inferences
- For most indices, the factsheet's since-inception number is several points per year above the live result. Growth Sectors 15 shows 15.87% since inception against 10.53% live; Nifty200 Quality 30 shows 16.64% against 10.57%; Alpha Low-Volatility 30 shows 17.71% against 12.13%. The factsheet figure starts at the base date, so it mostly reports back-calculated history. An investor reading only the factsheet would expect much more than the live record has delivered.
- The live evidence is uneven, not uniformly negative. Alpha 50 has 13.9 years live, shows +8.2 pp a year before fees, and its live excess was higher than its back-calculated excess. In this data it is the strongest live record. Its funds, however, lose about 1.9 pp a year to tracking difference (section 3).
- The quality-only and quality-low-vol indices have the weakest live records relative to their back-tests (Nifty100 Quality 30, Nifty200 Quality 30, Quality Low-Vol 30). That matches Lalwani (2022) in section 4.
- The indices launched in 2022-2023 owe much of their live excess to one regime: the small/mid and momentum rally of 2023 to mid-2024. Their lead fell from +20 to +28 pp a year (to Sep-2024) to +4 to +11 pp a year (to Oct-2026). These rows show regime and endpoint dependence, not a stable premium.
- These are index returns before fees. Subtract about 0.4-1.9 pp a year of fund tracking difference to see what an investor would have received (section 3).

### Gaps
- The launch-date close is treated as the first live value. Dissemination may have started the next session, which would move the start by a day; the effect is negligible.
- Methodology changes after launch (rebalancing frequency, caps, renames such as the Nifty Quality 30 to Nifty200 Quality 30 change) were not checked in the methodology documents. A methodology change during the live period would mean part of the "live" record ran under different rules.
- No statistical test was run. Most indices overlap heavily in holdings and time, so the 21 rows are not independent observations. Section 4 cites Lalwani's t-tests.

## 3. Fund-level live results (NAV-based, after TER and tracking error) vs a Nifty 50 index fund

### Takeaway
Factor funds lag their own TRI by a median of 0.56 pp a year. The range is 0.24-1.91 pp a year, and the largest gaps are in high-turnover indices: Alpha 50 lags about 1.9 pp a year and Midcap150 Momentum 50 lags 1.4 pp a year. The UTI Nifty 50 index fund lags its TRI by about 0.25 pp a year. Only 12 factor funds have at least 4 years of NAV history. Over their own windows, 10 of the 12 beat the UTI Nifty 50 index fund (direct plan), by -0.3 to +7.0 pp a year. Nearly all of those windows start in 2021-2022, so they share one market regime. Funds launched in late 2023 or later have 1-3 year records, mostly flat or negative.

### Cited Findings
**Method.** The window starts on each fund's first NAV in AMFI's history. That date was located through api.mfapi.in, an UNVERIFIED secondary mirror of AMFI, and the start NAV was then taken from AMFI's own historical NAV report, `https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=DD-Mon-YYYY&todt=DD-Mon-YYYY` (spot-check: UTI Nifty 200 Momentum 30 Direct, 12-Mar-2021, 9.9454 in both sources). The end NAV is from [AMFI NAVAll.txt](https://www.amfiindia.com/spages/NAVAll.txt) for 30-Oct-2026.
- **Benchmark fund:** UTI Nifty 50 Index Fund, Direct Growth (scheme 120716), using AMFI NAVs on the same dates.
- **Tracking difference (TD):** the fund's NAV CAGR minus the CAGR of the factor's TRI over the same dates, using TRI levels from [niftyindices](https://www.niftyindices.com/reports/historical-data).
- **Splits:** none of the series used here has a one-day NAV move outside 0.75x-1.33x, which rules out a unit split or consolidation.
- **What is and is not included:** NAV returns are after TER, the fund's own trading costs and cash drag. They are before the investor's taxes, stamp duty and STT, and, for ETFs, before the exchange spread and any premium or discount paid. Full table in scratchpad `fund_table.md`.

| Index | Fund (code) | Window start | NAV start → 30-Oct-2026 | Yrs | Fund CAGR | TRI CAGR same window | TD pp/yr | TER Oct-26 | UTI Nifty 50 Dir CAGR | Fund minus UTI N50 pp/yr |
|---|---|---|---|---|---|---|---|---|---|---|
| Dividend Opp 50 | Nippon India ETF (128639) | 2014-04-21 | 17.3923 → 74.0338 | 12.5 | 12.26% | 12.53% | -0.27 | 0.39 | 11.28% | +0.98 |
| Nifty50 Equal Weight | DSP IF Dir (141877) | 2017-10-23 | 10.0040 → 26.1394 | 9.0 | 11.24% | 12.04% | -0.80 | 0.49 | 10.53% | +0.71 |
| Nifty50 Value 20 | Nippon India IF Dir (148721) | 2021-02-23 | 9.8803 → 16.9730 | 5.7 | 9.99% | 10.52% | -0.53 | 0.52 | 9.28% | +0.71 |
| Nifty200 Momentum 30 | UTI IF Dir (148703) | 2021-03-12 | 9.9454 → 19.8433 | 5.6 | 13.04% | 13.52% | -0.48 | 0.82 | 8.94% | +4.11 |
| Nifty100 Quality 30 | Edelweiss IF Dir (149254) | 2021-10-07 | 10.1388 → 14.2552 | 5.1 | 6.96% | 7.24% | -0.27 | 0.59 | 6.26% | +0.70 |
| Alpha 50 | Kotak ETF (149397) | 2021-12-29 | 34.1096 → 49.7696 | 4.8 | 8.13% | 10.04% | -1.91 | 0.71 | 7.26% | +0.87 |
| Nifty100 Equal Weight | Sundaram Dir (149483)* | 2022-01-03 | 114.3091 → 183.1442 | 4.8 | 10.27% | 10.84% | -0.56 | 0.76 | 6.75% | +3.52 |
| Midcap150 Quality 50 | DSP IF Dir (150428) | 2022-08-04 | 10.0259 → 13.6603 | 4.2 | 7.57% | 7.81% | -0.24 | 0.45 | 7.86% | -0.29 |
| Nifty200 Quality 30 | ABSL ETF (150497) | 2022-08-19 | 14.7754 → 19.8955 | 4.2 | 7.35% | 7.68% | -0.34 | 0.33 | 7.35% | -0.00 |
| Alpha Low-Vol 30 | Nippon India IF Dir (150487) | 2022-08-22 | 9.8895 → 15.0699 | 4.2 | 10.58% | 11.28% | -0.70 | 0.56 | 7.75% | +2.82 |
| Nifty100 Low Vol 30 | Bandhan IF Dir (150636) | 2022-10-07 | 9.9781 → 15.0092 | 4.1 | 10.57% | 11.27% | -0.70 | 0.50 | 8.28% | +2.29 |
| Midcap150 Momentum 50 | Tata IF Dir (150738) | 2022-10-31 | 10.2217 → 17.4755 | 4.0 | 14.36% | 15.74% | -1.38 | 0.77 | 7.33% | +7.03 |
| Nifty500 Value 50 | UTI IF Dir (151739) | 2023-05-12 | 9.9047 → 20.4153 | 3.5 | 23.18% | 23.99% | -0.81 | 0.73 | 7.96% | +15.22 |
| Nifty200 Alpha 30 | Mirae ETF (152134) | 2023-10-23 | 16.6696 → 24.6177 | 3.0 | 13.78% | 14.73% | -0.95 | 0.78 | 7.11% | +6.67 |
| Alpha 50 | Bandhan IF Dir (152177) | 2023-11-10 | 10.0613 → 13.6895 | 3.0 | 10.92% | 12.82% | -1.90 | 0.75 | 6.92% | +4.00 |
| Smallcap250 Quality 50 | DSP IF Dir (152243) | 2023-12-26 | 10.0092 → 10.2774 | 2.8 | 0.93% | 1.35% | -0.42 | 0.38 | 3.58% | -2.65 |
| Smallcap250 MQ 100 | Mirae ETF (152455) | 2024-02-26 | 44.8770 → 45.6285 | 2.7 | 0.62% | 1.39% | -0.76 | 0.73 | 2.56% | -1.93 |
| Nifty500 Equal Weight | Nippon India IF Dir (152842) | 2024-09-11 | 9.9333 → 8.9916 | 2.1 | -4.56% | -4.06% | -0.50 | 0.55 | -2.69% | -1.87 |
| Top 10 Equal Weight | DSP IF Dir (152814) | 2024-09-06 | 9.8731 → 8.8675 | 2.2 | -4.88% | -4.48% | -0.40 | 0.40 | -2.56% | -2.33 |
| Nifty500 Momentum 50 | Motilal Oswal IF Dir (152875) | 2024-09-30 | 9.9588 → 7.9914 | 2.1 | -10.04% | -9.37% | -0.67 | 0.79 | -4.38% | -5.65 |
| Nifty200 Value 30 | ICICI Pru IF Dir (152936) | 2024-10-21 | 9.8599 → 10.2147 | 2.0 | 1.76% | 2.22% | -0.46 | 0.59 | -2.56% | +4.32 |
| Nifty500 Multicap MQ 50 | Edelweiss IF Dir (152985) | 2024-11-05 | 9.9806 → 8.4409 | 2.0 | -8.11% | -7.41% | -0.69 | 0.71 | -1.51% | -6.59 |
| Top 20 Equal Weight | HDFC IF Dir (153405) | 2025-03-25 | 9.9976 → 9.9244 | 1.6 | -0.46% | -0.08% | -0.38 | 0.37 | -0.61% | +0.15 |
| Nifty500 Quality 50 | Nippon India IF Dir (153470) | 2025-05-08 | 9.8749 → 10.1553 | 1.5 | 1.91% | 2.89% | -0.98 | 0.57 | -2.33% | +4.24 |
| Nifty500 Low Vol 50 | Nippon India IF Dir (153474) | 2025-05-08 | 9.8889 → 10.3344 | 1.5 | 3.03% | 3.54% | -0.52 | 0.63 | -2.33% | +5.35 |
| Top 15 Equal Weight | ICICI Pru IF Dir (153614) | 2025-06-27 | 10.0213 → 9.1157 | 1.3 | -6.82% | -6.52% | -0.30 | 0.48 | -6.76% | -0.06 |
| Flexicap Quality 30 | DSP IF Dir (153801) | 2025-08-29 | 9.9962 → 9.2120 | 1.2 | -6.75% | -6.04% | -0.71 | 0.70 | -4.08% | -2.67 |
| Total Mkt MQ 50 | Angel One IF Dir (153956) | 2025-11-27 | 10.0040 → 9.5720 | 0.9 | -4.3% total (not annualised) | -3.6% total | -0.71 total | 0.66 | -11.4% total | n/a |

*Sundaram Nifty 100 Equal Weight is an older fund (formerly Principal). Under the current scheme code, AMFI history in this download starts on 03-Jan-2022, so its earlier record was not captured.
- The UTI Nifty 50 Index Fund Direct's own TD against Nifty 50 TRI was -0.24 to -0.30 pp a year across these windows: for example 11.28% vs 11.58% from 2014-04-21, and 8.94% vs 9.18% from 2021-03-12. Same sources.
- TER is the Oct-2026 "Total TER" from the [AMFI TER disclosure](https://www.amfiindia.com/ter-of-mf-schemes). Historical TERs over each window were not collected.
- SEBI's passive-fund circular reportedly caps the tracking error of equity index funds and ETFs at 2%, measured on one year of data, and requires TD disclosure. This is UNVERIFIED (secondary): [Moneylife](https://moneylife.in/article/sebi-tracking-error-of-equity-etfs-and-index-funds-cannot-exceed-2-percentage/67279.html). A secondary source gives the circular number as SEBI/HO/IMD/DOF2/P/CIR/2022/69 (23-May-2022); I did not read the circular itself.

### Inferences
- The fund's TD exceeds its current TER in high-turnover indices: Alpha 50 by about 1.2 pp, Midcap150 Momentum 50 by about 0.6 pp, Nifty50 EW by about 0.3 pp. The likeliest explanation is rebalancing impact cost, plus cash and dividend timing. For Dividend Opp 50 and Midcap150 Quality 50, TD is at or below TER, which fits low-turnover indices. This is an inference; the funds do not disclose an impact-cost breakdown.
- Take Alpha 50, the longest-live and best index record. The index's 8.2 pp a year live lead over Nifty 50 TRI fell to about +0.9 pp a year over the Kotak ETF's 4.8-year window, net of fund costs. Part of the drop is the different window and part is the 1.9 pp a year TD. Index-level live evidence overstates what fund investors received by roughly the TD plus the TER gap to a Nifty 50 fund.
- Of the 12 fund windows of 4 years or more, 10 start between Feb-2021 and Oct-2022, so they share one market path. The +2 to +7 pp a year leads of momentum, low-vol and alpha-low-vol funds over the Nifty 50 fund come from one overlapping period. They are not independent confirmations.
- For an ETF, an investor's realised return also depends on the purchase and sale prices relative to NAV (section 5). The NAV-based figures above set an upper bound on what an ETF buyer received.

### Gaps
- AMFI's per-fund monthly TD disclosure file was not located: the URL I tried, `/research-information/other-data/tracking-difference`, returned 404. The TD figures above are my own NAV-vs-TRI arithmetic, not the funds' disclosed TD.
- The NAV histories for the oldest ETFs on Nifty100 Low Vol 30 (ICICI, 2017), Alpha Low-Vol 30 (ICICI, 2020), Midcap150 Quality 50 (DSP ETF, 2021) and NV20 (Nippon 2015, Kotak 2015) were either split-affected or truncated. Their longer records are therefore missing from this table.
- No information was collected on how much the regular plans trail the direct plans. The regular-plan TERs in the AMFI file run about 0.5-0.7 pp higher.

## 4. Evidence on back-test-to-live decay for Indian smart-beta indices (academic, vendor, IIMA factor library)

### Takeaway
The one peer-reviewed study that splits NSE factor indices at their launch dates found a large drop in performance after launch. Lalwani (2022/23) studied 9 indices with data to Aug-2022. Seven of the nine had lower annualised returns after launch, and none had a significant four-factor alpha after launch, though the before/after differences were not statistically significant either. This file's update to Oct-2026 points the same way: the median excess fell from +5.3 to +1.5 pp a year. The IIMA paper factors behave differently. The long-short momentum (WML) and value (HML) factors did not decay after the 2013 Agarwalla-Jacob-Varma paper; both were higher in 2014-2025 than in 1995-2013. Those factors are gross, long-short, broad-universe portfolios, which a long-only Rs 20,000 investor cannot hold. NSE Indices' own research reports full-period figures from the base date, and NSE Indices sells licences on these indices.

### Cited Findings
**Lalwani, peer-reviewed.**
- Citation: Vaibhav Lalwani (XLRI), "Are factor investing strategies successful out-of-sample: Evidence from the Nifty indices", *Applied Finance Letters* vol. 11 (2022; Crossref issue date 2023-01-23), pp. 94-108, DOI 10.24135/afl.v11i.604 — [article](https://doi.org/10.24135/afl.v11i.604), [PDF](https://ojs.aut.ac.nz/applied-finance-letters/1/article/download/604/159).
- Sample: 9 NSE strategy indices with at least 5 years live as of Sep-2022 — Nifty100 Low Vol 30, Alpha 50, Dividend Opp 50, Growth Sectors 15, High Beta 50, Low Vol 50, Nifty100 Quality 30, Alpha Quality Low-Vol 30 and Quality Low-Vol 30. Monthly TRI returns, from base date to Aug-2022. In-sample is base date to launch; out-of-sample is launch to Aug-2022. Benchmark is Nifty 500; the author says Nifty 50 gives similar results. Factor controls are the IIMA Agarwalla-Jacob-Varma SMB/HML/WML. **No fund costs or taxes**, so these are index-level, gross results.
- Annualised return, train → test: Nifty100 LV30 20% → 13%; Alpha 50 19% → 22%; Div Opp 50 12% → 11%; Growth Sectors 15 31% → 12%; High Beta 50 6% → 4%; Low Vol 50 20% → 16%; Nifty100 Q30 18% → 9%; Alpha Quality LV30 20% → 12%; Quality LV30 19% → 12% (Table 2). The volatility of most indices also fell after launch.
- Train-test differences in mean monthly return were not statistically significant: t-statistics from -0.16 to -1.68, Newey-West with 4 lags (Table 3). This low power is a reason for caution in both directions.
- About 4 of 9 indices had significant four-factor alpha in-sample (t > 2) and **none did after launch**. Even Alpha 50's abnormal return was insignificant after controlling for factors. Market beta rose in the test period for 7 of 9 indices, by about 0.09 on average (Section 3, Table 5).
- Active return vs Nifty 500, train → test: Nifty100 LV30 +5.9% → -0.9%; Alpha 50 +4.9% → +8.1%; Div Opp 50 +10.6% → -1.1%; Growth Sectors 15 +12.9% → -2.1%; High Beta 50 -8.6% → -9.7%; Low Vol 50 +5.5% → +1.4%; Nifty100 Q30 +5.8% → -2.6%; AQLV30 +5.4% → -0.8%; QLV30 +4.5% → -0.8% (Table 4).
- The author argues that factsheets showing performance from the base date "mask" the out-of-sample record, and that investors reading full-period figures are "likely to overestimate the expected future returns" — [PDF](https://ojs.aut.ac.nz/applied-finance-letters/1/article/download/604/159).
- Reasons this paper could mislead: only 9 indices; test windows of 5-11 years ending Aug-2022; overlapping, correlated indices; a journal outside the top tier. The update in section 2 extends the windows to Oct-2026 with the Nifty 50 as benchmark. Seven of Lalwani's nine indices had negative test-period active return against Nifty 500 (Table 4). Four of the seven still trailed Nifty 50 TRI from launch to Oct-2026: Growth Sectors 15, Nifty100 Quality 30, Quality LV30 and High Beta 50. Three were slightly ahead: Div Opp 50 (+1.0 pp a year), Nifty100 LV30 (+0.7) and AQLV30 (+1.5). The benchmark and the endpoint both differ from Lalwani's.

**Global studies cited by Lalwani.** These were not read in this session, so the details are as reported by Lalwani: McLean & Pontiff (2016) report that anomaly performance declines by up to 58% after publication; Linnainmaa & Roberts (2018) report lower out-of-sample factor returns; Jacobs & Müller (2020) report a reliable post-publication decline only in the US; Suhonen, Lennkh & Perez (2017) study 215 bank-index strategies across back-test and live periods — [Lalwani PDF](https://ojs.aut.ac.nz/applied-finance-letters/1/article/download/604/159).

**IIMA Indian Fama-French-Momentum data library.**
- Citation: Agarwalla, Jacob & Varma (2013, revised 2014), "Four factor model in Indian equities market", IIMA W.P. 2013-09-05.
- Contents: SMB, HML, WML and market factors at daily, monthly and yearly frequency. The latest release, 2025-12, covers Oct-1993 to Dec-2025. Built from CMIE Prowess DX, covering BSE and NSE stocks. Since the "new series", stocks below 10% of median market cap and stocks with a median price below Rs 1 are excluded. A survivorship-bias-adjusted version is recommended — [IIMA data library](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/), [Varma page](https://www.jrvarma.in/fama-french.html).
- The page reports annualised geometric returns since 01-Jan-1994: WML 10.65%, HML 6.61%, SMB -3.71%, market premium 4.93% (2025-12 release) — [IIMA](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/).
- My arithmetic on the yearly survivorship-adjusted file ([CSV](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/DATA/2025-12_FourFactors_and_Market_Returns_Yearly_SurvivorshipBiasAdjusted.csv)), geometric mean of calendar-year returns:
  - WML: 12.00% in 1995-2013 (19 years, 5 negative) vs 12.68% in 2014-2025 (12 years, 4 negative). For 2016-2023 it was 12.68%; for 2020-2025, 8.39%.
  - HML: 5.30% vs 8.58%. SMB: -9.06% vs +1.56%.
  - WML by year, 2014-2025: 11.3, 27.3, -1.7, 16.7, 22.8, 29.6, -3.8, 31.3, -0.1, 12.8, 20.6, -5.5.
  - These are paper long-short portfolios: gross of costs, involving shorting, and rebalanced on CMIE data. They are not investable by a retail investor.

**Vendor research (NSE Indices; conflict of interest, since it licenses these indices to fund houses).** The NSE momentum whitepaper, data as of 27-Feb-2026, reports full-period CAGRs from April 2005, mostly back-calculated:
- Nifty200 Momentum 30: 19.19% vs 15.08% for Nifty 200.
- Midcap150 Momentum 50: 23.00% vs 17.24% for Midcap 150.
- Nifty500 Momentum 50: 21.94% vs 18.85% for Nifty 500.
- It states a "performance gap of 300-600 bps" over most 10- and 15-year periods, and says quarterly rebalancing would add "around 20-50% more churn annually" than the semi-annual schedule.
- It does not separate back-calculated from live performance.
— [NSE Indices whitepaper](https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf). An earlier vendor paper is listed on the [Nifty200 Momentum 30 page](https://www.niftyindices.com/indices/equity/strategy-indices/nifty200-momentum-30): `nifty200_momentum_30_index_whitepaper_sep_20.pdf`, dated Sep-2020, just before the index launch. I did not read it.

**Other Indian studies.** A search turned up a CHRIST University thesis on BSE strategy indices (Bhagawan & Sathish Kumar), reporting that no BSE strategy index beat the Sensex across sub-periods, and an in-sample "smart beta in India" paper on CEEOL. Both are UNVERIFIED (search snippets only, not read): [CHRIST archive](https://archives.christuniversity.in/items/show/23770), [CEEOL](https://ceeol.com/search/article-detail?id=1068075).

### Inferences
- The IIMA results and the index results are not in conflict. The long-short factor premia (WML, HML) were not lower in 2014-2025 than before. What fell, for most indices, is the long-only, capped, large/mid-cap index version's excess over Nifty 50. The fall is largest where the index adds a quality screen or was launched after an unusually strong back-test window (Growth Sectors 15, Div Opp 50, NV20, the quality indices).
- The project's earlier finding was that a momentum rule on 40 large caps lost heavily to equal-weight buy-and-hold over 2016-2023. In the same years the IIMA WML factor earned 12.68% a year gross. The two are compatible: different universe (40 large caps vs broad market), long-only vs long-short, and costs. This is not evidence that a long-only large-cap momentum version captures WML.
- Low statistical power cuts both ways. Ten years of live data cannot reliably separate a 1-2 pp a year premium from zero, given factor-index tracking error against Nifty 50 of about 5-10% a year. That range is inferred from the betas and correlations on the factsheets (correlation with Nifty 50 of 0.84-0.95); I did not compute it.

### Gaps
- No SSRN, IIM, ISB or NSE working paper beyond Lalwani was found that measures the live-vs-back-test decay of Indian factor indices **at fund level** (after TER and TD).
- The McLean-Pontiff and other global papers were not read in this session; their figures are as reported in Lalwani.
- WebSearch hit a usage limit mid-session, so the literature search was narrower than intended. A follow-up should search SSRN for "Nifty smart beta out-of-sample", "Indian momentum anomaly decay" and "Indian factor ETF tracking difference".

## 5. Implementation for a Rs 20,000 investor: ETF spread and premium, index-fund frictions, statutory charges, turnover inside the index

### Takeaway
At Rs 20,000, the statutory and broker charges on one round trip are small: about Rs 15 for an ETF (about 0.08%) and about Rs 1.2 for a direct-plan index fund. The larger costs are recurring: the fund's TD of 0.24-1.91 pp a year (about Rs 50-380 a year on Rs 20,000) and, for ETFs, the price paid relative to NAV. The NSE ETF snapshot shows several factor ETFs with last trade 0.7-1.4% above the stated NAV. That snapshot is not a clean premium measure, but a gap of that size would cost more than a year of TER. A direct-plan index fund transacts at NAV and avoids the spread and premium.

### Cited Findings
**Statutory and broker charges on Rs 20,000.** Rates are from the repo's `config/costs.yaml`, which cites NSE circular NSE/FATAX/73524 (31-Mar-2026) for ETF STT and NSE's stamp duty table. The broker preset is shoonya, with zero delivery brokerage and a DP charge of Rs 9 + 18% GST per scrip per sell day. I did not re-verify these rates against the circular in this session; the file says "re-verify".
- ETF purchase: stamp 0.015% = Rs 3.00; NSE transaction charge 0.00297% = Rs 0.59; SEBI fee Rs 10 per crore = Rs 0.02; GST 18% on the last two = Rs 0.11. Total about Rs 3.7 (0.019%).
- ETF sale: STT 0.001% = Rs 0.20; transaction charge, SEBI fee and GST ≈ Rs 0.72; DP charge Rs 9 × 1.18 = Rs 10.62. Total about Rs 11.5 (0.058%).
- Round trip ≈ Rs 15 (0.077%), before spread. The repo models ETF slippage at 10 bps per side in its base tier, which is a further Rs 20 per side.
- Index fund, direct plan: the brief gives stamp duty of 0.005% on purchase (Rs 1.00) and STT of 0.001% on redemption of an equity-oriented fund (Rs 0.20). **I did not verify either rate against a primary source in this session.** No DP charge applies if units are held in statement-of-account form; if units are held in demat, a DP charge may apply on redemption, depending on the broker. Not verified.

**ETF price vs NAV snapshot.** NSE Indices' ETF list, [ETF.json](https://liveindexsa.niftyindices.com/jsonfiles/ETF.json), downloaded 31-Oct-2026 and probably reflecting the 30-Oct-2026 session, carries both a "nav" and an "ltP" (last traded price) field. LTP / nav - 1:
- Momentum ETFs: Motilal Midcap150 Momentum 50 (MOMIDMTM) +1.38%; Motilal Nifty200 Momentum 30 (MOMOMENTUM) +1.04%; MOMENTUM30 +0.98%; EMULTIMQ +0.88%; MOMENTUM50 +0.83%; NV20IETF +0.80%; GROWWMOM50 +0.74%.
- Others: DIVOPPBEES +0.48%; SBIETFQLTY +0.48%; VAL30IETF +0.42%; LOWVOLIETF +0.39%; ALPL30IETF +0.32%; ALPHA (Kotak Alpha 50) +0.31%; MIDQ50ADD +0.21%; MOALPHA50 +0.12%; AXISVALUE -0.17%.
- Caveat: Nifty 50 TRI rose about 0.5% on 30-Oct-2026 (34,866.61 → 35,043.45, [niftyindices](https://www.niftyindices.com/reports/historical-data)). If the "nav" field is the previous day's NAV, part of each gap is that day's market move, not a premium. The field definitions are not documented, so treat these figures as indicative only.
- The same file shows wide differences in trading activity. Its "trdVal" field (unit not stated) ranges from 0.23 for QUALITY30 and 1.14 for MON50EQUAL to 765 for ALPHA and 2,789 for LOWVOLIETF. Several factor ETFs therefore trade thinly — [ETF.json](https://liveindexsa.niftyindices.com/jsonfiles/ETF.json).

**Turnover inside the index.** Rebalancing frequency is from the September 2026 factsheets:
- Quarterly: Alpha 50, Nifty100 Alpha 30, Nifty200 Alpha 30, Nifty100 Low Volatility 30, High Beta 50, Low Volatility 50.
- Annual: Dividend Opportunities 50.
- Semi-annual: all others listed here, including all the momentum, quality and value indices and Nifty50 EW.
- Source: [NSE factsheets](https://www.niftyindices.com/indices/equity/strategy-indices).

NSE's whitepaper gives only relative churn: quarterly rebalancing of the momentum indices would add 20-50% more annual turnover than semi-annual — [NSE Indices whitepaper](https://www.niftyindices.com/docs/default-source/indices/nifty200-momentum-30/momentum-strategy-whitepaper_2026.pdf). No absolute turnover figure was found. The impact cost of this turnover falls on the fund and shows up in the TD in section 3: Alpha 50, quarterly, about -1.9 pp a year; Midcap150 Momentum 50 -1.4; Div Opp 50, annual, -0.27.

**Tax** (detail is with another researcher; rates as given in the brief and not verified here): STCG 20% within 12 months; LTCG 12.5% on gains above Rs 1.25 lakh a year. At Rs 20,000 of capital, a 10% gain is Rs 2,000, far below the Rs 1.25 lakh LTCG exemption. Whether the basic exemption limit can be set against STCG for a resident with little other income is for the tax researcher.

### Inferences
- For a one-off Rs 20,000 position, the ETF DP charge (Rs 10.62 per sell day) and the spread or premium matter more than STT or stamp duty. A direct-plan index fund on the same index avoids both but usually carries a higher TER than the ETF; for example, the DSP Top 10 EW ETF charges 0.23% and the index fund 0.40% Dir. Over multi-year holding the TER difference compounds, while the spread is paid once per trade. The break-even depends on holding period and on the premium actually paid, which I did not measure.
- Small and mid-cap factor ETFs (momentum, quality and momentum-quality on Midcap/Smallcap universes) are where a premium to NAV is most likely, judging by the snapshot. This was not confirmed against iNAV.

### Gaps
- No primary series of ETF iNAV vs traded price, or bid-ask spreads, was obtained. NSE publishes ETF iNAV intraday, but I found no historical download in this session. Without one, the premium and discount cost cannot be quantified.
- Minimum investment for direct-plan SIPs and lump sums, and exit loads, require each scheme's SID or KIM. These were not read; whether a Rs 100-500 SIP is possible is unconfirmed.
- The MF stamp duty (0.005%) and MF redemption STT (0.001%) rates were not checked against the Indian Stamp Act notification or the Finance Act, or against any SEBI/AMFI or NSE document.

## 6. Why live results could be overstated or misleading

### Takeaway
Even the "live" numbers above are fragile:
- Most windows are short. 12 of the 36 indices have less than 2.5 years live, and most funds launched in 2021-2024.
- Launch timing is selective: NSE launched 2023-2025 multi-factor indices whose back-tests showed +6 to +10 pp a year, and their live excess has ranged from -7.3 to +1.2 pp a year.
- Results depend heavily on the endpoint: the 2022-2023 launches showed +20 to +28 pp a year to Sep-2024 and +4 to +11 pp a year to Oct-2026.
- Survivorship among funds cannot be checked from live-scheme lists.
- Concentration is high: 30-50 stocks with 5% caps.

### Cited Findings
- **Short windows.** Among the 36 factor indices in section 2, 13 were launched in 2024-2025, with live windows of 1.2-2.7 years; 12 have less than 2.5 years. Over that period Nifty 50 TRI was 31,950.32 on 8-Feb-2024, 37,406.55 on 4-Sep-2024 and 35,043.45 on 30-Oct-2026. Source: [niftyindices TRI](https://www.niftyindices.com/reports/historical-data).
- **Launch after a strong back-test.** The indices launched in 2023-2025 showed back-calculated excesses over Nifty 50 TRI of +9.71 (Nifty500 Momentum 50), +8.61 (Nifty500 Multicap MQ 50), +8.96 and +9.19 (Smallcap250 and MidSmallcap400 MQ 100) and +6.24 pp a year (Nifty500 MQVLv 50). Their live excess to 30-Oct-2026 was -4.28, -7.28, +1.15, +0.86 and +0.02 respectively (section 2 tables, same source).
- **The reverse case.** Nifty500 Value 50 launched with almost no back-calculated excess (+0.08 pp a year) and then led by +7.69 pp a year live. The effect of launch selection on returns is not one-directional (same source).
- **Endpoint dependence.** Nifty200 Momentum 30 shows a live excess of +9.86 pp a year to 27-Sep-2024, +3.06 to 31-Oct-2025 and +2.65 to 30-Oct-2026. Nifty200 Alpha 30 shows +28.07, +11.51 and +10.53 (section 2 endpoint table).
- **Short-window volatility.** The Nifty 50 factsheet shows a 1-year TR of -9.45% and YTD -10.91% to 30-Oct-2026 ([Nifty 50 factsheet](https://www.niftyindices.com/Factsheet/ind_nifty50.pdf)). With the market down, relative results over 1-2 year windows can swing by several points a year.
- **Concentration.** Nifty200 Momentum 30 holds 30 stocks, with weights capped at the lower of 5% or 5 times the stock's free-float weight. Sector weights at 30-Sep-2026: Capital Goods 24.11%, Financial Services 21.17%, Metals & Mining 18.66%, Power 14.19%. Beta to Nifty 50 is 1.18 over 1 year — [Nifty200 Momentum 30 factsheet](https://www.niftyindices.com/Factsheet/Factsheet_Nifty200_Momentum30.pdf).
- **Higher market beta after launch.** Lalwani found market beta rose after launch for 7 of 9 indices (about +0.09 on average), so part of any live excess in a rising market is beta rather than factor premium — [Lalwani PDF](https://ojs.aut.ac.nz/applied-finance-letters/1/article/download/604/159).
- **Survivorship and the indices nobody productised.** Seven NSE factor indices with 1.7-13.9 years live have no fund in AMFI NAVAll (section 1). Among them, High Beta 50 trails Nifty 50 TRI by 3.71 pp a year and Quality Low-Vol 30 by 0.76, while AQVLV 30 leads by 3.67 and Low Vol 50 by 2.32. Funds exist mainly on indices chosen for launch, so the set of fund records is itself a selected sample. Closed or merged factor funds do not appear in NAVAll, so fund survivorship could not be checked — [AMFI NAVAll](https://www.amfiindia.com/spages/NAVAll.txt).
- **Factsheets can mislead.** Factsheet "Since Inception" figures start at the base date and contain 3.5-20 years of back-calculation, depending on the index (base and launch dates in section 1). Lalwani makes the same point — [Lalwani PDF](https://ojs.aut.ac.nz/applied-finance-letters/1/article/download/604/159).

### Inferences
- The cleanest live evidence is the indices launched before 2018 with 9-16 years live. For those, the gross live excess over Nifty 50 TRI is -3.7 to +8.2 pp a year, with a median of about +1.1 pp a year: 14 indices, 4 negative. Subtracting the 0.3-1.9 pp a year fund TD, and the TER gap to a 0.25% Nifty 50 index fund, leaves an expected net edge that is small and indistinguishable from zero for most of them. Alpha 50's index-level record is the clear exception, but its funds' TD is the largest.
- No statement here says any of these products will or will not beat Nifty 50 going forward. The numbers are reported next to the source data.

### Gaps
- The cross-sectional correlation between factor-index excess returns was not estimated. It is the input needed to say how many independent observations the 22 or so live records amount to.
- Survivorship among funds: no SEBI or AMFI list of wound-up or merged smart-beta schemes was found.

## 7. Downloadable datasets (URL, format, coverage, cost, access friction)

### Takeaway
All the data used here is free and can be scripted. The main frictions are niftyindices' one-year-per-request limit with an undocumented POST endpoint, AMFI's single-date NAV report, and AMFI's TER export, which is only exposed through the website's internal API.

### Cited Findings
- **NSE Indices TRI and price history.** [niftyindices.com historical data](https://www.niftyindices.com/reports/historical-data), "Total Returns Index" tab.
  - Access: POST to `/BackPage/getTotalReturnIndexString` with body `{"cinfo":"{'name':'<Trading_Index_Name upper>','startDate':'DD-Mon-YYYY','endDate':'DD-Mon-YYYY','indexName':'<long name>'}"}`. The response is JSON with Date, TotalReturnsIndex and NTR_Value (NTR for selected indices only).
  - Limits and setup: at most a 365-day range per request (enforced in the page script). A session cookie from the page itself is needed. Index names map through [IndexMapping.json](https://liveindexsa.niftyindices.com/assets/json/IndexMapping.json).
  - Coverage: from each base date. Free, no login.
  - The old `Backpage.aspx/...` endpoints return errors; the working path is `/BackPage/...`.
- **NSE Indices factsheets** (PDF, monthly, current month only): `https://www.niftyindices.com/Factsheet/<file>.pdf`, linked from each index page. They give base date, launch date, rebalancing frequency, returns and constituents.
- **NSE Indices ETF snapshot.** [ETF.json](https://liveindexsa.niftyindices.com/jsonfiles/ETF.json): JSON with 146 ETFs, fields symbol, assets (underlying index), nav, ltP, trdVal and qty. Current snapshot only; field definitions undocumented.
- **AMFI latest NAV.** [NAVAll.txt](https://www.amfiindia.com/spages/NAVAll.txt): semicolon-delimited text with all schemes' latest NAV (about 1.5 MB). Free.
- **AMFI historical NAV.** `https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx?frmdt=DD-Mon-YYYY&todt=DD-Mon-YYYY`: semicolon-delimited text, all schemes for the dates requested (about 1.2 MB per day). Free. Per-scheme full history needs many date requests.
- **api.mfapi.in** (UNVERIFIED secondary mirror of AMFI): `https://api.mfapi.in/mf/<scheme code>` returns a full daily NAV history as JSON. Free, but slow. Some responses arrived truncated (3 of about 45). Use it only to locate dates and verify values against AMFI.
- **AMFI TER disclosure.** [TER page](https://www.amfiindia.com/ter-of-mf-schemes). Internal API: `https://www.amfiindia.com/api/populate-te-rdata-revised?MF_ID=All&Month=MM-YYYY&strCat=<id>&strType=-1&excel=true`, which returns daily TER components (base expense, brokerage, transaction cost, statutory levies, total) for regular and direct plans as .xlsx. Category ids are 50 (Index Funds), 52 (Other ETFs), 101 (Index Funds - Equity) and 104 (Equity ETF). Free; the API is undocumented.
- **IIMA Fama-French-Momentum library.** [faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/](https://faculty.iima.ac.in/iffm/Indian-Fama-French-Momentum/): CSV files of SMB, HML, WML, market factor and risk-free rate, daily, monthly and yearly, plus size-value and size-momentum portfolio returns and breakpoints. Survivorship-adjusted and unadjusted versions. Oct-1993 to Dec-2025 (release 2025-12; three releases a year planned). Free; cite Agarwalla, Jacob & Varma (2013). Legacy series to 2019 is on a separate page.
- **Lalwani (2022) paper.** [PDF](https://ojs.aut.ac.nz/applied-finance-letters/1/article/download/604/159), open access.
- **NSE Indices research papers.** Linked from each index page (e.g. the momentum whitepaper PDF) and through the site's `/BackPage/getResearchPaper` endpoint. Vendor material.

### Inferences
- Every section 2 and section 3 figure can be reproduced from these free sources with about 150 HTTP requests. The scripts in the scratchpad `scripts/` folder do exactly this; they only fetch levels and compute ratios.

### Gaps
- No historical ETF iNAV or bid-ask dataset was found.
- No consolidated AMFI tracking-difference file was located.
- BSE (Asia Index) factor index history is not covered here. Lalwani notes that BSE publishes its strategy indices only from their launch date, with no back-calculated history.
