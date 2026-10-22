"""RBT 2017 (ABTO, Ano XXIII nº4, PDF p.84 "Dados por centro transplantador" — coração): concentração por equipe e por hospital.
Imprime só agregados (nenhum nome de equipe ou hospital). PDF: https://site.abto.org.br/wp-content/uploads/2020/06/rbt-imprensa-leitura-compressed.pdf
Uso: python3 -I scripts/rbt_equipes_2017.py <pdf>   (2009, 2010 e parciais 2011/2020/2025 foram transcritos à mão e conferidos com os totais impressos)
"""
import re,sys,subprocess
t=subprocess.run(['pdftotext','-f','84','-l','84','-layout',sys.argv[1],'-'],capture_output=True,text=True).stdout
rows=[];states={};cur=None
for ln in t.splitlines():
    m=re.match(r'\s+([A-ZÁÉÍÓÚÂÊÔÃÕÇa-záéíóúâêôãõç ]+) \((\d+)\)\s+([A-Z]{2})\s*$',ln)
    if m: cur=m.group(3); states[cur]=int(m.group(2)); continue
    if ln.strip().startswith(('NI -','Real.','Pacientes','RBT')): continue
    m=re.search(r'\s(\d+)\s*$',ln)
    if m and cur and len(ln)>150:
        # hospital column approx chars 59-110
        hosp=ln[59:110].strip()
        rows.append((cur,hosp,int(m.group(1))))
from collections import defaultdict
ss=defaultdict(int)
for s,h,n in rows: ss[s]+=n
print('n_rows',len(rows),'total',sum(r[2] for r in rows))
print('state check', {s:(ss[s],states[s]) for s in states if ss[s]!=states[s]} or 'ok', sum(states.values()))
def agg(v,label):
    v=sorted([x for x in v if x>0],reverse=True);T=sum(v)
    sh=[100*x/T for x in v]
    print(label,'T',T,'ge1',len(v),'ge10',sum(x>=10 for x in v),'top3 %.1f'%sum(sh[:3]),'top9 %.1f'%sum(sh[:9]),'hhi %.0f'%sum(s*s for s in sh),'lt10 %.1f'%(100*sum(x for x in v if x<10)/T), 'dist',v)
agg([r[2] for r in rows],'EQUIPE')
hh=defaultdict(int)
for s,h,n in rows: hh[(s,h)]+=n
print('n_hosp_listed',len(hh))
agg(list(hh.values()),'HOSPITAL')
