# Mainboard IPO dataset: tables

Generated 2026-10-31 19:26 UTC by `scripts/report_ipo.py` from `data/clean/ipo/ipos.parquet` (584 rows). Years are calendar years of the bid close. Returns are gross (no charges, no retail discount). Narrative and caveats: `research/ipo_dataset.md`.

## 1. Issues per year, by status

| year | already_listed | listed | not_found_on_nse | not_listed_on_nse_at_ipo | pending | withdrawn |
|---|---|---|---|---|---|---|
| 2016 | 0 | 26 | 1 | 0 | 0 | 0 |
| 2017 | 0 | 36 | 0 | 0 | 0 | 0 |
| 2018 | 0 | 24 | 1 | 0 | 0 | 0 |
| 2019 | 0 | 16 | 1 | 0 | 0 | 0 |
| 2020 | 0 | 14 | 0 | 1 | 0 | 1 |
| 2021 | 0 | 63 | 0 | 0 | 0 | 0 |
| 2022 | 1 | 39 | 0 | 0 | 0 | 0 |
| 2023 | 0 | 57 | 1 | 0 | 0 | 1 |
| 2024 | 0 | 90 | 0 | 0 | 0 | 0 |
| 2025 | 0 | 103 | 1 | 0 | 0 | 0 |
| 2026 | 0 | 103 | 1 | 0 | 3 | 0 |

## 2. Missing fields per year (listed issues)

| year | listed | list_close | list_open | allotment_date | p_1lot | retail_lots_allotted | retail_allottees | retail_valid_applications | retail_sub_boa | retail_sub | lot_size | issue_price | isin |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 26 | 0 | 0 | 26 | 26 | 26 | 26 | 26 | 26 | 3 | 3 | 0 | 0 |
| 2017 | 36 | 0 | 0 | 36 | 36 | 36 | 36 | 36 | 36 | 4 | 3 | 0 | 0 |
| 2018 | 24 | 0 | 0 | 22 | 22 | 22 | 22 | 22 | 22 | 3 | 2 | 0 | 0 |
| 2019 | 16 | 0 | 0 | 2 | 2 | 2 | 2 | 3 | 2 | 1 | 1 | 0 | 0 |
| 2020 | 14 | 0 | 0 | 3 | 2 | 3 | 3 | 6 | 2 | 0 | 0 | 0 | 0 |
| 2021 | 63 | 0 | 0 | 5 | 5 | 8 | 8 | 26 | 5 | 1 | 0 | 0 | 0 |
| 2022 | 39 | 0 | 0 | 3 | 3 | 4 | 4 | 13 | 3 | 1 | 1 | 0 | 0 |
| 2023 | 57 | 0 | 0 | 13 | 16 | 14 | 15 | 28 | 13 | 2 | 1 | 0 | 0 |
| 2024 | 90 | 0 | 0 | 8 | 11 | 10 | 13 | 14 | 7 | 1 | 1 | 0 | 0 |
| 2025 | 103 | 0 | 0 | 10 | 13 | 8 | 10 | 28 | 7 | 0 | 0 | 0 | 0 |
| 2026 | 103 | 0 | 0 | 3 | 4 | 5 | 5 | 11 | 3 | 0 | 0 | 0 | 0 |

## 3. Source of each field (listed issues)

| index | issue_price_src | lot_size_src | retail_sub_src | p_1lot_method | listing_match |
|---|---|---|---|---|---|
| allottees_over_applications | 0 | 0 | 0 | 9 | 0 |
| base_price | 0 | 0 | 0 | 0 | 2 |
| base_price_band_high | 0 | 0 | 0 | 0 | 3 |
| bhavcopy_base(list_disagrees) | 2 | 0 | 0 | 0 | 0 |
| bhavcopy_base(list_missing) | 20 | 0 | 0 | 0 | 0 |
| boa_min_bid | 0 | 15 | 0 | 0 | 0 |
| isin | 0 | 0 | 0 | 0 | 487 |
| min_bid_ratio | 0 | 0 | 0 | 420 | 0 |
| none | 0 | 12 | 16 | 140 | 0 |
| nse_boa | 0 | 0 | 445 | 0 | 0 |
| nse_detail | 0 | 544 | 0 | 0 | 0 |
| nse_detail_bids | 0 | 0 | 110 | 0 | 0 |
| nse_list(base_disagrees) | 1 | 0 | 0 | 0 | 0 |
| nse_list=bhavcopy_base | 548 | 0 | 0 | 0 | 0 |
| retail_undersubscribed | 0 | 0 | 0 | 2 | 0 |
| symbol | 0 | 0 | 0 | 0 | 79 |

## 4. Allotment chance of a 1-lot retail application

| year | n | = 100% | 50-<100% | 25-<50% | 10-<25% | 5-<10% | 2-<5% | <2% | p10 | median | p90 | mean |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2018 | 2 | 2 | 0 | 0 | 0 | 0 | 0 | 0 | 100.0% | 100.0% | 100.0% | 100.0% |
| 2019 | 14 | 3 | 4 | 1 | 2 | 2 | 2 | 0 | 4.3% | 42.9% | 100.0% | 46.4% |
| 2020 | 12 | 2 | 2 | 1 | 2 | 2 | 3 | 0 | 2.9% | 16.6% | 98.4% | 38.4% |
| 2021 | 58 | 8 | 9 | 4 | 18 | 7 | 7 | 5 | 2.7% | 14.6% | 100.0% | 32.7% |
| 2022 | 36 | 16 | 4 | 9 | 2 | 3 | 1 | 1 | 8.4% | 78.8% | 100.0% | 62.2% |
| 2023 | 41 | 4 | 6 | 3 | 12 | 8 | 4 | 4 | 2.0% | 14.4% | 94.8% | 29.3% |
| 2024 | 79 | 9 | 8 | 10 | 15 | 13 | 13 | 11 | 1.5% | 10.8% | 100.0% | 27.1% |
| 2025 | 90 | 19 | 12 | 5 | 17 | 13 | 15 | 9 | 2.2% | 16.4% | 100.0% | 37.2% |
| 2026 | 99 | 20 | 14 | 9 | 14 | 12 | 22 | 8 | 2.5% | 16.6% | 100.0% | 38.4% |
| all | 431 | 83 | 59 | 42 | 82 | 60 | 67 | 38 | 2.3% | 17.1% | 100.0% | 37.0% |

## 5a. Listing-day open over issue price

| year | n | mean | median | p25 | p75 | share_below_0 | min | max |
|---|---|---|---|---|---|---|---|---|
| 2016 | 26 | 12.1% | 8.3% | -0.6% | 21.6% | 26.9% | -11.3% | 57.7% |
| 2017 | 36 | 22.4% | 5.9% | 0.0% | 34.8% | 22.2% | -19.9% | 131.5% |
| 2018 | 24 | 5.2% | 1.4% | -7.8% | 4.9% | 41.7% | -24.4% | 69.1% |
| 2019 | 16 | 15.6% | 6.9% | -3.8% | 22.0% | 31.2% | -13.6% | 95.6% |
| 2020 | 14 | 44.3% | 43.3% | -2.2% | 84.0% | 28.6% | -12.5% | 115.0% |
| 2021 | 63 | 31.1% | 15.0% | -1.6% | 52.1% | 27.0% | -23.7% | 249.7% |
| 2022 | 39 | 9.4% | 3.5% | -1.2% | 12.0% | 30.8% | -8.8% | 56.0% |
| 2023 | 57 | 27.1% | 17.6% | 2.0% | 40.7% | 12.3% | -14.3% | 140.0% |
| 2024 | 90 | 28.8% | 16.4% | 2.6% | 40.0% | 17.8% | -13.2% | 181.5% |
| 2025 | 103 | 9.2% | 5.3% | 0.0% | 14.3% | 20.4% | -39.6% | 64.3% |
| 2026 | 103 | 14.1% | 7.2% | 0.0% | 23.0% | 22.3% | -34.6% | 111.3% |

## 5b. Listing-day close over issue price

| year | n | mean | median | p25 | p75 | share_below_0 | min | max |
|---|---|---|---|---|---|---|---|---|
| 2016 | 26 | 13.2% | 13.6% | 1.1% | 23.4% | 23.1% | -21.6% | 58.7% |
| 2017 | 36 | 23.7% | 7.7% | -0.5% | 33.7% | 27.8% | -15.9% | 143.1% |
| 2018 | 24 | 7.3% | 0.0% | -7.1% | 15.0% | 45.8% | -20.7% | 65.1% |
| 2019 | 16 | 19.6% | 6.6% | -2.0% | 25.4% | 31.2% | -9.3% | 127.4% |
| 2020 | 14 | 45.4% | 25.3% | 3.0% | 83.2% | 28.6% | -14.0% | 125.0% |
| 2021 | 63 | 32.0% | 17.6% | -1.5% | 42.6% | 28.6% | -27.4% | 267.2% |
| 2022 | 39 | 9.4% | 5.8% | -7.5% | 17.4% | 38.5% | -19.1% | 51.0% |
| 2023 | 57 | 29.1% | 21.3% | 4.0% | 46.4% | 14.0% | -10.0% | 162.6% |
| 2024 | 90 | 30.1% | 21.0% | 3.7% | 43.0% | 21.1% | -20.2% | 195.5% |
| 2025 | 103 | 9.5% | 5.0% | -2.3% | 19.2% | 33.0% | -36.6% | 72.5% |
| 2026 | 103 | 14.5% | 7.6% | -1.7% | 26.1% | 31.1% | -31.3% | 111.7% |

## 6. Overlapping windows and one block of Rs 15,000

| year | listed | end_is_listing_date | lot_cost_unknown | lot_cost_above_block | fit_block | overlap_full | max_concurrent_full | one_block_full | overlap_last_day | max_concurrent_last_day | one_block_last_day |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2016 | 26 | 26 | 3 | 0 | 23 | 20 | 4 | 12 | 18 | 3 | 14 |
| 2017 | 36 | 36 | 3 | 0 | 33 | 30 | 5 | 15 | 27 | 4 | 16 |
| 2018 | 24 | 22 | 2 | 0 | 22 | 19 | 7 | 9 | 17 | 6 | 11 |
| 2019 | 16 | 2 | 1 | 0 | 15 | 8 | 3 | 11 | 7 | 3 | 11 |
| 2020 | 14 | 3 | 0 | 0 | 14 | 9 | 5 | 8 | 9 | 3 | 9 |
| 2021 | 63 | 5 | 0 | 0 | 63 | 61 | 8 | 21 | 57 | 6 | 26 |
| 2022 | 39 | 3 | 1 | 0 | 38 | 33 | 5 | 16 | 31 | 4 | 20 |
| 2023 | 57 | 13 | 1 | 0 | 56 | 49 | 8 | 22 | 42 | 6 | 29 |
| 2024 | 90 | 8 | 1 | 0 | 89 | 75 | 9 | 40 | 58 | 8 | 55 |
| 2025 | 103 | 10 | 0 | 0 | 103 | 98 | 11 | 33 | 82 | 7 | 52 |
| 2026 | 103 | 3 | 0 | 0 | 103 | 100 | 12 | 27 | 89 | 9 | 44 |

## 7. Rows failing a cross-check

| issue_id | company | checks |
|---|---|---|
| ICICIPRULI_20160919 | ICICI Prudential Life Insurance Company Limited | issue_price_list_vs_base |
| PNBHF_20161025 | PNB Housing Finance Limited | issue_price_list_vs_base |
| RADIOCITY_20170306 | Music Broadcast Limited | issue_price_list_vs_base |
| AUBANK_20170628 | AU Small Finance Bank Limited | issue_price_list_vs_base |
| HGINFRA_20180226 | H.G.Infra Engineering Limited | exch_snapshot_before_close |
| ISEC_20180322 | ICICI Securities Limited | issue_price_list_vs_base |
| INDOSTAR_20180509 | IndoStar Capital Finance Limited | issue_price_list_vs_base |
| CREDITACC_20180808 | CreditAccess Grameen Limited | issue_price_list_vs_base |
| XELPMOC_20190123 | Xelpmoc Design and Tech Limited | boa_unreadable |
| SPANDANA_20190805 | Spandana Sphoorty Financial Limited | issue_price_list_vs_base |
| SWSL_20190806 | Sterling & Wilson Solar Limited | issue_price_list_vs_base |
| VISHWARAJ_20190930 | Vishwaraj Sugar Industries Limited | boa_unreadable |
| CHEMCON_20200921 | Chemcon Speciality Chemicals Limited | boa_unreadable |
| BECTORFOOD_20201215 | Mrs. Bectors Food Specialities Limited | boa_unreadable |
| IRFC_20210118 | Indian Railway Finance Corporation Limited | issue_price_list_vs_base |
| MTARTECH_20210303 | MTAR Technologies Limited | boa_unreadable |
| ANURAS_20210312 | Anupam Rasayan India Limited | issue_price_list_vs_base |
| NUVOCO_20210809 | Nuvoco Vistas Corporation Limited | issue_price_list_vs_base |
| SIGACHI_20211101 | Sigachi Industries Limited | boa_unreadable |
| SJS_20211101 | S J S Enterprises Limited | boa_no_retail_section |
| HPAL_20211215 | HP Adhesives Limited | boa_unreadable |
| AWL_20220127 | Adani Wilmar Limited | exch_snapshot_before_close |
| UMAEXPORTS_20220328 | UMA Exports Limited | boa_no_retail_section |
| DCX_20221031 | DCX System limited | issue_price_list_vs_base |
| ACI_20221109 | Archean Chemical Industries Limited | boa_unreadable |
| DHARMAJ_20221128 | Dharmaj Crop Guard Limited | boa_unreadable |
| GSLSU_20230313 | Global Surfaces Limited | boa_unreadable |
| HMAAGRO_20230620 | HMA Agro Industries Limited | boa_unreadable |
| PYRAMID_20230818 | Pyramid Technoplast Limited | boa_unreadable |
| AEROFLEX_20230822 | Aeroflex Industries Limited | boa_unreadable |
| VPRPL_20230824 | Vishnu Prakash R Punglia Limited | boa_unreadable |
| RATNAVEER_20230904 | Ratnaveer Precision Engineering Limited | boa_unreadable |
| JLHL_20230906 | Jupiter Life Line Hospitals Limited | boa_unreadable |
| EMSLIMITED_20230908 | EMS Limited | boa_unreadable |
| SAMHI_20230914 | SAMHI Hotels Limited | boa_unreadable |
| JSWINFRA_20230925 | JSW Infrastructure Limited | boa_one_lot_row_missing |
| VALIANTLAB_20230927 | Valiant Laboratories Limited | boa_unreadable |
| ESAFSFB_20231103 | ESAF Small Finance Bank Limited | issue_price_list_vs_base |
| IREDA_20231121 | Indian Renewable Energy Development Agency Limited | issue_price_list_vs_base |
| INDIASHLTR_20231213 | India Shelter Finance Corporation Limited | boa_one_lot_row_missing |
| INOXINDIA_20231214 | INOX India Limited | boa_one_lot_row_missing |
| SURAJEST_20231218 | Suraj Estate Developers Limited | boa_allottees_implausible |
| HAPPYFORGE_20231219 | Happy Forging Limited | boa_unreadable |
| MUFTI_20231219 | Credo Brands Marketing Limited | boa_unreadable |
| NOVAAGRI_20240123 | Nova Agritech Limited | boa_allottees_implausible |
| PARKHOTELS_20240205 | Apeejay Surrendra Park Hotels Limited | p_outside_subscription_bounds;boa_allottees_implausible |
| VSTL_20240213 | Vibhor Steel Tubes Limited | boa_unreadable |
| PLATIND_20240227 | Platinum Industries Limited | boa_unreadable |
| MUKKA_20240229 | Mukka Proteins Limited | boa_unreadable |
| JNKINDIA_20240423 | JNK India Limited | boa_unreadable |
| AFIL_20240619 | Akme Fintrade (India) Limited | issue_price_list_vs_base |
| DEEDEV_20240619 | DEE Development Engineers Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing |
| ABDL_20240625 | Allied Blenders and Distillers Limited | boa_allottees_implausible |
| SSDL_20240812 | Saraswati Saree Depot Limited | boa_unreadable |
| TOLINS_20240909 | Tolins Tyres Limited | boa_one_lot_row_missing |
| NORTHARC_20240916 | Northern Arc Capital Limited | issue_price_list_vs_base |
| DBEIL_20241021 | Deepak Builders & Engineers India Limited | boa_unreadable |
| AFCONS_20241025 | Afcons Infrastructure Limited | issue_price_list_vs_base |
| ACMESOLAR_20241106 | ACME Solar Holdings Limited | boa_unreadable |
| NTPCGREEN_20241119 | NTPC Green Energy Limited | issue_price_list_vs_base |
| INDOFARM_20241231 | Indo Farm Equipment Limited | p_ratio_vs_allottees;p_outside_subscription_bounds |
| DENTA_20250122 | Denta Water and Infra Solutions Limited | boa_one_lot_row_missing |
| BELRISE_20250521 | Belrise Industries Limited | boa_unreadable |
| AEGISVOPAK_20250526 | Aegis Vopak Terminals Limited | issue_price_list_vs_base |
| SAMBHV_20250625 | Sambhv Steel Tubes Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing |
| IGCL_20250626 | Indogulf Cropsciences Limited | boa_unreadable |
| CRIZAC_20250702 | CRIZAC LIMITED | boa_unreadable |
| SMARTWORKS_20250710 | Smartworks Coworking Spaces Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing |
| BLUESTONE_20250811 | BlueStone Jewellery and Lifestyle Limited | boa_unreadable |
| PATELRMART_20250819 | Patel Retail Limited | boa_allottees_implausible |
| AHCL_20250826 | Anlon Healthcare Limited | boa_unreadable |
| URBANCO_20250910 | Urban Company Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing |
| SAATVIK_20250919 | Saatvik Green Energy Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing |
| SOLARWORLD_20250923 | Solarworld Energy Solutions Limited | boa_unreadable |
| PACEDIGITK_20250926 | Pace Digitek Limited | boa_unreadable |
| TATACAP_20251006 | Tata Capital Limited | issue_price_list_vs_base |
| CANHLIFE_20251010 | Canara HSBC Life Insurance Company Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing;issue_price_list_vs_base |
| PWL_20251111 | Physicswallah Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing |
| GKSL_20251222 | Gujarat Kidney and Super Speciality Limited | boa_allottees_implausible |
| PNGSREVA_20260224 | PNGS Reva Diamond Jewellery Limited | boa_unreadable |
| SAIPARENT_20260324 | Sai Parenteral's Limited | boa_one_lot_row_too_small;boa_one_lot_row_missing |
| BLEL_20260812 | Behari Lal Engineering Limited | boa_unreadable |
| HTEL_20260824 | Hy-Tech Engineers Limited | boa_no_retail_section |
| MOMSBELIEF_20260901 | Rays of Belief Limited- For Profit Social Enterprise (FPSE) | issue_price_list_vs_base |
| SHAHINVEST_20260928 | Shah Investor's Home Limited | boa_one_lot_row_missing |

## 8. Issues not listed on NSE (or not yet)

| issue_id | company | issue_open | issue_close | status |
|---|---|---|---|---|
| GSBPL_20161109 | GreenSignal Bio Pharma Limited | 2016-11-09 | 2016-11-22 | not_found_on_nse |
| DEPL_20180928 | Dinesh Engineers Limited | 2018-09-28 | 2018-10-03 | not_found_on_nse |
| KPRAGRO_20190628 | K.P.R. Agrochem Limited | 2019-06-28 | 2019-07-02 | not_found_on_nse |
| AWHCL_20200304 | Antony Waste Handling Cell Limited | 2020-03-04 | 2020-03-16 | withdrawn |
| CAMS_20200921 | Computer Age Management Services Limited | 2020-09-21 | 2020-09-23 | not_listed_on_nse_at_ipo |
| RUCHISOYA_20220324 | Ruchi Soya Industries Limited | 2022-03-24 | 2022-03-28 | already_listed |
| PKH_20230630 | PKH Ventures Limited | 2023-06-30 | 2023-07-04 | withdrawn |
| PROTEAN_20231106 | Protean eGov Technologies Limited | 2023-11-06 | 2023-11-08 | not_found_on_nse |
| NSDL_20250730 | National Securities Depository Limited | 2025-07-30 | 2025-08-01 | not_found_on_nse |
| NSE_20260917 | National Stock Exchange of India Limited | 2026-09-17 | 2026-09-21 | not_found_on_nse |
| EDELALTS_20261026 | EAAA India Alternatives Limited | 2026-10-26 | 2026-10-28 | pending |
| BLSPOLY_20261027 | BLS Polymers Limited | 2026-10-27 | 2026-10-29 | pending |
| SFCTECH_20261027 | SFC Environmental Technologies Limited | 2026-10-27 | 2026-10-29 | pending |
