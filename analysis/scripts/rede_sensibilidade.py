"""Sensibilidades post hoc da descrição da rede.

  N1  HHI, 3 maiores, 9 maiores, % em centros <10/ano e centros ativos por ano: todos × sem hospitais de SP
  N2  Decomposição do crescimento (média anual 2000–01 × 2024–25) por grupo de centro: todos × sem SP;
      centro novo = 1º TxC observado ≥2004 (principal, observação inicial 2000–2003) ou ≥2002 (sensibilidade, 2000–2001)
  N3  SIH 2017: centros ativos e fatia dos 9 maiores (comparação com a referência do RBT de 2017)
Saídas agregadas, sem identificação de centro. Uso: python3 -I scripts/rede_sensibilidade.py data_2000 outputs_2000_2025/sensibilidade
"""
import sys
from pathlib import Path
import pandas as pd

base, out = Path(sys.argv[1]), Path(sys.argv[2])
out.mkdir(parents=True, exist_ok=True)
d = pd.read_csv(base / 'microdados/aih_txc_2000_2025.csv', usecols=['centro', 'uf_hosp', 'ano_inter', 'morte'])
assert len(d) == 5821 and d.morte.sum() == 819 and d.centro.nunique() == 64


def conc(g):
    s = g.groupby('centro').size()
    sh = s / s.sum() * 100
    return pd.Series({'admissions': int(s.sum()), 'active_centers': len(s), 'centers_ge10': int((s >= 10).sum()),
                      'HHI': round((sh ** 2).sum()), 'top3_pct': round(sh.nlargest(3).sum(), 1),
                      'top9_pct': round(sh.nlargest(9).sum(), 1), 'lt10_pct': round(s[s < 10].sum() / s.sum() * 100, 1)})


rows = []
for lab, x in [('All states', d), ('Without São Paulo', d[d.uf_hosp != 'SP'])]:
    t = x.groupby('ano_inter').apply(conc, include_groups=False)
    t.insert(0, 'sample', lab)
    rows.append(t.reset_index())
n1 = pd.concat(rows)
n1.to_csv(out / 'N1_concentracao_com_sem_SP.csv', index=False)

first = d.groupby('centro').ano_inter.min()


def decomp(x, corte):
    """Mean annual admissions 2000–01 vs 2024–25; share of the net change by center group (as in Supplementary Table S8)."""
    a = x[x.ano_inter.isin([2000, 2001])].groupby('centro').size() / 2
    b = x[x.ano_inter.isin([2024, 2025])].groupby('centro').size() / 2
    m = pd.DataFrame({'ini': a, 'fim': b}).fillna(0)
    m['first'] = first.reindex(m.index)
    grp = pd.Series('new', index=m.index)
    grp[(m['first'] < corte) & (m.fim > 0)] = 'incumbent_active'
    grp[(m['first'] < corte) & (m.fim == 0)] = 'incumbent_closed'
    delta = (m.fim - m.ini).groupby(grp).sum()
    net = m.fim.sum() - m.ini.sum()
    return {'mean_2000_01': m.ini.sum(), 'mean_2024_25': m.fim.sum(), 'net_change': net,
            'n_new_centers': int(((first >= corte) & first.index.isin(x.centro.unique())).sum()),
            **{f'pct_{k}': round(100 * delta.get(k, 0) / net, 1) for k in ['incumbent_active', 'new', 'incumbent_closed']}}


n2 = pd.DataFrame([{'sample': s, 'new_program_rule': r, **decomp(x, c)}
                   for s, x in [('All states', d), ('Without São Paulo', d[d.uf_hosp != 'SP'])]
                   for r, c in [('first observed ≥2002 (sensitivity)', 2002), ('first observed ≥2004 (main)', 2004)]])
n2.to_csv(out / 'N2_decomposicao_crescimento.csv', index=False)

# entries by year of first observed transplant (how many 'new' centers fall in 2002–2003)
entradas = first.value_counts().sort_index()
entradas.rename_axis('year_first_observed').rename('centers').to_csv(out / 'N2b_entradas_por_ano.csv')

n3 = n1[(n1.ano_inter.isin([2017, 2025])) & (n1['sample'] == 'All states')][['ano_inter', 'active_centers', 'top3_pct', 'top9_pct']]
n3.to_csv(out / 'N3_SIH_2017_2025.csv', index=False)
pd.set_option('display.width', 200)
print(n1[n1.ano_inter.isin([2000, 2008, 2017, 2020, 2023, 2024, 2025])].to_string(index=False))
print(n2.to_string(index=False)); print(entradas.to_string()); print(n3.to_string(index=False))
