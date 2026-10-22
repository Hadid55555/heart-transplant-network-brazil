"""Dados de referência do IBGE: população por UF, ano, sexo e idade e coordenadas das sedes municipais.

Os arquivos baixados ficam em ref/brutos/ (cópias incluídas no repositório; são baixados de novo se apagados).
"""
import glob
import os
import urllib.request

import numpy as np
import pandas as pd

AQUI = os.path.dirname(os.path.abspath(__file__))
REF = os.path.join(AQUI, "ref")
BRUTOS = os.path.join(REF, "brutos")
IPCA = os.path.join(REF, "ipca_fator_dez2025_2000_2025.csv")   # IPCA médio anual, fator para R$ de dez/2025
ANOS = list(range(2000, 2026))
URL_PROJ = "https://ftp.ibge.gov.br/Projecao_da_Populacao/Projecao_da_Populacao_2024/projecoes_2024_tab1_idade_simples.xlsx"
URL_LOC = ("https://geoftp.ibge.gov.br/organizacao_do_territorio/estrutura_territorial/localidades/"
           "Localidades_do_Brasil/2022/Localidades_UFs_shp.zip")
REGIAO = {**{u: "Norte" for u in "AC AM AP PA RO RR TO".split()}, **{u: "Nordeste" for u in "AL BA CE MA PB PE PI RN SE".split()},
          **{u: "Sudeste" for u in "ES MG RJ SP".split()}, **{u: "Sul" for u in "PR RS SC".split()},
          **{u: "Centro-Oeste" for u in "DF GO MS MT".split()}}
COD_UF = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO", "21": "MA", "22": "PI", "23": "CE",
          "24": "RN", "25": "PB", "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP",
          "41": "PR", "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}


def baixar(url, destino):
    if not os.path.exists(destino):
        os.makedirs(os.path.dirname(destino), exist_ok=True)
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (sih-txc)"})
        with urllib.request.urlopen(req, timeout=300) as r, open(destino, "wb") as f:
            f.write(r.read())
    return destino


def populacao(saida):
    """IBGE, Projeções da População, Revisão 2024 (idade simples, por UF e sexo), mesma fonte para todos os anos."""
    arq = baixar(URL_PROJ, os.path.join(BRUTOS, "projecoes_2024_tab1_idade_simples.xlsx"))
    x = pd.read_excel(arq, header=5)
    x.columns = [str(c).replace(".0", "") for c in x.columns]
    x = x[x.SIGLA.isin(COD_UF.values()) & x.SEXO.isin(["Homens", "Mulheres"])]
    idade = x.IDADE.astype(str).str.extract(r"(\d+)")[0].astype(int)       # "90+" -> 90
    long = x.assign(idade=idade).melt(id_vars=["SIGLA", "SEXO", "idade"], value_vars=[str(a) for a in ANOS],
                                      var_name="ano", value_name="populacao")
    long["ano"] = long.ano.astype(int)
    long["sexo"] = long.SEXO.map({"Homens": "M", "Mulheres": "F"})
    long = long.rename(columns={"SIGLA": "uf"})
    fx = pd.cut(long.idade, [-1, 11, 17, 39, 49, 59, 200], labels=["0-11", "12-17", "18-39", "40-49", "50-59", "60+"]).astype(str)
    q = (long.idade // 5 * 5).clip(upper=90)
    q5 = np.where(q >= 90, "90+", q.astype(str) + "-" + (q + 4).astype(str))
    a = long.assign(tipo_faixa="analise", faixa_etaria=fx)
    b = long.assign(tipo_faixa="quinquenal", faixa_etaria=q5)
    pop = pd.concat([a, b]).groupby(["uf", "ano", "sexo", "tipo_faixa", "faixa_etaria"], as_index=False).populacao.sum()
    pop["regiao"] = pop.uf.map(REGIAO)
    pop["populacao"] = pop.populacao.round().astype(int)
    pop = pop[["uf", "regiao", "ano", "sexo", "tipo_faixa", "faixa_etaria", "populacao"]].sort_values(
        ["uf", "ano", "sexo", "tipo_faixa", "faixa_etaria"])
    pop.to_csv(os.path.join(saida, "pop_uf_ano_sexo_idade.csv"), index=False, encoding="utf-8")
    return pop


def municipios(saida):
    """IBGE, Localidades do Brasil 2022: sede de cada município. codigo = 6 dígitos (como no SIH); codigo7 = código completo."""
    zipf = baixar(URL_LOC, os.path.join(BRUTOS, "Localidades_UFs_shp.zip"))
    pasta = os.path.join(BRUTOS, "loc")
    if not glob.glob(os.path.join(pasta, "*", "*.dbf")):
        import zipfile
        zipfile.ZipFile(zipf).extractall(pasta)
    from dbfread import DBF
    partes = [pd.DataFrame(iter(DBF(f, encoding="utf-8"))) for f in sorted(glob.glob(os.path.join(pasta, "*", "*.dbf")))]
    loc = pd.concat(partes, ignore_index=True)
    sede = loc[loc.SCT_LOCALI.isin(["Sede Municipal", "Capital Estadual", "Capital Federal"])].drop_duplicates("CD_MUN")
    m = pd.DataFrame({"codigo7": sede.CD_MUN.astype(str), "codigo": sede.CD_MUN.astype(str).str[:6], "nome": sede.NM_MUN,
                      "uf": sede.SIGLA_UF, "lat": sede.LAT_LOCALI.astype(float), "lon": sede.LONG_LOCAL.astype(float)})
    m = m.sort_values("codigo")
    m.to_csv(os.path.join(saida, "municipios_coord.csv"), index=False, encoding="utf-8")
    return m
