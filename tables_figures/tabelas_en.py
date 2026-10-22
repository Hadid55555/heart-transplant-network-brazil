"""English version of the analysis tables (Tabelas_TxC_SUS.xlsx): Tables 1–4 and Supplementary Tables S1–S15.

Titles and notes are in tabelas_en_notes.py; cells are translated from the Portuguese tables, and four supplementary tables
(S9, S10, S13, S15) are built from the post hoc outputs in outputs_2000_2025/sensibilidade/.
Outputs: tables_main_EN.md (Tables 1–4) and Supplementary_Tables_EN.html (S1–S15).
Usage: python3 -I tabelas_en.py <outputs_2000_2025/Tabelas_TxC_SUS.xlsx> <outdir>
"""
import csv, os, re, sys, html as _h
import openpyxl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from tabelas_en_notes import MAIN, SUPP  # noqa: E402

XLSX, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
wb = openpyxl.load_workbook(XLSX, read_only=True)
SENS = os.path.join(os.path.dirname(os.path.abspath(XLSX)), 'sensibilidade')

# ---------------------------------------------------------------- numbers
def fmt_int(n):
    s = str(n)
    return f"{n:,}" if len(s.lstrip('-')) >= 5 else s

def conv_num(s):
    if 'Model failed' in s or 'max|grad|' in s:
        return s
    s = re.sub(r'(\d),(\d)', '\\1\x01\\2', s)            # decimal comma
    def th(m):
        raw = m.group(0).replace('.', '')
        return fmt_int(int(raw))
    s = re.sub(r'(?<![\d.])[1-9]\d{0,2}(?:\.\d{3})+(?!\d)', th, s)  # thousands dot
    s = s.replace('\x01', '.')
    s = re.sub(r'\b(\d{4})-(\d{4})\b', '\\1–\\2', s)                 # periods
    s = re.sub(r'\(([\d,.]+)-([\d,.]+)\)', '(\\1–\\2)', s)             # IQR ranges
    s = re.sub(r'^(\d+)-(\d+)$', '\\1–\\2', s)                         # case blocks
    s = re.sub(r'^-(\d)', '−\\1', s)                                     # minus sign
    return s

# ---------------------------------------------------------------- glossary
EXACT = {
 'Característica': 'Characteristic',
 'Total': 'Total',
 'Adultos (≥18 anos)': 'Adults (≥18 years)',
 'Pediátricos (<18 anos)': 'Children (<18 years)',
 'Centros 2000–03': 'Incumbent centres (2000–03)',
 'Centros com 1º TxC observado ≥2004': 'Centres first observed ≥2004',
 'AIH, n': 'Admissions, n',
 'Centros, n': 'Centres, n',
 'Óbito hospitalar, n (%)': 'In-hospital death, n (%)',
 'Idade, mediana (IQR)': 'Age, years, median (IQR)',
 'Sexo feminino, n (%)': 'Female sex, n (%)',
 'Chagas em qualquer campo, n (%)': 'Chagas disease in any diagnosis field, n (%)',
 'Caráter urgência/outros (descritivo), n (%)': 'Admission type urgent/other (descriptive only), n (%)',
 'Tempo de internação, dias, mediana (IQR)': 'Length of stay, days, median (IQR)',
 'Operados fora da UF de residência, n (%)': 'Operated on outside the state of residence, n (%)',
 'Distância percorrida, km, mediana (IQR)': 'Distance travelled, km, median (IQR)',
 'Distância P75, km': 'Distance, 75th percentile, km',
 'Volume do centro no ano (V), mediana (IQR)': 'Centre volume in the year (V), median (IQR)',
 'Reembolso real por AIH, R$ dez/2025, mediana (IQR)': 'Real reimbursement per admission, R$ Dec 2025, median (IQR)',
 'Ano': 'Year',
 'AIH': 'Admissions',
 'Centros ativos (≥1 TxC)': 'Active centres (≥1 transplant)',
 'Centros com ≥10 TxC': 'Centres with ≥10 transplants',
 'Entradas': 'Entries',
 'Saídas (último ano com TxC)': 'Exits (last year with a transplant)',
 'UFs com centro': 'States with a centre',
 'HHI': 'HHI',
 '3 maiores centros, %': '3 largest centres, %',
 'TxC em centros <10/ano, %': 'Admissions in centres with <10/year, %',
 'Óbitos': 'Deaths',
 'Mortalidade bruta, %': 'Crude mortality, %',
 'Região de residência': 'Region of residence',
 'Período': 'Period',
 'TxC, n': 'Transplants, n',
 'Taxa bruta/milhão/ano': 'Crude rate per million per year',
 'Taxa padronizada/milhão/ano (IC95%)': 'Standardized rate per million per year (95% CI)',
 'Distância percorrida, km, mediana (P75)': 'Distance travelled, km, median (P75)',
 'Fora da UF, n (%)': 'Outside state of residence, n (%)',
 '≤300 km, % pop. (centro ≥1 | ≥5)': '≤300 km, % population (centre ≥1 | ≥5)',
 '≤500 km, % pop. (centro ≥1 | ≥5)': '≤500 km, % population (centre ≥1 | ≥5)',
 '≤1.000 km, % pop. (centro ≥1 | ≥5)': '≤1000 km, % population (centre ≥1 | ≥5)',
 'Brasil': 'Brazil',
 'Norte': 'North',
 'Nordeste': 'Northeast',
 'Sudeste': 'Southeast',
 'Sul': 'South',
 'Centro-Oeste': 'Centre-West',
 'Parâmetro': 'Parameter',
 'Multinível OR (IC95%)': 'Multilevel OR (95% CI)',
 'GEE OR (IC95% bootstrap de centros)': 'GEE OR (95% CI, centre bootstrap)',
 'Dentro: +10 TxC/ano acima da média do centro': 'Within: +10 transplants/year above the centre mean',
 "LRT global de 'entre' (2 gl): p = 0,167": 'Global LRT of "between" (2 df): P = 0.167',
 'LRT de não linearidade (1 gl): p = 0,585': 'LRT of non-linearity (1 df): P = 0.585',
 'referência': 'reference',
 'DP do centro (logit)': 'Centre SD (logit scale)',
 'ICC (escala latente)': 'ICC (latent scale)',
 'OR mediano do centro': 'Median OR of the centre',
 'Centros: 64 (AIH por centro: mediana 20, IQR 5,0–104,0, faixa 1–920); AIH 5.821; óbitos 819': 'Centres: 64 (admissions per centre: median 20, IQR 5.0–104.0, range 1–920); admissions 5821; deaths 819',
 'Passo da escada: principal = 2; categorias = 2; auxiliar = 1. Correlação exchangeable do GEE = 0,012; bootstrap: 1000 reamostragens válidas': 'Convergence step: main = 2; categories = 2; auxiliary = 1. GEE exchangeable correlation = 0.012; bootstrap: 1000 valid resamples',
 'Crianças, n': 'Children, n',
 'Taxa crianças/milhão 0–17 anos/ano (IC95%)': 'Rate in children per million aged 0–17 per year (95% CI)',
 'Fora da UF, crianças n (%)': 'Outside state, children, n (%)',
 'Fora da UF, adultos n (%)': 'Outside state, adults, n (%)',
 'Distância, crianças, km, mediana (P75)': 'Distance, children, km, median (P75)',
 'Distância, adultos, km, mediana (P75)': 'Distance, adults, km, median (P75)',
 'Centros com ≥1 TxC pediátrico/ano (mín–máx)': 'Centres with ≥1 paediatric transplant/year (min–max)',
 'Mulheres, n': 'Women, n',
 'Homens, n': 'Men, n',
 'Taxa padr. por idade, mulheres (IC95%)': 'Age-standardized rate, women (95% CI)',
 'Taxa padr. por idade, homens (IC95%)': 'Age-standardized rate, men (95% CI)',
 'Razão mulher/homem (IC95%)': 'Female-to-male rate ratio (95% CI)',
 'Edição do RBT': 'RBT edition',
 'UF': 'State',
 'Região': 'Region',
 'SIH (AIH)': 'SIH (admissions)',
 'RBT': 'RBT',
 'SIH − RBT': 'SIH − RBT',
 'SIH/RBT, %': 'SIH/RBT, %',
 '% das AIH em centros com 1º TxC ≥2004': '% of admissions in centres first observed ≥2004',
 'Centros': 'Centres',
 'analise': 'Analysis',
 'obitos': 'Deaths',
 'centros': 'Centres',
 'passo': 'Step',
 'Dentro +10 TxC/ano': 'Within, +10 transplants/year',
 'Entre 40 vs 20': 'Between, 40 vs 20',
 'Entre 5 vs 20': 'Between, 5 vs 20',
 'Entre P10 vs P50': 'Between, P10 vs P50',
 'Entre P90 vs P50': 'Between, P90 vs P50',
 'Principal (referência)': 'Main analysis (reference)',
 'Só adultos (≥18 anos)': 'Adults only (≥18 years)',
 'Sem 2020–2021': 'Excluding 2020–2021',
 'V com índice (contínuo; nós transladados +1)': 'V including the index case (continuous; knots shifted +1)',
 'Volume defasado (ano anterior; sem 2000)': 'Lagged volume (previous year; excluding 2000)',
 'Entre = média simples dos anos ativos (sem zeros)': 'Between = unweighted mean of active years (no zeros)',
 'Entre = média do período ativo (com zeros intermediários)': 'Between = mean of the active period (with intermediate zeros)',
 'Sem os 2 primeiros anos dos centros com 1º TxC ≥2004': 'Excluding the first 2 years of centres first observed ≥2004',
 'Sem centro(s) acima de 99,8% no funil (post hoc; n = 5)': 'Excluding centres above the 99.8% funnel-plot limit (post hoc; n = 5)',
 'Sem os 108 AIH de prováveis readmitidos': 'Excluding the 108 admissions of probable readmitted patients',
 'Uma linha por paciente (1ª AIH; óbito em qualquer AIH)': 'One row per patient (first admission; death in any admission)',
 'UFs com captura SIH/RBT ≥90%': 'States with SIH/RBT completeness ≥90%',
 'Ano como efeito fixo (fator)': 'Year as fixed effect (factor)',
 'Efeito fixo de centro (logística condicional, verossimilhança exata)': 'Centre fixed effect (conditional logistic regression, exact likelihood)',
 'Firth sem Chagas (sem efeito de centro)': 'Firth without Chagas (no centre effect)',
 'Firth com Chagas (sem efeito de centro)': 'Firth with Chagas (no centre effect)',
 'Só 2008–2025 (tabela SIGTAP)': '2008–2025 only (unified procedure table)',
 'Sem 2000–2001 (diagnóstico principal quase sempre Z94)': 'Excluding 2000–2001 (principal diagnosis almost always Z94)',
 'Sem AIH com hospital identificado por troca de identificador (regra 3 CNPJ→CNES)': 'Excluding admissions with hospital linked by identifier change (rule 3, tax number→CNES)',
 'Com indicador de tabela SIGTAP (2008+)': 'With indicator of unified procedure table (2008+)',
 'Modelo': 'Model',
 'Passo': 'Step',
 'Amostra': 'Sample',
 'Análise': 'Analysis',
 'Termo': 'Term',
 'OR (IC95%)': 'OR (95% CI)',
 '35 centros': '35 centres',
 'Primário: um dos 5 primeiros casos (vs demais)': 'Primary: one of the first 5 cases (vs later cases)',
 '5 primeiros': 'First 5',
 'Spline do nº do caso': 'Spline of case number',
 'log2(nº do caso)': 'log2(case number)',
 'por duplicação do nº do caso': 'per doubling of case number',
 'Categorias (ref. >50)': 'Categories (ref. >50)',
 'Idade do programa (ref. ≥10 anos)': 'Programme age (ref. ≥10 years)',
 'Blocos de 5 (ref. >20)': 'Blocks of 5 (ref. >20)',
 'Razão (IC95%)': 'Ratio (95% CI)',
 'M1: ns(ano,2) + região': 'M1: ns(year, 2) + region',
 'regiaoNorte': 'Region: North',
 'regiaoNordeste': 'Region: Northeast',
 'regiaoSul': 'Region: South',
 'regiaoCentro-Oeste': 'Region: Centre-West',
 'M2: M1 + nº centros ativos na região (descritivo)': 'M2: M1 + number of active centres in the region (descriptive)',
 'ncent': 'Active centres in the region (per centre)',
 'Cirurgia fora da UF (Firth, descritivo): OR': 'Surgery outside the state of residence (Firth, descriptive): OR',
 'faixa5<18': 'Age <18 (ref. 18–39)',
 'faixa540-49': 'Age 40–49',
 'faixa550-59': 'Age 50–59',
 'faixa560+': 'Age ≥60',
 'sexoFF': 'Female (ref. male)',
 'reg_refNorte': 'Region: North (ref. Southeast)',
 'reg_refNordeste': 'Region: Northeast',
 'reg_refSul': 'Region: South',
 'reg_refCentro-Oeste': 'Region: Centre-West',
 'dcat>0-100': 'Distance to nearest centre >0–100 km (ref. 0 km)',
 'dcat>100-300': 'Distance >100–300 km',
 'dcat>300-500': 'Distance >300–500 km',
 'dcat>500': 'Distance >500 km',
 'Décimo': 'Decile of predicted risk',
 'Óbitos observados': 'Observed deaths',
 'Óbitos esperados': 'Expected deaths',
 'Observado, %': 'Observed, %',
 'Esperado, %': 'Expected, %',
 'Variável': 'Variable',
 'Faltantes, n': 'Missing, n',
 'Faltantes, %': 'Missing, %',
 'Grupo de centro': 'Centre group',
 'AIH/ano 2000–01': 'Admissions/year 2000–01',
 'AIH/ano 2024–25': 'Admissions/year 2024–25',
 'Variação': 'Change',
 '% da variação total': '% of total change',
 'Centros 2000–03 ainda ativos em 2024–25': 'Incumbent centres still active in 2024–25',
 'Centros 2000–03 sem atividade em 2024–25': 'Incumbent centres without activity in 2024–25',
 'Centros com 1º TxC ≥2004': 'Centres first observed ≥2004',
 'p': 'P',
 '—': '—',
}
PATTERNS = [
 (r'^Sem Centro (P?\d+)$', lambda m: f'Without Centre {m.group(1)}'),
 (r'^Faixa etária (\S+), n \(%\)$', lambda m: f'Age group {m.group(1).replace("-", "–").replace("60+", "≥60")} years, n (%)'),
 (r'^Região do hospital (.+), n \(%\)$', lambda m: f'Region of the hospital: {EXACT.get(m.group(1), m.group(1))}, n (%)'),
 (r'^AIH em centro-ano V (.+), n \(%\)$', lambda m: f'Admissions in centre-years with V {m.group(1).replace("-", "–")}, n (%)'),
 (r'^Etiologia: (.+)$', None),
 (r'^Entre: V−1 médio = (.+)$', lambda m: 'Between: mean V − 1 = ' + m.group(1)),
 (r'^Categoria V (.+) \(AIH/óbitos na categoria: (\d+) / (\d+)\)$', lambda m: f'Category V {m.group(1).replace(" (referência)", " (reference)")} (admissions/deaths in category: {m.group(2)}/{m.group(3)})'),
 (r'^(.+) \(instável\)$', lambda m: m.group(1) + ' (unstable)'),
 (r'^caso (\d+) vs caso (\d+)$', lambda m: f'case {m.group(1)} vs case {m.group(2)}'),
 (r'^RBT (\d{4})$', lambda m: f'RBT {m.group(1)}'),
 (r'^(\d{4})-(\d{2}) a (\d{4})-(\d{2})$', lambda m: f'{m.group(1)}-{m.group(2)} to {m.group(3)}-{m.group(4)}'),
]
ETIO = {
 'Insuficiência cardíaca inespecífica (I50)': 'unspecified heart failure (I50)', 'Outras cardiomiopatias (I42.x, I43)': 'other cardiomyopathies (I42.x, I43)',
 'Isquêmica (I20–I25)': 'ischaemic (I20–I25)', 'Z94 (estado pós-transplante)': 'Z94 (transplant status)', 'Outros códigos': 'other codes',
 'Cardiomiopatia dilatada (I42,0)': 'dilated cardiomyopathy (I42.0)', 'Cardiopatia congênita (Q20–Q28)': 'congenital heart disease (Q20–Q28)',
 'Falência/rejeição de enxerto (T86)': 'graft failure/rejection (T86)', 'Miocardite (I40–I41, I51,4)': 'myocarditis (I40–I41, I51.4)',
 'Doença de Chagas (B57)': 'Chagas disease (B57)', 'Valvar (I05–I09, I34–I38)': 'valvular (I05–I09, I34–I38)'}

def tr(x):
    if x is None:
        return ''
    if isinstance(x, bool):
        return str(x)
    if isinstance(x, int):
        return fmt_int(x)
    if isinstance(x, float):
        return str(int(x)) if x.is_integer() else f'{x:g}'
    s = str(x).strip()
    if re.fullmatch(r'\d+\.0', s):
        return s[:-2]
    if s in EXACT:
        return EXACT[s]
    m = re.match(r'^Etiologia: (.+), n \(%\)$', s)
    if m:
        return 'Principal diagnosis: ' + ETIO.get(m.group(1), m.group(1)) + ', n (%)'
    for pat, fn in PATTERNS:
        if fn is None:
            continue
        m = re.match(pat, s)
        if m:
            return conv_num(fn(m))
    return conv_num(s)

PT_WORDS = re.compile(r'\b(de|do|da|dos|das|com|sem|por|ano|anos|centro|centros|óbito|óbitos|não|são|até|mês|período|faixa|taxa|média|mediana|entre|dentro|total pago|caso|casos|região)\b|[ãõçáéíóúâêô]', re.I)

def sheet_rows(name):
    rows = []
    for r in wb[name].iter_rows(values_only=True):
        if all(v is None for v in r):
            continue
        rows.append(list(r))
    width = max(len(r) for r in rows)
    rows = [r + [None] * (width - len(r)) for r in rows]
    # drop fully empty columns
    keep = [j for j in range(width) if any(r[j] is not None for r in rows)]
    return [[r[j] for j in keep] for r in rows]

def translate_sheet(name):
    return [[tr(v) for v in r] for r in sheet_rows(name)]

ABBR = ('CI, confidence interval; df, degrees of freedom; GEE, generalized estimating equations; HHI, Herfindahl–Hirschman index; '
        'ICC, intraclass correlation coefficient; IQR, interquartile range; LRT, likelihood ratio test; OR, odds ratio; P75, 75th percentile; '
        'RBT, Brazilian Transplant Registry; SE, standard error; SIH, Hospital Information System; V, number of transplants of the centre in the year '
        '(including the index case); V − 1, number of other transplants of the centre in the year.')
def abbr_for(*texts, header=''):
    """Only the abbreviations that appear in this table (title, cells, note).
    'SE' is also a state code (Sergipe), so it counts only when it appears in the header or the note."""
    blob = ' '.join(texts)
    keep = []
    for entry in re.split(r'; (?=[A-Za-z0-9V])', ABBR.rstrip('.')):
        key = entry.split(',')[0].strip()
        pat = re.escape(key).replace('\\ ', ' ')
        where = (header + ' ' + texts[1]) if key == 'SE' else blob
        if re.search(r'(?<![A-Za-z0-9])' + pat + r'(?![A-Za-z0-9])', where):
            keep.append(entry)
    if 'V − 1' in blob:
        keep = [k for k in keep if not (k.startswith('V,') and 'V ' not in blob.replace('V − 1', ''))]
    return ('; '.join(keep) + '.') if keep else ''

PAIRS = [('centre', 'center'), ('programme', 'program'), ('paediatric', 'pediatric'), ('aetiology', 'etiology'), ('ischaemic', 'ischemic'),
         ('modelled', 'modeled'), ('labelled', 'labeled'), ('travelled', 'traveled'), ('centring', 'centering'), ('centred', 'centered'),
         ('analysed', 'analyzed'), ('standardised', 'standardized')]
def us(t):
    """American spelling (JHLT house style)."""
    for gb, u in PAIRS:
        t = re.sub(gb, u, t)
        t = re.sub(gb.capitalize(), u.capitalize(), t)
    return t

# ---------------------------------------------------------------- tables built from the post hoc outputs
def _csv(name):
    with open(os.path.join(SENS, name), encoding='utf-8') as f:
        return list(csv.DictReader(f))

def _ci(r, k=2):
    return f"{float(r['OR']):.{k}f} ({float(r['lo']):.{k}f}–{float(r['hi']):.{k}f})"

def build_concentration():
    by = {(r['sample'], r['ano_inter']): r for r in _csv('N1_concentracao_com_sem_SP.csv')}
    rows = [['Year', 'Comparison', 'Active centers', 'HHI', '3 largest, %', '9 largest, %', 'Admissions in centers <10/year, %']]
    for y in ['2000', '2008', '2017', '2020', '2023', '2025']:
        a_, s_ = by[('All states', y)], by[('Without São Paulo', y)]
        f = lambda k, n=0: f"{float(a_[k]):.{n}f} | {float(s_[k]):.{n}f}"
        rows.append([y, 'SIH, all states | without SP', f('active_centers'), f('HHI'), f('top3_pct', 1), f('top9_pct', 1), f('lt10_pct', 1)])
    n6 = _csv('N6_concentracao_SIH_vs_RBT.csv')
    for y in sorted({r['ano'] for r in n6}):
        a_ = next(r for r in n6 if r['ano'] == y and r['fonte'] == 'SIH'); b_ = next(r for r in n6 if r['ano'] == y and r['fonte'] != 'SIH')
        f = lambda k, n=0: f"{float(a_[k]):.{n}f} | {float(b_[k]):.{n}f}"
        rows.append([y, f"SIH | RBT by hospital ({a_['transplantes']} | {b_['transplantes']} transplants)", f('centros_ativos'), f('hhi'),
                     f('top3_pct', 1), f('top9_pct', 1), f('lt10_pct', 1)])
    return rows

LAB = {'Principal (intercepto aleatório)': 'Main model (random intercept)',
       'Random slope de ano por centro': 'Random intercept and random slope of year by center',
       'Random slope sem correlação': 'Random intercept and slope, uncorrelated',
       'Sensibilidade: 1º TxC observado ≥2002 (janela 2000–2001)': 'Sensitivity: first observed ≥2002 (observation window 2000–2001)',
       'Principal: 1º TxC observado ≥2004 (janela 2000–2003)': 'Main: first observed ≥2004 (observation window 2000–2003)',
       'Sem os centros com atividade prévia confirmada no RBT': 'Main window, excluding new centers with confirmed earlier activity in RBT team lists',
       'Sem atividade prévia confirmada ou possível no RBT': 'Main window, excluding new centers with confirmed or possible earlier activity in RBT team lists',
       'All states': 'all states', 'Without São Paulo': 'without São Paulo'}

def build_posthoc():
    rows = [['Analysis', 'Sample or definition', 'Result']]
    for r in _csv('N2_decomposicao_crescimento.csv'):
        rows.append(['Source of growth (2000–01 vs 2024–25), % of net change: incumbent active | new | incumbent closed',
                     f"{LAB.get(r['sample'], r['sample'])}; new program = {r['new_program_rule']} ({r['n_new_centers']} new centers)",
                     f"{float(r['pct_incumbent_active']):.1f} | {float(r['pct_new']):.1f} | {float(r['pct_incumbent_closed']):.1f}"])
    for r in _csv('R3_cinco_primeiros_janela.csv'):
        rows.append(['First 5 recorded cases of new centers vs later cases: OR (95% CI)',
                     f"{LAB.get(r['definicao'], r['definicao'])}; {r['centros']} centers, {r['AIH']} admissions", _ci(r)])
    for r in _csv('R4_aprendizado_sem_atividade_previa_RBT.csv'):
        if r['amostra'] not in LAB:
            continue
        what = ('First 5 recorded cases of new centers vs later cases: OR (95% CI)' if r['termo'].startswith('5 primeiros')
                else 'Case number of new centers, per doubling: OR (95% CI)')
        rows.append([what, f"{LAB[r['amostra']]}; {r['centros']} centers, {r['AIH']} admissions", _ci(r)])
    for r in _csv('R1_dentro_random_slope.csv'):
        rows.append(['Within-center term, +10 transplants/year above the center mean: OR (95% CI)', LAB.get(r['modelo'], r['modelo']),
                     _ci(r) if r['OR'] not in ('', 'NA') else 'did not converge'])
    return rows

def build_sources():
    rows = [['Year', 'Transplants, SIH | RBT', 'Centers billing ≥1 transplant (SIH)', 'Active teams (RBT)',
             'Establishments with heart transplant habilitation, December (CNES)', 'Of which in the North (CNES)']]
    for r in _csv('N7_centros_por_fonte.csv'):
        rows.append([r['ano'], f"{r['SIH_transplantes']} | {r['RBT_transplantes']}", r['SIH_centros_ativos'],
                     (str(int(float(r['RBT_equipes_atuantes']))) if r['RBT_equipes_atuantes'] not in ('', 'nan') else '—'),
                     r['CNES_habilitados_dez'], r['CNES_habilitados_Norte_dez']])
    return rows

def build_missing():   # only the variables with missing values
    rr = translate_sheet('TS16')
    return [rr[0]] + [r for r in rr[1:] if r[1] not in ('0', '0.0')]

BUILD = {'concentration': build_concentration, 'posthoc': build_posthoc, 'sources': build_sources, 'missing': build_missing}

def rows_of(item):
    if 'build' in item:
        return BUILD[item['build']]()
    return item['rows'] if 'rows' in item else translate_sheet(item['sheet'])

# ---------------------------------------------------------------- main tables -> markdown
def md_table(rows):
    esc = lambda c: c.replace('|', '\\|')
    return '\n'.join(['| ' + ' | '.join(esc(c) for c in rows[0]) + ' |', '|' + '|'.join(['---'] * len(rows[0])) + '|']
                     + ['| ' + ' | '.join(esc(c) for c in r) + ' |' for r in rows[1:]])

md = []
for sheet, num, title, note in MAIN:
    rows = translate_sheet(sheet)
    if str(num) == '3':   # key periods only (all periods in Figure 2)
        rows = [rows[0]] + [r for r in rows[1:] if r[1].replace('-', '–') in ('2000–2003', '2008–2011', '2023–2025', '2000–2025')]
    ab = abbr_for(title, note, ' '.join(' '.join(r) for r in rows), header=' '.join(rows[0]))
    md.append(f'**Table {num}.** {title}\n\n{md_table(rows)}\n\n*{note} {ab}*\n')
open(f'{OUT}/tables_main_EN.md', 'w', encoding='utf-8').write(us('\n'.join(md)))

# ---------------------------------------------------------------- supplementary tables -> html
parts = []
for item in SUPP:
    rows = rows_of(item)
    head = ''.join(f'<th>{_h.escape(c)}</th>' for c in rows[0])
    body = ''.join('<tr>' + ''.join(f'<td>{_h.escape(c)}</td>' for c in r) + '</tr>' for r in rows[1:])
    ab = abbr_for(item['title'], item['note'], ' '.join(' '.join(r) for r in rows), header=' '.join(rows[0]))
    note = item['note'] + (' ' + ab if item.get('abbr', True) and ab else '')
    parts.append(f'<section class="stab"><h3>Table {item["num"]}. {_h.escape(item["title"])}</h3>'
                 f'<table><thead><tr>{head}</tr></thead><tbody>{body}</tbody></table><p class="note">{_h.escape(note)}</p></section>')
open(f'{OUT}/Supplementary_Tables_EN.html', 'w', encoding='utf-8').write(us('\n'.join(parts)))

# ---------------------------------------------------------------- check: no Portuguese left in the cells
left = [(it['num'], c) for it in SUPP for r in rows_of(it) for c in r if PT_WORDS.search(c) and 'Model failed' not in c]
left += [(num, c) for sheet, num, _, _ in MAIN for r in translate_sheet(sheet) for c in r if PT_WORDS.search(c)]
print('Cells with Portuguese words:', len(left))
for x in left[:50]:
    print(x)
