"""English titles and notes of the main tables (Tables 1–4) and of Supplementary Tables S1–S15.

MAIN: (sheet of Tabelas_TxC_SUS.xlsx, number, title, note). SUPP: one entry per supplementary table, with the rows read
from a sheet ("sheet"), built from the analysis outputs ("build", see tabelas_en.py) or given here ("rows").
"""

MAIN = [('T1',
  1,
  'Characteristics of heart transplant admissions paid for by the Brazilian Unified Health System, 2000–2025, by age and center type',
  'Incumbent centers: first transplant recorded in the SIH in 2000–2003 (earlier experience unknown). Centers first observed ≥2004: first transplant '
  'recorded in 2004 or later; this does not necessarily coincide with the opening of the program. In-hospital death: death during the transplant '
  'admission; not survival. Principal diagnosis as coded in the admission record. **Admission type is descriptive only and is not comparable between '
  'periods: its coding changed in 2008. In 2000–2007, 24.7% of admissions were coded elective (01), 0.8% urgent (02) and 65.8% code 05; in '
  '2008–2025, 20.8% were elective and 79.2% urgent. It does not enter any model.** Reimbursement corrected by the IPCA consumer price index to '
  'December 2025 reais. No missing data for the variables in this table (Supplementary Table S13).'),
 ('T2',
  2,
  'Evolution of the public heart transplant network by year, 2000–2025',
  'Entries: centers with their first transplant in the year (not defined for 2000, the start of the series). Exits: centers whose last year with a '
  'transplant was the year of the row (not defined for 2024–2025, as the center may resume activity). HHI: Herfindahl–Hirschman index of center '
  'shares of the admissions of the year (0–10,000); it measures concentration of supply, not competition. Crude mortality: death during the '
  'transplant admission.'),
 ('T3',
  3,
  'Use and geographic distribution of heart transplantation by region of residence and period, 2000–2025',
  'Denominator: 5806 admissions; the 15 admissions without a recorded municipality of residence are excluded from all residence-based analyses. '
  'Standardized rate: direct method by age (6 groups) and sex; standard population, Brazil 2025 (IBGE projections, 2024 revision); annual rate per '
  'million inhabitants; 95% CI by the gamma method of Fay and Feuer. Rates count recorded admissions, not people. Distance: geodesic distance '
  'between the seats of the municipalities of residence and of the hospital. Potential proximity: % of the population (2022 Census, fixed weights) '
  'within 300, 500 or 1000 km (geodesic, seat to seat, regardless of state borders) of a center active in the year, with at least 1 | at least 5 '
  'transplants in the year; mean of the years of the period. It is a geographic proxy and does not measure access, indication, listing or capacity. '
  'Row 2000–2025: whole period (proximity not applicable). Use as recorded in the SIH, which captures part of the transplants in the country '
  '(Supplementary Table S1). Fifteen admissions without municipality of residence (2005–2006) are excluded from this table. Periods shown: '
  '2000–2003, 2008–2011, 2023–2025 and the whole period; all periods are shown in Figure 2.'),
 ('T4',
  4,
  'Annual center volume and in-hospital death: multilevel logistic model (main estimate) and GEE (supporting population-average estimate)',
  'Adjustment: age group (<18, 18–39, 40–49, 50–59, ≥60 years), sex and year (natural spline, 2 df). Main exposure: V − 1, split at the admission '
  'level into "between centers" (mean of V − 1 over the admissions of the center; restricted cubic spline with knots at the 10th, 50th and 90th '
  'percentiles) and "within center" (deviation from that mean; linear, per +10 transplants/year). The 90th percentile of "between" coincides with '
  'the maximum (the largest center, 15.8% of admissions). Multilevel model: random center intercept; estimates the association conditional on the '
  'center. GEE: logit, exchangeable correlation, cluster = center; estimates the population-average association; CI by center bootstrap (1000 '
  'resamples). The two models estimate different quantities; divergence between them is not a robustness test. Volume categories (V, including the '
  'index case) in a separate model, which does not separate between- and within-center variation. ‡ Contrast in which "between" exceeds the '
  'second-highest mean center volume (25.9): from 25.9 to 41.7 the between-center curve rests on a single center; the estimate is an extrapolation '
  'from that center and should not be read in isolation (see the full curve in Figure 3); in these rows the GEE bootstrap CI is unstable. The global '
  'evidence for "between" is the 2-df LRT. ICC on the latent scale. Observational associations; volume is an operational marker of the center, not a '
  'measure of quality.')]

SUPP = [{'num': 'S1',
  'title': 'Completeness of the SIH relative to the Brazilian Transplant Registry (RBT), by state of the hospital (2020, 2023, 2024)',
  'note': 'State-level comparison with the RBT edition of the same year. National series (SIH/RBT): 2000: 107/123 (87.0%); 2001: 99/135 (73.3%); '
          '2002: 122/160 (76.2%); 2003: 159/189 (84.1%); 2004: 178/226 (78.8%); 2005: 172/181 (95.0%); 2006: 131/149 (87.9%); 2007: 131/161 (81.4%); '
          '2008: 175/201 (87.1%); 2009: 169/201 (84.1%); 2010: 151/166 (91.0%); 2011: 142/160 (88.8%); 2012: 193/228 (84.6%); 2013: 216/272 (79.4%); '
          '2014: 262/311 (84.2%); 2015: 300/353 (85.0%); 2016: 284/357 (79.6%); 2017: 320/380 (84.2%); 2018: 308/358 (86.0%); 2019: 341/383 (89.0%); '
          '2020: 268/308 (87.0%); 2021: 262/334 (78.4%); 2022: 303/363 (83.5%); 2023: 321/430 (74.7%); 2024: 362/443 (81.7%); 2025: 345/427 (80.8%). '
          'RBT values for 2000–2004 from the 10-year report (1995–2004; 2002 derived from the period total) and for 2005–2007 from the 2015 '
          'first-semester edition; the 2025 total (427) was checked in the RBT 2025 annual report. No patient-level linkage; SIH/RBT above 100% '
          "means more admissions than registry records. Last column: % of the state's admissions in centers first observed ≥2004.",
  'sheet': 'TS1'},
 {'num': 'S2',
  'title': 'Sensitivity analyses of the volume model: OR (95% CI)',
  'note': 'Same model as Table 4 unless stated; knots and reference values fixed at those of the main analysis. Step: step of the convergence '
          'sequence at which the model was accepted (Supplementary Methods; "—" = model fitted without the sequence). Lagged volume: transplants of '
          'the center in the previous year. The analysis excluding centers above the 99.8% limit of a funnel plot was defined after seeing the data '
          '(post hoc); the funnel plot is not shown because it invites a reading of center performance that the risk adjustment cannot support. '
          'Firth: penalized logistic regression without a center effect.',
  'sheet': 'TS2'},
 {'num': 'S3',
  'title': 'Post hoc analyses of the within-center term (+10 transplants/year)',
  'note': 'All analyses in this table were defined after seeing the main results and are exploratory. Same adjustment as Table 4.',
  'rows': [['Analysis', 'Admissions', 'Centers', 'OR (95% CI)', 'P'],
           ['Main analysis (reference)', '5821', '64', '0.81 (0.73–0.91)', '<0.001'],
           ['Interaction with period: 2000–2007', '5821', '64', '0.70 (0.58–0.84)', '<0.001'],
           ['Interaction with period: 2008–2025', '5821', '64', '0.89 (0.77–1.03)', '0.105'],
           ['Ratio between periods (2000–2007 ÷ 2008–2025)', '5821', '64', '0.79 (0.62–1.00)', '0.052'],
           ['2000–2007 only (center mean recalculated within the period)', '1099', '—', '0.70 (0.53–0.94)', '0.016'],
           ['Adjusted for log2 of program years', '5821', '64', '0.80 (0.72–0.90)', '<0.001'],
           ['Centers with ≥5 consecutive years of activity only', '5600', '33', '0.82 (0.74–0.92)', '<0.001'],
           ['Centers with mean <10 transplants/year', '5821', '64', '0.73 (0.52–1.02)', '0.066'],
           ['Centers with mean ≥10 transplants/year', '5821', '64', '0.82 (0.73–0.92)', '<0.001'],
           ['Ratio between center sizes (≥10 ÷ <10)', '5821', '64', '1.12 (0.79–1.59)', '0.52']]},
 {'num': 'S4',
  'title': 'Centers first observed ≥2004 (exploratory): in-hospital death by sequential case number',
  'note': 'Multilevel model with a random center intercept; adjusted for age group, sex and year (spline). Primary exposure: one of the first 5 '
          'cases of the center. Without Center 02 (the largest center of this group): 34 centers, 1598 admissions, 202 deaths. Leave-one-center-out '
          'of the primary analysis (35 refits): OR 1.04 to 1.36. Exploratory; 271 deaths in 35 centers. The contrast of cases 6–10 vs >20 is '
          'exploratory and should not be used for policy.',
  'sheet': 'TS3'},
 {'num': 'S5',
  'title': 'Children and women: use, surgery outside the state of residence, distance and female-to-male rate ratio, by period',
  'note': 'Children: <18 years; rate per million residents aged 0–17 years (exact Poisson 95% CI). Centers with ≥1 pediatric transplant: annual '
          'minimum–maximum in the period. Women and men: age-standardized rates (standard, Brazil 2025, both sexes); female-to-male ratio with 95% '
          'CI on the log scale. Description of relative use; it does not allow conclusions about under-representation or inequality in access to '
          'indication or listing.',
  'sheet': 'T5'},
 {'num': 'S6',
  'title': 'Characteristics and in-hospital death by sex',
  'note': 'Descriptive, without statistical tests. Female-to-male rate ratios by period are in Supplementary Table S5. Sex-specific age-standardized '
          'rates and the remaining Table 1 variables by sex can be produced with the same code if requested.',
  'rows': [['', 'Men', 'Women'],
           ['Adults (≥18 years): admissions', '3665', '1523'],
           ['Adults: in-hospital deaths, n (%)', '544 (14.8)', '215 (14.1)'],
           ['Adults: mean age, years', '49.0', '47.5'],
           ['Adults: mean length of stay, days', '18.2', '17.3'],
           ['Children (<18 years): admissions', '355', '278'],
           ['Children: in-hospital deaths, n (%)', '29 (8.2)', '31 (11.2)'],
           ['Children: mean age, years', '10.1', '8.2'],
           ['Children: mean length of stay, days', '21.6', '20.0'],
           ['All: admissions', '4020', '1801'],
           ['All: in-hospital deaths, n (%)', '573 (14.3)', '246 (13.7)']]},
 {'num': 'S7',
  'title': 'Count models (trend in use) and descriptive model of surgery outside the state of residence',
  'note': 'Region × year: Pearson χ²/df (Poisson) = 3.22; likelihood ratio test Poisson vs negative binomial P <0.001, so negative binomial; '
          'quantile residuals Kolmogorov–Smirnov P = 0.876. Offset log(population); year as spline (2 df); region (ref. Southeast). Counts are crude '
          '(not standardized). Number of active centers in the region: descriptive covariate, without causal reading. State × year model (negative '
          'binomial, random state intercept): state SD = 1.12; active centers in the state (descriptive): ratio 1.43 (1.32–1.54). Surgery outside '
          'the state: Firth regression because of structural separation; references 18–39 years, male, Southeast, 0 km.',
  'sheet': 'TS8'},
 {'num': 'S8',
  'title': 'Source of growth: mean annual admissions in 2000–01 and 2024–25 by center group',
  'note': 'Post hoc, descriptive. Groups by first and last year with a transplant in the SIH. "Without activity in 2024–25" does not mean confirmed '
          'closure of the program. "Centers first observed ≥2004" reflects entry into the series, not necessarily the opening of a program.',
  'sheet': 'TS19'},
 {'num': 'S9',
  'title': "Network concentration without hospitals in São Paulo and compared with the registry's counts by team (post hoc)",
  'note': 'Post hoc. Same definitions as Table 2. Upper rows: SIH, all states and after excluding admissions in hospitals of the state of São Paulo, '
          'where SIH capture relative to the RBT was lowest (Supplementary Table S1). Lower rows: SIH compared with the heart transplants by team '
          'published by the RBT, summed by hospital, for the only annual editions with a per-team table (2009, Ano XV nº 4; 2010, Ano XVI nº 4; '
          '2017, Ano XXIII nº 4). Counted by team, the RBT listed 33, 26 and 36 active teams in these years; in 2017 the 9 largest teams performed '
          '67.6% of transplants. Aggregates only; no center is identified. SP, São Paulo; HHI, Herfindahl–Hirschman index; RBT, Brazilian Transplant '
          'Registry; SIH, Hospital Information System.',
  'build': 'concentration',
  'abbr': False},
 {'num': 'S10',
  'title': 'Post hoc sensitivity analyses of the network description and of the volume model',
  'note': 'All analyses in this table were defined after seeing the main results. "New" centers are those whose first recorded transplant fell after '
          'the initial observation window (main: 2000–2003; sensitivity: 2000–2001); a longer window reduces the chance that a center that resumed '
          "activity is counted as new. Earlier activity: at least 1 heart transplant in an RBT team list covering only years before the center's "
          'first SIH admission (confirmed, 3 centers) or more transplants in a list that included that year than the SIH recorded up to it '
          '(possible, 1 center); names were used only for this local comparison. The random-slope models add a center-specific linear trend in '
          'calendar year (per decade) to the main model, so that the within-center term is not driven by centers that grew while mortality fell; '
          'likelihood ratio test for the random slope, χ² = 9.80 (2 df), P = 0.007; global test of the between-center term in that model, P = 0.201. '
          'Same adjustment as Table 4. CI, confidence interval; OR, odds ratio.',
  'build': 'posthoc',
  'abbr': False},
 {'num': 'S11',
  'title': 'Change of procedure table in 2008 and exploratory trend model with breakpoints',
  'note': 'Breakpoint models are exploratory. In 200 bootstrap resamples the first breakpoint ranged from 2003 to 2018 and the second from 2011 to '
          '2021; only 9.5% of resamples reproduced the pair 2006/2017. Breakpoint positions are unstable and should not be read as dates of change '
          'in the system. Absence of a detectable discontinuity in 2008 does not prove equivalence of the two procedure tables.',
  'rows': [['Model', 'Estimate (95% CI)', 'P'],
           ['Indicator 2008+: multilevel, year spline (2 df) + indicator', 'OR 0.85 (0.55–1.29)', '0.44'],
           ['Indicator 2008+: logistic with 2 breakpoints + indicator (SE by center)', 'OR 1.00 (0.65–1.53)', '0.999'],
           ['Exploratory: linear trend', 'ΔBIC 7.1', ''],
           ['Exploratory: 1 breakpoint (2003)', 'ΔBIC 8.9', ''],
           ['Exploratory: 2 breakpoints (2006, 2017)', 'ΔBIC 0', ''],
           ['Segment 2000–2006, annual OR', '1.09 (1.03–1.15)', ''],
           ['Segment 2006–2017, annual OR', '0.90 (0.87–0.93)', ''],
           ['Segment 2017–2025, annual OR', '1.02 (0.97–1.08)', '']]},
 {'num': 'S12',
  'title': 'Risk model diagnostics (age group, sex, year): calibration by deciles of predicted risk',
  'note': 'C statistic 0.617 (0.597–0.637) (DeLong). The model adjusts only for age, sex and year; pre-transplant severity is not recorded in the '
          'SIH, and observed/expected ratios do not measure performance.',
  'sheet': 'TS12'},
 {'num': 'S13',
  'title': 'Missing data by variable in the analysis dataset (5821 admissions)',
  'note': 'Empty field in the analysis file. Cause of death: empty in all admissions without death and in 568 of 819 admissions with death (69.4%); '
          'not used. Days since previous record: filled only in the 54 second admissions of probable readmitted patients. Municipality of residence '
          'unknown in 15 admissions of 2005–2006 (excluded only from analyses by residence); principal diagnosis empty in 15 admissions. Variable '
          'names are those of the analysis file.',
  'build': 'missing',
  'abbr': False},
 {'num': 'S14',
  'title': 'RECORD checklist (items specific to routinely collected data)',
  'note': 'RECORD items as listed by Benchimol et al. (PLoS Med 2015). The STROBE items are addressed in the corresponding sections of the '
          'manuscript.',
  'rows': [['RECORD item', 'Content', 'Location'],
           ['1.1 Type of data in title/abstract',
            'National hospital discharge database (SIH/SUS), reduced admission files (RD)',
            'Abstract (Methods)'],
           ['1.2 Geographic region and timeframe in title/abstract', 'Brazil; admissions from 1 January 2000 to 31 December 2025', 'Title; Abstract'],
           ['1.3 Linkage between databases',
            'No patient-level linkage across external databases. Within the SIH: probable-patient identification (date of birth + sex + municipality '
            'of residence; 54 probable patients with 2 admissions). Facility level: hospital tax numbers crosswalked to CNES codes before 2004 (3 '
            'rules). RBT and private-plan data compared as aggregate counts only',
            'Methods (Study population); Supplementary Methods'],
           ['6.1 Methods of study population selection',
            'Procedure performed: codes 46800018 and 47800011 (SIH table, 2000–2007) and 05.05.02.004-1 (unified SUS table, from 2008), with '
            'official correspondence; exclusion of procedure only requested (374) and admission outside 2000–2025 (161)',
            'Methods (Data source; Study population); Supplementary Figure S1; Supplementary Methods'],
           ['6.2 Validation of codes or algorithms',
            'No patient-level validation. Counts compared with the RBT by year (2000–2025) and by state (2020, 2023, 2024); 2008–2025 counts by '
            'billing month reproduce the official online tabulation (TabNet) exactly; no detectable discontinuity in mortality at the 2008 table '
            'change',
            'Supplementary Tables S1, S11; Limitations'],
           ['6.3 Linkage flow diagram',
            'No patient-level linkage across databases. Facility crosswalk: 307, 7 and 70 admissions linked by rules 1–3; no admission left without '
            'a center',
            'Supplementary Methods (Centers)'],
           ['7.1 Codes and algorithms for exposures, outcomes and confounders',
            'Outcome: death field = 1 in the transplant admission. Exposure: annual center volume from CNES (tax number linked to CNES by 3 rules '
            'before 2004). Covariates: age group, sex, year. Principal-diagnosis groups: B57 Chagas; I20–I25 ischemic; I42.0 dilated; I42.x/I43 '
            'other cardiomyopathies; Q20–Q28 congenital; I05–I09/I34–I38 valvular; I40–I41/I51.4 myocarditis; I50 unspecified heart failure; T86 '
            'graft failure/rejection; Z94; others. Chagas in any field = B57 in principal or secondary diagnoses',
            'Methods; Table 1; Supplementary Methods'],
           ['12.1 Extent of access to the database',
            'Full access to the public RD files of the 27 states, billing months January 2000 to June 2026 (8580 of 8586 files read; 6 missing from '
            'states without a center); public mirror converted 1:1 from the official files, checksum verified per file; extraction on 13–14 October '
            '2026',
            'Methods (Data source); Supplementary Figure S1'],
           ['12.2 Data cleaning methods',
            'Selection by procedure code; restriction by admission date; one row per admission number (no duplicates); initial admission records '
            'only (no continuation records; not one admission per person); hospital identifier harmonized (tax number→CNES); 15 admissions without '
            'municipality of residence excluded only from residence analyses; centers anonymized',
            'Supplementary Methods; Supplementary Table S13'],
           ['12.3 Linkage methods',
            'No patient-level linkage. Probable-patient identification within the SIH (exact match on date of birth, sex and municipality of '
            'residence); facility crosswalk tax number→CNES by 3 explicit rules',
            'Methods; Supplementary Methods; Supplementary Methods'],
           ['13.1 Selection flow diagram',
            '8580 files → 6356 records with transplant performed or requested → 374 requested only → 5982 → 161 outside 2000–2025 → 5821 admissions; '
            'analytical subsets',
            'Supplementary Figure S1'],
           ['19.1 Limitations of routinely collected data',
            'Partial completeness relative to the RBT; in-hospital outcome only; no severity, mechanical support, urgency, waiting time or donor '
            'data; coding changes in 2008 (procedure table, admission type); tax-number linkage before 2004; poor diagnosis and cause-of-death '
            'coding; left censoring of center start',
            'Discussion (Limitations)'],
           ['22.1 Accessibility of protocol, raw data and code',
            'Raw data publicly available from DATASUS; extraction and analysis code at '
            'https://github.com/Hadid55555/heart-transplant-network-brazil (record-level files are not shared)',
            'Declarations (Data availability)']],
  'abbr': False},
 {'num': 'S15',
  'title': 'Heart transplant centers by source, 2007–2025: billing (SIH), registry (RBT) and habilitation (CNES)',
  'note': 'SIH: hospitals billing at least 1 heart transplant admission to the public system in the year. RBT: national heart transplant totals (all '
          'payers) and active heart transplant teams as stated in each annual edition (2009: active teams table; 2010–2012: text and team counts; '
          '2013–2025: "em N estados, com X equipes atuantes"); — not stated. CNES: establishments holding the SUS habilitation 24.11 (heart '
          'transplantation) in December, from the public CNES habilitation tabulation, available from March 2007; habilitation does not imply '
          'activity. In the North, all habilitated establishments were in the state of Pará. A team is not a hospital: one hospital may hold more '
          'than one team. CNES, National Registry of Health Establishments; RBT, Brazilian Transplant Registry; SIH, Hospital Information System.',
  'build': 'sources',
  'abbr': False}]
