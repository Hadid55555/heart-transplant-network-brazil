# Heart transplantation in Brazil's public health system, 2000–2025

Code for the article:

> Hadid L, Salek L, Passos FS, Caldonazo T. Heart transplantation in Brazil's public health system, 2000–2025: a nationwide analysis of network growth, regional utilization and center volume.

The code downloads the public hospital discharge files of the Brazilian Unified Health System (SIH/SUS, DATASUS), selects every heart transplant admission from January 2000 to December 2025, and produces the tables and figures of the article and its supplementary material.

## Data

| Source | Use | Access |
|---|---|---|
| SIH/SUS reduced admission files (RD), DATASUS | Admissions, centers, in-hospital death | Public. Downloaded by `extraction/sih_txc.py` from the healthbr-data mirror of the official files (SHA-256 checked) or from the DATASUS FTP (`--fonte ftp`) |
| IBGE population projections (2024 revision), 2022 Census, municipal seats | Standardized rates, distances, geographic proximity | Public; copies in `extraction/ref/` and `analysis/data_2000/ibge_covariaveis/` |
| Brazilian Transplant Registry (RBT/ABTO) annual reports | National and state totals; counts by team | Public reports; aggregate transcriptions in `analysis/data_2000/rbt/` |
| CNES habilitation (TabNet/DATASUS) | Hospitals habilitated for heart transplantation, by state | Public query run by `analysis/scripts/cnes_habilitacao_tabnet.py` |

**No record-level data are included.** The SIH files are public, but the files built from them (one row per admission) stay on the user's computer and are excluded by `.gitignore`. Hospitals are identified only by codes ("Centro NN"), and the analysis scripts write aggregate results.

One sensitivity analysis (first cases of new centers after excluding centers with activity in the registry's team lists before their first SIH admission) needed a comparison with the named team lists of the registry. That comparison identifies hospitals and was done only on the authors' computer; its aggregate result is in `analysis/data_2000/rbt/agregados/R4_aprendizado_sem_atividade_previa_RBT.csv`.

## Requirements

- Python 3.11 or later: `pip install -r requirements.txt`
- R 4.3.3 with the packages in `R_packages.txt`
- `pdftotext` (poppler-utils), only for `analysis/scripts/rbt_equipes_2017.py`

## How to reproduce

```bash
bash extraction/run_extraction.sh   # 1. download the SIH files and build the de-identified analysis files (several hours)
bash run_all.sh                     # 2. analyses, tables and figures
```

Step 1 reads the monthly RD files of the 27 states from January 2000 to June 2026 (8580 of the 8586 files were available when the study was run) and writes `analysis/data_2000/microdados/aih_txc_2000_2025.csv` (one row per admission) and `centro_ano.csv` (center by year). The scripts check the expected totals (5821 admissions, 819 in-hospital deaths, 64 centers) and stop if they differ.

Step 2 writes:

- `analysis/outputs_2000_2025/`: results of each analysis block, logs and `Tabelas_TxC_SUS.xlsx`;
- `tables_figures/out/`: Tables 1–4 (`tables_main_EN.md`) and Supplementary Tables S1–S15 (`Supplementary_Tables_EN.html`);
- `tables_figures/figures/out/`: Figures 1–4 and Supplementary Figures S1–S3 (PDF, TIFF 600 dpi, PNG).

The center bootstrap of the GEE (1000 resamples on 4 cores) takes several hours. Seeds are fixed in the scripts.

## Structure

| Folder | Content |
|---|---|
| `extraction/` | `sih_txc.py` (2008–2025, SIGTAP code 05.05.02.004-1), `extrair_2000_2007.py` (old SIH table, codes 46800018 and 47800011), `montar_base.py` (joins both periods; links the hospital tax number to the CNES before 2004), `exportar_base.py` (de-identified analysis files), `base.py` and `referencias.py` |
| `analysis/scripts/` | `param.R` and `comum.R` (parameters, data preparation, convergence sequence of the multilevel models); blocks 1–7; post hoc and external validation scripts; `tabelas_finais.py` |
| `tables_figures/` | English tables (`tabelas_en.py`, `tabelas_en_notes.py`) and figures (`figures/`) |

## Where each result comes from

| Article | Scripts |
|---|---|
| Selection of admissions (Figure 1) | `analysis/scripts/figura_fluxograma.R`; `tables_figures/figures/make_flowchart.py` |
| Network by year, concentration, source of growth (Table 2, Figure 2, Supplementary Tables S8–S10, S15) | `bloco1.py`, `bloco7_posthoc.R`, `rede_sensibilidade.py`, `rbt_equipes_2017.py`, `cnes_habilitacao_tabnet.py`, `validacao_externa.py` |
| Rates by region of residence, distance, proximity (Table 3, Figure 3, Supplementary Tables S5 and S7, Supplementary Figure S3) | `bloco2_geografia.R`, checked by `bloco2_conferencia.py`; `bloco5_sintese.R` |
| Volume and in-hospital death (Table 4, Figure 4, Supplementary Tables S2, S3 and S10–S12, Supplementary Figure S1) | `comum.R`, `bloco3_volume.R`, `figura3_e_loco.R`, `loco_lrt.R`, `volume_posthoc.R`, `posthoc_dentro.R`, `posthoc_dentro_2.R`, `bloco6_suplemento.R`; checked by `bloco3e4_conferencia.py` |
| First cases of new centers (Supplementary Table S4, Supplementary Figure S2) | `bloco4_aprendizado.R`, `volume_posthoc.R` |

Analysis parameters are set in `analysis/scripts/param.R`. A center is "new" when its first transplant in the data is in or after 2004 (`TXC_ENT=2004`; initial observation window 2000–2003). `analysis/prepare_window.py` applies this definition to the analysis files.

Comments and variable names in the scripts are in Portuguese.

## License and citation

Code under the MIT License (`LICENSE`). If you use it, please cite the article (`CITATION.cff`).

## Contact

Leonardo Hadid, Instituto Nacional de Cardiologia, Rio de Janeiro, Brazil. leonardohadid@gmail.com
