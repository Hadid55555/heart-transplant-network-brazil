import os, sys, numpy as np, pandas as pd
from math import sqrt
base, out = sys.argv[1], sys.argv[2]
INI = int(os.environ.get('TXC_INI', '2000'))
ENT = int(os.environ.get('TXC_ENT', INI + 2))   # entrante = 1º TxC observado a partir de ENT
INC = f'Centros {INI}-{(ENT - 1) % 100:02d}'
d = pd.read_csv(f'{base}/microdados/aih_txc_{INI}_2025.csv')
ca = pd.read_csv(f'{base}/microdados/centro_ano.csv')
assert (d.tipo_centro == np.where(d.ano_primeiro_txc_centro >= ENT, 'entrante', 'incumbente')).all()
PRE=[f'{a}-{a+3}' for a in range(INI,2008,4)]
d['periodo']=pd.cut(d.ano_inter,[a-1 for a in range(INI,2008,4)]+[2007,2011,2015,2019,2022,2025],labels=PRE+['2008-2011','2012-2015','2016-2019','2020-2022','2023-2025'])
d['V']=d.volume_centro_ano
d['Vcat']=pd.cut(d.V,[0,9,19,39,999],labels=['<10','10-19','20-39','>=40'])
def wilson(k,n,z=1.96):
    if n==0: return (np.nan,np.nan)
    p=k/n; den=1+z*z/n; c=(p+z*z/(2*n))/den; h=z*sqrt(p*(1-p)/n+z*z/(4*n*n))/den
    return (c-h,c+h)
def pct(k,n): return f"{k} ({100*k/n:.1f}%)" if n else "0"
def med(x): 
    q=np.nanpercentile(x,[25,50,75]); return f"{q[1]:.0f} ({q[0]:.0f}-{q[2]:.0f})"
def medf(x,f="{:.1f}"):
    q=np.nanpercentile(x,[25,50,75]); return f"{f.format(q[1])} ({f.format(q[0])}-{f.format(q[2])})"
groups={'Total':d,'Adultos':d[d.pediatrico==0],'Pediátricos':d[d.pediatrico==1],
        INC:d[d.tipo_centro=='incumbente'],f'1º TxC observado >={ENT}':d[d.tipo_centro=='entrante']}
rows=[]
def add(label,fn):
    rows.append([label]+[fn(g) for g in groups.values()])
add('AIH, n',lambda g:f"{len(g)}")
add('Centros, n',lambda g:f"{g.centro.nunique()}")
add('Óbito hospitalar, n (%)',lambda g:pct(int(g.morte.sum()),len(g)))
add('Idade, mediana (IQR)',lambda g:med(g.idade))
for f in ['0-11','12-17','18-39','40-49','50-59','60+']:
    add(f'  Faixa etária {f}, n (%)',lambda g,f=f:pct(int((g.faixa_etaria==f).sum()),len(g)))
add('Sexo feminino, n (%)',lambda g:pct(int((g.sexo=='F').sum()),len(g)))
add('Chagas em qualquer campo, n (%)',lambda g:pct(int(g.chagas_qualquer.sum()),len(g)))
for e in d.etiologia_grupo.value_counts().index:
    add(f'  Etiologia: {e}, n (%)',lambda g,e=e:pct(int((g.etiologia_grupo==e).sum()),len(g)))
add('Caráter urgência/outros (descritivo), n (%)',lambda g:pct(int((g.carater=='urgencia_outros').sum()),len(g)))
add('Tempo de internação, dias, mediana (IQR)',lambda g:med(g.dias_perm))
add('Operados fora da UF de residência, n (%)',lambda g:pct(int(g.fora_uf.sum()),len(g)))
add('Distância percorrida, km, mediana (IQR)',lambda g:med(g.dist_km_centro_operou))
add('Distância P75, km',lambda g:f"{np.nanpercentile(g.dist_km_centro_operou,75):.0f}")
for r in (['Norte'] if INI<2008 else [])+['Sudeste','Nordeste','Sul','Centro-Oeste']:
    add(f'  Região do hospital {r}, n (%)',lambda g,r=r:pct(int((g.regiao_hosp==r).sum()),len(g)))
add('Volume do centro no ano (V), mediana (IQR)',lambda g:med(g.V))
for c in ['<10','10-19','20-39','>=40']:
    add(f'  AIH em centro-ano V {c}, n (%)',lambda g,c=c:pct(int((g.Vcat==c).sum()),len(g)))
add('Reembolso real por AIH, R$ dez/2025, mediana (IQR)',lambda g:medf(g.val_tot_real_dez2025,"{:,.0f}"))
t1=pd.DataFrame(rows,columns=['Variável']+list(groups.keys()))

# Tabela 2: rede por ano
ca['ativo']=ca.n_txc>=1
anos=list(range(INI,2026)); r2=[]
ult=ca[ca.ativo].groupby('centro').ano.max(); prim=ca[ca.ativo].groupby('centro').ano.min()
for a in anos:
    x=ca[(ca.ano==a)&ca.ativo]; n=x.n_txc.sum(); sh=x.n_txc/n
    dd=d[d.ano_inter==a]
    r2.append(dict(Ano=a,AIH=int(n),Centros_ativos_ge1=len(x),Centros_ativos_ge10=int((x.n_txc>=10).sum()),
        Entradas=int((prim==a).sum()) if a>INI else np.nan, Ultimo_ano_de_atividade=int((ult==a).sum()) if a<=2023 else np.nan,
        UFs_com_centro=x.uf_hosp.nunique(), HHI=round(float(((sh*100)**2).sum()),0), Top3_pct=round(100*float(sh.sort_values(ascending=False).head(3).sum()),1),
        AIH_em_centros_lt10_pct=round(100*float(x[x.n_txc<10].n_txc.sum()/n),1),
        Obitos=int(dd.morte.sum()), Mortalidade_bruta_pct=round(100*dd.morte.mean(),1)))
t2=pd.DataFrame(r2)
# conferencia com numeros previos (periodos agrupados)
def pool(ys):
    x=ca[ca.ano.isin(ys)].groupby('centro').n_txc.sum(); x=x[x>0]; sh=x/x.sum()
    return dict(AIH_media_ano=round(x.sum()/len(ys),1),HHI=round(float(((sh*100)**2).sum()),0),Top3=round(100*float(sh.sort_values(ascending=False).head(3).sum()),1))
conf=pd.DataFrame({f'{INI}-{(INI+1)%100:02d}':pool([INI,INI+1]),'2024-25':pool([2024,2025])})
# mortalidade bruta
def mort(g,key):
    o=[]
    for k,x in g.groupby(key,observed=True):
        n=len(x); m=int(x.morte.sum()); lo,hi=wilson(m,n); o.append(dict(Categoria=str(k),AIH=n,Obitos=m,Mort_pct=round(100*m/n,1),IC95=f"{100*lo:.1f}-{100*hi:.1f}"))
    return pd.DataFrame(o)
mv=mort(d,'Vcat'); mt=mort(d,'tipo_centro'); mp=mort(d,'periodo')
e=d[d.tipo_centro=='entrante'].sort_values(['centro','ano_inter','mes_inter','id_aih']).copy()
e['seq']=e.groupby('centro').cumcount()+1
e['bloco5']=pd.cut(e.seq,[0,5,10,15,20,50,9999],labels=['1-5','6-10','11-15','16-20','21-50','>50'])
e['idade_prog']=pd.cut(e.ano_programa,[0,4,9,99],labels=['<5','5-9','>=10'])
ms=mort(e,'bloco5'); ma=mort(e,'idade_prog')
DOM=e.centro.value_counts().index[0]   # maior centro novo
ms_ex=mort(e[e.centro!=DOM],'bloco5'); 
vc=pd.DataFrame({'AIH_por_Vcat':d.Vcat.value_counts().sort_index()})
with pd.ExcelWriter(f'{out}/Bloco1_tabelas.xlsx') as w:
    t1.to_excel(w,sheet_name='Tabela1',index=False); t2.to_excel(w,sheet_name='Tabela2_rede',index=False); conf.to_excel(w,sheet_name='Conferencia_pooled')
    mv.to_excel(w,sheet_name='Mort_por_volume',index=False); mt.to_excel(w,sheet_name='Mort_por_tipo',index=False); mp.to_excel(w,sheet_name='Mort_por_periodo',index=False)
    ms.to_excel(w,sheet_name='Mort_seq_entrantes',index=False); ms_ex.to_excel(w,sheet_name='Mort_seq_sem_maior_novo',index=False); ma.to_excel(w,sheet_name='Mort_idade_prog_entr',index=False)
t1.to_csv(f'{out}/Tabela1.csv',index=False,encoding='utf-8-sig'); t2.to_csv(f'{out}/Tabela2.csv',index=False,encoding='utf-8-sig')
pd.set_option('display.width',250); pd.set_option('display.max_columns',30)
print(t1.to_string(index=False)); print(); print(t2.to_string(index=False)); print(); print(conf)
print('\nMort por V\n',mv.to_string(index=False)); print('\nPor tipo\n',mt.to_string(index=False)); print('\nPor periodo\n',mp.to_string(index=False))
print('\nSeq entrantes\n',ms.to_string(index=False)); print('\nSeq sem o maior centro novo\n',ms_ex.to_string(index=False)); print('\nIdade programa entr\n',ma.to_string(index=False))
# figura 1
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
fig,ax=plt.subplots(3,1,figsize=(8,9),sharex=True)
ax[0].plot(t2.Ano,t2.Centros_ativos_ge1,marker='o',label='>=1 TxC/ano'); ax[0].plot(t2.Ano,t2.Centros_ativos_ge10,marker='s',label='>=10 TxC/ano'); ax[0].set_ylabel('Centros ativos'); ax[0].legend(frameon=False)
ax[1].plot(t2.Ano,t2.HHI,marker='o',color='tab:red'); ax[1].set_ylabel('HHI (0-10.000)')
ax[2].plot(t2.Ano,t2.Top3_pct,marker='o',label='3 maiores centros (%)'); ax[2].plot(t2.Ano,t2.AIH_em_centros_lt10_pct,marker='s',label='AIH em centros <10/ano (%)'); ax[2].set_ylabel('%'); ax[2].legend(frameon=False); ax[2].set_xlabel('Ano')
for a in ax: a.spines[['top','right']].set_visible(False)
from matplotlib.ticker import MaxNLocator
ax[2].xaxis.set_major_locator(MaxNLocator(integer=True))
plt.tight_layout(); plt.savefig(f'{out}/Figura1_rede.png',dpi=150)
