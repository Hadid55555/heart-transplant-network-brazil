#!/usr/bin/env python3
"""Transplante cardíaco no SIH/SUS antes do SIGTAP: internações de 2000 a 2007 (AIH reduzida, RD, tabela antiga).

Códigos da tabela SIH/SUS anterior a jan/2008 que correspondem a 05.05.02.004-1 (Transplante de coração), segundo a
tabela oficial de correspondência "Relatório de Procedimentos da Tabela SIA/SIH, Relacionados aos Procedimentos
Novos" (SES-RS): 46800018 (transplante de coração) e 47800011 (retransplante de coração).

Lê as competências jan/<ini>–dez/2007 com as rotinas de sih_txc.py. As internações desse período processadas em 2008
ou depois já vêm com o código SIGTAP e são lidas dos parciais de saida_txc/ (rodar sih_txc.py antes).
Saída: saida_2000_2007/aih_2000_2007.csv (e parciais/, manifest_sih_rd.json)

Uso: python3 extrair_2000_2007.py --ini 2000 --fim 2007
"""
import argparse
import glob
import json
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from types import SimpleNamespace

import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import sih_txc as S  # noqa: E402

SAIDA = os.path.join(AQUI, "saida_2000_2007")
CODIGOS = ["46800018", "47800011"]
COLS = ["ANO_CMPT", "MES_CMPT", "UF_ZI", "ESPEC", "N_AIH", "IDENT", "PROC_REA", "PROC_SOLIC", "MORTE", "DIAS_PERM", "IDADE",
        "COD_IDADE", "NASC", "SEXO", "DT_INTER", "DT_SAIDA", "DIAG_PRINC", "DIAG_SECUN", "CID_MORTE", "CAR_INT", "CNES",
        "CGC_HOSP", "MUNIC_MOV", "MUNIC_RES", "NATUREZA", "NAT_JUR", "RACA_COR",
        "VAL_SH", "VAL_SP", "VAL_SADT", "VAL_RN", "VAL_ACOMP", "VAL_ORTP", "VAL_SANGUE", "VAL_SADTSR", "VAL_TRANSP",
        "VAL_OBSANG", "VAL_PED1AC", "VAL_UTI", "VAL_TOT", "US_TOT", "UTI_MES_TO", "UTI_INT_TO", "MARCA_UTI"] + \
       [f"DIAGSEC{i}" for i in range(1, 10)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ini", type=int, default=2000)
    ap.add_argument("--fim", type=int, default=2007)
    ap.add_argument("--workers", type=int, default=8)
    a = ap.parse_args()
    S.PROCS = {c: "TxC tabela antiga" for c in CODIGOS}
    S.COLUNAS = COLS
    pasta = os.path.join(SAIDA, "parciais")
    os.makedirs(pasta, exist_ok=True)
    mpath = os.path.join(SAIDA, "manifest_sih_rd.json")
    if not os.path.exists(mpath):
        S.baixar(f"{S.ESPELHO}/manifest.json", mpath)
    manifesto = json.load(open(mpath))["partitions"]
    jan = SimpleNamespace(ini=a.ini, fim=a.fim, cmpt_fim=200712, fonte="espelho")
    tarefas = S.janela(jan)
    feitos = {f[:-4] for f in os.listdir(pasta) if f.startswith("RD") and f.endswith(".csv")}
    pend = [t for t in tarefas if f"RD{t[0]}{t[1] % 100:02d}{t[2]:02d}" not in feitos]
    print(f"{len(tarefas)} arquivos na janela ({a.ini}-01 a 2007-12); {len(pend)} pendentes", flush=True)
    tmp = os.path.join(SAIDA, "tmp_dl")
    os.makedirs(tmp, exist_ok=True)
    with ThreadPoolExecutor(a.workers) as ex:
        futs = [ex.submit(S.processar, t, jan, pasta, tmp, manifesto) for t in pend]
        for i, f in enumerate(as_completed(futs), 1):
            r = f.result()
            if r["status"] != "lido":
                print("  FALHOU", r["arquivo"], r.get("erro"), flush=True)
            if i % 200 == 0:
                print(f"  {i}/{len(pend)}", flush=True)
    os.rmdir(tmp)
    cob = S.cobertura(SimpleNamespace(saida=SAIDA), tarefas)
    print(f"cobertura: {int(cob.status.eq('lido').sum())}/{len(cob)}; faltando: {', '.join(cob.loc[~cob.status.eq('lido'), 'arquivo'])}")

    nomes = {f"RD{u}{y % 100:02d}{m:02d}" for u, y, m in tarefas}
    arqs = [f for f in glob.glob(os.path.join(pasta, "RD*.csv")) if os.path.basename(f)[:-4] in nomes]
    d = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False) for f in arqs], ignore_index=True)
    d["fonte"] = "tabela antiga"
    p08 = pd.concat([pd.read_csv(f, dtype=str, keep_default_na=False)
                     for f in glob.glob(os.path.join(AQUI, "saida_txc", "parciais", "RD*.csv"))], ignore_index=True)
    p08 = p08[(p08.DT_INTER.str[:4] <= str(a.fim)) & (p08.DT_INTER.str[:4] >= str(a.ini))].assign(fonte="SIGTAP, processada 2008+")
    d = pd.concat([d, p08.reindex(columns=list(d.columns))], ignore_index=True).fillna("")
    for c in d.columns:
        d[c] = d[c].astype(str).str.strip()
    d = d[d.DT_INTER.str[:4].between(str(a.ini), str(a.fim))]
    d.to_csv(os.path.join(SAIDA, f"aih_{a.ini}_{a.fim}.csv"), index=False)
    print(f"AIH (internação {a.ini}–{a.fim}): {len(d)}; realizado={d.PROC_REA.isin(CODIGOS + ['0505020041']).sum()}")


if __name__ == "__main__":
    main()
