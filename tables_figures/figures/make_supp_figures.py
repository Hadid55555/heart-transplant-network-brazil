"""Supplementary Figures S1-S3 in English, in the same style as make_figures.py (Figure 1, the selection flowchart, is in make_flowchart.py).

Reads only aggregate output tables already written by the R pipeline (no microdata, no model refits).
Writes TIFF (600 dpi, LZW), PDF (vector) and PNG (300 dpi).
Usage: python3 -I make_supp_figures.py <outputs_2000_2025_dir> <out_dir>

Sources
  S1  bloco3/Bloco3_tabelas.xlsx: LOCO (64 refits x 3 contrasts), ML_contrastes (all-center reference)
  S2  bloco4/Bloco4_tabelas.xlsx: Figura5_dados (adjusted estimates, 95% CI, deaths/admissions)
  S3  bloco2/conf_proximidade_ano.csv (= sheet Proximidade_ano); bloco7/Bloco7_posthoc.xlsx: R5_por_ano
"""
import os, sys, csv
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import random
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
from xlsx_raw import read_sheet

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    'font.family': 'Liberation Sans', 'font.size': 8, 'axes.labelsize': 8, 'xtick.labelsize': 7.5,
    'ytick.labelsize': 7.5, 'legend.fontsize': 7.5, 'axes.linewidth': 0.6, 'xtick.major.width': 0.6,
    'ytick.major.width': 0.6, 'xtick.major.size': 3, 'ytick.major.size': 3, 'axes.spines.top': False,
    'axes.spines.right': False, 'axes.edgecolor': '#333333', 'xtick.color': '#333333', 'ytick.color': '#333333',
    'axes.labelcolor': '#1f1f1f', 'text.color': '#1f1f1f', 'legend.frameon': False, 'pdf.fonttype': 42,
    'savefig.dpi': 600,
})
INK, MUTED = '#1f1f1f', '#6b6b6b'
REGIONS = [('Norte', 'North', '#2a78d6', 'o'), ('Nordeste', 'Northeast', '#eb6834', 's'),
           ('Sudeste', 'Southeast', '#1baf7a', '^'), ('Sul', 'South', '#eda100', 'D'),
           ('Centro-Oeste', 'Center-West', '#e87ba4', 'v')]
BLUE, ORANGE, GREEN = '#2a78d6', '#eb6834', '#1baf7a'


def panel(ax, letter, x=-0.09, y=1.04):
    ax.text(x, y, letter, transform=ax.transAxes, fontsize=10, fontweight='bold', va='bottom', ha='left')


def save(fig, name):
    for ext, kw in [('tiff', {'dpi': 600, 'pil_kwargs': {'compression': 'tiff_lzw'}}), ('pdf', {}), ('png', {'dpi': 300})]:
        fig.savefig(OUT / f'{name}.{ext}', bbox_inches='tight', facecolor='white', **kw)
    plt.close(fig)


def sheet(path, name):
    rows = read_sheet(path, name); h = rows[0]
    return [dict(zip(h, r)) for r in rows[1:] if r]


def fmt(n):  # journal style: no separator up to 4 digits, comma from 5 digits
    return f'{n:,}' if n >= 10000 else str(n)



# ---------------- Figure S1: leave-one-center-out ----------------
B3 = SRC / 'bloco3/Bloco3_tabelas.xlsx'
loco = sheet(B3, 'LOCO'); ref = sheet(B3, 'ML_contrastes')
assert len(loco) == 192 and len({r['centro_excluido'] for r in loco}) == 64
keys = [('P90', 'Between centers: mean V − 1 at\nP90 (41.7) vs P50 (17.2)'),
        ('P10', 'Between centers: mean V − 1 at\nP10 (4.9) vs P50 (17.2)'),
        ('Dentro', 'Within center: +10 transplants/year\nabove the center mean')]
pick = lambda c, k: ('P90' in c) if k == 'P90' else ('P10' in c) if k == 'P10' else c.startswith('Dentro')
rng = random.Random(20251)
fig, ax = plt.subplots(figsize=(7.0, 2.7))
for i, (k, lab) in enumerate(keys):
    y = len(keys) - 1 - i
    vals = [r['OR'] for r in loco if pick(r['contraste'], k)]
    assert len(vals) == 64
    ax.scatter(vals, [y + rng.uniform(-0.13, 0.13) for _ in vals], s=11, color=BLUE, alpha=0.6, lw=0, zorder=2)
    full = next(r['OR'] for r in ref if pick(r['contraste'], k))
    ax.plot([full, full], [y - 0.28, y + 0.28], color=INK, lw=1.8, zorder=3)
    ax.text(3.3, y, f'{full:.2f}', va='center', ha='left', fontsize=7)
ax.text(3.3, len(keys) - 0.45, 'OR, all\ncenters', va='bottom', ha='left', fontsize=6.5, color=MUTED)
ax.axvline(1, color=MUTED, lw=0.8, ls='--', zorder=1)
ax.set_xscale('log'); ax.set_xlim(0.08, 3)
tk = [0.1, 0.2, 0.5, 1, 2]
ax.xaxis.set_major_locator(FixedLocator(tk)); ax.xaxis.set_major_formatter(FixedFormatter(['0.1', '0.2', '0.5', '1', '2']))
ax.xaxis.set_minor_locator(NullLocator())
ax.set_yticks(range(len(keys))); ax.set_yticklabels([lab for _, lab in keys][::-1]); ax.set_ylim(-0.6, len(keys) - 0.4)
ax.tick_params(axis='y', length=0); ax.spines['left'].set_visible(False)
ax.set_xlabel('OR of in-hospital death with one center left out at a time (log scale)')
h = [Line2D([], [], marker='o', ls='', color=BLUE, alpha=0.6, ms=4, label='Model refitted without one center (64 refits)'),
     Line2D([], [], marker='|', ls='', color=INK, ms=9, mew=1.8, label='Model with all centers')]
ax.legend(handles=h, loc='lower center', bbox_to_anchor=(0.45, 1.0), ncol=2)
save(fig, 'FigureS1')

# ---------------- Figure S2: exploratory learning analysis ----------------
f5 = sheet(SRC / 'bloco4/Bloco4_tabelas.xlsx', 'Figura5_dados')
samples = list(dict.fromkeys(r['amostra'] for r in f5))
import re as _re
def _tit(sm, todos):
    m = _re.search(r'\((\d+) AIH, (\d+) óbitos', sm); a, o = m.group(1), m.group(2)
    if todos:
        return f"All {_re.search(r'Todos os (\d+) centros', sm).group(1)} new centers ({a} admissions, {o} deaths)"
    return f"Excluding the largest new center ({a} admissions, {o} deaths)"
assert samples[0].startswith('Todos os') and samples[1].startswith('Sem o')
titles = [_tit(samples[0], True), _tit(samples[1], False)]
POS = {('Blocos', '1-5'): -0.14, ('Indicador', '1-5'): 0.14, ('Blocos', '6-10'): 1, ('Blocos', '11-15'): 2,
       ('Blocos', '16-20'): 3, ('Blocos', '>20'): 4, ('Indicador', '>5'): 5.2}
fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.3), sharey=True, gridspec_kw={'wspace': 0.16})
for ax, smp, ttl, L in zip(axs, samples, titles, 'AB'):
    for r in (r for r in f5 if r['amostra'] == smp):
        kind = 'Blocos' if r['tipo'].startswith('Blocos') else 'Indicador'
        x = POS[(kind, r['ponto'])]; col, mk = (BLUE, 'o') if kind == 'Blocos' else (ORANGE, 's')
        ax.plot([x, x], [r['lo'], r['hi']], color=col, lw=1.1)
        ax.plot(x, r['est'], marker=mk, color=col, ms=4.5, ls='')
        ha, dx = ('right', 0.06) if (kind, r['ponto']) == ('Blocos', '1-5') else ('left', -0.06) if r['ponto'] == '1-5' else ('center', 0)
        ax.text(x + dx, r['hi'] + 0.6, f"{r['ob']}/{r['n']}", ha=ha, va='bottom', fontsize=6.3, color=col)
    ax.axvline(4.6, color='#d9d9d9', lw=0.6)
    ax.set_xticks([0, 1, 2, 3, 4, 5.2]); ax.set_xticklabels(['1–5', '6–10', '11–15', '16–20', '>20', '>5'])
    ax.set_xlim(-0.95, 5.7); ax.set_ylim(0, 39)
    ax.set_title(ttl.replace(" (", "\n("), fontsize=7.8, pad=6)
    ax.set_xlabel('Sequential case number in the center')
    panel(ax, L, x=-0.09 if L == 'A' else -0.08)
axs[1].tick_params(axis='y', length=0); axs[1].spines['left'].set_visible(False)
axs[0].set_ylabel('Adjusted in-hospital death, % (95% CI)')
h = [Line2D([], [], marker='o', color=BLUE, ms=4.5, lw=1.1, label='Blocks of 5 cases'),
     Line2D([], [], marker='s', color=ORANGE, ms=4.5, lw=1.1, label='Primary indicator (first 5 vs later cases)')]
fig.legend(handles=h, loc='lower center', bbox_to_anchor=(0.5, -0.07), ncol=2)
fig.text(0.5, -0.115, 'Exploratory. Adjusted for age group, sex and year (spline), with a random center intercept. '
         'Labels, deaths/admissions.', ha='center', va='top', fontsize=6.5, color=MUTED)
save(fig, 'FigureS2')

# ---------------- Figure S3: proximity by region (A) and admissions by center group (B) ----------------
prox = list(csv.DictReader(open(SRC / 'bloco2/conf_proximidade_ano.csv', encoding='utf-8')))
assert len(prox) == 26 * 2 * 6
series = [('Brasil', 'Brazil', INK, 'o')] + REGIONS
fig = plt.figure(figsize=(7.0, 8.0))
gs = fig.add_gridspec(2, 1, height_ratios=[2.05, 1], hspace=0.42)
gA = gs[0].subgridspec(2, 3, wspace=0.12, hspace=0.32)
RAD = [('le300', '≤300 km'), ('le500', '≤500 km'), ('le1000', '≤1000 km')]
THR = [('1', 'Center with ≥1 transplant/year'), ('5', 'Center with ≥5 transplants/year')]
axA = None
for i, (thr, tlab) in enumerate(THR):
    for j, (col_, rlab) in enumerate(RAD):
        ax = fig.add_subplot(gA[i, j])
        for pt, en, col, mk in series:
            rr = sorted((r for r in prox if r['local'] == pt and r['limiar'] == thr), key=lambda r: int(r['ano']))
            ax.plot([int(r['ano']) for r in rr], [float(r[col_]) for r in rr], color=col, marker=mk, ms=1.8,
                    lw=1.3 if pt == 'Brasil' else 0.9, label=en, zorder=3 if pt == 'Brasil' else 2)
        ax.set_ylim(-4, 104); ax.set_xlim(1999, 2026); ax.set_xticks([2000, 2010, 2020])
        ax.set_yticks([0, 25, 50, 75, 100])
        if j: ax.set_yticklabels([])
        if i == 0: ax.set_title(rlab, fontsize=7.8, pad=3)
        else: ax.set_xlabel('Year')
        if j == 2: ax.text(1.04, 0.5, tlab.replace('with ', 'with\n'), transform=ax.transAxes, rotation=270, va='center',
                           ha='left', fontsize=7, linespacing=1.2)
        if i == 0 and j == 0: axA = ax; panel(ax, 'A', x=-0.3, y=1.06)
fig.text(0.04, 0.705, 'Population (2022 Census) within the distance\nof an active center, %', rotation=90, ha='center',
         va='center', fontsize=8)
hA, lA = axA.get_legend_handles_labels()
fig.legend(hA, lA, loc='upper center', bbox_to_anchor=(0.5, 0.405), ncol=6, columnspacing=1.2, handletextpad=0.4, markerscale=1.8)
g = sheet(SRC / 'bloco7/Bloco7_posthoc.xlsx', 'R5_por_ano')
G = [('Centros 2000–03 ainda ativos em 2024–25', 'Incumbent centers (first observed 2000–03), still active in 2024–25', BLUE, 'o'),
     ('Centros 2000–03 sem atividade em 2024–25', 'Incumbent centers (first observed 2000–03), inactive in 2024–25', ORANGE, 's'),
     ('Centros com 1º TxC ≥2004', 'New centers (first observed from 2004)', GREEN, '^')]
ax = fig.add_subplot(gs[1])
for k, en, col, mk in G:
    ax.plot([r['ano'] for r in g], [r[k] for r in g], color=col, marker=mk, ms=3.5, lw=1.4, label=en)
ax.set_ylabel('Admissions per year, n'); ax.set_xlabel('Year of admission')
ax.set_xticks(range(2000, 2026, 5)); ax.set_xlim(1999.3, 2025.7); ax.set_ylim(0, 200)
ax.legend(loc='upper left', ncol=1, handlelength=2.2)
panel(ax, 'B', x=-0.075)
save(fig, 'FigureS3')

print('ok', sorted(p.name for p in OUT.iterdir() if p.name.startswith('FigureS')))
