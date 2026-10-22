# Conferência independente do bloco 2 (taxas e proximidade recalculadas por outro caminho, em Python).
# Uso: python3 -I scripts/bloco2_conferencia.py data_2000_w04 outputs_2000_2025/bloco2
import os, sys, numpy as np, pandas as pd
from scipy.stats import chi2
from pyproj import Geod
base, out = sys.argv[1], sys.argv[2]
INI = int(os.environ.get('TXC_INI', '2000'))
PER = [f'{a}-{a+3}' for a in range(INI, 2008, 4)] + ['2008-2011', '2012-2015', '2016-2019', '2020-2022', '2023-2025']
d = pd.read_csv(f'{base}/microdados/aih_txc_{INI}_2025.csv', dtype={'munic_res': str, 'munic_hosp': str})
p = pd.read_csv(f'{base}/ibge_covariaveis/pop_uf_ano_sexo_idade.csv'); p = p[p.tipo_faixa == 'analise']
cut = lambda a: pd.cut(a, [a0 - 1 for a0 in range(INI, 2008, 4)] + [2007, 2011, 2015, 2019, 2022, 2025], labels=PER).astype(str)
d_all = d.copy(); d = d[d.uf_res.notna()]   # bloco 2 é por residência (exclui as 15 AIH sem município de residência)
d['per'] = cut(d.ano_inter); p['per'] = cut(p.ano)
w = p[p.ano == 2025].groupby(['faixa_etaria', 'sexo']).populacao.sum(); w = w / w.sum()
def ff(x, n, w):  # Fay & Feuer 1997
    r = (w * x / n).sum(); v = (w**2 * x / n**2).sum(); wm = (w / n).max()
    lo = 0 if x.sum() == 0 else v / (2 * r) * chi2.ppf(.025, 2 * r * r / v)
    hi = (v + wm**2) / (2 * (r + wm)) * chi2.ppf(.975, 2 * (r + wm)**2 / (v + wm**2))
    return r * 1e6, lo * 1e6, hi * 1e6
rows = []
for reg in ['Brasil', 'Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']:
    for per in PER:
        dd = d[(d.per == per) & ((d.regiao_res == reg) | (reg == 'Brasil'))]
        pp = p[(p.per == per) & ((p.regiao == reg) | (reg == 'Brasil'))]
        x = dd.groupby(['faixa_etaria', 'sexo']).size().reindex(w.index, fill_value=0)
        n = pp.groupby(['faixa_etaria', 'sexo']).populacao.sum().reindex(w.index)
        r, lo, hi = ff(x.values, n.values, w.values)
        rows.append(dict(local=reg, periodo=per, n_py=len(dd), dsr_py=r, lo_py=lo, hi_py=hi))
py = pd.DataFrame(rows)
rr = pd.read_csv(f'{out}/conf_taxa_regiao.csv')
m = py.merge(rr, on=['local', 'periodo'])
print('Taxa padronizada região × período: células', len(m), '| contagens iguais:', (m.n_py == m.n).all(),
      '| máx |dif| DSR:', float((m.dsr_py - m.dsr).abs().max()), '| máx |dif| IC:', float(max((m.lo_py - m.dsr_lo).abs().max(), (m.hi_py - m.dsr_hi).abs().max())))
# proximidade por pyproj (outra implementação geodésica)
g = Geod(ellps='WGS84')
co = pd.read_csv(f'{base}/ibge_covariaveis/municipios_coord.csv', dtype={'codigo': str, 'codigo7': str})
cz = pd.read_excel(f'{base}/ibge_covariaveis/CD2022_Populacao_Coletada_Imputada_e_Total_Municipio_e_UF.xlsx', header=None, skiprows=3)
cz = cz[[2, 3, 7]].dropna(); cz.columns = ['ufc', 'mun', 'pop']
cz['codigo7'] = cz.ufc.astype(int).astype(str).str.zfill(2) + cz.mun.astype(int).astype(str).str.zfill(5)
mu = cz.merge(co, on='codigo7')
d_all['h'] = np.where(d_all.munic_hosp.str[:2] == '53', '530010', d_all.munic_hosp)
cy = d_all.groupby(['centro', 'ano_inter', 'h']).size().reset_index(name='n').merge(co[['codigo', 'lat', 'lon']], left_on='h', right_on='codigo')
pr = pd.read_csv(f'{out}/conf_proximidade_ano.csv'); pr = pr[pr.local == 'Brasil']
res = []
for a in [INI, 2008, 2016, 2025] if INI < 2008 else [2008, 2016, 2025]:
    for lim in [1, 5]:
        c = cy[(cy.ano_inter == a) & (cy.n >= lim)].drop_duplicates('h')
        D = np.full((len(mu), len(c)), np.nan)
        for j, (la, lo) in enumerate(zip(c.lat, c.lon)):
            D[:, j] = g.inv(mu.lon.values, mu.lat.values, np.full(len(mu), lo), np.full(len(mu), la))[2] / 1000
        dm = D.min(1)
        for k in [300, 500, 1000]:
            v = 100 * mu['pop'][dm <= k].sum() / mu['pop'].sum()
            res.append(dict(ano=a, limiar=lim, raio=k, py=v, R=float(pr[(pr.ano == a) & (pr.limiar == lim)][f'le{k}'].iloc[0])))
res = pd.DataFrame(res); res['dif'] = res.py - res.R
print('Municípios pareados:', len(mu), '| pop:', int(mu["pop"].sum()))
print(res.round(3).to_string(index=False))
print('Crianças (n por período):', d[d.idade < 18].groupby('per').size().to_dict())
print('Fora da UF total:', int(d.fora_uf.sum()), '| mediana distância Brasil:', d.dist_km_centro_operou.median())
