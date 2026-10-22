"""Habilitação SUS para transplante de coração no CNES.

Consulta pública agregada no TabNet/DATASUS (CNES, Habilitações; habilitação 24.11 TRANSPLANTE DE CORACAO):
número de estabelecimentos habilitados por UF em dezembro de cada ano. A série do TabNet começa em mar/2007;
não há dado de habilitação por estabelecimento anterior a isso (o portal do CNES mostra só o período vigente),
então a abertura dos programas em 2002–2006 não pode ser confirmada pelo CNES.
Saída agregada (sem estabelecimento). Uso: python3 -I scripts/cnes_habilitacao_tabnet.py outputs_2000_2025/sensibilidade
"""
import csv, html, io, re, subprocess, sys, urllib.parse
from pathlib import Path

out = Path(sys.argv[1]); out.mkdir(parents=True, exist_ok=True)
DEF = 'http://tabnet.datasus.gov.br/cgi/tabcgi.exe?cnes/cnv/habbr.def'
arqs = [f'hbbr{y % 100:02d}12.dbf' for y in range(2007, 2026)]
campos = [('Linha', 'Ano/mês_compet.'), ('Coluna', 'Unidade_da_Federação'), ('Incremento', 'Qtde_Estabelec._Habilitados')]
campos += [('Arquivos', a) for a in arqs] + [('SHabilitação', '203'), ('formato', 'prn'), ('mostre', 'Mostra')]  # 203 = .2411-TRANSPLANTE DE CORACAO
corpo = '&'.join(urllib.parse.quote(k.encode('latin1')) + '=' + urllib.parse.quote(v.encode('latin1')) for k, v in campos)
r = subprocess.run(['curl', '-sS', '--max-time', '120', '-X', 'POST', '--data', corpo, DEF], capture_output=True, check=True)
pre = re.search(r'<PRE>(.*?)</PRE>', r.stdout.decode('latin1'), re.S | re.I)
assert pre, 'TabNet não devolveu tabela'
linhas = [l for l in html.unescape(pre.group(1)).strip().splitlines() if l.strip() and not l.startswith('&')]
tab = list(csv.reader(io.StringIO('\n'.join(linhas)), delimiter=';'))
cab, dados = tab[0], tab[1:]
with open(out / 'N4_CNES_habilitacao_coracao_UF_dez.csv', 'w', newline='', encoding='utf-8') as f:
    w = csv.writer(f); w.writerow(['ano'] + cab[1:])
    for l in dados:
        w.writerow([l[0][:4]] + [0 if v.strip() in ('-', '') else int(v) for v in l[1:]])
print('\n'.join(';'.join(l) for l in tab))
