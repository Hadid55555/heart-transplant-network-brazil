"""Leitura da base de internações e definição da base analítica (uma linha por N_AIH, sem AIH de longa permanência)."""
import numpy as np
import pandas as pd

REGIAO_UF = {"Norte": ["AC", "AM", "AP", "PA", "RO", "RR", "TO"],
             "Nordeste": ["AL", "BA", "CE", "MA", "PB", "PE", "PI", "RN", "SE"],
             "Sudeste": ["ES", "MG", "RJ", "SP"], "Sul": ["PR", "RS", "SC"], "Centro-Oeste": ["DF", "GO", "MS", "MT"]}
UF_REG = {u: r for r, us in REGIAO_UF.items() for u in us}
IDADE_CAT = [-1, 11, 17, 39, 49, 59, 200]
IDADE_LAB = ["0-11", "12-17", "18-39", "40-49", "50-59", "60+"]
UF_IBGE = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
           "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
           "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
           "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}


def etiologia(cid):
    c = cid.fillna("").str.strip().str.upper()
    return pd.Series(np.select(
        [c.str.startswith("B57"), c.str.startswith(("I20", "I21", "I22", "I23", "I24", "I25")),
         c.str.startswith("I420"), c.str.startswith(("I42", "I43")), c.str.startswith(("Q2",)),
         c.str.startswith(("I05", "I06", "I07", "I08", "I09", "I34", "I35", "I36", "I37", "I38")),
         c.str.startswith(("I40", "I41", "I514")), c.str.startswith("I50"), c.str.startswith(("I47", "I49")),
         c.str.startswith("T86"), c.str.startswith("Z94")],
        ["Doença de Chagas (B57)", "Isquêmica (I20–I25)", "Cardiomiopatia dilatada (I42.0)",
         "Outras cardiomiopatias (I42.x, I43)", "Cardiopatia congênita (Q20–Q28)", "Valvar (I05–I09, I34–I38)",
         "Miocardite (I40–I41, I51.4)", "Insuficiência cardíaca inespecífica (I50)", "Arritmia (I47, I49)",
         "Falência/rejeição de enxerto (T86)", "Z94 (estado pós-transplante)"],
        default="Outros códigos"), index=cid.index)


def carregar(micro, ipca_csv):
    d = pd.read_csv(micro, low_memory=False, dtype=str, keep_default_na=False)
    num = ["MORTE", "DIAS_PERM", "UTI_MES_TO", "idade_anos", "ano_internacao", "ano_saida", "ano_cmpt"] + \
          [c for c in d.columns if c.startswith("VAL_")]
    for c in num:
        d[c] = pd.to_numeric(d[c], errors="coerce")
    for c in ["MUNIC_RES", "MUNIC_MOV", "CNES", "NASC", "SEXO", "IDENT", "CAR_INT", "DIAG_PRINC", "N_AIH"]:
        d[c] = d[c].str.strip()
    d["ano"] = d.ano_internacao.astype(int)
    d["dt_i"] = pd.to_datetime(d.DT_INTER, format="%Y%m%d", errors="coerce")
    d["dt_s"] = pd.to_datetime(d.DT_SAIDA, format="%Y%m%d", errors="coerce")
    d["ped"] = (d.idade_anos < 18).astype(int)
    d["idade_cat"] = pd.cut(d.idade_anos, IDADE_CAT, labels=IDADE_LAB).astype(str)
    d["fem"] = d.SEXO.isin(["2", "3"]).astype(int)
    d["urg"] = (d.CAR_INT.str.zfill(2) != "01").astype(int)
    d["etiologia"] = etiologia(d.DIAG_PRINC)
    d["chagas"] = (d.etiologia == "Doença de Chagas (B57)").astype(int)
    sec = d[[f"DIAGSEC{i}" for i in range(1, 10)] + ["DIAG_SECUN"]].apply(lambda s: s.str.strip().str.upper().str.startswith("B57"))
    d["chagas_qualquer"] = ((d.chagas == 1) | sec.any(axis=1)).astype(int)
    d["uf_res"] = d.MUNIC_RES.str[:2].map(UF_IBGE)
    d["reg"] = d.uf.map(UF_REG)
    d["reg_res"] = d.uf_res.map(UF_REG)
    d["fora_uf"] = (d.uf != d.uf_res).astype(int)
    d["uti"] = d.UTI_MES_TO.fillna(0)
    ipca = pd.read_csv(ipca_csv).set_index("ano")["fator_dez2025"]
    d["tot_r"] = d.VAL_TOT.fillna(0) * d.ano.map(ipca)          # valor total em R$ de dez/2025
    return d


def duplicidades(d):
    """Base analítica: uma linha por N_AIH (a de competência mais recente), sem IDENT = 5 (longa permanência).
    Também marca o paciente provável (nascimento + sexo + município de residência) e o intervalo desde o registro
    anterior do mesmo paciente."""
    d = d.sort_values(["dt_i", "N_AIH"]).copy()
    d["pac"] = d.NASC + "|" + d.SEXO + "|" + d.MUNIC_RES
    d["pac_valido"] = d.NASC.str.len().eq(8) & ~d.NASC.isin(["00000000"])
    d["dias_desde_anterior"] = d[d.pac_valido].groupby("pac").dt_i.diff().dt.days
    base = d.sort_values(["ANO_CMPT", "MES_CMPT"]).drop_duplicates("N_AIH", keep="last")
    return base[base.IDENT != "5"].copy()
