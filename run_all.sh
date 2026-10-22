#!/usr/bin/env bash
# Reproduces the analysis outputs, tables and figures after extraction/run_extraction.sh (see README.md).
set -euo pipefail
export LANG=C.UTF-8 TXC_INI=2000
ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT/analysis"
O=outputs_2000_2025; S=$O/sensibilidade
test -f data_2000/microdados/aih_txc_2000_2025.csv || { echo "Run extraction/run_extraction.sh first"; exit 1; }

# main definition of a new center: first observed transplant in or after 2004 (initial observation window 2000-2003)
python3 -I prepare_window.py data_2000 data_2000_w04 2004
mkdir -p $O/posthoc $S
python3 -I scripts/cnes_habilitacao_tabnet.py $S                 # CNES habilitation by state (public TabNet query)
cp data_2000/rbt/agregados/*.csv $S/                              # registry counts by team and the registry-list sensitivity analysis
python3 -I scripts/rede_sensibilidade.py data_2000 $S             # network description: without Sao Paulo, growth by center group
python3 -I scripts/validacao_externa.py $S                         # SIH vs registry vs CNES
Rscript scripts/volume_posthoc.R data_2000 $S > $S/stdout_volume.txt 2>&1
Rscript scripts/posthoc_dentro.R data_2000 $O > $O/posthoc/stdout.txt 2>&1
Rscript scripts/posthoc_dentro_2.R data_2000 $O > $O/posthoc/stdout_2.txt 2>&1
bash scripts/rodar_analise.sh                                      # blocks 1-7 and Tabelas_TxC_SUS.xlsx (GEE bootstrap: slow)

# English tables and figures
cd "$ROOT/tables_figures"
python3 -I tabelas_en.py "$ROOT/analysis/$O/Tabelas_TxC_SUS.xlsx" out
cd figures
for s in make_figures.py make_supp_figures.py make_central.py; do python3 -I $s "$ROOT/analysis/$O" out; done
echo "Done: analysis/$O, tables_figures/out, tables_figures/figures/out"
