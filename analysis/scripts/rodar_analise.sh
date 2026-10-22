#!/usr/bin/env bash
# Blocos 1–7, conferências, fluxograma e tabelas (Tabelas_TxC_SUS.xlsx, usada por tables_figures/).
# Dados: data_2000_w04/ (analysis/prepare_window.py). Saídas: outputs_2000_2025/.
set -euo pipefail
export LANG=C.UTF-8 TXC_INI=2000 TXC_ENT=2004 NUCLEOS=4   # bootstrap do GEE em 4 núcleos (a semente por núcleo depende disso)
cd "$(dirname "$0")/.."
D=data_2000_w04; O=outputs_2000_2025
mkdir -p $O/bloco1 $O/bloco2 $O/bloco3 $O/bloco4 $O/bloco5 $O/bloco6 $O/bloco7 $O/_local
rm -f $O/_local/diag_b*.csv
test -f $D/microdados/aih_txc_2000_2025.csv || { echo "Faltam os microdados em $D/microdados/"; exit 1; }
python3 -I scripts/bloco1.py $D $O/bloco1 > $O/bloco1/log_bloco1.txt
Rscript scripts/bloco2_geografia.R $D $O/bloco2 > $O/bloco2/stdout.txt 2>&1
python3 -I scripts/bloco2_conferencia.py $D $O/bloco2 > $O/bloco2/conferencia_bloco2.txt
DIAG_FILE=$O/_local/diag_b3.csv Rscript scripts/bloco3_volume.R $D $O/bloco3 > $O/bloco3/stdout.txt 2>&1 & p3=$!
DIAG_FILE=$O/_local/diag_b6.csv Rscript scripts/bloco6_suplemento.R $D $O > $O/bloco6/stdout.txt 2>&1 & p6=$!
wait $p3; wait $p6
Rscript scripts/figura3_e_loco.R $D $O/bloco3 > $O/bloco3/stdout_fig3.txt 2>&1
Rscript scripts/loco_lrt.R $D $O > $O/bloco3/stdout_loco_lrt.txt 2>&1
DIAG_FILE=$O/_local/diag_b4.csv Rscript scripts/bloco4_aprendizado.R $D $O/bloco4 > $O/bloco4/stdout.txt 2>&1
DIAG_FILE=$O/_local/diag_b5.csv Rscript scripts/bloco5_sintese.R $D $O > $O/bloco5/stdout.txt 2>&1
Rscript scripts/bloco7_posthoc.R $D $O > $O/bloco7/stdout.txt 2>&1
python3 -I scripts/compila_diag.py $O/_local $O/bloco7/R12_diagnostico_convergencia.csv
python3 -I scripts/bloco3e4_conferencia.py $D $O > $O/conferencia_blocos3e4.txt
Rscript scripts/figura_fluxograma.R $D $O/bloco1 > $O/bloco1/stdout_fluxograma.txt 2>&1 || true
python3 -I scripts/tabelas_finais.py $D $O > $O/stdout_tabelas.txt 2>&1
echo "Concluído."
