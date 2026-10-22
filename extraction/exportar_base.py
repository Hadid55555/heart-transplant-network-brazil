#!/usr/bin/env python3
"""Exporta a base de análise de-identificada, 2000–2025 (uma linha por internação).

Entrada: saida_2000_2007/txc_2000_2025_internacao_microdados.csv (montar_base.py)
Saídas em export/:
  aih_txc_2000_2025.csv       uma linha por AIH, sem CNES, CNPJ, número da AIH nem data de nascimento
  centro_ano.csv              centro × ano, com zeros
  pop_uf_ano_sexo_idade.csv, municipios_coord.csv (referencias.py)
Centros: código "Centro NN" (ordem de frequência nos registros de 2008–2025) ou "Centro PNN" (centros sem registro a partir
de 2008, ordem de frequência). tipo_centro é recalculado na análise (analysis/prepare_window.py).

Uso: python3 exportar_base.py
"""
import os
import sys

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import base as B  # noqa: E402
import referencias as R  # noqa: E402

LOCAL = os.path.join(AQUI, "saida_2000_2007")
OUT = os.path.join(AQUI, "export")
os.makedirs(OUT, exist_ok=True)
ANOS = list(range(2000, 2026))


def regra_cnes(d):
    """Como o hospital foi identificado em cada AIH (só antes de 2004 há AIH sem CNES no registro)."""
    pre = pd.read_csv(os.path.join(LOCAL, "aih_2000_2007.csv"), dtype=str, keep_default_na=False)
    pre = pre[pre.PROC_REA.isin(["46800018", "47800011", "0505020041"])]
    r1 = set(pre[(pre.CNES != "") & (pre.CGC_HOSP != "")].CGC_HOSP)
    r3 = set(pd.read_csv(os.path.join(LOCAL, "mapa_cgc_cnes_regra3.csv"), dtype=str).query("cnes == cnes").cgc)
    cgc = d.N_AIH.map(pre.drop_duplicates("N_AIH").set_index("N_AIH").CGC_HOSP)
    orig = d.CNES_ORIG.fillna("").str.strip() != ""
    return np.select([orig, cgc.isin(r1), cgc.isin(r3)], ["original", "1_pares_txc", "3_troca_identificador"],
                     "2_arquivos_2004_2005")


def main():
    d0 = B.carregar(os.path.join(LOCAL, "txc_2000_2025_internacao_microdados.csv"), R.IPCA)
    anon = {}
    sigtap = pd.read_csv(os.path.join(AQUI, "saida_txc", "txc_2008_2025_internacao_microdados.csv"), dtype=str,
                         usecols=["CNES"], keep_default_na=False).CNES.str.strip().value_counts().index
    anon.update({c: f"Centro {i:02d}" for i, c in enumerate(sigtap, 1)})
    extra = [c for c in d0.CNES.value_counts().index if c not in anon]
    anon.update({c: f"Centro P{i:02d}" for i, c in enumerate(extra, 1)})
    d = B.duplicidades(d0)
    d = d.sort_values(["dt_i", "uf", "N_AIH"]).reset_index(drop=True)
    d["id_aih"] = np.arange(1, len(d) + 1)
    chave = np.where(d.pac_valido, d.pac, "sem_nasc_" + d.id_aih.astype(str))
    d["paciente_provavel_id"] = pd.factorize(pd.Series(chave))[0] + 1
    primeiro = d.groupby("CNES").ano.min()
    d["ano_primeiro_txc_centro"] = d.CNES.map(primeiro)
    d["tipo_centro"] = np.where(d.ano_primeiro_txc_centro <= 2001, "incumbente", "entrante")
    d["ano_programa"] = d.ano - d.ano_primeiro_txc_centro + 1
    d["volume_centro_ano"] = d.groupby(["CNES", "ano"]).N_AIH.transform("size")
    cm = d.CID_MORTE.fillna("").str.strip()
    a = pd.DataFrame({
        "id_aih": d.id_aih, "centro": d.CNES.map(anon), "uf_hosp": d.uf, "regiao_hosp": d.reg,
        "ano_inter": d.ano, "mes_inter": d.dt_i.dt.month, "ano_saida": d.dt_s.dt.year,
        "competencia": d.ANO_CMPT.str.strip() + d.MES_CMPT.str.strip().str.zfill(2), "dias_perm": d.DIAS_PERM,
        "idade": d.idade_anos, "faixa_etaria": d.idade_cat, "pediatrico": d.ped,
        "sexo": np.where(d.fem == 1, "F", np.where(d.SEXO == "1", "M", "ignorado")),
        "uf_res": d.uf_res, "regiao_res": d.reg_res, "fora_uf": d.fora_uf,
        "carater": np.where(d.urg == 0, "eletivo", "urgencia_outros"),
        "diag_princ": d.DIAG_PRINC.str.strip().str.upper(), "chagas_qualquer": d.chagas_qualquer, "etiologia_grupo": d.etiologia,
        "morte": d.MORTE.astype(int), "cid_morte": np.where(cm.isin(["", "0000"]), "", cm), "uti_dias": d.uti,
        "val_sh": d.VAL_SH.round(2), "val_sp": d.VAL_SP.round(2), "val_tot": d.VAL_TOT.round(2),
        "val_tot_real_dez2025": d.tot_r.round(2), "paciente_provavel_id": d.paciente_provavel_id,
        "dias_desde_registro_anterior": d.dias_desde_anterior, "tipo_centro": d.tipo_centro,
        "ano_primeiro_txc_centro": d.ano_primeiro_txc_centro, "ano_programa": d.ano_programa,
        "volume_centro_ano": d.volume_centro_ano, "munic_res": d.MUNIC_RES.str.strip(), "munic_hosp": d.MUNIC_MOV.str.strip(),
    })
    for c in ["ano_saida", "dias_desde_registro_anterior"]:
        a[c] = a[c].astype("Int64")
    sem_res = a.uf_res.isna()          # MUNIC_RES "000000" (residência ignorada)
    a["fora_uf"] = a.fora_uf.astype("Int64").mask(sem_res)

    # distâncias geodésicas (WGS84) entre sedes municipais; Regiões Administrativas do DF -> sede de Brasília (530010)
    from pyproj import Geod
    geod = Geod(ellps="WGS84")
    mun = R.municipios(OUT)
    co = mun.set_index("codigo")[["lat", "lon"]]

    def coords(s):
        s = pd.Series(np.asarray(s, dtype=str)).where(lambda z: ~z.str.startswith("53"), "530010")
        c = co.reindex(s)
        return c.lat.to_numpy(), c.lon.to_numpy()
    la1, lo1 = coords(a.munic_res)
    la2, lo2 = coords(a.munic_hosp)
    ok = ~(np.isnan(la1) | np.isnan(la2))
    dist = np.full(len(a), np.nan)
    dist[ok] = geod.inv(lo1[ok], la1[ok], lo2[ok], la2[ok])[2] / 1000
    a["dist_km_centro_operou"] = np.round(dist, 1)
    # centro ativo mais próximo no ano: municípios de hospital com ≥1 transplante no ano
    prox = np.full(len(a), np.nan)
    for ano, idx in a.groupby("ano_inter").groups.items():
        tl, tg = coords(a.loc[a.ano_inter == ano, "munic_hosp"].unique())
        rl, rg = coords(a.loc[idx, "munic_res"])
        for k, pl, pg in zip(idx, rl, rg):
            if not np.isnan(pl):
                prox[a.index.get_loc(k)] = (geod.inv(np.full(len(tl), pg), np.full(len(tl), pl), tg, tl)[2] / 1000).min()
    a["dist_km_centro_mais_proximo_ano"] = np.round(prox, 1)
    a["periodo_tabela"] = np.where(a.ano_inter >= 2008, "SIGTAP", "SIH antiga")
    a["regra_cnes"] = regra_cnes(d)
    a.to_csv(os.path.join(OUT, "aih_txc_2000_2025.csv"), index=False, encoding="utf-8")

    info = a.groupby("centro").agg(uf_hosp=("uf_hosp", lambda s: s.mode().iat[0]), regiao_hosp=("regiao_hosp", lambda s: s.mode().iat[0]),
                                   tipo_centro=("tipo_centro", "first"), ano_primeiro_txc_centro=("ano_primeiro_txc_centro", "first"))
    grade = pd.MultiIndex.from_product([sorted(info.index), ANOS], names=["centro", "ano"])
    ca = a.groupby(["centro", "ano_inter"]).agg(n_txc=("id_aih", "size"), obitos=("morte", "sum"), n_ped=("pediatrico", "sum"))
    ca.index.names = ["centro", "ano"]
    ca = ca.reindex(grade, fill_value=0).reset_index().merge(info.reset_index(), on="centro")
    ca = ca[["centro", "uf_hosp", "regiao_hosp", "ano", "n_txc", "obitos", "n_ped", "tipo_centro", "ano_primeiro_txc_centro"]]
    ca.to_csv(os.path.join(OUT, "centro_ano.csv"), index=False, encoding="utf-8")

    pop = R.populacao(OUT)

    ok = []

    def chk(nome, cond, det=""):
        ok.append(bool(cond))
        print(f"[{'OK' if cond else 'FALHOU'}] {nome} {det}")
    chk("5821 AIH, 819 óbitos, 64 centros", len(a) == 5821 and a.morte.sum() == 819 and a.centro.nunique() == 64,
        f"({len(a)} AIH; {a.morte.sum()} óbitos; {a.centro.nunique()} centros)")
    chk("centro_ano soma = AIH", ca.n_txc.sum() == len(a))
    chk("sem CNES, CNPJ, N_AIH e nascimento", not {"CNES", "N_AIH", "NASC", "CGC_HOSP"} & set(a.columns))
    chk("distâncias ausentes só onde a residência é ignorada",
        (a.dist_km_centro_operou.isna() == a.uf_res.isna()).all() and (a.dist_km_centro_mais_proximo_ano.isna() == a.uf_res.isna()).all())
    chk("população 27 UFs × 26 anos", pop[pop.tipo_faixa == "analise"].groupby(["uf", "ano"]).ngroups == 27 * 26)
    print("regra_cnes:", a.regra_cnes.value_counts().to_dict())
    print("TODAS AS CONFERÊNCIAS OK" if all(ok) else "HÁ CONFERÊNCIAS COM FALHA")
    return 0 if all(ok) else 1


if __name__ == "__main__":
    sys.exit(main())
