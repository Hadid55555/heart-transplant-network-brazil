"""Minimal raw reader for .xlsx sheets (the R-written workbooks confuse openpyxl's dimension info)."""
import zipfile, re
import xml.etree.ElementTree as ET
NS = {'m': 'http://schemas.openxmlformats.org/spreadsheetml/2006/main',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}

def _col(ref):
    s = re.match(r'[A-Z]+', ref).group(0); n = 0
    for ch in s: n = n * 26 + ord(ch) - 64
    return n - 1

def read_sheet(path, name):
    z = zipfile.ZipFile(path)
    wb = ET.fromstring(z.read('xl/workbook.xml'))
    rels = ET.fromstring(z.read('xl/_rels/workbook.xml.rels'))
    rid = [s.get('{%s}id' % NS['r']) for s in wb.find('m:sheets', NS) if s.get('name') == name][0]
    target = [r.get('Target') for r in rels if r.get('Id') == rid][0].lstrip('/')
    target = target if target.startswith('xl/') else 'xl/' + target
    ss = []
    if 'xl/sharedStrings.xml' in z.namelist():
        for si in ET.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si', NS):
            ss.append(''.join(t.text or '' for t in si.iter('{%s}t' % NS['m'])))
    rows = []
    for row in ET.fromstring(z.read(target)).find('m:sheetData', NS):
        vals = {}
        for c in row:
            t = c.get('t'); v = c.find('m:v', NS)
            if t == 's': val = ss[int(v.text)]
            elif t == 'inlineStr': val = ''.join(x.text or '' for x in c.iter('{%s}t' % NS['m']))
            elif v is None or v.text is None: val = None
            elif t in ('str', 'b', 'e'): val = v.text
            else:
                f = float(v.text); val = int(f) if f.is_integer() else f
            vals[_col(c.get('r'))] = val
        rows.append([vals.get(i) for i in range(max(vals) + 1)] if vals else [])
    return rows
