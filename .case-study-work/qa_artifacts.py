from pathlib import Path
import json,math,re,zipfile,xml.etree.ElementTree as ET
from PIL import Image,ImageOps,ImageDraw
import pdfplumber
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1];WORK=Path(__file__).resolve().parent
D=json.loads((WORK/'case_data.json').read_text(encoding='utf-8'))
pdf=ROOT/'output/pdf/Electro_Group_End_to_End_Case_Study.pdf'
reader=PdfReader(str(pdf));texts=[p.extract_text() for p in reader.pages]
print('PDF page text coverage:',[(i+1,len(t)) for i,t in enumerate(texts)])
assert all(len(t)>80 for t in texts)
full='\n'.join(texts)
for f in D['features']:assert f['id'] in full,f['id']
assert all(k[3]!='Define exact numerator denominator event and population with process owner' for k in D['kpis'])
assert len(D['wire_rows'])==32 and len(D['features'])==192 and len(D['data'])==488
with pdfplumber.open(pdf) as book:
    bounds=[]
    for i,page in enumerate(book.pages):
        words=page.extract_words()
        bad=[w['text'] for w in words if w['x0']<46 or w['x1']>566 or w['top']<43 or (w['bottom']>749 and w['top']<749)]
        if bad:bounds.append([i+1,bad])
    print('PDF margin exceptions:',bounds)
    (WORK/'pdf_bounds.json').write_text(json.dumps(bounds),encoding='utf-8')

xlsx=ROOT/'outputs/electro-group-case-study/Electro_Group_Department_Features_and_Data.xlsx'
ns={'s':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
with zipfile.ZipFile(xlsx) as z:
    strings=[]
    if 'xl/sharedStrings.xml' in z.namelist():
        ss=ET.fromstring(z.read('xl/sharedStrings.xml'))
        strings=[''.join(el.itertext()) for el in ss.findall('s:si',ns)]
    tabs=ET.fromstring(z.read('xl/workbook.xml')).find('s:sheets',ns)
    assert len(tabs)==13
    error_cells=[]; data_by_sheet={}
    for j,tab in enumerate(tabs,1):
        tree=ET.fromstring(z.read(f'xl/worksheets/sheet{j}.xml'))
        cells={}
        for c in tree.findall('.//s:sheetData/s:row/s:c',ns):
            v=c.find('s:v',ns);text=v.text if v is not None else ''
            if c.attrib.get('t')=='s': text=strings[int(text)]
            elif c.attrib.get('t')=='inlineStr': text=''.join(c.find('s:is',ns).itertext())
            if c.attrib.get('t')=='e':error_cells.append([tab.attrib['name'],c.attrib['r'],text])
            cells[c.attrib['r']]=text
        data_by_sheet[tab.attrib['name']]=cells
        assert tree.find('s:sheetViews/s:sheetView',ns).attrib.get('showGridLines')=='0'
    assert not error_cells,error_cells
    assert float(data_by_sheet['Coverage']['C31'])==192
    assert float(data_by_sheet['Coverage']['D31'])==21
    assert float(data_by_sheet['Coverage']['E31'])==171
    for i,row in enumerate(D['wire_rows'],6):
        for j,value in enumerate(row):
            actual=data_by_sheet['Wire master'][f'{chr(65+j)}{i}']
            if isinstance(value,(int,float)):assert float(actual)==value
            else:assert actual==value
    assert data_by_sheet['Worked examples']['B26']=='Not supplied'
    print('Workbook verified: 13 sheets, 192 features, 488 fields, original 32 wire rows preserved, no cached formula errors.')

pagefiles=sorted((WORK/'pdf-pages').glob('page-*.png'))[:len(reader.pages)]
montages=[]
for first in range(0,len(pagefiles),4):
    canvas=Image.new('RGB',(1740,2260),'#C8CDD3');draw=ImageDraw.Draw(canvas)
    for j,f in enumerate(pagefiles[first:first+4]):
        im=Image.open(f).convert('RGB');im.thumbnail((850,1100))
        x=(j%2)*870+10;y=(j//2)*1130+20
        canvas.paste(im,(x,y));draw.text((x,y-15),f'Page {first+j+1}',fill='black')
    outfile=WORK/f'pdf_contact_{first//4+1:02d}.png';canvas.save(outfile);montages.append(str(outfile))
print('PDF review sheets:',len(montages))
workbook_previews=list(WORK.glob('preview_*.png'))
print('Workbook previews:',len(workbook_previews))
(WORK/'final_qa.json').write_text(json.dumps({'pdf_pages':len(reader.pages),'pdf_review_sheets':montages,'workbook_previews':[str(f) for f in workbook_previews],'margin_exceptions':bounds,'workbook_formula_errors':error_cells},indent=2),encoding='utf-8')
