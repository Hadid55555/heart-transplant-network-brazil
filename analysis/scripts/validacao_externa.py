"""Validação externa da descrição da rede (só agregados).

  N6  Concentração por hospital: SIH × RBT (contagens por equipe publicadas pelo RBT, somadas por hospital) em 2009, 2010 e 2017
  N7  Centros por ano segundo a fonte: SIH (≥1 TxC faturado), RBT (equipes atuantes) e CNES (estabelecimentos habilitados em dezembro)
Entradas: N1 (SIH, rede_sensibilidade.py), N5/N5b (RBT: rbt_equipes_2017.py e transcrição dos relatórios, em data_2000/rbt/agregados/)
e N4 (CNES, cnes_habilitacao_tabnet.py).
Uso: python3 -I scripts/validacao_externa.py outputs_2000_2025/sensibilidade
"""
import sys
from pathlib import Path
import pandas as pd

R = Path(sys.argv[1])
sih = pd.read_csv(R / 'N1_concentracao_com_sem_SP.csv').query("sample == 'All states'").set_index('ano_inter')
rbt = pd.read_csv(R / 'N5_RBT_equipes_agregado.csv')
rbt = rbt[rbt.observacao.str.contains('HOSPITAL') & ~rbt.observacao.str.contains('PARCIAL')].set_index('ano')
cols = {'active_centers': 'centros_ativos', 'HHI': 'hhi', 'top3_pct': 'top3_pct', 'top9_pct': 'top9_pct', 'lt10_pct': 'lt10_pct'}
linhas = []
for a in rbt.index:
    s = sih.loc[a]; r = rbt.loc[a]
    linhas.append({'ano': a, 'fonte': 'SIH', 'transplantes': int(s.admissions), **{v: s[k] for k, v in cols.items()}})
    linhas.append({'ano': a, 'fonte': 'RBT (por hospital)', 'transplantes': int(r.total_cardiaco), 'centros_ativos': int(r.equipes_ge1),
                   'hhi': r.hhi, 'top3_pct': r.top3_pct, 'top9_pct': r.top9_pct, 'lt10_pct': r.lt10_pct})
n6 = pd.DataFrame(linhas); n6.to_csv(R / 'N6_concentracao_SIH_vs_RBT.csv', index=False)

eq = pd.read_csv(R / 'N5b_RBT_coracao_total_equipes.csv').set_index('ano')
hab = pd.read_csv(R / 'N4_CNES_habilitacao_coracao_UF_dez.csv').set_index('ano')
anos = range(2007, 2026)
n7 = pd.DataFrame({'ano': list(anos),
                   'SIH_transplantes': [int(sih.loc[a].admissions) for a in anos],
                   'RBT_transplantes': [int(eq.loc[a].transplantes_cardiacos_RBT) for a in anos],
                   'SIH_centros_ativos': [int(sih.loc[a].active_centers) for a in anos],
                   'RBT_equipes_atuantes': [eq.loc[a].equipes_atuantes_RBT for a in anos],
                   'CNES_habilitados_dez': [int(hab.loc[a].Total) for a in anos],
                   'CNES_habilitados_Norte_dez': [int(hab.loc[a].get('PA', 0)) for a in anos]})
n7.to_csv(R / 'N7_centros_por_fonte.csv', index=False)
pd.set_option('display.width', 200)
print(n6.to_string(index=False)); print(n7.to_string(index=False))
