# Tabelas do artigo e do suplemento (Tabelas_TxC_SUS.xlsx), montadas só a partir das saídas dos blocos 1–7:
# nenhum número é digitado aqui, os valores são lidos de outputs_2000_2025/ e apenas formatados. Uma aba por tabela,
# com os cabeçalhos em português; tables_figures/tabelas_en.py faz a versão em inglês.
# Uso: python3 -I scripts/tabelas_finais.py data_2000_w04 outputs_2000_2025
import os, sys, re, math
import numpy as np, pandas as pd

base, out = sys.argv[1], sys.argv[2]
INI = int(os.environ.get('TXC_INI', '2000'))
ENT = int(os.environ.get('TXC_ENT', INI + 2))   # centro novo = 1º TxC observado a partir de ENT
INC = f'{INI}–{(ENT - 1) % 100:02d}'              # "2000–03": janela de observação inicial
X = lambda f, s: pd.read_excel(f'{out}/{f}', sheet_name=s)
d = pd.read_csv(f'{base}/microdados/aih_txc_{INI}_2025.csv')
_vm = d.assign(Vm1=d.volume_centro_ano - 1).groupby('centro').Vm1.mean().sort_values(ascending=False)
SEG = _vm.iloc[1]   # acima do 2º maior volume médio, a curva "entre" depende de 1 centro

# ------------------------------------------------------------------ formatação
def num(x, k=2):
    if x is None or (isinstance(x, float) and (math.isnan(x) or math.isinf(x))): return '—'
    s = f'{x:,.{k}f}'
    return s.replace(',', '§').replace('.', ',').replace('§', '.')
def ic(e, lo, hi, k=2): return f'{num(e, k)} ({num(lo, k)}–{num(hi, k)})'
def pfmt(p):
    if p is None or (isinstance(p, float) and math.isnan(p)): return ''
    return '<0,001' if p < 0.001 else num(p, 3)
def br(s):
    """Converte texto numérico do bloco 1 (ponto decimal, vírgula de milhar) para o padrão brasileiro, sem alterar valores."""
    if not isinstance(s, str): return s
    s = re.sub(r'(\d),(\d{3})', r'\1§\2', s)
    s = re.sub(r'(\d)\.(\d)', r'\1,\2', s)
    return s.replace('§', '.').replace('>=', '≥').replace('<=', '≤')
def nums(s):  # números contidos num texto (para conferir que a conversão não alterou valores)
    s = str(s)
    return [float(z) for z in re.findall(r'\d+(?:\.\d+)?', re.sub(r'(\d),(\d{3})', r'\1\2', s))]
def nums_br(s):
    s = str(s).replace('.', '').replace(',', '.')
    return [float(z) for z in re.findall(r'\d+(?:\.\d+)?', s)]

TABS = []   # (aba, título, DataFrame)
def add(aba, titulo, df):
    df = df.copy(); df.columns = [str(c) for c in df.columns]
    TABS.append((aba, titulo, df.fillna('—').astype(str).replace({'nan': '—', 'None': '—'})))

# ------------------------------------------------------------------ Tabela 1 (bloco 1; só formatação)
t1 = pd.read_csv(f'{out}/bloco1/Tabela1.csv')
t1f = t1.map(br)
for c in t1.columns[1:]:   # conferência: mesmos números antes e depois da formatação
    for a, b in zip(t1[c], t1f[c]):
        assert np.allclose(nums(a), nums_br(b)), (a, b)
t1f.columns = ['Característica', 'Total', 'Adultos (≥18 anos)', 'Pediátricos (<18 anos)', f'Centros {INC}', f'Centros com 1º TxC observado ≥{ENT}']
t1f['Característica'] = t1f['Característica'].str.strip()
add('T1', f'Características das internações de transplante cardíaco no SUS, {INI}–2025, por idade e por tipo de centro', t1f)

# ------------------------------------------------------------------ Tabela 2 (bloco 1; só formatação)
t2 = pd.read_csv(f'{out}/bloco1/Tabela2.csv')
t2f = pd.DataFrame({
    'Ano': t2.Ano.astype(int).astype(str), 'AIH': t2.AIH.astype(int).astype(str),
    'Centros ativos (≥1 TxC)': t2.Centros_ativos_ge1.astype(int).astype(str), 'Centros com ≥10 TxC': t2.Centros_ativos_ge10.astype(int).astype(str),
    'Entradas': t2.Entradas.map(lambda v: '—' if pd.isna(v) else str(int(v))),
    'Saídas (último ano com TxC)': t2.Ultimo_ano_de_atividade.map(lambda v: '—' if pd.isna(v) else str(int(v))),
    'UFs com centro': t2.UFs_com_centro.astype(int).astype(str), 'HHI': t2.HHI.map(lambda v: num(v, 0)),
    '3 maiores centros, %': t2.Top3_pct.map(lambda v: num(v, 1)), 'TxC em centros <10/ano, %': t2.AIH_em_centros_lt10_pct.map(lambda v: num(v, 1)),
    'Óbitos': t2.Obitos.astype(int).astype(str), 'Mortalidade bruta, %': t2.Mortalidade_bruta_pct.map(lambda v: num(v, 1))})
add('T2', f'Evolução da rede de transplante cardíaco no SUS por ano, {INI}–2025', t2f)

# ------------------------------------------------------------------ Tabela 3 (bloco 2)
add('T3', f'Utilização e distribuição geográfica do transplante cardíaco por região de residência e período, {INI}–2025',
    pd.read_csv(f'{out}/bloco2/Tabela3.csv'))

# ------------------------------------------------------------------ Tabela 4 (bloco 3)
t4 = pd.read_csv(f'{out}/bloco3/Tabela4.csv')
nb = [int(z) for z in re.findall(r'bootstrap: (\d+) reamostragens válidas', ' '.join(t4.iloc[:, 0].astype(str)))]
assert nb and nb[0] >= 950, f'Tabela 4 parece vir de execução de teste (bootstrap válido = {nb}); rode o bloco 3 com B = 1000'
def fix_t4(txt):
    txt = str(txt)
    m = re.search(r'IQR ([\d.]+)–([\d.]+)', txt)
    if m: txt = txt.replace(m.group(0), f'IQR {num(float(m.group(1)), 1)}–{num(float(m.group(2)), 1)}')
    m = re.search(r'exchangeable do GEE = ([\d.]+)', txt)
    if m: txt = txt.replace(m.group(0), f'exchangeable do GEE = {num(float(m.group(1)), 3)}')
    txt = txt.replace('Categoria V >=40', 'Categoria V ≥40').replace('V 10-19', 'V 10–19').replace('V 20-39', 'V 20–39')
    txt = re.sub(r'\((\d+) / (\d+)\)', lambda z: f'({num(int(z.group(1)), 0)} / {num(int(z.group(2)), 0)})', txt)
    return txt
t4.iloc[:, 0] = t4.iloc[:, 0].map(fix_t4)
ref = t4.iloc[:, 0].str.startswith('Categoria V <10 vs <10')
t4.loc[ref, t4.columns[0]] = t4.loc[ref, t4.columns[0]].str.replace('Categoria V <10 vs <10', 'Categoria V <10 (referência)')
t4.loc[ref, t4.columns[1]] = 'referência'
cat_ord = {'Categoria V <10 (refer': 0, 'Categoria V 10–19': 1, 'Categoria V 20–39': 2, 'Categoria V ≥40': 3}
key = t4.iloc[:, 0].map(lambda z: next((v for k, v in cat_ord.items() if z.startswith(k)), None))
idx_cat = key[key.notna()].sort_values().index
t4 = pd.concat([t4.loc[:idx_cat.min() - 1], t4.loc[idx_cat], t4.loc[idx_cat.max() + 1:]]).reset_index(drop=True)
def _valor_entre(txt):
    m = re.match(r'Entre: V−1 médio = (P90 \(([\d,]+)\)|P10 \(([\d,]+)\)|([\d,]+)) vs', str(txt))
    if not m: return None
    v = m.group(2) or m.group(3) or m.group(4); return float(v.replace(',', '.'))
_um = t4.iloc[:, 0].map(lambda z: (_valor_entre(z) or 0) > SEG)
t4.loc[_um, t4.columns[0]] = t4.loc[_um, t4.columns[0]] + ' ‡'
t4.loc[_um, 'GEE OR (IC95% bootstrap de centros)'] = t4.loc[_um, 'GEE OR (IC95% bootstrap de centros)'].astype(str) + ' (instável)'
t4 = t4.drop(columns=['GEE (IC95% sanduíche)'])
add('T4', 'Volume anual do centro e óbito hospitalar: modelo logístico multinível (estimativa principal) e GEE', t4)

# ------------------------------------------------------------------ Tabela 5 (bloco 2)
add('T5', 'Crianças e mulheres: utilização, cirurgia fora da UF, distância e razão de taxas mulher/homem, por período',
    pd.read_csv(f'{out}/bloco2/Tabela5.csv'))

# ------------------------------------------------------------------ Suplemento
cap = X('bloco6/Bloco6_tabelas.xlsx', 'Captura_UF')
add('TS1', 'Captura do SIH em relação ao Registro Brasileiro de Transplantes (RBT/ABTO) por UF do hospital (2020, 2023, 2024)',
    pd.DataFrame({'Ano': cap.ano, 'Edição do RBT': cap.edicao_RBT, 'UF': cap.uf, 'Região': cap.regiao, 'SIH (AIH)': cap.SIH, 'RBT': cap.RBT,
                  'SIH − RBT': cap.dif_abs, 'SIH/RBT, %': cap.captura_pct.map(lambda v: num(v, 1)),
                  f'% das AIH em centros com 1º TxC ≥{ENT}': cap.pct_AIH_entrante.map(lambda v: num(v, 1))}))
add('TS2', 'Análises de sensibilidade do modelo de volume: OR (IC95%)', pd.read_csv(f'{out}/bloco6/TabelaS6_sensibilidades.csv'))
r4 = X('bloco4/Bloco4_tabelas.xlsx', 'Resultados')
r4f = pd.DataFrame({'Amostra': r4.amostra, 'Análise': r4.analise, 'Termo': r4.termo, 'OR (IC95%)': [ic(a, b, c) for a, b, c in zip(r4.OR, r4.lo, r4.hi)],
                    'p': r4.p.map(pfmt), 'Passo': r4.passo})
add('TS3', f'Primeiros casos (exploratório): óbito hospitalar pelo nº sequencial do caso nos centros com 1º TxC observado ≥{ENT}', r4f)
tr = X('bloco2/Bloco2_tabelas.xlsx', 'Tendencia_regiao_IRR'); dp = X('bloco2/Bloco2_tabelas.xlsx', 'Dispersao').iloc[0]; mu = X('bloco2/Bloco2_tabelas.xlsx', 'Modelo_UF')
fo = X('bloco2/Bloco2_tabelas.xlsx', 'ForaUF_Firth')
s8 = pd.concat([pd.DataFrame({'Modelo': tr.modelo, 'Termo': tr.termo, 'Razão (IC95%)': [ic(a, b, c) for a, b, c in zip(tr.IRR, tr.lo, tr.hi)], 'p': tr.p.map(pfmt)}),
                pd.DataFrame({'Modelo': 'Cirurgia fora da UF (Firth, descritivo): OR', 'Termo': fo.termo, 'Razão (IC95%)': [ic(a, b, c) for a, b, c in zip(fo.OR, fo.lo, fo.hi)], 'p': fo.p.map(pfmt)})])
add('TS8', 'Modelos de contagem (tendência de utilização) e modelo descritivo de cirurgia fora da UF', s8)
rd = X('bloco6/Bloco6_tabelas.xlsx', 'Risco_calibracao'); rauc = X('bloco6/Bloco6_tabelas.xlsx', 'Risco_AUC').iloc[0]
add('TS12', 'Diagnóstico do modelo de risco (faixa etária, sexo, ano): calibração por décimos de risco predito',
    pd.DataFrame({'Décimo': rd.decil, 'AIH': rd.n, 'Óbitos observados': rd.O, 'Óbitos esperados': rd.E.map(lambda v: num(v, 1)),
                  'Observado, %': rd.obs_pct.map(lambda v: num(v, 1)), 'Esperado, %': rd.esp_pct.map(lambda v: num(v, 1))}))
add('TS16', f'Dados faltantes por variável no banco de análise ({num(len(d), 0)} AIH)',
    pd.DataFrame({'Variável': d.columns, 'Faltantes, n': d.isna().sum().values, 'Faltantes, %': (100 * d.isna().mean()).map(lambda v: num(v, 1)).values}))
r5 = pd.read_excel(f'{out}/bloco7/Bloco7_posthoc.xlsx', sheet_name='R5_decomposicao')
add('TS19', f'Origem do crescimento: média anual de AIH em {INI}–{(INI + 1) % 100:02d} e 2024–25 por grupo de centro (post hoc)',
    pd.DataFrame({'Grupo de centro': r5.grupo, 'Centros': r5.centros, f'AIH/ano {INI}–{(INI + 1) % 100:02d}': r5[f'media_{INI}_{(INI + 1) % 100:02d}'].map(lambda v: num(v, 1)),
                  'AIH/ano 2024–25': r5.media_2024_25.map(lambda v: num(v, 1)), 'Variação': r5.variacao.map(lambda v: num(v, 1)),
                  '% da variação total': r5.pct_da_variacao.map(lambda v: num(v, 1))}))

# ------------------------------------------------------------------ escrita
with pd.ExcelWriter(f'{out}/Tabelas_TxC_SUS.xlsx') as xw:
    pd.DataFrame([(aba, tit) for aba, tit, _ in TABS], columns=['Aba', 'Título']).to_excel(xw, sheet_name='Indice', index=False)
    for aba, _, df in TABS:
        df.to_excel(xw, sheet_name=aba, index=False)
print(f'{len(TABS)} tabelas escritas em {out}/Tabelas_TxC_SUS.xlsx')
