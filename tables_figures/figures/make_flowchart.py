"""Figure 1: selection of heart transplant admissions (RECORD item 13.1), in the style of make_figures.py.

Reads only aggregate counts (bloco1/fluxograma_etapas.csv and fluxograma_contagens.csv, from figura_fluxograma.R).
Writes TIFF (600 dpi, LZW), PDF (vector) and PNG (300 dpi).
Usage: python3 -I make_flowchart.py <outputs_2000_2025_dir> <out_dir>
"""
import csv, sys
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 8, 'text.color': '#1f1f1f', 'pdf.fonttype': 42, 'savefig.dpi': 600})
MUTED = '#6b6b6b'

et = {r['etapa']: int(r['n']) for r in csv.DictReader(open(SRC / 'bloco1/fluxograma_etapas.csv', encoding='utf-8'))}
ct = list(csv.DictReader(open(SRC / 'bloco1/fluxograma_contagens.csv', encoding='utf-8')))
FILES_READ = et['Arquivos RD lidos']; RECORDS = et['Registros nos arquivos lidos']
TXC = et['Registros com TxC realizado ou solicitado']; EXCL_REQ = et['Excluídos: só solicitado']
PERF = et['TxC realizado']; OUT_WIN = next(v for k, v in et.items() if k.startswith('Excluídos: internação fora'))
COHORT = et['Base de análise']
FILES_TOTAL = 8586          # 27 states x 318 months (Jan 2000-Jun 2026); figura_fluxograma.R (ARQ_TOT)
BEFORE_2000 = 12            # admissions before 2000 among those outside the window; figura_fluxograma.R
assert TXC - EXCL_REQ == PERF and PERF - OUT_WIN == COHORT
one_per_pt = int(next(r['AIH'] for r in ct if r['etapa'].startswith('Sensibilidade: uma linha')))
n_rep_pts = COHORT - one_per_pt  # probable patients with 2 admissions


def fmt(n):  # journal style: no separator up to 4 digits, comma from 5 digits
    return f'{n:,}' if n >= 10000 else str(n)


fig = plt.figure(figsize=(7.0, 5.6))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 10); ax.set_ylim(0.6, 8.6); ax.axis('off')


def box(x, y, w, h, txt, fill='white', fs=7.8, weight='normal'):
    ax.add_patch(Rectangle((x - w / 2, y - h / 2), w, h, facecolor=fill, edgecolor='#4d4d4d', lw=0.6))
    ax.text(x, y, txt, ha='center', va='center', fontsize=fs, linespacing=1.4, fontweight=weight)


def arrow(x0, y0, x1, y1, head=True):
    ax.annotate('', xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle='-|>' if head else '-', color='#333333', lw=0.7, mutation_scale=7, shrinkA=0, shrinkB=0))


CX, W = 3.45, 6.3
box(CX, 8.05, W, 0.85, f'SIH/SUS hospital admission files (reduced AIH), 27 states, Jan 2000–Jun 2026:\n'
    f'{FILES_READ} of {FILES_TOTAL} monthly files read ({fmt(RECORDS)} records)')
arrow(CX, 7.625, CX, 6.85)
box(CX, 6.4, W, 0.9, 'Records with heart transplantation\n(code 46800018/47800011 until 2007; 0505020041 from 2008)\n'
    f'as procedure performed or requested: n = {TXC}')
arrow(CX, 5.95, CX, 4.75); arrow(CX, 5.4, 6.9, 5.4, head=False)
box(8.35, 5.4, 2.9, 0.85, f'Excluded: {EXCL_REQ}\ntransplantation recorded only as\nrequested (not performed)', fill='#f2f2f2')
box(CX, 4.4, W, 0.6, f'Transplantation as procedure performed: n = {PERF}')
arrow(CX, 4.1, CX, 3.1); arrow(CX, 3.65, 6.9, 3.65, head=False)
box(8.35, 3.65, 2.9, 0.85, f'Excluded: {OUT_WIN}\nadmission date outside\nJan 1, 2000–Dec 31, 2025', fill='#f2f2f2')
box(CX, 2.45, W, 1.3, f'Analysis cohort: {COHORT} heart transplant admissions\n'
    f'64 centers · 819 in-hospital deaths\n'
    f'No duplicate or continuation records · {n_rep_pts} probable patients with 2 admissions\n'
    'Main analyses use the full cohort (subsets: Supplementary Tables S2 and S4)', fill='#e8f0fb', weight='normal')
ax.text(0.3, 1.45, 'Source: public healthbr-data mirror of the DATASUS files (Parquet converted 1:1 from .dbc; SHA-256 checked per file). '
        'Missing from the mirror:\nRoraima Jan–May 2000 and Amapá Oct 2007 (states without a transplant center). '
        f'Outside the window: {BEFORE_2000} admitted before 2000 and\n{OUT_WIN - BEFORE_2000} after 2025. '
        'AIH, hospital admission authorization; SIH/SUS, Hospital Information System of the Unified Health System.',
        ha='left', va='top', fontsize=6.5, color=MUTED, linespacing=1.35)
for ext, kw in [('tiff', {'dpi': 600, 'pil_kwargs': {'compression': 'tiff_lzw'}}), ('pdf', {}), ('png', {'dpi': 300})]:
    fig.savefig(OUT / f'Figure1.{ext}', bbox_inches='tight', facecolor='white', **kw)
print('ok Figure1')
