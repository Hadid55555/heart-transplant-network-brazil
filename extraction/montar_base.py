#!/usr/bin/env python3
"""Junta as internações de 2000–2007 (tabela antiga) e 2008–2025 (SIGTAP) numa única base, no formato de sih_txc.py.

Regras:
  - 2000–2007: só AIH com o transplante realizado (PROC_REA 46800018/47800011, ou 0505020041 se processada em 2008+).
  - Hospital antes de 2004: o SIH registrava só o CNPJ (CGC_HOSP). O CNES vem de (1) pares CNPJ–CNES nos registros
    de transplante de 2004–2007; (2) arquivos RD de 2004–2005 da mesma UF; (3) troca de identificador: no mesmo
    município há um único CNES cujos registros só trazem o CNPJ provisório '77777' + CNES. Sem correspondência:
    'CGC:<cnpj>'.
Entradas: saida_2000_2007/aih_2000_2007.csv (extrair_2000_2007.py) e saida_txc/txc_2008_2025_internacao_microdados.csv
Saída: saida_2000_2007/txc_2000_2025_internacao_microdados.csv. Os arquivos desta pasta identificam hospitais.

Uso: python3 montar_base.py
"""
import json
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import sih_txc as S  # noqa: E402

LOCAL = os.path.join(AQUI, "saida_2000_2007")
VELHOS = ["46800018", "47800011"]


def mapa_regras_1_2(d):
    """(1) pares CNPJ–CNES nos registros de TxC 2004–2007; (2) arquivos RD de 2004–2005 da UF (só CGC_HOSP e CNES)."""
    import pyarrow.parquet as pq
    mp = d[(d.CNES != "") & (d.CGC_HOSP != "")].groupby("CGC_HOSP").CNES.agg(lambda s: s.mode().iat[0]).to_dict()
    manifesto = json.load(open(os.path.join(LOCAL, "manifest_sih_rd.json")))["partitions"]
    sem = d[(d.CNES == "") & (d.CGC_HOSP != "") & ~d.CGC_HOSP.isin(mp)]
    for cgc, x in sem.groupby("CGC_HOSP"):
        uf = S.UF_IBGE[x.MUNIC_MOV.str[:2].mode().iat[0]]
        for k in [f"2004-01-{uf}", f"2004-06-{uf}", f"2005-01-{uf}"]:
            dst = os.path.join(LOCAL, f"bruto_{k}.parquet")
            if not os.path.exists(dst):
                of = manifesto[k]["output_files"][0]
                S.baixar(f"{S.ESPELHO}/{of['path'][len('sih/rd/'):]}", dst)
                if S.sha256(dst) != of["sha256"]:
                    raise ValueError(f"SHA-256 divergente em {k}")
            t = pq.read_table(dst, columns=["CGC_HOSP", "CNES"]).to_pandas()
            v = t[t.CGC_HOSP.str.strip() == cgc].CNES.str.strip().value_counts()
            if len(v):
                mp[cgc] = v.index[0]
                break
    return mp


def mapa_hospital(d):
    mp = mapa_regras_1_2(d)
    sem = d[(d.CNES == "") & (d.CGC_HOSP != "") & ~d.CGC_HOSP.isin(mp)]
    reg = []
    for cgc, x in sem.groupby("CGC_HOSP"):
        mun = x.MUNIC_MOV.mode().iat[0]
        y = d[(d.MUNIC_MOV == mun) & (d.CNES != "")]
        real = y[~y.CGC_HOSP.str.startswith("77777") & (y.CGC_HOSP != "")].CNES.unique()
        cand = sorted(set(y.CNES) - set(real))
        if len(cand) == 1:
            mp[cgc] = cand[0]
            reg.append({"cgc": cgc, "cnes": cand[0], "municipio": mun, "regra": "troca de identificador"})
        else:
            reg.append({"cgc": cgc, "cnes": "", "municipio": mun, "regra": f"sem correspondência ({len(cand)} candidatos)"})
    pd.DataFrame(reg).to_csv(os.path.join(LOCAL, "mapa_cgc_cnes_regra3.csv"), index=False)
    print(f"CNPJ→CNES: {len(mp)} mapeados; regra 3 aplicada a {sum(r['cnes'] != '' for r in reg)}")
    return mp


def main():
    d = pd.read_csv(os.path.join(LOCAL, "aih_2000_2007.csv"), dtype=str, keep_default_na=False)
    n_bruto = len(d)
    d = d[d.PROC_REA.isin(VELHOS + ["0505020041"])].copy()
    mp = mapa_hospital(d)
    d["CNES_ORIG"] = d.CNES
    d["CNES"] = np.where(d.CNES != "", d.CNES, d.CGC_HOSP.map(mp).fillna("CGC:" + d.CGC_HOSP))
    # variáveis derivadas no mesmo padrão de sih_txc.consolidar
    for c in S.VALORES:
        d[c] = pd.to_numeric(d.get(c, pd.Series("", index=d.index)).replace("", np.nan), errors="coerce").fillna(0)
    for c in S.INTEIROS:
        d[c] = pd.to_numeric(d.get(c, pd.Series("", index=d.index)).replace("", np.nan), errors="coerce").astype("Int64")
    d["grupo"] = "Transplante cardíaco"
    d["procedimento"] = d.PROC_REA.map({"46800018": "Transplante de coração (tabela antiga)", "47800011": "Retransplante de coração (tabela antiga)",
                                        "0505020041": "Transplante de coração"})
    mov = d.MUNIC_MOV.str.strip()
    d["uf"] = mov.str[:2].map(S.UF_IBGE)
    d["regiao"] = mov.str[:1].map(S.REGIAO)
    d["uf_res"] = d.MUNIC_RES.str.strip().str[:2].map(S.UF_IBGE)
    dt_i = pd.to_datetime(d.DT_INTER, format="%Y%m%d", errors="coerce")
    dt_s = pd.to_datetime(d.DT_SAIDA, format="%Y%m%d", errors="coerce")
    d["ano_internacao"] = dt_i.dt.year.astype("Int64")
    d["ano_saida"] = dt_s.dt.year.astype("Int64")
    d["ano_cmpt"] = pd.to_numeric(d.ANO_CMPT, errors="coerce").astype("Int64")
    cod = d.COD_IDADE.str.strip()
    idade = d.IDADE.astype("Float64").to_numpy(dtype=float, na_value=np.nan)
    d["idade_anos"] = np.select([cod.eq("4"), cod.eq("5"), cod.isin(["0", "1", "2", "3"])], [idade, 100 + idade, 0.0], np.nan)
    d["sexo_desc"] = d.SEXO.map({"1": "Masculino", "2": "Feminino", "3": "Feminino"}).fillna("Ignorado")
    d = d[d.ano_internacao.between(2000, 2007)]
    novo = pd.read_csv(os.path.join(AQUI, "saida_txc", "txc_2008_2025_internacao_microdados.csv"), dtype=str, keep_default_na=False)
    for c in novo.columns:
        if c not in d.columns:
            d[c] = ""
    d["periodo_tabela"] = "SIH antiga (2000–2007)"
    novo["periodo_tabela"] = "SIGTAP (2008–2025)"
    novo["CNES_ORIG"] = novo.CNES
    tudo = pd.concat([d[list(novo.columns)], novo], ignore_index=True)
    assert tudo.N_AIH.duplicated().sum() == 0, "N_AIH repetido entre os períodos"
    tudo.to_csv(os.path.join(LOCAL, "txc_2000_2025_internacao_microdados.csv"), index=False)

    print(f"2000–2007: {n_bruto} linhas extraídas -> {len(d)} AIH realizadas")
    print(f"base 2000–2025: {len(tudo)} AIH; óbitos {pd.to_numeric(tudo.MORTE).sum():.0f}")
    print("hospital sem CNES após o mapeamento:", int(tudo.CNES.str.startswith("CGC:").sum()), "AIH")
    print("centros distintos:", tudo.CNES.nunique())


if __name__ == "__main__":
    main()
