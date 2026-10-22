#!/usr/bin/env bash
# Builds the de-identified analysis files from the public SIH/SUS files (see README.md).
# Downloads about 8,600 monthly files; everything written here is record-level and excluded by .gitignore.
set -euo pipefail
cd "$(dirname "$0")"
python3 sih_txc.py --ini 2008 --fim 2025 --cmpt-fim 202606 --saida saida_txc   # SIGTAP 05.05.02.004-1
python3 extrair_2000_2007.py --ini 2000 --fim 2007                             # old table: 46800018, 47800011
python3 montar_base.py                                                         # joins both periods; CNPJ -> CNES before 2004
python3 exportar_base.py                                                       # de-identified files in export/
mkdir -p ../analysis/data_2000/microdados
cp export/aih_txc_2000_2025.csv export/centro_ano.csv ../analysis/data_2000/microdados/
echo "Done: analysis/data_2000/microdados/"
