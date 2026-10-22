# Conferência independente dos blocos 3 e 4 (modelos refeitos em Python/statsmodels).
# Uso: python3 -I scripts/bloco3e4_conferencia.py data_2000_w04 outputs_2000_2025
import os, sys, numpy as np, pandas as pd
import statsmodels.api as sm
base, out = sys.argv[1], sys.argv[2]
INI = int(os.environ.get('TXC_INI', '2000'))
d = pd.read_csv(f'{base}/microdados/aih_txc_{INI}_2025.csv').sort_values(['centro', 'ano_inter', 'mes_inter', 'id_aih']).reset_index(drop=True)

def rcs_nl(x, k):  # Harrell, 3 nós, normalização por (k3 - k1)^2 (padrão do Hmisc)
    p = lambda z: np.clip(z, 0, None) ** 3
    return (p(x - k[0]) - p(x - k[1]) * (k[2] - k[0]) / (k[2] - k[1]) + p(x - k[2]) * (k[1] - k[0]) / (k[2] - k[1])) / (k[2] - k[0]) ** 2

# ---------------- bloco 3
d['Vm1'] = d.volume_centro_ano - 1
d['entre'] = d.groupby('centro').Vm1.transform('mean'); d['dentro10'] = (d.Vm1 - d.entre) / 10
kE = np.percentile(d.entre, [10, 50, 90])
d['e1'] = d.entre; d['e2'] = rcs_nl(d.entre.values, kE)
r = pd.read_csv(f'{out}/_local/conf_base_modelo.csv').sort_values('id_aih').set_index('id_aih')
x = d.set_index('id_aih').loc[r.index]
print('Bloco 3 — nós de entre (Python):', kE.round(4))
print('  |dif| máx entre/dentro/e2 vs R:', float(abs(x.entre - r.entre).max()), float(abs(x.dentro10 * 10 - r.dentro).max()), float(abs(x.e2 - r.e2).max()))
kA = np.array([d.ano_inter.min(), np.median(d.ano_inter), d.ano_inter.max()])
d['y1'] = d.ano_inter; d['y2'] = rcs_nl(d.ano_inter.values.astype(float), kA)  # mesmo espaço que ns(ano, 2)
fx = d.idade.lt(18).map({True: '<18', False: None}).fillna(d.faixa_etaria)
X = pd.get_dummies(fx, prefix='faixa5').drop(columns='faixa5_18-39').astype(float)
X['sexoFF'] = (d.sexo == 'F').astype(float)
X = pd.concat([d[['e1', 'e2', 'dentro10']], X, d[['y1', 'y2']]], axis=1); X = sm.add_constant(X)
g = sm.GEE(d.morte, X, groups=d.centro, family=sm.families.Binomial(), cov_struct=sm.cov_struct.Exchangeable()).fit()
gr = pd.read_csv(f'{out}/bloco3/conf_gee_R.csv').set_index('termo').gee_R
comp = pd.DataFrame({'Python': g.params.rename({'faixa5_<18': 'faixa5<18', 'faixa5_40-49': 'faixa540-49', 'faixa5_50-59': 'faixa550-59', 'faixa5_60+': 'faixa560+'})})
comp['R'] = gr.reindex(comp.index)
print('  GEE exchangeable, R (geepack) × Python (statsmodels):'); print(comp.dropna().round(5).to_string())
print('  Mortalidade bruta por V:', d.groupby(pd.cut(d.volume_centro_ano, [0, 9, 19, 39, 999])).morte.agg(['size', 'sum']).values.tolist())
# ---------------- bloco 4
e = d[d.tipo_centro == 'entrante'].copy(); e['seq'] = e.groupby('centro').cumcount() + 1
rs = pd.read_csv(f'{out}/_local/conf_seq.csv').set_index('id_aih')
print('Bloco 4 — nº sequencial idêntico ao do R:', bool((e.set_index('id_aih').seq == rs.seq.reindex(e.id_aih).values).all()))
bl = pd.cut(e.seq, [0, 5, 10, 15, 20, 1e9], labels=['1-5', '6-10', '11-15', '16-20', '>20'])
print(f'  Blocos (AIH, óbitos), {e.centro.nunique()} centros:', e.groupby(bl, observed=True).morte.agg(['size', 'sum']).values.tolist())
DOM = e.centro.value_counts().index[0]; s5 = e.centro != DOM
print(f'  Sem {DOM}:', int(s5.sum()), 'AIH,', int(e.morte[s5].sum()), 'óbitos; blocos:', e[s5].groupby(bl[s5], observed=True).morte.agg(['size', 'sum']).values.tolist())
print('  Casos 1–5:', int((e.seq <= 5).sum()), 'AIH,', int(e.morte[e.seq <= 5].sum()), 'óbitos')
