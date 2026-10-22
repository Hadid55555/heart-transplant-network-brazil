"""Builds the analysis data folder for the main definition of new center (first observed transplant in or after 2004,
i.e. an initial observation window of 2000-2003).

Copies <src> (output of extraction/exportar_base.py plus the reference data in data_2000/) to <dst> and
recomputes tipo_centro in microdados/aih_txc_2000_2025.csv and microdados/centro_ano.csv:
"entrante" (new) if ano_primeiro_txc_centro >= <first_year>, otherwise "incumbente". No other column is changed.

Usage: python3 -I prepare_window.py data_2000 data_2000_w04 2004
"""
import shutil
import sys
from pathlib import Path

import pandas as pd

src, dst = Path(sys.argv[1]), Path(sys.argv[2])
ent = int(sys.argv[3]) if len(sys.argv) > 3 else 2004
shutil.copytree(src, dst, dirs_exist_ok=True)
for name in ["aih_txc_2000_2025.csv", "centro_ano.csv"]:
    f = dst / "microdados" / name
    d = pd.read_csv(f, dtype=str, keep_default_na=False)
    d["tipo_centro"] = ["entrante" if int(a) >= ent else "incumbente" for a in d["ano_primeiro_txc_centro"]]
    d.to_csv(f, index=False, encoding="utf-8")
    print(f, len(d), "rows;", d.drop_duplicates("centro").tipo_centro.value_counts().to_dict())
