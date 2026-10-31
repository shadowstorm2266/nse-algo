# Tender-offer share buybacks in India as a small-shareholder edge (2016-2026)

Notes compiled 2026-10-31. Scope: Indian listed companies, tender-offer buybacks, resident individual with little or no other income, Rs 20,000 capital. No backtests were run. All arithmetic is on published figures, with the formula and inputs shown. "UNVERIFIED (secondary)" marks anything not taken from SEBI, NSE, BSE, RBI, the Income Tax Department, India Code or e-Gazette, a company letter of offer (LoF) or post-buyback public announcement (PBA), a peer-reviewed journal, or an SSRN/IIM/ISB/NSE working paper. Downloaded files are in `C:/Users/Advik/AppData/Local/Temp/claude/C--Users-Advik-desktop-nse-algo/505a1726-172d-483b-ba01-281b0a6c0ca7/scratchpad/r3_buyback/`.

## 1. Regulatory mechanics: SEBI Buy-back Regulations 2018 as amended, tender timeline, open-market route, record date under T+1

### Takeaway
A tender offer reserves the higher of 15% of the offer or the small shareholders' proportional entitlement for holders worth at most Rs 2 lakh at the record-date close. Tendering lasts 5 working days, runs through the exchange mechanism, and pays STT at 0.1%. In recent offers, settlement came 17-19 calendar days after the record date. The 2023 amendment phased out the open-market route by 1 Apr 2025. A 2026 amendment brought it back from 1 Aug 2026, and that route has no small-shareholder reservation. Under T+1, the last day to buy is the trading day before the record date.

### Cited Findings
- **Definition of small shareholder (primary).** A "Small Shareholder" holds shares with "market value, on the basis of closing price of shares on BSE or NSE, on which the highest trading volume ... on the Record Date was recorded, of not more than Rs 2,00,000" (Regulation 2(i)(n)). For TCS 2023 the cut-off was the NSE close of Rs 3,457.10, so holders of up to 57 shares qualified. — [TCS LoF, Nov 2023, para 19.7 (SEBI)](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf). The same wording appears in the Wipro LoF of June 2026, para 20.5.8: NSE close Rs 198.37, so up to 1,008 shares qualified. — [Wipro LoF 2026 (SEBI)](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf)
- **15% reservation (primary).** "In accordance with Regulation 6 ... the reservation for the Small Shareholders will be the higher of: 15% of the number of Equity Shares which the Company proposes to buy back ... or the number of Equity Shares entitled as per their shareholding as on the Record Date". For TCS 2023 the comparison was 61,44,579 shares (15%) against 4,09,657 (proportional), so 61,44,579 were reserved. — [TCS LoF 2023, paras 19.9-19.11](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf)
- **Fractional entitlements (primary, matters at Rs 20,000).** Fractional entitlement "shall be ignored". Small shareholders holding 3 or fewer shares get "a Tender Form with zero entitlement". They "may tender Additional Equity Shares ... and will be given preference in the Acceptance of one Equity Share". — [Bajaj Auto LoF, Mar 2024, paras 19.13-19.14 (SEBI)](https://www.sebi.gov.in/sebi_data/commondocs/mar-2024/Bajaj_Auto_Limited_LOO_p.pdf)
- **Holdings clubbed by PAN.** Holdings under the same PAN are combined to decide small-shareholder status, so several demat accounts do not give several reservations. — SIS Ltd PA, Jun 2025 (SEBI-hosted), [link](https://www.sebi.gov.in/sebi_data/commondocs/jun-2025/SIS%20Limited_PN_p.pdf). This comes from a search-result summary; I did not open the document. Treat it as UNVERIFIED until read.
- **Exchange mechanism circulars (primary).** The tender route uses the "Mechanism for acquisition of shares through Stock Exchange pursuant to Tender-Offers under Takeovers, Buy-Back and Delisting". The governing circulars are CIR/CFD/POLICYCELL/1/2015 (13 Apr 2015), CFD/DCR2/CIR/P/2016/131 (9 Dec 2016), SEBI/HO/CFD/DCRIII/CIR/P/2021/615 (13 Aug 2021) and SEBI/HO/CFD/PoD-2/P/CIR/2023/35 (8 Mar 2023). — [TCS PBA, Dec 2023, para 1.2 (SEBI)](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf)
- **STT on tendered shares (primary).** "Since the Buyback of shares shall take place through the settlement mechanism of the Stock Exchange, Securities Transaction Tax at 0.1% of the value of the transaction will be applicable." — [TCS LoF 2023, para 21.5](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf). The Bajaj Auto LoF of 2024 has the same text (line "Securities Transaction Tax at 0.1% ... will be applicable"). — [Bajaj Auto LoF 2024](https://www.sebi.gov.in/sebi_data/commondocs/mar-2024/Bajaj_Auto_Limited_LOO_p.pdf)
- **Tender timeline, TCS 2023 (primary).** Board 11 Oct 2023; PA 16 Nov; record date 25 Nov (a Saturday); tendering 1-7 Dec ("5 (Five) Working Days"); settlement, acceptance communication and return of unaccepted shares 12 Dec; extinguishment by 26 Dec. — [TCS LoF 2023](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf), [TCS PBA 2023](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf)
- **Tender timeline, Infosys 2025 (primary).** PA dated 7 Nov 2025; record date Fri 14 Nov; LoF 18 Nov; tendering 20-26 Nov; settlement and release of unaccepted shares 3 Dec; extinguishment 4 Dec. — [Infosys PBA, 4 Dec 2025 (BSE filing, Business Standard mirror)](https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/05122025/72F11864-D6DF-41CC-807A-289037B9E42B-152644.pdf)
- **Tender timeline, Wipro 2026 (primary).** Board-meeting intimation 9 Apr 2026; board 16 Apr; record date Fri 5 Jun; tendering 11-17 Jun; settlement 24 Jun. — [Wipro LoF 2026](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf)
- **Older timelines were longer (UNVERIFIED, secondary).** TCS 2018: record date 18 Aug 2018, payout 25 Sep. Dec 2018-Aug 2019 offers mostly took 6-9 weeks from record date to payout. — [HDFC Securities TCS note, 8 Mar 2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf); [HDFC Securities BSE note, 29 Aug 2019](https://www.hdfcsec.com/hsl.docs//BSE%20Ltd%20-%20Buyback%20update-201908291228149800252.pdf)
- **2023 amendment and open-market phase-out (UNVERIFIED, secondary).** The stock-exchange (open-market) route limit fell from 15% to 10% of paid-up capital and free reserves from 1 Apr 2023, to 5% from 1 Apr 2024, and to zero from 1 Apr 2025. Offers that opened before 1 Apr 2025 were grandfathered. Sources disagree on the notification date (7 Feb 2023 versus effect around 8-9 Mar 2023). — [Nishith Desai hotline](https://nishithdesai.com/research-and-articles/hotline/capital-markets-hotline/capital-markets-hotline-sebi-buy-back-of-securities-amendment-regulations-2023-8507). SEBI's investor page says the route "will not be allowed after April 1, 2025"; this comes from a search snippet and I did not open the page. — [investor.sebi.gov.in](https://investor.sebi.gov.in/buy_back_of_shares.html)
- **2024 amendments (UNVERIFIED, secondary).** The first amendment, SEBI/LAD-NRO/GN/2024/180 of 17 May 2024, lets material price movements be excluded from the VWAP and floor-price calculations. The second, SEBI/LAD-NRO/GN/2024/210 of 20 Nov 2024, covers entitlement computation when promoters opt out. — [taxguru, 2024 amendment](https://taxguru.in/sebi/sebi-buy-back-securities-amendment-regulations-2024.html); [taxguru, second amendment](https://taxguru.in/sebi/securities-exchange-board-india-buy-back-securities-second-amendment-regulations-2024.html)
- **2026 amendment: open-market route back from 1 Aug 2026 (UNVERIFIED, secondary).** SEBI consulted on 2 Apr 2026 and 8 May 2026. The board approved on 19 Jun 2026. The amendment regulations were notified 1 Jul 2026 (reported number SEBI/LAD-NRO/GN/2026/306) and took effect 1 Aug 2026. Reported terms:
  - open-market buyback must be less than 15% of paid-up capital and free reserves;
  - it must open within 4 working days of the PA and close within 66 working days;
  - at least 40% of the earmarked amount must be used in the first half (reported from the board decision);
  - promoter holdings are frozen at ISIN level, except for shares tendered in a tender offer;
  - a merchant banker becomes optional;
  - the gap between buybacks follows the Companies Act.

  SEBI cited the changed tax framework. — [AZB & Partners, 27 Oct 2026](https://www.azbpartners.com/bank/sebi-notifies-amendments-to-buyback-of-securities-regulations-2018/); [Cyril Amarchand blog, Jun 2026](https://corporate.cyrilamarchandblogs.com/2026/06/reintroduction-of-open-market-buyback-through-the-stock-exchange-and-other-changes-to-buyback-regime/); [LiveLaw](https://www.livelawbiz.com/amp/securities-law/sebi/securities-and-exchange-board-of-india-amends-buy-back-regulations-caps-stock-exchange-buybacks-15-percent-from-august-1-540220)
- **No reservation on the open-market route.** A SEBI-hosted July 2026 consultation addendum notes that the tender route reserves 15% for small investors and the open-market route does not. — [SEBI document (search snippet, not opened)](https://www.sebi.gov.in/sebi_data/commondocs/jul-2026/1%20list_p.pdf)
- **Last day to buy under T+1 (UNVERIFIED, secondary).** Under T+1, ex-date and record date generally fall on the same day. A buy on the ex-date settles after the record date, so the last day to buy is the trading day before the record date. A trading holiday can split the two dates. — [Zerodha support](https://support.zerodha.com/category/console/corporate-actions/ca-others/articles/what-does-ex-date-and-record-date-mean). The final move to T+1 on 27 Jan 2023 (NSE circular NSE/CMTR/54992, 26 Dec 2022) is reported by a blog only and is UNVERIFIED. Under T+2 the rule was two trading days: for the TCS record date of 23 Feb 2022, HDFC gave 21 Feb 2022 as the last buy date. — [HDFC TCS note 2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf)

### Inferences
- A Rs 20,000 holder is always a small shareholder, since the cap is Rs 2 lakh. For high-priced stocks, rounding decides the outcome. Rs 20,000 buys 5 TCS shares at Rs 3,457, entitled to 5 x 1/6, which rounds to 0. It buys 2 Bajaj Auto shares at Rs 7,909, entitled to 2 x 7/27, which also rounds to 0. Acceptance then comes only from the additional-share pool and the one-share preference, so the category-level acceptance ratio need not apply to a holder this small.
- Record dates that fall on non-trading days (TCS 25 Nov 2023 was a Saturday) move the effective last buy date to the last trading day whose T+1 settlement lands by the record date. Check each case against the exchange's record-date notice.
- With the open-market route back since 1 Aug 2026, companies can choose a route that gives small holders no reservation. Tender-offer supply could fall from FY 2026-27 onward. This is untested; no post-August data has been compiled.

### Gaps
- I did not read the consolidated 2018 Regulations on sebi.gov.in, the 2023 amendment gazette (number and date) or the 2026 amendment gazette text. The Cyril Amarchand 2023 blog fetch failed. The 2023 and 2026 amendment details above are secondary.
- I did not locate the primary NSE or BSE circulars on the T+1 transition and on the ex-date/record-date convention.
- The schedule rules (maximum days from PA to record date, and record date to opening) were not extracted from the Regulations' schedule. The figures above are observed dates in individual offers.

## 2. Historical small-shareholder acceptance ratios and buyback premiums, 2016-2026

### Takeaway
In the documents compiled, the small-shareholder acceptance ratio (AR = shares accepted / shares tendered in the reserved category) usually ran 2-5x the entitlement ratio, or reached 100%. The primary figures:

| Offer | Small-shareholder AR |
|---|---|
| TCS 2023 | 34.81% |
| Wipro 2019 | 53.49% |
| Infosys 2025 | 55.17% |

Buyback premiums over the record-date close were 16.7-26.4% in the large-cap offers checked. The broker-compiled tables show very different outcomes by period. The median annualised return of a "buy after announcement, tender, sell the rest at payout" sequence was +19.1% (23 offers, Dec 2020-Feb 2022) against -6.35% (22 offers, Dec 2018-Aug 2019). Those return figures are pre-cost and pre-tax, from a broker, and UNVERIFIED.

### Cited Findings

**Table A. Offers checked against company documents** (AR computed as reserved shares / validly tendered shares in the small-shareholder category; premium = buyback price / record-date close - 1)

| Company (year) | Board / intimation | Record date | Buyback price (Rs) | Record-date close (Rs) | Premium vs record-date close | Small entitlement | Small actual AR | General actual AR | Source |
|---|---|---|---|---|---|---|---|---|---|
| TCS (2023) | Board 11 Oct 2023 | 25 Nov 2023 | 4,150 | 3,457.10 (NSE) | 20.04% | 1 per 6 = 16.67% | 61,44,579 / 1,76,52,809 = **34.81%** | 3,48,19,276 / 25,09,40,139 = 13.88% | [LoF](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf), [PBA](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf) |
| Infosys (2025) | PA 7 Nov 2025 | 14 Nov 2025 | 1,800 | not extracted | n/a | 2 per 11 = 18.18% | 1,50,00,000 / 2,71,90,448 = **55.17%** | 8,50,00,000 / 79,84,33,905 = 10.65% | [PBA](https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/05122025/72F11864-D6DF-41CC-807A-289037B9E42B-152644.pdf), [notice](https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/19112025/F15A1874-23AA-4C73-B3A7-A427EDB912CB-172222.pdf) |
| Wipro (2019) | n/a | 21 Jun 2019 | 325 | n/a | n/a | n/a | 4,84,61,539 / 9,06,01,525 = **53.49%** | 27,46,15,384 / 4,67,01,50,622 = 5.88% | [PBA](https://www.wipro.com/content/dam/nexus/en/investor/buy-back/buyback2019/post-buyback-public-announcement-for-buy-back-of-equity-shares.pdf) |
| Wipro (2023) | Intimation 21 Apr 2023 (close 368.05); board 27 Apr | 16 Jun 2023 | 445 | 381.30 (NSE) | 16.71% | 62 per 265 = 23.40% | 77-78%, UNVERIFIED ([Chittorgarh](https://www.chittorgarh.com/buyback/tcs-buyback/55/), [Business Today](https://www.businesstoday.in/markets/stocks/story/wipro-share-buyback-check-offer-opening-date-last-date-entitlement-ratio-for-reserved-and-general-category-535693-2026-06-09)) | n/a | [LoF](https://www.sebi.gov.in/sebi_data/commondocs/jun-2023/Wipro_LTD_LOO_p.pdf) |
| Bajaj Auto (2024) | Board 8 Jan 2024 | 29 Feb 2024 | 10,000 | 7,909.35 (NSE) | 26.43% | 7 per 27 = 25.93% | about 26%, UNVERIFIED ([Upstox](https://upstox.com/news/market-news/stocks/bajaj-auto-buyback-know-about-acceptance-ratio-return-and-retail-quota-ahead-of-june-24-record-date/article-195782/)) | n/a | [LoF](https://www.sebi.gov.in/sebi_data/commondocs/mar-2024/Bajaj_Auto_Limited_LOO_p.pdf) |
| Wipro (2026) | Intimation 9 Apr 2026 (close 202.87); board 16 Apr | 5 Jun 2026 | 250 | 198.37 (NSE) | 26.03% | 11 per 56 = 19.64% | not found | n/a | [LoF](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf) |
| Bajaj Auto (2026) | Intimation 30 Apr 2026 | about 24 Jun 2026, UNVERIFIED | 12,000 | n/a (premium 25.74% over NSE close of 29 Apr 2026) | n/a | not extracted | not found | n/a | [PA](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Bajaj%20Auto%20Limited%20-%20PA_p.pdf) |

Notes on Table A:
- The Wipro 2023 general entitlement was 26 per 603 (4.31%). Wipro 2026 general was 10 per 197 (5.08%), Bajaj 2024 general was 1 per 82, and Infosys 2025 general was 17 per 706.
- Participation. In TCS 2023, 8,41,551 valid small-shareholder bids came in against 22,48,078 small shareholders: 37.4% took part. Small holders held 89.33% of the offer size. In Wipro 2026, 30,15,488 small shareholders held 45.77 crore shares, 76.28% of the 60-crore-share offer. In Wipro 2023, small holders held 64.11% of the offer.
- Wipro 2020: per a search-result excerpt of the Wipro PBA (document not opened), the small-shareholder category received a 6.24% response, which implies 100% acceptance.

**Table B. TCS and 2016-17 large caps, broker-compiled (UNVERIFIED, secondary)**

Sources: [HDFC Securities TCS note, 8 Mar 2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf), [HDFC Securities TCS note, 3 Sep 2018](https://www.hdfcsec.com/hsl.docs//TCS%20-%20Buyback%20Opportunity%20Note%20update%20-%20030918-201809031748079081979.pdf), [HDFC Securities Infosys note, 20 Nov 2017](https://www.hdfcsec.com/hsl.docs//Infosys%20-%20Buyback%20Opportunity%20Note%20Update%20-%20201117-201711201333499923090.pdf). The "price after" column is the closing price (CMP) on the payout date.

| Company (offer) | Board date (price day after, Rs) | Record date | Buyback price (Rs) | Small entitlement | Small actual AR | Price on payout date (Rs) | HDFC return for buy-after-announcement* |
|---|---|---|---|---|---|---|---|
| TCS 2017 | 20 Feb 2017 (2,506.5) | 8 May 2017 | 2,850 | 45% | 100% | 2,695.4 | 47.2% p.a. |
| TCS 2018 | 15 Jun 2018 (1,830.7) | 18 Aug 2018 (close 2,012.75) | 2,100 | 44.8% | 100% | 2,183.1 | 52.6% p.a. |
| TCS 2020 | 7 Oct 2020 (2,825) | 28 Nov 2020 | 3,000 | 40.0% | 100% (1,63,364 of 8,01,794 small holders tendered) | 3,173 | 23.3% p.a. |
| TCS 2022 | n/a | 23 Feb 2022 (close 3,563.80) | 4,500 | 1 per 7 = 14.3% | 24% or 26% (Chittorgarh contradicts itself); general 2.45% | n/a | n/a |
| HCL Tech 2017 | 20 Mar 2017 (863) | 22 May 2017 | 1,000 | 38% | 68% | 840 | 34.4% |
| Mphasis 2017 | 31 Jan 2017 (560) | 31 Mar 2017 | 635 | 74% | 100% | 619 | 40.2% |
| Hexaware 2017 | 25 Oct 2016 (202) | 6 Jan 2017 | 240 | 5% | 22% | 219 | 32.0% |
| Sasken 2017 | 27 Oct 2016 (416) | 6 Jan 2017 | 410 | 23% | 100% | 391 | -4.3% |
| SKF 2017 | 13 Feb 2017 (1,407) | 7 Apr 2017 | 1,500 | 57% | 100% | 1,613 | 19.8% |
| Infosys 2017 | 19 Aug 2017 (923) | 1 Nov 2017 | 1,150 | 23 per 81 = 28% | not found | n/a | n/a |
| Wipro 2017 | 20 Jul 2017 (269) | 15 Sep 2017 | 320 | n/a | not found | n/a | n/a |

\* HDFC assumes entry at the board-date-plus-one price and sale of unaccepted shares on payout day. The returns are pre-cost and pre-tax, and are annualised in the 2022 note. The 2017 note's column is "returns earned by investor who bought after announcement".

The 2018 note also states: "On an overall basis in the past offers, the acceptance ratio is either 100% or 1.8 to 5.6 times the entitlement ratio" ([HDFC 2018](https://www.hdfcsec.com/hsl.docs//TCS%20-%20Buyback%20Opportunity%20Note%20update%20-%20030918-201809031748079081979.pdf)). The Nov 2017 note gives "1.8 to 4.7 times" ([HDFC Nov 2017](https://www.hdfcsec.com/hsl.docs//Infosys%20-%20Buyback%20Opportunity%20Note%20Update%20-%20201117-201711201333499923090.pdf)).

**Table C. Tender offers completed Dec 2018-Aug 2019, broker-compiled (UNVERIFIED, secondary)**

Source: [HDFC Securities BSE Ltd note, 29 Aug 2019](https://www.hdfcsec.com/hsl.docs//BSE%20Ltd%20-%20Buyback%20update-201908291228149800252.pdf). Columns: record date; buyback price (Rs); small entitlement; small actual AR; price on payout date; HDFC annualised return. HDFC's return assumes entry at the board-date-plus-one price and sale of unaccepted shares at payout, pre-cost and pre-tax.

| Company | Record date | Buyback price | Entitlement | Actual AR | Payout price | Annualised return |
|---|---|---|---|---|---|---|
| Triveni Engg | 19-Jun-19 | 100 | 10.6% | 33.9% | 56.1 | -32.7% |
| Savita Oil | 12-Jun-19 | 1,605 | 13.0% | 30.3% | 902.9 | -92.4% |
| SH Kelkar | 20-Jun-19 | 180 | 12.8% | 33.8% | 112.1 | -48.6% |
| FDC | 07-Jun-19 | 350 | 9.2% | 19.5% | 159.5 | -24.6% |
| GeeCee | 07-Jun-19 | 135 | 7.6% | 43.7% | 110.4 | 18.0% |
| James Warren Tea | 17-May-19 | 115 | 41.8% | 100% | 110.0 | -21.0% |
| eClerx | 10-May-19 | 1,500 | 13.3% | 18.8% | 786.0 | -63.0% |
| Expleo | 12-Apr-19 | 550 | 9.3% | 28.2% | 411.9 | 9.2% |
| Tulive | 22-Apr-19 | 350 | 100% | 100% | 249.9 | 136.3% |
| Quick Heal | 26-Apr-19 | 275 | 16.5% | 29.5% | 183.9 | -35.5% |
| Zenith Fibres | 12-Apr-19 | 55 | 20.0% | 100% | 52.1 | 4.2% |
| Balrampur Chini | 18-Apr-19 | 175 | 8.1% | 38.7% | 154.0 | 122.4% |
| Metroglobal | 12-Apr-19 | 56 | 50.8% | 100% | 57.0 | 34.7% |
| Aarti Drugs | 29-Mar-19 | 900 | 2.6% | 7.4% | 593.8 | -32.0% |
| PBM Polytex | 08-Mar-19 | 80 | 20.8% | 100% | 75.9 | 5.0% |
| Techno Electric | 03-Jan-19 | 410 | 21.0% | 44.3% | 241.9 | 64.0% |
| Tech Mahindra | 06-Mar-19 | 950 | 10.5% | 26.7% | 797.1 | 10.4% |
| IEX | 15-Feb-19 | 185 | 7.3% | 29.5% | 156.0 | -10.1% |
| Monte Carlo | 22-Feb-19 | 550 | 6.5% | 12.0% | 346.4 | -9.6% |
| R Systems | 01-Feb-19 | 65 | 8.8% | 34.0% | 46.6 | -3.1% |
| Shanti Gears | 08-Feb-19 | 140 | 21.4% | 100% | 134.0 | 21.5% |
| HEG | 09-Feb-19 | 5,500 | 10.0% | 17.2% | 2,088.8 | -110.5% |

BSE Ltd 2019 (the note's subject): record-date close Rs 525.20, buyback price Rs 680 (premium 29.5%), entitlement 13.5%; actual AR not given.

**Table D. Tender offers completed Dec 2020-Feb 2022, broker-compiled (UNVERIFIED, secondary)**

Source: [HDFC Securities TCS note, 8 Mar 2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf). Same columns and assumptions as Table C.

| Company | Record date | Buyback price | Entitlement | Actual AR | Payout price | Annualised return |
|---|---|---|---|---|---|---|
| Ajanta Pharma | 14-Jan-22 | 2,550 | 19.9% | 56.2% | 1,741.6 | -19.9% |
| MOIL | 31-Dec-21 | 250 | 19.7% | 66.3% | 171.2 | 94.6% |
| MPS | 17-Dec-21 | 900 | 18.3% | 46.6% | 658.4 | 33.8% |
| Cheviot | 17-Dec-21 | 1,725 | 9.2% | 30.7% | 1,353.1 | 6.2% |
| Nucleus Software | 27-Nov-21 | 700 | 15.4% | 50.4% | 571.5 | 18.2% |
| SH Kelkar | 12-Nov-21 | 210 | 5.9% | 29.9% | 169.8 | 137.0% |
| Goldiam | 27-Oct-21 | 1,200 | 6.4% | 55.2% | 775.9 | -3.0% |
| eClerx | 30-Sep-21 | 2,850 | 17.6% | 45.2% | 2,379.3 | 80.2% |
| Mahalaxmi Rubtech | 27-Aug-21 | 70 | 34.2% | 100% | 77.6 | 26.6% |
| Star Cement | 26-Aug-21 | 150 | 12.8% | 28.8% | 104.0 | 2.8% |
| Gandhi Spl Tubes | 31-Aug-21 | 550 | 12.5% | 40.8% | 434.2 | 49.1% |
| R Systems | 27-Aug-21 | 225 | 7.1% | 87.4% | 209.5 | 68.3% |
| Shriram Pistons | 12-Aug-21 | 1,020 | 87.8% | 100% | 925.3 | -3.0% |
| Welspun India | 24-May-21 | 120 | 9.2% | 78.2% | 122.7 | 114.3% |
| Quick Heal | 30-Apr-21 | 245 | 12.2% | 100% | 276.9 | 80.4% |
| SIS | 09-Apr-21 | 550 | 9.9% | 23.8% | 431.0 | 19.1% |
| Smartlink | 01-Mar-21 | 95 | 25.0% | 100% | 96.5 | 11.7% |
| Aarti Drugs | 01-Apr-21 | 1,000 | 1.4% | 9.4% | 756.6 | 37.3% |
| Savita Oil | 05-Mar-21 | 1,400 | 4.8% | 19.2% | 1,065.1 | 10.4% |
| NIIT | 24-Feb-21 | 240 | 11.1% | 30.4% | 169.7 | -21.3% |
| Gujarat Apollo | 26-Feb-21 | 222 | 13.7% | 100% | 212.7 | 11.4% |
| Suprajit | 22-Feb-21 | 320 | 3.7% | 27.2% | 255.0 | 25.8% |
| Bharat Rasayan | 05-Mar-21 | 11,500 | 15.2% | 36.2% | 9,893.0 | -1.4% |

Several payout prices sit far below the buyback price (Aarti Drugs, NIIT, Bharat Rasayan). Some Rs-level payout figures may reflect splits or bonuses in the source; this is unchecked.

**Summary arithmetic on Tables C and D** (my calculation on the published rows; script in scratchpad `scripts/calc.py`)

| Period | Offers | Median small AR | Mean small AR | Offers at AR = 100% | Median AR / entitlement (AR < 100%) | Median annualised return | Mean annualised return | Negative returns |
|---|---|---|---|---|---|---|---|---|
| Dec 2018-Aug 2019 (Table C) | 22 | 33.85% | 47.6% | 6 | 2.59x | -6.35% | -2.6% | 12 of 22 |
| Dec 2020-Feb 2022 (Table D) | 23 | 46.6% | 54.9% | 5 | 3.3x | +19.1% | +33.9% | 5 of 23 |

Record per claim, Tables B-D:
- Source: HDFC Securities retail research notes (broker, not primary).
- Period: 2016-2022. Sample: 8 + 22 + 23 offers.
- In-sample: these are descriptive tables of completed offers, not out-of-sample tests.
- Costs and taxes: not included.
- Could be overstated: the entry price is the day-after-board price, not a record-date entry; returns are annualised over short holds; the sample covers only offers that "completed in the last 1 year" at each note date; the 2019 window shows the result depends heavily on the period.

### Inferences
- The small-shareholder AR is set by participation. Across Tables A-D, small holders tendered far less than their full entitlement: 37.4% of TCS 2023 small holders bid, and 20% of TCS 2020 small holders tendered. That kept AR above entitlement. AR fell in large, widely publicised offers with big premiums: TCS went from 100% in 2017-2020 to 24-26% in 2022 and 34.8% in 2023.
- The 2019 window shows the unaccepted shares can wipe out the premium. HEG, Savita, eClerx and SH Kelkar showed payout prices 35-62% below the buyback price, giving deeply negative annualised returns even at 17-34% acceptance.
- For large IT offers in 2023-2025, the primary small-shareholder ARs were 34.8% (TCS 2023) and 55.2% (Infosys 2025). The general category got 10.7-13.9%. The small-shareholder reservation roughly tripled to quintupled the accepted fraction against the general category.

### Gaps
- Primary PBAs were not obtained for TCS 2017/2018/2020/2022, HCL Tech 2017/2018, Wipro 2017/2020/2023/2026, Infosys 2017, Bajaj Auto 2024/2026, or the small and mid caps in Tables C-D. Those ARs remain broker or aggregator figures. tcs.com PDF links returned HTML to a script; Chittorgarh's robots.txt disallows AI crawlers, so I did not scrape it beyond one page.
- Prices "around the record date" and "after the offer" exist only where an LoF states the record-date close, or where HDFC reports the payout-date price. There are no primary post-offer price series; that needs exchange bhavcopies (Section 7).
- No complete 2022-2026 list of tender offers with ARs was found. HCL Tech 2018 and many 2023-2026 small caps are missing.

## 3. Academic and regulator studies on Indian buyback announcement returns and record-date behaviour

### Takeaway
The Indian literature found covers announcement-window abnormal returns, with mixed and small results. No study was found that measures the record-date price path, the post-offer drop on unaccepted shares, or the returns from the small-shareholder reservation. The most recent peer-reviewed paper reports a significant positive pre-announcement drift and a significant negative post-announcement drift, but its tables are hard to reconcile with its abstract.

### Cited Findings
- **Suresha B., Desai, Thomas, John and Koshy (2024)**, "Announcement effect of tender offer share buyback around turmoil period - evidence from India", *Investment Management and Financial Innovations* 21(3), 160-169, doi:10.21511/imfi.21(3).2024.14. Published 5 Aug 2024, open access. — [PDF](https://businessperspectives.org/images/pdf/applications/publishing/templates/article/assets/20528/IMFI_2024_03_Suresha%20B.pdf)
  - Sample: NSE-listed tender-offer buybacks, 75 firms Apr 2016-Feb 2020 and 43 firms Mar 2020-Mar 2022.
  - Method: market-model event study, window -21 to +21 days, in-sample, no costs or taxes.
  - Abstract: "statistically significant cumulative abnormal average returns (CAAR) were also found on the event day".
  - Table 2 (pre-COVID) instead shows event-day CAAR 0.3009 with t = 0.705, which is not significant. The pre-event window CAAR is 3.6075 (t = 8.45) and the post-event window -5.4442 (t = -12.75). Units are not stated, probably percent.
  - Table 4 (post-COVID): event-day 0.001 (t = 0.06), pre-event window 0.028 (t = 3.33), post-event window -0.053 (t = -6.23).
  - The authors read the negative post-event CAAR as "profit booking and portfolio adjustments".
  - Caveats: modest journal; abstract and tables disagree; the event is the announcement, not the record date or settlement.
- **Peer-reviewed by venue, not opened (summaries from search results).**
  - *Vision* 13(1), 2009, 68 announcements: day-0 average abnormal return 2.83% and 41-day CAR 5.16%. Open-market repurchases showed greater signalling than fixed-price tender offers. — [RePEc entry](https://ideas.repec.org/a/sae/vision/v13y2009i1p59-78.html)
  - Varma and Munjal, *Indian Journal of Finance* (2016, per search), 54 tender offers 2004-2013: positive reaction on the day after announcement. — [i-scholar entry](https://i-scholar.in/index.php/ijf/article/view/202572)
  - Another tender-offer study found negative abnormal returns after the offer closed and none around the announcement. — [i-scholar GJRM](https://i-scholar.in/index.php/gjrm/article/view/78497)
  - Chatterjee and Mukherjee (2015, *Global Business Review*), open-market buybacks 2008-2012: no increase in CARs. Chatterjee and Dutta (2015, *Vikalpa* 40(4)) studies open-market announcements; contents not retrieved.
- **SEBI's own rationale for the 2023 phase-out (secondary report of the SEBI position).** "inequity was inherent in the open market buyback mechanism, as the company's purchase orders could get matched with only one or a few" shareholders. Tax treatment was also cited. — [Nishith Desai hotline](https://nishithdesai.com/research-and-articles/hotline/capital-markets-hotline/capital-markets-hotline-sebi-buy-back-of-securities-amendment-regulations-2023-8507)

### Inferences
- The announcement-window evidence is not the trade studied here. The "buy before record date" sequence enters after the announcement and the record-date run-up, and its main risk is the post-settlement price of unaccepted shares, which no paper found measures.
- The negative post-event CAAR (Suresha et al.) agrees in direction with the broker tables, where unaccepted shares often sold below the record-date price. This direction is not quantified for the record-date entry.

### Gaps
- No SSRN, IIM, ISB or NSE working paper on Indian tender-offer buybacks, small-shareholder acceptance or record-date behaviour was found in the searches run. This is a gap; such work may exist under other keywords.
- No SEBI study or annual-report statistic on the number of tender offers by year, or on small-shareholder acceptance, was retrieved.

## 4. Tax treatment for FY 2026-27 (tax year 2026-27 under the Income-tax Act, 2025) and whether it changed after the 1 Oct 2024 deemed-dividend rule

### Takeaway
The rule did change. The Finance Act, 2026 (No. 4 of 2026, assented 30 Mar 2026) omitted the buyback limb of "dividend", s.2(40)(f) of the Income-tax Act 2025. From 1 Apr 2026, buyback consideration is taxed as capital gains under s.69(1): consideration less cost. Promoters pay an additional tax under the new s.69(2). For a resident individual with no other income, short-term gains on STT-paid shares are taxed at 20% under s.196(1). However, s.196(2) reduces those gains by the unused basic exemption, which is Rs 4,00,000 under the new regime in s.202. The tax on a Rs 20,000 position would therefore be nil. The companies say no TDS is deducted for residents.

### Cited Findings
- **Finance Act 2026 commencement (primary).** "THE FINANCE ACT, 2026 (NO. 4 OF 2026) [30th March, 2026]". Under s.1(2)(a), "sections 2 to 129 ... shall come into force on the 1st day of April, 2026". — [Gazette of India Extraordinary No. 9, 30 Mar 2026](https://egazette.gov.in/WriteReadData/2026/271439.pdf)
- **Deemed-dividend limb removed (primary).** Finance Act 2026 s.35: "In section 2 of the Income-tax Act, 2025 ... (b) in clause (40),-- (A) sub-clause (f) shall be omitted". — [same gazette](https://egazette.gov.in/WriteReadData/2026/271439.pdf). The omitted text, as enacted, reads: s.2(40)(f) "any payment by a company on purchase of its own shares from a shareholder as per section 68 of the Companies Act, 2013". — [Income-tax Act 2025, Gazette No. 35, 21 Aug 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf)
- **Capital-gains rule (primary).** ITA 2025 s.69(1): "If a shareholder ... receives any consideration from any company for the purchase of its own shares ... the difference between the cost of acquisition and the value of consideration so received shall be deemed to be the 'Capital gains' arising to such shareholder ... in the year in which the company purchases the shares". The original s.69(2) said that consideration "of the nature referred to in section 2(40)(f) ... shall be deemed to be nil". That was the deemed-dividend mechanism. — [ITA 2025 gazette](https://egazette.gov.in/WriteReadData/2025/265620.pdf)
- **New s.69(2) and (3), promoters only (primary).** Finance Act 2026 s.42 substitutes s.69(2) and (3). Where a company buys back "in accordance with the provisions of section 68 of the Companies Act, 2013 and the shareholder ... is a promoter", tax is (a) normal tax plus (b) "an additional income-tax". The additional rates are:

  | Gain | Promoter is a domestic company | Promoter is any other person |
  |---|---|---|
  | STCG under s.196 | 2% | 10% |
  | LTCG under s.197/198 | 9.5% | 17.5% |

  For a listed company, "promoter" follows reg. 2(k) of the SEBI Buy-back Regulations. — [FA 2026 gazette](https://egazette.gov.in/WriteReadData/2026/271439.pdf)
- **Surcharge on promoter tax.** The Finance Act's rates chapter says: "In cases in which tax has to be charged and paid under section 69 ... the tax shall be charged and paid at the rates as specified in those sections and shall be increased by a surcharge ... at the rate of 12% of such tax". — [FA 2026 gazette](https://egazette.gov.in/WriteReadData/2026/271439.pdf). I did not confirm which Act's "section 69" that sub-section refers to; it matters for promoters only. Secondary sources disagree on how the surcharge applies. — [taxguru](https://taxguru.in/income-tax/buy-taxation-finance-act-2026-resettling-unsettledae.html) (UNVERIFIED)
- **STCG rate and basic-exemption adjustment (primary).** s.196(1) covers an equity share whose sale "is chargeable to securities transaction tax", at a rate of 20%. s.196(2): "In the case of an individual ... being a resident, where the total income, as reduced by short-term capital gains ... is below the maximum amount which is not chargeable to income-tax, then ... such short-term capital gains shall be reduced by the amount by which the total income as so reduced falls short". — [ITA 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf)
- **LTCG (primary).** s.198(2)(a) taxes "long-term capital gains exceeding 125000 at the rate of 12.5%", with STT paid on acquisition and transfer. s.198(3) has the same basic-exemption shortfall rule. — [ITA 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf)
- **New-regime slab and rebate (primary).** s.202 table: "Upto 400000 Nil". s.156(2) allows a rebate up to Rs 60,000 if income is at most Rs 12 lakh under s.202(1). s.156(3) caps it at tax "as per the rates provided in section 202(1)". — [ITA 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf)
- **Set-off and carry-forward of capital losses (primary).**
  - s.108(2)(a): a short-term capital loss "shall be set off against the income, computed in respect of any other capital asset". s.108(2)(b): a long-term loss is set off only against long-term gains.
  - s.109(2): "the loss under the head 'Capital gains' shall not be set off against income under any other head".
  - s.111(1)-(2): unabsorbed capital loss is carried forward. A short-term loss can be used against any capital gains, a long-term loss only against long-term gains, "for not more than eight tax years".
  - Source: [ITA 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf)
- **No TDS for residents under the new regime (primary, company document).** "For Resident Shareholders, the Company is not required to deduct any Tax at Source." The same LoF describes the new system: STCG at 20% if held 12 months or less; LTCG at 12.5% with Rs 1.25 lakh exempt; pre-1 Feb 2018 grandfathering of cost; additional s.69(2)(b) tax for promoters. — [Wipro LoF, Jun 2026](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf)
- **The 1 Oct 2024-31 Mar 2026 regime (primary, company document).** "Previously, from October 1, 2024, until March 31, 2026, buyback proceeds were fully taxed as deemed dividends at the shareholder's applicable slab rates, the original cost of acquiring the shares was recognized as a capital loss, which be offset against other capital gains." — [Wipro LoF 2026](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf). The Finance (No. 2) Act 2024 text (s.2(22)(f), s.46A, s.194) was not read in this session.
- **Dividend TDS threshold (primary, ITA 2025).** The s.393 exemption table excludes dividends to an individual shareholder paid other than in cash where the year's total "does not exceed 10,000". — [ITA 2025](https://egazette.gov.in/WriteReadData/2025/265620.pdf). For FY 2024-25 and FY 2025-26 under the 1961 Act, I did not verify the TDS rate under s.194 (10% for residents), the threshold (reportedly Rs 5,000, then Rs 10,000 from 1 Apr 2025) or Form 15G under s.197A; all three are UNVERIFIED.
- **Commentary agrees on the 2026 reversal (UNVERIFIED, secondary).** Vinod Kothari (1 Feb 2026) says the pre-Oct 2024 position is restored except for the promoter rates, and the capital loss carries forward 8 years. — [Vinod Kothari](https://vinodkothari.com/2026/02/buyback-taxation-rationalised-with-limited-relief-to-promoter-shareholders/). Cyril Amarchand ties SEBI's reinstatement of open-market buybacks to the "updated tax regime". — [CAM blog](https://corporate.cyrilamarchandblogs.com/2026/06/reintroduction-of-open-market-buyback-through-the-stock-exchange-and-other-changes-to-buyback-regime/)
- **Earlier regimes (UNVERIFIED, from background knowledge, no primary text read).** From 5 Jul 2019 to 30 Sep 2024, listed companies paid buyback tax under 1961-Act s.115QA, and shareholders were exempt under s.10(34A). Before 5 Jul 2019, shareholders in listed-company buybacks were taxed on capital gains. These regimes matter for comparing historical returns but were not checked against the statute.

### Inferences
- **FY 2026-27, zero-income resident.**
  - Gain on accepted shares = (buyback price - cost) x shares accepted, which is STCG under s.196 if held 12 months or less.
  - A loss on unaccepted shares sold below cost is a short-term capital loss. It is set off against that gain in the same year under s.108(2)(a).
  - Net STCG up to Rs 4 lakh (less any other income) is reduced to nil by s.196(2), so tax is nil and no TDS applies.
  - A net loss carries forward 8 tax years, but only against future capital gains (s.109(2), s.111). The return-filing condition for carry-forward was not checked.
- **1 Oct 2024-31 Mar 2026, zero-income resident.**
  - The whole accepted consideration was dividend income at slab rates, nil within the basic exemption and rebate.
  - The full cost of the accepted shares became a capital loss, usable only against later capital gains.
  - For someone whose gains are already untaxed because of the basic exemption, that loss has little tax value.
  - TDS could hit accepted consideration above the per-company threshold, refundable by filing a return. Rate and threshold are unverified.
- Small holders face roughly the same tax in both regimes. The 2026 change matters more for higher-income holders and for which route companies choose (Section 6).

### Gaps
- The Finance (No. 2) Act 2024, Finance Act 2025 and CBDT circulars were not downloaded, so the 2024-26 TDS rate, threshold and Form 15G position rest on the company LoF and secondary sources.
- Not verified: the ITA 2025 equivalents of the Form 15G declaration, the loss-return filing condition, and how s.156 rebate interacts with s.196 gains. The latter is moot at zero income because of s.196(2).
- Incometaxindia.gov.in returned HTTP 403 to fetches, so no CBDT FAQ or circular on buybacks after 1 Apr 2026 was read.

## 5. Expected value of "buy before record date, tender, sell unaccepted shares" for a Rs 20,000 resident with zero other income

### Takeaway
Before costs, the per-event result is roughly AR x premium plus (1 - AR) x the move in the unaccepted shares. In the large-cap offers checked, the first term was about 4-13% of the position. Whether the event ended positive depended mostly on how far the unaccepted shares fell between the record date and settlement. Breakeven drops were 4-10% at observed or entitlement-level ARs. Round-trip costs on Rs 20,000 are about 0.39% (Rs 78) at base slippage and 0.53% (Rs 106) at 10 bps. Tax is nil in both regimes for this person. Rounding makes Rs 20,000 too small to get a proportional entitlement in high-priced stocks. None of these figures is a backtest; the price after settlement is the missing input.

### Cited Findings
- **Cost inputs.**
  - The repo config (owner's file, re-verify before use) gives: STT 0.1% on delivery buy and sell; stamp 0.015% on buy; NSE transaction charge 0.00297% per leg; SEBI fee Rs 10 per crore; GST 18% on transaction charge plus SEBI fee plus DP charge; zero delivery brokerage; DP charge Rs 9 + GST per scrip per sell day. — `C:/Users/Advik/desktop/nse-algo/config/costs.yaml` (not a primary source).
  - STT of 0.1% on the tendered shares is confirmed by company LoFs: [TCS 2023](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf), [Bajaj Auto 2024](https://www.sebi.gov.in/sebi_data/commondocs/mar-2024/Bajaj_Auto_Limited_LOO_p.pdf).
  - Not verified: whether the exchange transaction charge and the DP charge apply to tender-window bids. I assumed both apply, which is conservative.
- **Cost arithmetic on Rs 20,000** (my calculation; script in scratchpad `scripts/calc.py`).
  - Buy leg = 20,000 x (0.1% + 0.015% + 0.00297% + 0.0001%) + 18% x (transaction + SEBI) = **Rs 23.72**.
  - Sell legs, excluding DP = 20,000 x (0.1% + 0.00297% + 0.0001%) + GST = **Rs 20.72**.
  - DP charge = 9 x 1.18 = **Rs 10.62** per sell day.
  - Totals, assuming two sell days (tender settlement plus the market sale of unaccepted shares) and slippage on both market legs:

    | Slippage per side | Total cost | Share of position |
    |---|---|---|
    | 3 bps (base) | Rs 77.69 | 0.388% |
    | 10 bps (stress) | Rs 105.69 | 0.528% |

  - With one sell day (100% acceptance): Rs 67.07 (0.335%) at base slippage.
- **Holding period from last buy day to settlement (primary dates).**
  - TCS 2023: buy by Fri 24 Nov 2023 (record date Sat 25 Nov), settlement 12 Dec, about 18 days.
  - Infosys 2025: record date 14 Nov, settlement 3 Dec, about 20 days.
  - Wipro 2026: record date 5 Jun, settlement 24 Jun, about 20 days.
  - Sources: [TCS PBA](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf), [Infosys PBA](https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/05122025/72F11864-D6DF-41CC-807A-289037B9E42B-152644.pdf), [Wipro LoF 2026](https://www.sebi.gov.in/sebi_data/commondocs/jun-2026/Wipro%20Limited%20-%20LOF_p.pdf)
  - Pre-2023 offers took about 5-9 weeks per the HDFC tables (UNVERIFIED).
- **How far the price after the offer sat below the earlier price** (arithmetic on the published HDFC rows, UNVERIFIED secondary inputs; script `scripts/calc2.py`). This compares the payout-date price with the day-after-board price, not with the record-date price.

  | Period | Median premium of buyback price over day-after-board price | Median payout price vs day-after-board price | Median payout price vs buyback price | Offers with payout price below day-after-board price |
  |---|---|---|---|---|
  | Dec 2020-Feb 2022, 23 offers | 18.7% | -1.8% | -20.3% | 14 of 23 |
  | Dec 2018-Aug 2019, 22 offers | 22.7% | -9.0% | -28.5% | 18 of 22 |

  Sources: [HDFC 2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf), [HDFC 2019](https://www.hdfcsec.com/hsl.docs//BSE%20Ltd%20-%20Buyback%20update-201908291228149800252.pdf)

### Formulas and per-event illustrations (arithmetic on published figures)
Definitions:
- Pe = entry price. The proxy is the LoF's record-date close; the actual buy is on the trading day before.
- Pb = buyback price.
- Pu = sale price of unaccepted shares after settlement.
- AR = fraction of your tendered shares accepted.
- c = round-trip cost fraction, 0.39%.

Formulas:
- Return R = AR x (Pb/Pe - 1) + (1 - AR) x (Pu/Pe - 1) - c.
- Breakeven Pu* = [Pe x (1 + c) - AR x Pb] / (1 - AR).
- Rupees on Rs 20,000 = 200 x R(%).

**Table E. Illustrative returns at three assumed moves in Pu** (Pu/Pe - 1 = 0%, -5%, -10%)

| Event | Pe (Rs) | Pb (Rs) | Premium | AR used | AR x premium | R at 0% | R at -5% | R at -10% | Breakeven move in Pu |
|---|---|---|---|---|---|---|---|---|---|
| TCS 2023 | 3,457.10 | 4,150 | 20.04% | 34.81% (primary) | 6.98% | 6.59% (Rs 1,318) | 3.33% | 0.07% | -10.10% (Rs 3,107.79) |
| Wipro 2023 | 381.30 | 445 | 16.71% | 77% (UNVERIFIED) | 12.87% | 12.48% | 11.33% | 10.18% | -54.2% |
| Wipro 2023 | 381.30 | 445 | 16.71% | 23.40% (entitlement floor) | 3.91% | 3.52% | -0.31% | -4.14% | -4.59% |
| Bajaj Auto 2024 | 7,909.35 | 10,000 | 26.43% | 26% (UNVERIFIED) | 6.87% | 6.48% | 2.78% | -0.92% | -8.76% |
| Wipro 2026 | 198.37 | 250 | 26.03% | 19.64% (entitlement floor) | 5.11% | 4.72% | 0.70% | -3.32% | -5.88% |
| TCS 2022 | 3,563.80 | 4,500 | 26.27% | 14.29% (entitlement floor) | 3.75% | 3.36% | -0.93% | -5.22% | -3.92% |
| TCS 2018 | 2,012.75 | 2,100 | 4.33% | 100% (UNVERIFIED) | 4.33% | about 4.0% (one sell day) | n/a | n/a | n/a |

Notes on Table E:
- The Pu moves are assumptions, not observations. Actual Pu needs bhavcopy data (Section 7).
- Rounding at Rs 20,000. TCS 2023: 5 shares, entitlement 5 x 1/6 = 0. Bajaj 2024: 2 shares, entitlement 0. Wipro 2026: 100 shares, entitlement 19 (`calc.py`). For the first two, acceptance would come only from the additional-share allocation and the one-share preference ([Bajaj LoF 19.14](https://www.sebi.gov.in/sebi_data/commondocs/mar-2024/Bajaj_Auto_Limited_LOO_p.pdf)). The holder's AR is lumpy: 0 of 2, 1 of 2 (50%), or 2 of 2. It is not the category AR.

### After-tax (zero other income)
- **(a) Deemed-dividend regime (buybacks 1 Oct 2024-31 Mar 2026).**
  - Dividend = AR x N x Pb, taxed at slab rates. Nil within the basic exemption and rebate.
  - Capital loss = the cost of the accepted shares, plus any loss on the unaccepted shares, carried forward against future capital gains.
  - After-tax cash equals pre-tax cash. Any TDS above the threshold is a timing cost until refunded (threshold unverified, Section 4).
- **(b) Capital-gains regime (buybacks from 1 Apr 2026, FY 2026-27).**
  - STCG = AR x N x (Pb - Pe), less the loss on the unaccepted shares (s.108(2)(a)).
  - Nil tax via s.196(2) while total income is below Rs 4 lakh. No TDS for residents (Wipro LoF 2026).
  - After-tax equals pre-tax. STT counts as a cost, not a deduction.

### Per-year figures
- **Supply of tender offers.**
  - About 19 per year: 75 NSE tender offers between Apr 2016 and Feb 2020 ([Suresha et al. 2024](https://businessperspectives.org/images/pdf/applications/publishing/templates/article/assets/20528/IMFI_2024_03_Suresha%20B.pdf)).
  - About 21 per year: 43 between Mar 2020 and Mar 2022 (same source).
  - 23 completed in the year to 7 Mar 2022 ([HDFC, UNVERIFIED](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf)).
  - SEBI's buyback filings list shows 25 distinct companies filing between 29 Apr 2026 and 28 Oct 2026 ([SEBI filings](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=22&smid=17), first page only). Their route (tender or open market) was not checked: Kajaria, Bajaj Auto, Cyient, Wipro, Zydus, Welspun Living, CMS Info, TeamLease, PVR INOX, VRL, TCI, Genus Power and others.
- **Access for Rs 20,000.** Any tender offer with a share price at or below Rs 20,000 is open to this holder. Where the price exceeds about Rs 20,000 / (1/entitlement ratio), roughly Rs 3,000-5,000 at 15-25% entitlements, the holder gets zero entitlement and relies on the additional pool.
- **Capital lock and overlap.** At about 18-20 days per event, one Rs 20,000 position could cycle through at most about 15-18 non-overlapping events a year. Overlapping record dates force a choice or a split of capital.
- **Annual formula.** Annual rupees = sum over events of 20,000 x R_i, simple and not compounded. Example only: 10 events at R = +3% and 2 at R = -4% give 20,000 x (0.30 - 0.08) = Rs 4,400. The distribution of R_i is not known from primary data. The broker tables show period-level medians of +19.1% per year (2020-22) and -6.35% per year (2018-19) for a different entry (day after board), pre-cost and pre-tax, and UNVERIFIED.

### Inferences
- The sign of each event depends mainly on Pu, the post-settlement price of the 45-80% of shares not accepted. The broker data put the median payout price 20-28% below the buyback price and 2-9% below the day-after-board price. That is the same order as the breakeven drops in Table E.
- For a Rs 20,000 holder, the favourable cases (Wipro-type offers with low share prices and high small-shareholder AR) are the ones where proportional entitlement works. In high-priced stocks the outcome is close to a lottery on one share.
- In rupees, a good event yields about Rs 700-2,500 on Rs 20,000 over about 3 weeks, before the Pu effect. A bad 10% Pu drop at low AR turns it into a loss of Rs 600-1,000.

### Gaps
- Not obtained: Pu (closing price on or after settlement day) for any primary-sourced event; the record-date-eve price, as opposed to the record-date close; the Infosys 2025 record-date close.
- The per-holder AR distribution for zero-entitlement holders is not published. PBAs give category totals only.
- Not verified: whether the transaction charge and the DP charge apply on tender bids, and how brokers charge for tender participation.

## 6. Why these numbers could be overstated or may have decayed

### Takeaway
At least six things push the published figures above what a small holder would get today:
- crowding of the small-shareholder category in publicised large-cap offers;
- the post-settlement fall in unaccepted shares, which most figures omit;
- the open-market route reinstated in 2026 without a small-shareholder reservation;
- reliance on broker and aggregator tables, which cover only completed offers in chosen windows;
- rounding at small position sizes;
- capital locked for 3-9 weeks per event.

The tax change on 1 Apr 2026 made buybacks tax-neutral for shareholders. That may raise the number of buybacks, but it also makes the open-market route attractive again.

### Cited Findings
- **Crowding in publicised offers.** TCS small-shareholder AR was 100% in 2017, 2018 and 2020, then 24-26% in 2022 and 34.81% in 2023. In 2023 there were 8,41,551 small bids, and small holders held 89.33% of the offer. — [HDFC 2022 (UNVERIFIED)](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf); [TCS PBA 2023](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf); [TCS LoF 2023](https://www.sebi.gov.in/sebi_data/commondocs/nov-2023/Tata_Consultancy_LOO_p.pdf)
  - HDFC's 2017 note warned that "if a lot of new investors buy at current price ... with the objective of tendering ... the acceptance ratio is likely to drop", as happened in Mphasis and HCL Tech. — [HDFC Nov 2017](https://www.hdfcsec.com/hsl.docs//Infosys%20-%20Buyback%20Opportunity%20Note%20Update%20-%20201117-201711201333499923090.pdf)
  - The 2022 note added that the 2020 offer was undersubscribed because "there was very little difference between the then prevailing market price and the buyback price". AR depends on the premium. — [HDFC 2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf)
- **Price drop on unaccepted shares.** Median payout price was 20-28% below the buyback price, with 14 of 23 (2020-22) and 18 of 22 (2018-19) payout prices below the day-after-board price (Section 5, broker data, UNVERIFIED). The peer-reviewed event study reports a significant negative post-announcement CAAR. — [Suresha et al. 2024](https://businessperspectives.org/images/pdf/applications/publishing/templates/article/assets/20528/IMFI_2024_03_Suresha%20B.pdf)
  - Market-wide period effects dominate. In 2019, Savita Oil (-92.4% p.a.), HEG (-110.5%) and eClerx (-63.0%) lost money despite premiums and acceptance (HDFC 2019, UNVERIFIED).
- **Open-market route back, with no reservation.** SEBI reinstated the stock-exchange route from 1 Aug 2026 after the tax change ([AZB](https://www.azbpartners.com/bank/sebi-notifies-amendments-to-buyback-of-securities-regulations-2018/), [CAM](https://corporate.cyrilamarchandblogs.com/2026/06/reintroduction-of-open-market-buyback-through-the-stock-exchange-and-other-changes-to-buyback-regime/), UNVERIFIED). A SEBI consultation addendum notes the tender route's 15% small-investor reservation has no open-market counterpart ([SEBI, search snippet](https://www.sebi.gov.in/sebi_data/commondocs/jul-2026/1%20list_p.pdf)). Companies that pick the open-market route take away the small-shareholder advantage.
- **Tax-driven supply changes.** The deemed-dividend rule (1 Oct 2024-31 Mar 2026) taxed the whole consideration at slab rates. That was costly for high-income holders, which may have discouraged buybacks; the number of buybacks in that window was not measured here. From 1 Apr 2026, shareholders pay capital-gains tax and promoters pay an additional tax ([FA 2026](https://egazette.gov.in/WriteReadData/2026/271439.pdf)). The SEBI filings list shows at least 25 companies filing buyback documents between 29 Apr and 28 Oct 2026 ([SEBI](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=22&smid=17)), against roughly 19-23 tender offers a year earlier. Routes were not checked.
- **Survivorship and selection in the published figures.**
  - The broker tables cover only offers "announced and completed in the last 1 year" at each note date, and the notes were written to promote participation in a live offer.
  - News reports focus on large IT offers with high ARs.
  - Aggregator figures conflict: TCS 2022 shows 24% in one place and 26% in another on the same [Chittorgarh page](https://www.chittorgarh.com/buyback/tcs-buyback/55/).
  - Projected ARs, such as Infosys 2025 at 45-50% or Wipro 2026 at 45-80%, are often quoted as if they were outcomes.
- **Capital lock.** About 18-20 days per event from 2023, and 5-9 weeks before (Section 5). The annualised returns in the broker tables assume capital is redeployed at once and that events never overlap.

### Inferences
- The figure most likely to be overstated is the AR × premium term taken alone. Every published "expected return" note assumes a Pu (often "CMP holds"). The broker's own payout prices show Pu usually falls.
- Large offers with the biggest premiums draw the most small bids, so the best-premium events tend to have the lowest small-shareholder AR (TCS 2022-2023). This is a negative feedback that would cap the edge if more small holders join.
- The 2026 regime shift (capital-gains tax plus an open-market route without reservation) is a structural break. Data from 2016-2025 may not describe FY 2026-27 onward.

### Gaps
- No count of buybacks by route and year from SEBI (annual report or handbook) was retrieved, so the "fewer buybacks after the tax change" question remains open.
- No data on how many tender offers moved to the open-market route after 1 Aug 2026.
- Not measured: how AR depends on premium size and on media coverage. That would need the full set of LoFs and PBAs.

## 7. Datasets and documents needed to backtest this (record dates, offer prices, acceptance ratios, daily prices)

### Takeaway
No free, clean, machine-readable dataset of Indian tender-offer acceptance ratios was found. A backtest would need four things joined by ISIN or symbol:
- the PA or LoF for each offer, giving record date, price, size, reserved shares, entitlement ratios, and the record-date close;
- the PBA, giving tendered shares by category and the settlement date;
- daily exchange prices (bhavcopy), for the record-date-eve price and the post-settlement price;
- corporate-action adjustments.

The primary documents exist but must be collected by hand or with polite scraping; the SEBI listing blocks scripted pagination.

### Cited Findings: datasets and sources

| Dataset | URL | Format | Coverage | Cost | Access friction | Fields it supplies |
|---|---|---|---|---|---|---|
| SEBI Filings, Buybacks (PA, LoF, some PBAs) | [sebi.gov.in listing](https://www.sebi.gov.in/sebiweb/home/HomeAction.do?doListing=yes&sid=3&ssid=22&smid=17) | HTML list with PDFs | 1,403 records, back to about 2010 | Free | Page 1 loads; the AJAX pagination endpoint returned "Unauthorized Request Blocked" to curl, so browse manually; robots.txt allows crawling | Record date, price, size, reserved shares, small-shareholder count, entitlement ratios, record-date close, schedule, tax and STT notes |
| Company PBAs (post-buyback public announcements) | BSE/NSE filings, e.g. [Infosys PBA](https://bsmedia.business-standard.com/_media/bs/data/announcements/bse/05122025/72F11864-D6DF-41CC-807A-289037B9E42B-152644.pdf), [TCS PBA](https://www.sebi.gov.in/sebi_data/commondocs/dec-2023/Tata_Consultancy_POPA_p.pdf), company IR pages ([Wipro 2019](https://www.wipro.com/content/dam/nexus/en/investor/buy-back/buyback2019/post-buyback-public-announcement-for-buy-back-of-equity-shares.pdf)) | PDF | Per offer | Free | Scattered. tcs.com returned HTML to curl. BSE and NSE archives need browser-like requests | Shares tendered and accepted by category, valid bids, settlement date (this is the AR source) |
| BSE/NSE corporate announcements and archives | bseindia.com corporate filings; [nsearchives.nseindia.com](https://nsearchives.nseindia.com/corporate/ECLERX_18122025222044_NSEBSELOF.pdf) | PDF and JSON APIs | All listed companies | Free | Anti-bot cookies and headers; per-company search | PA, LoF, PBA, record-date notices |
| Daily prices (bhavcopy) | NSE and BSE bhavcopy archives; the repo's data layer also has daily data for 2016-01-01..2026-04-07 (per project memory) | CSV | Daily OHLC and volume | Free | Corporate-action adjustment needed (e.g. bonus and split adjustments, such as Wipro's price levels in 2023 vs 2026) | Pe (record-date-eve close), Pu (settlement-day and later closes) |
| HDFC Securities retail-research buyback notes (secondary) | [2017](https://www.hdfcsec.com/hsl.docs//Infosys%20-%20Buyback%20Opportunity%20Note%20Update%20-%20201117-201711201333499923090.pdf), [2018](https://www.hdfcsec.com/hsl.docs//TCS%20-%20Buyback%20Opportunity%20Note%20update%20-%20030918-201809031748079081979.pdf), [2019](https://www.hdfcsec.com/hsl.docs//BSE%20Ltd%20-%20Buyback%20update-201908291228149800252.pdf), [2022](https://www.hdfcsec.com/hsl.docs/TCS%20-%20Buyback%20offer%20update%20(2022)-202203091005461110198.pdf) | PDF tables | 53 offers over 2016-2022 (Tables B-D) | Free | Tables extract with `pdftotext -raw`; layout mode garbles columns | Entitlement, actual AR, board-date+1 price, payout price, return (UNVERIFIED) |
| Chittorgarh buyback pages (secondary) | [example](https://www.chittorgarh.com/buyback/tcs-buyback/55/) | HTML with embedded JSON | About 220 offers (IDs up to about 219) | Free | robots.txt disallows AI and SEO crawlers, so do not scrape automatically; internally inconsistent | Locating documents; retail AR history per company (UNVERIFIED) |
| Other aggregators (ipocentral, ipoji, investorgain, broker blogs) | e.g. [ipoji closed buybacks](https://www.ipoji.com/buyback/closed-buyback?page=1) | HTML | Varies | Free | Mostly entitlements and projections, few actual ARs | Locating offers only (UNVERIFIED) |
| Legal texts | [Finance Act 2026 gazette](https://egazette.gov.in/WriteReadData/2026/271439.pdf); [Income-tax Act 2025 gazette](https://egazette.gov.in/WriteReadData/2025/265620.pdf) | PDF | Statute | Free | incometaxindia.gov.in returned 403 to scripted requests; e-Gazette worked | Tax rules by date |

**Minimum fields per event for a backtest:**
- symbol and ISIN;
- board-intimation date;
- PA date;
- record date and last cum date (T-1 under T+1);
- buyback price;
- offer size in shares;
- reserved shares (15% or proportional);
- small-shareholder count and holdings at the record date;
- small and general entitlement ratios;
- small-category shares validly tendered (PBA), giving AR;
- tendering window;
- settlement date;
- Pe and Pu series from bhavcopy;
- route (tender or open market);
- tax regime by date: before 5 Jul 2019, 5 Jul 2019-30 Sep 2024, 1 Oct 2024-31 Mar 2026, from 1 Apr 2026;
- a per-holder rounding rule (fractional entitlement ignored; one-share preference for zero-entitlement small holders).

### Inferences
- A holdout-respecting study is possible in principle from primary LoFs and PBAs plus bhavcopy. Collecting the AR field is the main labour, since PBAs are not in one place.
- Rounding and the one-share preference should be modelled per holding size. The category AR overstates or understates what a Rs 20,000 holder gets in high-priced stocks.
- Per the repo's rules, any such study would need to be logged in `research/trials.jsonl`, and the holdout dates in `config/research.yaml` would apply. None was run here.

### Gaps
- No bulk download of PBAs exists. NSE/BSE APIs were not tested in this session.
- No SEBI annual-report table of buyback counts by route and year was retrieved.
- The SEBI listing's 1,403 records could not be paginated by script. Only the 25 most recent (29 Apr-28 Oct 2026) were read.



