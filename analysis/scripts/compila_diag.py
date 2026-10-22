# Junta o diagnóstico do passo 2 da escada de convergência gravado pelos blocos 3–6 (DIAG_FILE; ver comum.R).
# Uso: python3 -I scripts/compila_diag.py <pasta com diag_b3.csv … diag_b6.csv> outputs_2000_2025/bloco7/R12_diagnostico_convergencia.csv
import sys, os, pandas as pd
pasta, saida = sys.argv[1], sys.argv[2]
BLOCO = {'b3': '3 (H1)', 'b4': '4 (aprendizado)', 'b5': '5 (síntese)', 'b6': '6 (suplemento)'}
partes = []
for k, rot in BLOCO.items():
    f = f'{pasta}/diag_{k}.csv'
    if os.path.exists(f): partes.append(pd.read_csv(f).assign(bloco=rot))
D = pd.concat(partes, ignore_index=True)
D = D[['bloco', 'modelo', 'passo', 'ajuste', 'logLik', 'dif_logLik', 'grad_rel', 'dif_fixef_EP', 'mensagens']]
D.to_csv(saida, index=False, encoding='utf-8-sig')
# resumo por modelo: o bobyqa do passo 2 está no maior logLik? quantos otimizadores no mesmo ótimo? maior diferença entre eles?
o = D[D.ajuste.isin(['bobyqa', 'Nelder_Mead', 'nloptwrap', 'nlminbwrap'])]
mesmo = o[o.dif_logLik >= -1e-3]
R = D[D.ajuste == 'bobyqa (passo 2)'][['bloco', 'modelo', 'passo', 'dif_logLik', 'grad_rel', 'mensagens']].merge(
    mesmo.groupby('modelo').agg(otim_mesmo_otimo=('ajuste', 'size'), dif_max_EP=('dif_fixef_EP', 'max')).reset_index(), on='modelo')
print(f'{D.modelo.nunique()} modelos passaram pelo passo 2; {len(D)} ajustes registrados')
print(R.to_string(index=False))
