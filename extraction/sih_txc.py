#!/usr/bin/env python3
"""Transplante cardíaco no SIH/SUS (AIH reduzida, RD), procedimento SIGTAP 05.05.02.004-1, a partir de 2008.

Baixa os arquivos RD<UF><AA><MM> de jan/<ini> até a competência --cmpt-fim, mantém as AIH com o procedimento
realizado ou solicitado e grava, em <saida>/:
  parciais/RD*.csv                                um CSV por arquivo mensal (retomável) e _cobertura.jsonl
  txc_<ini>_<fim>_internacao_microdados.csv       AIH com o procedimento realizado e internação entre <ini> e <fim>

Fontes (--fonte): "espelho" (padrão), espelho público healthbr-data (https://data.sidneybissoli.com/sih/rd/) com
Parquet convertido 1:1 dos .dbc do DATASUS e SHA-256 conferido por partição; "ftp", FTP oficial do DATASUS
(requer datasus-dbc e dbfread).

Uso (como no estudo): python3 sih_txc.py --ini 2008 --fim 2025 --cmpt-fim 202606 --saida saida_txc
"""
import argparse
import hashlib
import json
import os
import sys
import tempfile
import threading
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

import numpy as np
import pandas as pd

ESPELHO = "https://data.sidneybissoli.com/sih/rd"
FTP = "ftp://ftp.datasus.gov.br/dissemin/publicos/SIHSUS/200801_/Dados"

UFS = ("AC AL AM AP BA CE DF ES GO MA MG MS MT PA PB PE PI PR RJ RN RO RR RS SC "
       "SE SP TO").split()

PROCS = {"0505020041": "Transplante cardíaco"}
PROC_NOME = {"0505020041": "Transplante de coração"}
PREFIXO = "txc"

VALORES = ["VAL_SH", "VAL_SP", "VAL_SADT", "VAL_RN", "VAL_ACOMP", "VAL_ORTP", "VAL_SANGUE",
           "VAL_SADTSR", "VAL_TRANSP", "VAL_OBSANG", "VAL_PED1AC", "VAL_UTI", "VAL_TOT", "US_TOT",
           "VAL_SH_FED", "VAL_SP_FED", "VAL_SH_GES", "VAL_SP_GES"]
UTI = ["UTI_MES_IN", "UTI_MES_AN", "UTI_MES_AL", "UTI_MES_TO", "UTI_INT_TO", "MARCA_UTI"]
COLUNAS = (["ANO_CMPT", "MES_CMPT", "UF_ZI", "ESPEC", "N_AIH", "IDENT", "PROC_REA", "PROC_SOLIC", "MORTE",
            "DIAS_PERM", "IDADE", "COD_IDADE", "NASC", "SEXO", "DT_INTER", "DT_SAIDA", "DIAG_PRINC",
            "DIAG_SECUN", "CID_MORTE", "CAR_INT", "CNES", "MUNIC_MOV", "MUNIC_RES", "COBRANCA",
            "NAT_JUR", "RACA_COR", "GESTAO", "COMPLEX", "FINANC", "SEQ_AIH5"]
           + [f"DIAGSEC{i}" for i in range(1, 10)] + VALORES + UTI)
INTEIROS = ["MORTE", "DIAS_PERM", "IDADE", "UTI_MES_IN", "UTI_MES_AN", "UTI_MES_AL",
            "UTI_MES_TO", "UTI_INT_TO"]

UF_IBGE = {"11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP", "17": "TO",
           "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB", "26": "PE", "27": "AL",
           "28": "SE", "29": "BA", "31": "MG", "32": "ES", "33": "RJ", "35": "SP", "41": "PR",
           "42": "SC", "43": "RS", "50": "MS", "51": "MT", "52": "GO", "53": "DF"}
REGIAO = {"1": "Norte", "2": "Nordeste", "3": "Sudeste", "4": "Sul", "5": "Centro-Oeste"}


lock = threading.Lock()


def baixar(url, destino, tentativas=4):
    for i in range(tentativas):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "sih-txc/1.0"})
            with urllib.request.urlopen(req, timeout=300) as r, open(destino, "wb") as f:
                while True:
                    bloco = r.read(1 << 20)
                    if not bloco:
                        break
                    f.write(bloco)
            return
        except Exception:
            if i == tentativas - 1:
                raise
            time.sleep(2 ** (i + 1))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloco in iter(lambda: f.read(1 << 20), b""):
            h.update(bloco)
    return h.hexdigest()


def ler_espelho(chave, info, tmpdir):
    import pyarrow.compute as pc
    import pyarrow.parquet as pq

    tabelas, total = [], 0
    for of in info["output_files"]:
        destino = os.path.join(tmpdir, chave + "_" + os.path.basename(of["path"]))
        baixar(f"{ESPELHO}/{of['path'][len('sih/rd/'):]}", destino)
        try:
            if sha256(destino) != of["sha256"]:
                raise ValueError(f"SHA-256 divergente em {of['path']}")
            arq = pq.ParquetFile(destino)
            presentes = [c for c in COLUNAS if c in arq.schema_arrow.names]
            t = arq.read(columns=presentes)
            total += t.num_rows
            vs = __import__("pyarrow").array(list(PROCS))
            filtro = pc.is_in(t["PROC_REA"], value_set=vs)
            if "PROC_SOLIC" in t.column_names:
                filtro = pc.or_(filtro, pc.is_in(t["PROC_SOLIC"], value_set=vs))
            t = t.filter(filtro)
            tabelas.append(t.to_pandas(ignore_metadata=True))
        finally:
            os.remove(destino)
    df = pd.concat(tabelas, ignore_index=True) if tabelas else pd.DataFrame()
    return df, total


def ler_ftp(uf, ano, mes, tmpdir):
    import datasus_dbc
    from dbfread import DBF

    nome = f"RD{uf}{ano % 100:02d}{mes:02d}"
    dbc = os.path.join(tmpdir, nome + ".dbc")
    dbf = os.path.join(tmpdir, nome + ".dbf")
    baixar(f"{FTP}/{nome}.dbc", dbc)
    try:
        datasus_dbc.decompress(dbc, dbf)
        tab = DBF(dbf, encoding="latin-1", raw=False, char_decode_errors="replace")
        regs = [{k: (str(v) if v is not None else "") for k, v in r.items()} for r in tab]
        df = pd.DataFrame(regs)
        total = len(df)
        df = df[df["PROC_REA"].isin(PROCS) | df["PROC_SOLIC"].isin(PROCS)][[c for c in COLUNAS if c in df.columns]]
    finally:
        for p in (dbc, dbf):
            if os.path.exists(p):
                os.remove(p)
    return df.reset_index(drop=True), total


def processar(tarefa, args, pasta, tmpdir, manifesto):
    uf, ano, mes = tarefa
    nome = f"RD{uf}{ano % 100:02d}{mes:02d}"
    parcial = os.path.join(pasta, nome + ".csv")
    try:
        if args.fonte == "espelho":
            chave = f"{ano}-{mes:02d}-{uf}"
            info = manifesto.get(chave)
            if info is None:
                raise FileNotFoundError(f"partição {chave} ausente no espelho")
            df, total = ler_espelho(chave, info, tmpdir)
            origem = info.get("source_url", "")
        else:
            df, total = ler_ftp(uf, ano, mes, tmpdir)
            origem = f"{FTP}/{nome}.dbc"
        for c in COLUNAS:
            if c not in df.columns:
                df[c] = pd.NA
        df = df[COLUNAS]
        df["arquivo_origem"] = nome
        df.to_csv(parcial + ".tmp", index=False)
        os.replace(parcial + ".tmp", parcial)
        reg = {"arquivo": nome, "uf": uf, "ano": ano, "mes": mes, "status": "lido",
               "registros_arquivo": int(total), "registros_txc": int(len(df)),
               "fonte": args.fonte, "origem": origem}
    except Exception as e:
        reg = {"arquivo": nome, "uf": uf, "ano": ano, "mes": mes, "status": "falhou",
               "registros_arquivo": None, "registros_txc": None, "fonte": args.fonte,
               "origem": "", "erro": f"{type(e).__name__}: {e}"}
    with lock:
        with open(os.path.join(pasta, "_cobertura.jsonl"), "a") as f:
            f.write(json.dumps(reg, ensure_ascii=False) + "\n")
    return reg


def janela(args):
    """Competências de jan/<ini> até <cmpt_fim> (AAAAMM; padrão: jan/<fim+1>)."""
    fim = args.cmpt_fim or (args.fim + 1) * 100 + 1
    meses = [(a, m) for a in range(args.ini, fim // 100 + 1) for m in range(1, 13) if a * 100 + m <= fim]
    return [(uf, a, m) for a, m in meses for uf in UFS]


def extrair(args):
    pasta = os.path.join(args.saida, "parciais")
    os.makedirs(pasta, exist_ok=True)
    tarefas = janela(args)

    manifesto = {}
    if args.fonte == "espelho":
        mpath = os.path.join(args.saida, "manifest_sih_rd.json")
        if not os.path.exists(mpath):
            baixar(f"{ESPELHO}/manifest.json", mpath)
        manifesto = json.load(open(mpath))["partitions"]

    feitos = {f[:-4] for f in os.listdir(pasta) if f.startswith("RD") and f.endswith(".csv")}
    pendentes = [t for t in tarefas if f"RD{t[0]}{t[1] % 100:02d}{t[2]:02d}" not in feitos]
    print(f"{len(tarefas)} arquivos na janela; {len(tarefas) - len(pendentes)} já feitos; "
          f"{len(pendentes)} pendentes", flush=True)

    tmpdir = tempfile.mkdtemp(prefix="sih_dl_", dir=args.saida)
    ok = falhas = 0
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = [ex.submit(processar, t, args, pasta, tmpdir, manifesto) for t in pendentes]
        for i, fut in enumerate(as_completed(futs), 1):
            r = fut.result()
            if r["status"] == "lido":
                ok += 1
            else:
                falhas += 1
                print(f"  FALHOU {r['arquivo']}: {r['erro']}", flush=True)
            if i % 100 == 0 or i == len(futs):
                print(f"  {i}/{len(futs)} (ok={ok}, falhas={falhas})", flush=True)
    os.rmdir(tmpdir)
    return tarefas


def cobertura(args, tarefas):
    pasta = os.path.join(args.saida, "parciais")
    regs = {}
    path = os.path.join(pasta, "_cobertura.jsonl")
    if os.path.exists(path):
        for linha in open(path):
            r = json.loads(linha)
            regs[r["arquivo"]] = r  # a última tentativa vale
    linhas = []
    for uf, a, m in tarefas:
        nome = f"RD{uf}{a % 100:02d}{m:02d}"
        r = regs.get(nome, {"arquivo": nome, "uf": uf, "ano": a, "mes": m, "status": "não tentado"})
        if os.path.exists(os.path.join(pasta, nome + ".csv")):
            r["status"] = "lido"
        linhas.append(r)
    return pd.DataFrame(linhas)


def consolidar(args):
    pasta = os.path.join(args.saida, "parciais")
    arquivos = sorted(f for f in os.listdir(pasta) if f.startswith("RD") and f.endswith(".csv"))
    partes = [pd.read_csv(os.path.join(pasta, f), dtype=str, keep_default_na=False) for f in arquivos]
    df = pd.concat([p for p in partes if len(p)], ignore_index=True)
    for c in VALORES:
        df[c] = pd.to_numeric(df[c].str.strip(), errors="coerce")
    for c in INTEIROS:
        df[c] = pd.to_numeric(df[c].str.strip(), errors="coerce").astype("Int64")
    df["so_solicitado"] = (~df["PROC_REA"].isin(PROCS)).astype(int)
    df["procedimento"] = df["PROC_REA"].map(PROC_NOME)
    mov = df["MUNIC_MOV"].str.strip()
    df["uf"] = mov.str[:2].map(UF_IBGE)
    df["regiao"] = mov.str[:1].map(REGIAO)
    df["uf_res"] = df["MUNIC_RES"].str.strip().str[:2].map(UF_IBGE)
    dt_i = pd.to_datetime(df["DT_INTER"].str.strip(), format="%Y%m%d", errors="coerce")
    dt_s = pd.to_datetime(df["DT_SAIDA"].str.strip(), format="%Y%m%d", errors="coerce")
    df["ano_internacao"] = dt_i.dt.year.astype("Int64")
    df["ano_saida"] = dt_s.dt.year.astype("Int64")
    df["ano_cmpt"] = pd.to_numeric(df["ANO_CMPT"], errors="coerce").astype("Int64")
    cod = df["COD_IDADE"].str.strip()
    idade = df["IDADE"].astype("Float64")
    df["idade_anos"] = np.select(
        [cod.eq("4").to_numpy(), cod.eq("5").to_numpy(), cod.isin(["0", "1", "2", "3"]).to_numpy()],
        [idade.to_numpy(dtype=float, na_value=np.nan), 100 + idade.to_numpy(dtype=float, na_value=np.nan), 0.0],
        default=np.nan)
    df["faixa_etaria"] = pd.cut(df["idade_anos"], [-1, 11, 17, 39, 49, 59, 69, 200],
                                labels=["0-11", "12-17", "18-39", "40-49", "50-59", "60-69", "70+"]).astype(str)
    df["grupo"] = np.where(df["idade_anos"].isna(), "Idade ignorada",
                           np.where(df["idade_anos"] < 18, "Pediátrico", "Adulto"))
    df["mes_internacao"] = dt_i.dt.strftime("%Y-%m")
    df["regiao_res"] = df["MUNIC_RES"].str.strip().str[:1].map(REGIAO)
    df["fora_uf_res"] = (df["uf_res"].notna() & df["uf"].notna() & (df["uf_res"] != df["uf"])).astype(int)
    df.loc[df["idade_anos"].isna(), "faixa_etaria"] = "Ignorado"
    df["sexo_desc"] = df["SEXO"].str.strip().map({"1": "Masculino", "2": "Feminino", "3": "Feminino"}).fillna("Ignorado")
    return df


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--ini", type=int, default=2008)
    ap.add_argument("--fim", type=int, default=2025)
    ap.add_argument("--saida", default="saida_txc")
    ap.add_argument("--fonte", choices=["espelho", "ftp"], default="espelho")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--cmpt-fim", type=int, default=None,
                    help="última competência AAAAMM a baixar (padrão: jan do ano seguinte a --fim)")
    ap.add_argument("--so-consolidar", action="store_true", help="não baixa; só consolida os parciais")
    args = ap.parse_args()
    args.workers = max(4, min(8, args.workers))
    os.makedirs(args.saida, exist_ok=True)

    tarefas = janela(args) if args.so_consolidar else extrair(args)
    cob = cobertura(args, tarefas)
    lidos = cob["status"].eq("lido")
    print(f"\nArquivos na janela: {len(cob)} | lidos: {lidos.sum()} | faltando: {(~lidos).sum()}")
    if (~lidos).any():
        print("Faltando:", ", ".join(cob.loc[~lidos, "arquivo"]))

    todos = consolidar(args)
    todos = todos[todos["so_solicitado"].eq(0)].copy()
    d = todos[todos["ano_internacao"].between(args.ini, args.fim)].copy()
    d["n_aih_duplicado"] = d["N_AIH"].duplicated(keep=False).astype(int)
    arq = os.path.join(args.saida, f"{PREFIXO}_{args.ini}_{args.fim}_internacao_microdados.csv")
    d.sort_values(["ano_internacao", "uf", "N_AIH"]).to_csv(arq, index=False, encoding="utf-8-sig")
    print(f"AIH com o procedimento realizado, internação {args.ini}–{args.fim}: {len(d)} | óbitos {int(d['MORTE'].sum())}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
