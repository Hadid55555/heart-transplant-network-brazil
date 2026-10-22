"""Central illustration (graphical abstract): network growth, regional access and the volume safety check.

Reads only aggregate output tables (no microdata). State tiles show crude rates by state of residence; no center is located.
Usage: python3 -I make_central.py <outputs_2000_2025_dir> <out_dir>
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from collections import Counter
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap, Normalize
from matplotlib.patches import FancyBboxPatch, Rectangle, Circle
from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
from xlsx_raw import read_sheet

SRC, OUT = Path(sys.argv[1]), Path(sys.argv[2])
INK, MUTED, NAVY, TINT, LINE = '#1f1f1f', '#5f6670', '#14365f', '#f3f6fa', '#d5dde8'
BLUE, ORANGE = '#2a78d6', '#eb6834'
plt.rcParams.update({'font.family': 'Liberation Sans', 'font.size': 7, 'text.color': INK, 'axes.edgecolor': '#555555',
                     'xtick.color': '#555555', 'ytick.color': '#555555', 'pdf.fonttype': 42})

W, H = 7.2, 4.5
fig = plt.figure(figsize=(W, H))
bg = fig.add_axes([0, 0, 1, 1]); bg.set_xlim(0, W); bg.set_ylim(0, H); bg.axis('off')


def fax(x, y, w, h):
    return fig.add_axes([x / W, y / H, w / W, h / H])


# ---------------- title band
bg.add_patch(Rectangle((0, H - 0.66), W, 0.66, color=NAVY, lw=0))
bg.text(0.2, H - 0.17, 'CENTRAL ILLUSTRATION', color='#9fbbe0', fontsize=6.2, fontweight='bold', va='center')
bg.text(0.2, H - 0.37, "Heart transplantation in Brazil's public health system, 2000–2025", color='white',
        fontsize=10.5, fontweight='bold', va='center')
bg.text(0.2, H - 0.55, 'Nationwide discharge records (SIH/SUS)   |   5821 transplant admissions   |   64 centers   |   '
        '819 in-hospital deaths (14.1%)', color='#d3e0f2', fontsize=6.6, va='center')

# ---------------- three panels with numbered badges (the 3 questions of the paper)
PX, PW, PY, PH = [0.15, 2.48, 4.81], 2.24, 0.62, 3.1
heads = [('Did the network grow?', 'Yes, mainly through new centers'),
         ('Did it reach every region?', 'Not the North'),
         ('Was there a mortality cost?', 'No clear safety signal')]
for x0, (q, a) in zip(PX, heads):
    bg.add_patch(FancyBboxPatch((x0, PY), PW, PH, boxstyle='round,pad=0,rounding_size=0.07', fc=TINT, ec=LINE, lw=0.6))
for i, (x0, (q, a)) in enumerate(zip(PX, heads), 1):
    bg.add_patch(Circle((x0 + 0.22, PY + PH - 0.24), 0.13, color=NAVY))
    bg.text(x0 + 0.22, PY + PH - 0.245, str(i), color='white', fontsize=8, fontweight='bold', ha='center', va='center')
    bg.text(x0 + 0.43, PY + PH - 0.17, q, fontsize=6.6, color=MUTED, va='center')
    bg.text(x0 + 0.43, PY + PH - 0.33, a, fontsize=8.2, color=NAVY, fontweight='bold', va='center')

# ---- panel 1: network
rows = read_sheet(SRC / 'bloco1/Bloco1_tabelas.xlsx', 'Tabela2_rede')
h = rows[0]; d = [dict(zip(h, r)) for r in rows[1:] if r and isinstance(r[0], int)]
yr = [r['Ano'] for r in d]; g1 = [r['Centros_ativos_ge1'] for r in d]; g10 = [r['Centros_ativos_ge10'] for r in d]
ax = fax(PX[0] + 0.3, PY + 1.33, PW - 0.62, 1.15)
ax.fill_between(yr, g1, color=BLUE, alpha=0.12, lw=0); ax.plot(yr, g1, color=BLUE, lw=1.5)
ax.fill_between(yr, g10, color=ORANGE, alpha=0.12, lw=0); ax.plot(yr, g10, color=ORANGE, lw=1.5)
for y, col, lab, dy in [(g1, BLUE, 'Active centers', 4), (g10, ORANGE, 'Centers with ≥10/year', 3)]:
    ax.plot([yr[0], yr[-1]], [y[0], y[-1]], 'o', color=col, ms=3.4, mec='white', mew=0.6, zorder=4)
    ax.text(yr[0] - 0.8, y[0], f'{y[0]}', ha='right', va='center', fontsize=7, fontweight='bold', color=col)
    ax.text(yr[-1] + 0.8, y[-1], f'{y[-1]}', ha='left', va='center', fontsize=7, fontweight='bold', color=col)
ax.set_xlim(1998.8, 2026.2); ax.set_ylim(0, 50); ax.set_yticks([])
ax.plot([1999.5, 2001.5], [48, 48], color=BLUE, lw=1.5); ax.text(2002.1, 48, 'Active centers', va='center', fontsize=6.1, color=BLUE)
ax.plot([2013.2, 2015.2], [48, 48], color=ORANGE, lw=1.5); ax.text(2015.8, 48, '≥10 transplants/year', va='center', fontsize=6.1, color=ORANGE)
ax.set_xticks([2000, 2025]); ax.tick_params(labelsize=6.2, length=2)
for s in ['top', 'right', 'left']: ax.spines[s].set_visible(False)
ax.patch.set_alpha(0)
for k, (big, small) in enumerate([('68% → 25%', 'of transplants done in\ncenters with <10/year'),
                                  ('73%', 'of the growth came\nfrom new centers')]):
    x = PX[0] + 0.12 + k * 1.06
    bg.add_patch(FancyBboxPatch((x, PY + 0.14), 0.98, 0.9, boxstyle='round,pad=0,rounding_size=0.05', fc='white', ec=LINE, lw=0.5))
    bg.text(x + 0.49, PY + 0.7, big, ha='center', va='center', fontsize=10.5 if k else 9.6, fontweight='bold', color=NAVY)
    bg.text(x + 0.49, PY + 0.38, small, ha='center', va='center', fontsize=5.4, color=INK, linespacing=1.2)

# ---- panel 2: tile map of crude rate by state of residence, 2000–2025
rows = read_sheet(SRC / 'bloco2/Bloco2_tabelas.xlsx', 'Taxa_UF_periodo')
n, py, reg = Counter(), Counter(), {}
for r in rows[1:]:
    if r: n[r[0]] += r[3]; py[r[0]] += r[4]; reg[r[0]] = r[1]
rate = {u: n[u] / py[u] * 1e6 for u in n}
GRID = {'RR': (2, 0), 'AP': (4, 0), 'AM': (1, 1), 'PA': (3, 1), 'MA': (4, 1), 'CE': (5, 1), 'RN': (6, 1),
        'AC': (0, 2), 'RO': (1, 2), 'TO': (3, 2), 'PI': (4, 2), 'PE': (5, 2), 'PB': (6, 2),
        'MT': (2, 3), 'GO': (3, 3), 'BA': (4, 3), 'AL': (5, 3), 'MS': (2, 4), 'DF': (3, 4), 'MG': (4, 4), 'SE': (5, 4),
        'SP': (3, 5), 'RJ': (4, 5), 'ES': (5, 5), 'PR': (3, 6), 'SC': (3, 7), 'RS': (3, 8)}
cmap = LinearSegmentedColormap.from_list('seq', ['#eaf1fb', '#9dc1ee', '#2a78d6', '#14365f'])
norm = Normalize(0, 2.2)
ax = fax(PX[1] + 0.06, PY + 0.86, 1.5, 1.86)
ax.set_xlim(-0.6, 6.6); ax.set_ylim(8.6, -0.6); ax.axis('off')
for u, (c, r) in GRID.items():
    v = rate[u]; north = reg[u] == 'Norte'
    ax.add_patch(FancyBboxPatch((c - 0.43, r - 0.43), 0.86, 0.86, boxstyle='round,pad=0,rounding_size=0.12',
                                fc=cmap(norm(min(v, 2.2))), ec=ORANGE if north else 'white', lw=1.3 if north else 0.5))
    ax.text(c, r, u, ha='center', va='center', fontsize=5.4, color='white' if v > 1.2 else INK,
            fontweight='bold' if north else 'normal')
ax.text(-0.45, 4.6, 'North\nregion', fontsize=5.8, color=ORANGE, va='center', fontweight='bold', linespacing=1.1)
x2 = PX[1] + 1.56
bg.text(x2, PY + 2.42, '0.1×', fontsize=13, fontweight='bold', color=ORANGE, va='center')
bg.text(x2, PY + 2.12, "the Southeast's\ntransplant rate", fontsize=5.6, va='center', linespacing=1.2)
bg.text(x2, PY + 1.62, '~2000 km', fontsize=10, fontweight='bold', color=NAVY, va='center')
bg.text(x2, PY + 1.33, 'median distance\ntraveled by North\nresidents since 2008', fontsize=5.6, va='center', linespacing=1.2)
cax = fax(PX[1] + 0.3, PY + 0.52, 1.1, 0.07)
cb = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation='horizontal', ticks=[0, 1, 2])
cb.outline.set_visible(False); cb.ax.tick_params(labelsize=5.6, length=0, pad=1.5); cb.ax.set_xticklabels(['0', '1', '≥2'])
bg.text(PX[1] + 0.85, PY + 0.25, 'Transplants per million per year by state\nof residence (crude, 2000–2025)',
        fontsize=5.2, color=MUTED, ha='center', va='center', linespacing=1.2)
bg.text(x2, PY + 0.86, '1 program in the\nNorth, 2002–2006', fontsize=5.6, va='center', linespacing=1.2, color=INK)

# ---- panel 3: volume and in-hospital death
ax = fax(PX[2] + 0.18, PY + 1.42, PW - 0.36, 1.15)
items = [('Lower vs median center volume', 'between centers; 10th percentile vs median', 1.20, 0.78, 1.84, ORANGE),
         ('+10 transplants/year', 'within centers; vs the center\'s own mean', 0.81, 0.73, 0.91, BLUE)]
for i, (lab, sub, o, l, hh, col) in enumerate(items):
    y = 1 - i
    ax.plot([l, hh], [y, y], color=INK, lw=1.2, solid_capstyle='butt', zorder=3)
    ax.plot(o, y, 's', color=col, ms=6, mec='white', mew=0.6, zorder=4)
    ax.text(0.52, y + 0.52, lab, fontsize=6.5, fontweight='bold', va='center', ha='left', zorder=5, bbox=dict(fc=TINT, ec='none', pad=0.3))
    ax.text(0.52, y + 0.3, sub, fontsize=5.4, color=MUTED, va='center', ha='left', zorder=5, bbox=dict(fc=TINT, ec='none', pad=0.3))
    ax.text(2.15, y - 0.24, f'OR {o:.2f} ({l:.2f}–{hh:.2f})', fontsize=6, va='center', ha='right')
ax.vlines(1, -0.55, 0.15, color=MUTED, lw=0.7, ls=(0, (3, 2))); ax.vlines(1, 0.75, 1.15, color=MUTED, lw=0.7, ls=(0, (3, 2)))
ax.set_xscale('log'); ax.set_xlim(0.5, 2.2); ax.set_ylim(-0.55, 1.75); ax.set_yticks([])
ax.xaxis.set_major_locator(FixedLocator([0.5, 1, 2])); ax.xaxis.set_major_formatter(FixedFormatter(['0.5', '1', '2']))
ax.xaxis.set_minor_locator(NullLocator()); ax.tick_params(labelsize=6, length=2)
for s in ['top', 'right', 'left']: ax.spines[s].set_visible(False)
ax.patch.set_alpha(0)
ax.set_xlabel('Odds ratio of in-hospital death (95% CI)', fontsize=5.8, labelpad=1.5)
ax.text(0.97, -0.42, '← lower odds', fontsize=5.2, color=MUTED, ha='right')
x0 = PX[2] + 0.12
for k, (big, small) in enumerate([('P = 0.167', 'mean center volume;\nup to 1.84× not excluded'),
                                  ('2000–2007', 'busier years within a center\nsafer mainly in this period')]):
    x = x0 + k * 1.06
    bg.add_patch(FancyBboxPatch((x, PY + 0.14), 0.98, 0.9, boxstyle='round,pad=0,rounding_size=0.05', fc='white', ec=LINE, lw=0.5))
    bg.text(x + 0.49, PY + 0.7, big, ha='center', va='center', fontsize=9.6, fontweight='bold', color=NAVY)
    bg.text(x + 0.49, PY + 0.38, small, ha='center', va='center', fontsize=5.4, color=INK, linespacing=1.2)

# ---------------- take-home band
bg.add_patch(Rectangle((0, 0), W, 0.5, color='white', lw=0))
bg.add_patch(Rectangle((0.15, 0.1), 0.05, 0.32, color=ORANGE, lw=0))
bg.text(0.3, 0.3, 'Brazil expanded its public heart transplant network through new programs without a clear rise in '
        'in-hospital mortality,', fontsize=6.9, color=NAVY, fontweight='bold', va='center')
bg.text(0.3, 0.16, 'but the North remains without an active program. Associations only; adjusted for age, sex and year; '
        'administrative data without pre-transplant severity.', fontsize=6.0, color=MUTED, va='center')

for ext, kw in [('tiff', {'dpi': 600, 'pil_kwargs': {'compression': 'tiff_lzw'}}), ('pdf', {}), ('png', {'dpi': 300})]:
    fig.savefig(OUT / f'Central_Illustration.{ext}', facecolor='white', **kw)
print('ok')
