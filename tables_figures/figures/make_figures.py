"""Figures 2-4 in English, styled after the figures of major cardiology and general medical journals.

Reads only aggregate output tables (no microdata). Writes TIFF (600 dpi, LZW), PDF (vector) and PNG (300 dpi).
Usage: python3 -I make_figures.py <outputs_2000_2025_dir> <out_dir>
"""
import csv, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, LogNorm
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
from xlsx_raw import read_sheet

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

INK, MUTED, GRID, BAND = '#1f1f1f', '#6b6b6b', '#e4e4e4', '#f2f2f0'
plt.rcParams.update({
    'font.family': 'Liberation Sans', 'font.size': 7.5, 'axes.labelsize': 7.5, 'xtick.labelsize': 7,
    'ytick.labelsize': 7, 'legend.fontsize': 7, 'axes.linewidth': 0.6, 'xtick.major.width': 0.6,
    'ytick.major.width': 0, 'xtick.major.size': 2.5, 'ytick.major.size': 0, 'ytick.major.pad': 3,
    'axes.spines.top': False, 'axes.spines.right': False, 'axes.spines.left': False,
    'axes.edgecolor': '#444444', 'xtick.color': '#444444', 'ytick.color': '#444444',
    'axes.labelcolor': INK, 'text.color': INK, 'legend.frameon': False, 'pdf.fonttype': 42,
    'axes.grid': True, 'axes.grid.axis': 'y', 'grid.color': GRID, 'grid.linewidth': 0.5, 'axes.axisbelow': True,
    'savefig.dpi': 600,
})
# categorical slots (validated: light surface, CVD-safe adjacent pairs); markers and direct labels give second channels
REGIONS = [('Norte', 'North', '#2a78d6', 'o'), ('Nordeste', 'Northeast', '#eb6834', 's'),
           ('Sudeste', 'Southeast', '#1baf7a', '^'), ('Sul', 'South', '#eda100', 'D'),
           ('Centro-Oeste', 'Center-West', '#e87ba4', 'v')]
BLUE, ORANGE = '#2a78d6', '#eb6834'


def title(ax, letter, text, x=0.0):
    """Panel letter + short heading, left-aligned above the plot (Lancet/JACC style)."""
    ax.set_title(f'$\\bf{{{letter}}}$   {text}', loc='left', x=x, fontsize=8, pad=6, color=INK)


def end_label(ax, x, y, text, color, dy=0, **kw):
    ax.annotate(text, (x, y), xytext=(5, dy), textcoords='offset points', va='center', ha='left',
                fontsize=7, color=INK, **kw)
    ax.plot([], [], color=color)


def save(fig, name):
    for ext, kw in [('tiff', {'dpi': 600, 'pil_kwargs': {'compression': 'tiff_lzw'}}), ('pdf', {}), ('png', {'dpi': 300})]:
        fig.savefig(OUT / f'{name}.{ext}', bbox_inches='tight', facecolor='white', **kw)
    plt.close(fig)


# ---------------- Figure 2: network by year ----------------
rows = read_sheet(SRC / 'bloco1/Bloco1_tabelas.xlsx', 'Tabela2_rede')
h = rows[0]; d = [dict(zip(h, r)) for r in rows[1:] if r and isinstance(r[0], int)]
yr = [r['Ano'] for r in d]
fig, axs = plt.subplots(3, 1, figsize=(7.0, 6.9), sharex=True, gridspec_kw={'hspace': 0.42})


def series(ax, key, color, marker, label, fmt='{:.0f}', dy_end=0, dy_start=0):
    y = [r[key] for r in d]
    ax.plot(yr, y, color=color, lw=1.6, marker=marker, ms=3.2, mec='white', mew=0.5, zorder=3)
    ax.annotate(fmt.format(y[0]), (yr[0], y[0]), xytext=(-5, dy_start), textcoords='offset points', ha='right',
                va='center', fontsize=7, color=INK, fontweight='bold')
    ax.annotate(fmt.format(y[-1]), (yr[-1], y[-1]), xytext=(5, dy_end), textcoords='offset points', ha='left',
                va='center', fontsize=7, color=INK, fontweight='bold')
    if label:
        ax.annotate(label, (yr[-1], y[-1]), xytext=(22, dy_end), textcoords='offset points', ha='left',
                    va='center', fontsize=7, color=color if color == INK else INK)
    return y


ax = axs[0]
series(ax, 'Centros_ativos_ge1', BLUE, 'o', '≥1 transplant/year')
series(ax, 'Centros_ativos_ge10', ORANGE, 's', '≥10 transplants/year')
ax.set_ylim(0, 40); ax.set_yticks([0, 10, 20, 30, 40]); ax.set_ylabel('Active centers, n')
title(ax, 'A', 'Active centers')
ax = axs[1]
series(ax, 'HHI', INK, 'o', None)
ax.set_ylim(400, 1200); ax.set_yticks([400, 600, 800, 1000, 1200]); ax.set_ylabel('HHI (0–10,000)')
title(ax, 'B', 'Concentration of admissions (Herfindahl–Hirschman index; lower = less concentrated)')
ax = axs[2]
series(ax, 'Top3_pct', BLUE, 'o', '3 largest centers', fmt='{:.0f}%', dy_end=4)
series(ax, 'AIH_em_centros_lt10_pct', ORANGE, 's', 'Centers with <10/year', fmt='{:.0f}%', dy_end=-4)
ax.set_ylim(0, 80); ax.set_yticks([0, 20, 40, 60, 80]); ax.set_ylabel('Share of admissions, %')
title(ax, 'C', 'Share of transplants by type of center')
ax.set_xlabel('Year of admission'); ax.set_xticks(range(2000, 2026, 5)); ax.set_xlim(1998.6, 2026.0)
for a in axs:
    a.axvspan(2019.5, 2021.5, color=BAND, lw=0, zorder=0)
axs[0].text(2020.5, 39, 'COVID-19', ha='center', va='top', fontsize=6.3, color=MUTED)
save(fig, 'Figure2')

# ---------------- Figure 3: rates (small multiples) and distance (heat map) by region of residence ----------------
PER = ['2000-2003', '2004-2007', '2008-2011', '2012-2015', '2016-2019', '2020-2022', '2023-2025']
PLAB = ['2000–03', '', '2008–11', '', '2016–19', '', '2023–25']
PFULL = [p.replace('-', '–') for p in PER]
rows = read_sheet(SRC / 'bloco2/Bloco2_tabelas.xlsx', 'Taxa_regiao_periodo'); h = rows[0]
rate = {(r[1], r[2]): dict(zip(h, r)) for r in rows[1:] if r}
rows = read_sheet(SRC / 'bloco2/Bloco2_tabelas.xlsx', 'Distancia_periodo'); h = rows[0]
dist = {(r[1], r[0]): dict(zip(h, r)) for r in rows[1:] if r}
panels = [('Brasil', 'Brazil', INK, 'o')] + REGIONS
fig = plt.figure(figsize=(7.0, 7.4))
gs = fig.add_gridspec(3, 3, height_ratios=[1, 1, 1.15], hspace=0.42, wspace=0.12)
xs = list(range(len(PER)))
br = [rate[('Brasil', p)]['dsr'] for p in PER]
for k, (pt, en, col, mk) in enumerate(panels):
    ax = fig.add_subplot(gs[k // 3, k % 3])
    y = [rate[(pt, p)]['dsr'] for p in PER]
    lo = [rate[(pt, p)]['dsr_lo'] for p in PER]; hi = [rate[(pt, p)]['dsr_hi'] for p in PER]
    if pt != 'Brasil':
        ax.plot(xs, br, color='#b5b5b5', lw=1.0, ls=(0, (3, 2)), zorder=1)
    ax.fill_between(xs, lo, hi, color=col, alpha=0.14, lw=0, zorder=2)
    ax.plot(xs, y, color=col, lw=1.6, marker=mk, ms=3.6, mec='white', mew=0.5, zorder=3)
    ax.set_ylim(0, 2.6); ax.set_yticks([0, 0.5, 1.0, 1.5, 2.0, 2.5])
    ax.set_xlim(-0.5, 6.5); ax.set_xticks(xs); ax.set_xticklabels(PLAB if k >= 3 else [''] * 7, fontsize=6.6)
    if k == 4: ax.set_xlabel('Period of admission (2000–2025)')
    if k % 3: ax.set_yticklabels([])
    else: ax.set_ylabel('Per million per year')
    ax.set_title(en, loc='left', fontsize=7.8, fontweight='bold', color=INK, pad=3)
    ax.annotate(f'{y[-1]:.2f}', (6, y[-1]), xytext=(0, 7 if pt != 'Norte' else 8), textcoords='offset points',
                ha='center', fontsize=6.6, color=INK)
    if k == 0:
        ax.text(-0.32, 1.32, r'$\bf{A}$   Standardized transplant rate by region of residence (95% CI)',
                transform=ax.transAxes, fontsize=8) if False else ax.text(-0.32, 1.22, r'$\bf{A}$   Standardized transplant rate by region of residence (95% CI)', transform=ax.transAxes, fontsize=8)
    if k == 1:
        ax.plot([], [], color='#b5b5b5', lw=1.0, ls=(0, (3, 2)), label='Brazil')
        ax.legend(loc='upper left', fontsize=6.5, handlelength=2.2, borderaxespad=0.2)
# B: heat map of median distance traveled
ax = fig.add_subplot(gs[2, :])
order = ['Brasil', 'Norte', 'Nordeste', 'Sudeste', 'Sul', 'Centro-Oeste']
names = ['Brazil', 'North', 'Northeast', 'Southeast', 'South', 'Center-West']
M = [[max(dist[(o, p)]['mediana'], 1) for p in PER] for o in order]
cmap = LinearSegmentedColormap.from_list('seqblue', ['#eef4fc', '#9dc1ee', '#2a78d6', '#163f73'])
im = ax.imshow(M, cmap=cmap, norm=LogNorm(1, 3000), aspect='auto')
for i in range(len(order)):
    for j in range(len(PER)):
        v = dist[(order[i], PER[j])]['mediana']
        ax.text(j, i, f'{v:,.0f}', ha='center', va='center', fontsize=6.8,
                color='white' if M[i][j] > 300 else INK, fontweight='bold' if order[i] == 'Norte' else 'normal')
ax.set_xticks(xs); ax.set_xticklabels(PFULL, fontsize=6.8)
ax.set_yticks(range(len(names))); ax.set_yticklabels(names)
ax.grid(False); ax.tick_params(length=0)
for s in ax.spines.values(): s.set_visible(False)
ax.set_xticks([x + 0.5 for x in xs[:-1]], minor=True); ax.set_yticks([y + 0.5 for y in range(5)], minor=True)
ax.grid(which='minor', color='white', lw=1.5); ax.tick_params(which='minor', length=0)
ax.set_title(r'$\bf{B}$   Median distance from home to transplant hospital, km', loc='left', x=-0.115, fontsize=8, pad=6)
cb = fig.colorbar(im, ax=ax, fraction=0.025, pad=0.015)
cb.set_ticks([1, 10, 100, 1000]); cb.set_ticklabels(['≤1', '10', '100', '1000']); cb.outline.set_visible(False)
cb.ax.tick_params(labelsize=6.3, length=0); cb.ax.minorticks_off()
save(fig, 'Figure3')

# ---------------- Figure 4: volume and in-hospital death ----------------
# A: between-center association as OR vs the median center (P50), with 95% CI, log scale; B: within-center estimates (forest)
REV = SRC / 'sensibilidade'
cur = [dict(r) for r in csv.DictReader(open(REV / 'curva_entre_OR_vs_P50.csv'))]
x = [float(r['entre']) for r in cur]; orr = [float(r['OR']) for r in cur]
lo = [float(r['lo']) for r in cur]; hi = [float(r['hi']) for r in cur]
fig = plt.figure(figsize=(7.2, 3.4))
gs = fig.add_gridspec(1, 4, width_ratios=[1.0, 0.78, 0.6, 0.42], wspace=0.0)
ax = fig.add_subplot(gs[0])
ax.axvspan(25.85, 41.66, color=BAND, lw=0, zorder=0)
ax.fill_between(x, lo, hi, color=ORANGE, alpha=0.16, lw=0)
ax.plot(x, orr, color=ORANGE, lw=1.8)
ax.axhline(1, color=MUTED, lw=0.7, ls=(0, (3, 2)))
ax.set_yscale('log'); ticks = [0.25, 0.5, 1, 2, 4]
ax.yaxis.set_major_locator(FixedLocator(ticks)); ax.yaxis.set_major_formatter(FixedFormatter(['0.25', '0.5', '1', '2', '4']))
ax.yaxis.set_minor_locator(NullLocator())
ax.set_ylim(0.2, 5); ax.set_xlim(0, 42); ax.set_xticks([0, 10, 20, 30, 40])
ax.set_xlabel("Center's mean annual volume\n(other transplants per year)")
ax.set_ylabel('Odds ratio vs median center (95% CI)')
ax.plot([4.9, 17.2], [1.20, 1.0], 'o', color=ORANGE, ms=3.5, mec='white', mew=0.5, zorder=4)
ax.annotate('10th percentile vs median\nOR 1.20 (0.78–1.84)', (4.9, 1.20), xytext=(1.0, 0.30), fontsize=6.5,
            arrowprops=dict(arrowstyle='-', color=MUTED, lw=0.5, shrinkB=3))
ax.text(1.0, 4.4, 'Global test P = 0.167', ha='left', va='top', fontsize=6.6, color=INK)
ax.text((25.85 + 41.66) / 2, 4.4, 'Curve rests\non one center', ha='center', va='top', fontsize=6.2, color=MUTED)
title(ax, 'A', 'Between centers')
rs = [dict(r) for r in csv.DictReader(open(REV / 'R1_dentro_random_slope.csv'))]
rsr = next((r for r in rs if r['modelo'].startswith('Random slope de ano') and r['OR'] not in ('', 'NA')), None)
ph = [dict(r) for r in csv.DictReader(open(SRC / 'posthoc/posthoc_dentro.csv', encoding='utf-8-sig'))]
g = lambda k: next(r for r in ph if r['analise'].startswith(k))
items = [('Main model', 0.81, 0.73, 0.91, False), ('GEE', 0.82, 0.72, 0.99, False), ('Center fixed effects', 0.81, 0.73, 0.91, False)]
if rsr: items.append(('Center-specific year trends', float(rsr['OR']), float(rsr['lo']), float(rsr['hi']), True))
for lab, k in [('2000–2007 only', '(c) Interação dentro × período: dentro em 2000–2007'),
               ('2008–2025 only', '(c) Interação dentro × período: dentro em 2008–2025')]:
    r = g(k); items.append((lab, float(r['OR']), float(r['lo']), float(r['hi']), True))
n = len(items); yy = list(range(n))[::-1]
axL, axF, axR = fig.add_subplot(gs[1]), fig.add_subplot(gs[2]), fig.add_subplot(gs[3])
for a in (axL, axF, axR):
    a.set_ylim(-0.6, n + 0.1); a.grid(False); a.set_yticks([])
    for y in yy[::2]:
        a.axhspan(y - 0.5, y + 0.5, color='#f4f4f2', lw=0, zorder=0)
for a in (axL, axR):
    a.set_xlim(0, 1); a.set_xticks([]); a.spines['bottom'].set_visible(False)
for y, (lab, o, l, h, post) in zip(yy, items):
    axL.text(0.12, y, lab + (' *' if post else ''), va='center', ha='left', fontsize=7)
    axF.plot([l, h], [y, y], color=INK, lw=1.1, solid_capstyle='butt', zorder=3)
    axF.plot(o, y, 's', color=BLUE if not post else 'white', mec=BLUE, mew=1.1, ms=5, zorder=4)
    axR.text(0.08, y, f'{o:.2f} ({l:.2f}–{h:.2f})', va='center', ha='left', fontsize=7)
axL.text(0.12, n - 0.25, 'Analysis', fontweight='bold', fontsize=7, va='center')
axR.text(0.08, n - 0.25, 'OR (95% CI)', fontweight='bold', fontsize=7, va='center')
axF.axvline(1, color=MUTED, lw=0.7, ls=(0, (3, 2)), zorder=1)
axF.set_xscale('log'); axF.set_xlim(0.5, 1.4)
axF.xaxis.set_major_locator(FixedLocator([0.5, 0.7, 1.0, 1.4])); axF.xaxis.set_major_formatter(FixedFormatter(['0.5', '0.7', '1', '1.4']))
axF.xaxis.set_minor_locator(NullLocator())
axF.set_xlabel('OR per 10 transplants/year\nabove the center mean')
axL.set_title(r'$\bf{B}$   Within centers', loc='left', x=0.08, fontsize=8, pad=6)
axL.text(0.12, -1.25, '* Post hoc (open squares).', fontsize=6.3, color=MUTED, va='top')
save(fig, 'Figure4')
print('ok', sorted(p.name for p in OUT.iterdir() if p.suffix == '.png'))
