from pathlib import Path
import json,re,math
from collections import Counter,defaultdict
from xml.sax.saxutils import escape
from reportlab.platypus import SimpleDocTemplate,BaseDocTemplate,PageTemplate,Frame,Paragraph,Spacer,PageBreak,Table,TableStyle,KeepTogether,CondPageBreak
from reportlab.platypus.tableofcontents import TableOfContents
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
from reportlab.lib.enums import TA_LEFT,TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.graphics.shapes import Drawing,Rect,String,Line,Polygon
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pypdf import PdfReader

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(__file__).resolve().parent
D=json.loads((WORK/'case_data.json').read_text(encoding='utf-8'))
OUT=ROOT/'output/pdf'
OUT.mkdir(parents=True,exist_ok=True)
FONT=Path('C:/Windows/Fonts/arial.ttf')
pdfmetrics.registerFont(TTFont('Body',str(FONT)))
pdfmetrics.registerFont(TTFont('BodyBold','C:/Windows/Fonts/arialbd.ttf'))
pdfmetrics.registerFont(TTFont('BodyItalic','C:/Windows/Fonts/ariali.ttf'))
pdfmetrics.registerFontFamily('Body',normal='Body',bold='BodyBold',italic='BodyItalic',boldItalic='BodyBold')
SS=getSampleStyleSheet()
styles={
'body':ParagraphStyle('body',fontName='Body',fontSize=10.5,leading=14.2,spaceAfter=7,textColor=colors.HexColor('#202124')),
'small':ParagraphStyle('small',fontName='Body',fontSize=9,leading=12,spaceAfter=5),
'feature':ParagraphStyle('feature',fontName='Body',fontSize=10.2,leading=13.3,spaceAfter=6),
'h1':ParagraphStyle('h1',fontName='BodyBold',fontSize=19,leading=23,spaceAfter=13,keepWithNext=True,textColor=colors.black),
'h2':ParagraphStyle('h2',fontName='BodyBold',fontSize=12.4,leading=16,spaceBefore=9,spaceAfter=6,keepWithNext=True,textColor=colors.black),
'title':ParagraphStyle('title',fontName='BodyBold',fontSize=30,leading=35,spaceAfter=18,textColor=colors.black),
'sub':ParagraphStyle('sub',fontName='Body',fontSize=16,leading=21,spaceAfter=14,textColor=colors.black),
'cell':ParagraphStyle('cell',fontName='Body',fontSize=8.6,leading=11.5,spaceAfter=0),
'thead':ParagraphStyle('thead',fontName='BodyBold',fontSize=8.8,leading=11.7,textColor=colors.white),
}
story=[]
def clean(s):return str(s).replace('\u2011','-').replace('\u2013','-').replace('\u2014','-')
def p(s,style='body'):return Paragraph(clean(s),styles[style])
def para(s,style='body'):story.append(p(s,style))
def h(s,level=1):
    z=p(escape(s),'h1' if level==1 else 'h2')
    if level==1:z._toc_level=0
    story.append(z)
def new(s):story.append(PageBreak());h(s)
def table(headers,rows,widths):
    data=[[p(escape(str(x)),'thead') for x in headers]]+[[p(escape('' if x is None else str(x)),'cell') for x in row] for row in rows]
    t=Table(data,colWidths=widths,repeatRows=1,hAlign='LEFT')
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#363A40')),('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#F3F4F6')]),('GRID',(0,0),(-1,-1),.4,colors.HexColor('#D9D9D9')),('VALIGN',(0,0),(-1,-1),'MIDDLE'),('LEFTPADDING',(0,0),(-1,-1),7),('RIGHTPADDING',(0,0),(-1,-1),7),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
    story.extend([t,Spacer(1,8)])
def footer(canvas,doc):
    canvas.saveState();canvas.setFont('Body',8);canvas.setFillColor(colors.HexColor('#5B6067'))
    if doc.page>1:canvas.drawString(48,29,'Electro Group and Electrotech Services   |   Company case study   |   15 October 2026')
    canvas.drawRightString(564,29,str(doc.page));canvas.restoreState()
class Report(BaseDocTemplate):
    def __init__(self,filename):
        super().__init__(str(filename),pagesize=letter,leftMargin=48,rightMargin=48,topMargin=45,bottomMargin=45,title='Electro Group and Electrotech Services Company Case Study',author='Prepared with Codex')
        self.addPageTemplates(PageTemplate(id='main',frames=[Frame(48,45,516,702,id='frame',leftPadding=0,rightPadding=0,topPadding=0,bottomPadding=0)],onPage=footer))
    def afterFlowable(self,f):
        if hasattr(f,'_toc_level'):
            text=f.getPlainText();key='section_'+str(self.seq.nextf('heading'))
            self.canv.bookmarkPage(key);self.notify('TOCEntry',(f._toc_level,text,self.page,key))
            self.canv.addOutlineEntry(text,key,level=f._toc_level,closed=True)

para('ELECTRO GROUP OF INDUSTRIES','small')
story.append(Spacer(1,30))
para('Electro Group and<br/>Electrotech Services','title')
para('End to end company case study','sub')
para('Department functions, operating workflows, application features and data requirements','sub')
story.append(Spacer(1,22))
para('Prepared for company process mapping and operations planning')
para('15 October 2026')
story.append(Spacer(1,32))
para('The existing project provides a starting point for engineering calculations, calibration reporting and employment letters. The proposed operating model connects these functions to customer orders, material, production, quality, finance, service and employee processes.')
para(f'This package covers {len(D["departments"])} department functions, {len(D["features"])} feature requirements, {len(D["data"])} data field entries, six workflows with {len(D["workflows"])} steps, {len(D["controls"])} control requirements and {len(D["kpis"])} proposed performance measures.')
para('The companion Excel register contains the complete field inventory, all retrieved wire rows, engineering reference options, catalogue entries, process steps and outstanding data requests.','small')
para('Evidence labels distinguish source code, live spreadsheet data, public company statements and proposed capabilities. Financial and operating outcomes require company records.','small')

new('Contents')
del story[-1]._toc_level
toc=TableOfContents();toc.levelStyles=[ParagraphStyle('toc1',fontName='Body',fontSize=10,leading=12,spaceBefore=0,spaceAfter=0,leftIndent=0,firstLineIndent=0)]
story.append(toc)

new('1 Executive case and scope')
para('The company needs a joined operating record from customer requirement to accepted product or service and financial closure. The existing app already handles selected technical calculations and document preparation. The next operating improvement is to connect those outputs to approved orders, jobs, material transactions, reviewed releases and accountable owners.')
para('This is an operational case study and requirements baseline. It includes the current project and a proposed complete functional model. The 24 functions are a coverage structure for validation; they are not presented as the company\'s verified organisation chart. One person or team may perform several functions.')
h('Evidence and interpretation',2)
table(['Label','Meaning','Use in this study'],[
['Present in source','Observed in local app files','Confirms implemented code; live execution and adoption not established'],
['Live spreadsheet data','Read from the connected sheet on the study date','Confirms 32 wire records and the two visible sheet tabs'],
['Public company statement','Published on the matching company websites','Supports business scope; independent performance and certification not established'],
['Proposed','Recommended process or capability','Requires process owner validation and implementation'],
['Not supplied','No underlying internal records available in this study','No invented revenue, staff count, output, stock, cost saving or ROI']],[112,187,217])
h('Current evidence and practical limits',2)
para('The reviewed local files are the interface, application logic, spreadsheet backend, setup guide, service worker and application manifest. The connected workbook is titled Industrial Heater Coil Wire Database. Its metadata shows only nichrome_wires and kanthal_d_wires. All six relevant columns were read across the full 1000 row grid for each visible tab. There are 23 and 9 populated data rows respectively. [L01-L06, G01]')
para('The code supports calibration_reports, performance_reports, offer_letters and appointment_letters. Those tabs were not visible in the connected workbook on the study date. This does not prove no reports or letters exist: browser local storage, another workbook or a different deployment may hold records. Operational document counts and historical transaction data remain unverified.')
para('No profit improvement or time saving is claimed as achieved. The measurement section defines how to collect a baseline and verify results after implementation.')

new('2 Company profile and business context')
h('Verified study identity',2)
para('The user confirmed Electro Group and Electrotech Services as the study scope. The project uses Electro Group of Industries branding for the operations interface and Electrotech Services branding for document workflows. The matching public website uses the name Electro Tech Services. [L01-L03, S01]')
table(['Item','Company published detail','Evidence'],[
['Business address','Plot No. Adj. S.M. 180, Industrial Estate Baikampady, New Mangalore 575011, Karnataka','S04'],
['Website','https://electrotechind.in/','S01'],
['Public business telephone','0824 2406417; +91 7022259317; +91 9141347017','S04'],
['Public business email','electrotechservices97@gmail.com','S04'],
['Service history statement','Website states servicing since 1995; legal incorporation date not established','S03'],
['Associated heating business','The websites link to one another; legal ownership and group structure need confirmation','S12 S13'],
['Associated address','Electro Heat Systems, D-123 Industrial Estate, Baikampady, New Mangalore 575011','S12'],
['Associated history statement','Electro Heat Systems states manufacturing since 1998','S13']],[115,341,60])
h('How the company creates value',2)
para('The published business scope combines engineering and manufacture of heating and packaging equipment with repair, calibration and application specific machine work. This supports several operating patterns: custom design and manufacture, equipment supply, consumable supply, workshop repair, on site service and calibration. Actual revenue mix, order volumes and capacity are not available. [S01-S03]')
para('The operating model therefore needs different job types. A stocked film sale requires item, quantity, price and dispatch controls. A custom oven needs approved design revisions, purchased components, fabrication, panel integration and customer acceptance. A calibration job needs instrument identity, standard evidence, raw readings and reviewed certificate issue. These differences drive the proposed workflows.')
h('Identity and certification evidence to obtain',2)
para('Confirm legal names, registration documents, sites, entity relationships, tax registrations, signatory authority, exact accreditation or product certification scope, and current certificates before configuring documents or making compliance claims. Website statements about traceability and testing do not by themselves establish a company accreditation or a licence covering every product.')

new('3 Product and service portfolio')
para('The following catalogue families were visible in the public sources. Catalogue entries can overlap across categories and brands; the count is not a deduplicated stock keeping unit count. Current price, stock, model variants, capacity, lead time, discontinued status and actual sales history were not supplied.')
table(['Family','Visible entries','Examples and evidence'],[
['Packaging machinery',12,'Sealing, filling, coding and shrinking equipment. The category reports 14 results; page two was unavailable. S05'],
['Plastic processing',3,'Hopper drying/loading and loop handle equipment. S06'],
['Heating equipment',7,'Ovens, furnaces, generators, hot plates and related equipment. S07'],
['Controls and panels',3,'Timers/counters, panel boxes and temperature controllers. S08'],
['Sensors',1,'One thermocouple and sensor category entry. S09'],
['Packaging materials',3,'Shrink film, strapping and wrapping film. S10'],
['Custom machines',6,'Stirring, coding, sealing, industrial oven and conveyor entries. S11'],
['Associated heating catalogue',15,'Band, cartridge, tubular, infrared and other heater families with controls and sensors. S14']],[145,72,299])
h('Service scope',2)
para('Electrotech publicly describes repair, replacement and maintenance for electrical ovens, sealing machines and control panels. Its service page also describes temperature controller calibration and traceability to NABL certification. The study does not treat that wording as independent evidence of laboratory accreditation. Obtain the reference certificates, applicable scope, method and issuer authorisation for actual jobs. [S03]')
para('Electro Heat Systems describes testing activities including electrical breakdown, insulation resistance, resistance and dimensions. These are published company statements, and the precise product plan, method, equipment and acceptance limits must be validated before a digital inspection workflow is released. [S13]')
h('Portfolio completeness actions',2)
para('The workbook contains all 50 catalogue entries retrieved in this study. Request the current complete company product master, including candle machinery details, the two inaccessible packaging entries, SKU identifiers, approved technical specifications and pricing. The candle category appears in navigation but its product page was unavailable. No item names were invented for the inaccessible entries.')
para('Assign business line and order type independently. An oven can create a manufacturing order, a commissioning project and later a service ticket. Each remains linked to the same equipment serial while keeping its own scope, acceptance and commercial records.')

new('4 Existing application capabilities')
para('The current project is a browser application built from HTML, CSS and JavaScript with a Google Apps Script backend and Google Sheets storage. The manifest and service worker support an installable app shell. This section reports source observations, not an end to end live application acceptance test. [L01-L06]')
table(['Module','Capabilities observed','Boundary'],[
['Overview','Calibration total, pass, due soon, heater runs, offer, appointment and performance counts','These are app metrics, not a reconciled enterprise dashboard'],
['Heater calculator','Material database, electrical and geometry calculations, automatic and manual inputs, result selection','No complete released design history or job costing record observed'],
['Calibration','Editable certificate, readings, customer reuse, numbering, due date, register, print and CSV','Independent issue approval and immutable revision control not established'],
['Performance','Calibration linking, shared context/sequence, Celsius or percentage error, separate register and export','Requires valid linked calibration and complete readings'],
['Offer letters','Editable placeholders, live A4 preview, confirmation, register and export','Employment offer workflow; not payroll processing'],
['Appointments','Four page document, compensation annexure, issue/register/export','Entered gross values and document issue do not establish signed acceptance'],
['Storage','Spreadsheet calls, local record storage and fallback messages','Live workbook currently shows only wire tabs'],
['Installation','Browser install prompts and same origin app asset caching','Offline shared data and durable background synchronisation not established']],[92,234,190])
h('Existing data organisation',2)
para('Wire tables use id, swg, thickness, ohm, minw and maxw. Four document tables have searchable index columns and store complete editable content in payload_json. Browser local storage keeps reports, customer reuse details, document numbering state and heater calculation count. A full heater calculation history is not established by the count alone. [L03 L04]')
para('The backend validates administrator credentials for wire table writes. Source handlers for document saves do not use that wire administrator check. The setup guide calls out deployment access restrictions for shared internal records. The actual deployed access policy was not inspected. This is a concrete requirement for identity and record access review before wider use. [L04 L05]')

new('5 Engineering logic and wire master findings')
h('Calculation rules observed in source',2)
para('Base resistance = voltage squared divided by wattage. Adjusted resistance = base resistance multiplied by one plus extra resistance percentage divided by 100. Wire length = adjusted resistance divided by the selected row resistance per metre. Turns = wire length in millimetres divided by pi times effective core diameter. Pitch = core winding length divided by turns. [L03]')
para('Surface area in square centimetres = pi times heater outside diameter in millimetres times heater length in millimetres divided by 100. Watt density = wattage divided by that area. The code selects insulation thickness of 1.5 mm below 8 W/cm2, 1.7 mm from 8 to below 9, and 2.0 mm at 9 or above. These are application rules, not independently validated universal design limits. [L03]')
para('The initial wire row is the first row whose inclusive wattage band contains the input. The code then evaluates subsequent rows. The pipe selection remains fixed while automatic core geometry is evaluated for each wire thickness. For SWG 22 to 32, the pitch pass threshold is 98 percent of twice the wire thickness. For SWG 33 to 45 it is twice the wire thickness. A released design requires engineering validation of these rules and operating conditions. [L03]')
h('Actual data findings',2)
table(['Finding','Observed evidence','Required review'],[
['Repeated rows','Nichrome SWG 32, 36, 42 and 44 have exact repeated technical values with different IDs','Confirm intentional alternatives or remove ambiguity through controlled master revision'],
['Different resistance for same gauge','Nichrome SWG 38 has 62.88 and 59.408; SWG 40 has 93.2 and 94 in the ohm column','Validate alloy, tolerance, supplier basis and intended selection key'],
['Overlapping bands','For example Nichrome 900 to 1049 W matches both SWG 24 and 25 bands','Document precedence; current first match is order dependent'],
['Uncovered Kanthal band','1591 to 1599 W is between the supplied 1590 maximum and 1600 minimum','Confirm intended band limits'],
['Gauge acceptance coverage','Kanthal rows include SWG 20 and 21; source pitch acceptance branches start at SWG 22','Verify intended behavior for high wattage starting rows'],
['Reference list meaning','Core and pipe values are hardcoded geometry references without quantities','Do not present them as actual available stock balances']],[116,205,195])

new('6 Calibration and document behavior')
h('Calibration result behavior',2)
para('The current calibration calculation uses observed error = device reading minus standard input. Allowed absolute error = absolute standard input multiplied by the entered claimed error percentage divided by 100. Each completed row passes when its absolute error is within that limit with a small numeric comparison tolerance. Error display is rounded to two decimals. The overall report is Pass only when every reading passes; otherwise it is Review. [L03]')
para('A zero standard input gives zero allowed error under this percentage of reading rule. The agreed tolerance basis must therefore be checked for each method. An absolute Celsius tolerance, percentage of full scale or uncertainty aware conformity rule cannot be assumed to match the current percentage of reading implementation.')
h('Performance result behavior',2)
para('Performance reports support absolute Celsius error or percentage error. Percentage error is observed minus reference divided by the absolute reference, multiplied by 100. A zero reference in percentage mode cannot be calculated. Completed reports use Pass or Fail; incomplete evaluation uses Pending. A linked calibration is required by the save validation. [L03 L04]')
h('Numbering and due dates',2)
para('Numbering uses browser sequence state and saved records, including manually entered sequence continuity. Backend save functions use locks for writing rows. This does not establish a globally unique controlled issue sequence across concurrent browsers. The proposed issue service must allocate unique numbers and retain the approved report revision. [L03 L04]')
para('The default calibration due date is one calendar year after the calibration date less one day. For 15 October 2026 this gives 14 October 2027. This is a software default; the interval must follow the actual instrument, contract and approved calibration programme. [L03]')
h('Required release additions',2)
para('Before controlled issue, add reference validity and scope checks, approved method revision, competence authorisation, customer agreed decision rule, uncertainty where applicable, independent review, issued revision retention, controlled amendment and restricted export. The workbook separates these proposed features from the existing report builder.')
h('Human resources document behavior',2)
para('Offer and appointment workflows generate documents and maintain confirmed or issued records. Appointments have their own sequence and four page format with compensation information. Selection, accepted terms, signed acknowledgement, employee ID, attendance, payroll processing and statutory outputs require separate records and controls. Template clauses and default gross amounts must be approved by the company before use. [L02-L04]')

new('7 Department coverage model')
para('Each profile below states purpose, process, feature behavior, important records, handoffs and acceptance criteria. Feature IDs match the companion register. Proposed functions should be mapped to the real organisation and may share staff. All features are proposed unless marked Present in source.')
table(['Code','Function','Features'],[[d['code'],d['name'],len(d['features'])] for d in D['departments']],[56,400,60])

for i,d in enumerate(D['departments'],1):
    new(f'7 {i} {d["name"]}')
    para(d['purpose'])
    para('<b>Process</b> '+escape(d['workflow']))
    for f in d['features']:
        badge=' <i>Present in source ['+escape(f['source'])+']</i>' if f['status']=='Present in source' else ''
        para('<b>'+f['id']+' '+escape(f['feature'])+'</b>'+badge+'<br/>'+escape(f['behavior']),'feature')
    para('<b>Records and fields</b> '+escape(', '.join(x.replace('_',' ') for x in d['fields']))+'.','small')
    para('<b>Measures</b> '+escape('; '.join(d['kpis']))+'.','small')
    para('<b>Handoffs</b> '+escape(d['handoffs']),'small')
    para('<b>Control</b> '+escape(d['control']),'small')
    para('<b>Acceptance</b> '+escape(d['acceptance']),'small')

new('8 End to end workflow model')
para('The six workflows describe the proposed handoffs between functions. They are not claims that every step is already implemented. Each step has an output record, a completion gate and an exception route in the companion workbook. A job changes state only after the defined prerequisite is satisfied.')
table(['Workflow','Trigger','Completion evidence'],[
['WF01 Enquiry to cash','Customer requests a custom heater','Approved design, material and production trail, accepted shipment, invoice and receipt'],
['WF02 Calibration','Customer requests instrument calibration','Identified item, valid standard, readings, reviewed issued report and custody closure'],
['WF03 Purchase to payment','Approved need for material or service','Approved PO, accepted receipt, matched invoice and reconciled payment'],
['WF04 Employee lifecycle','Approved vacancy','Accepted terms, joining, access, pay and eventual exit clearance'],
['WF05 Service and maintenance','Customer complaint or planned service','Diagnosis, approved work, actuals, test and customer acknowledgement'],
['WF06 Custom equipment project','Accepted project scope','Released designs, build tests, installation, site acceptance and handover pack']],[142,158,216])
h('Cross department record chain',2)
para('Customer ID links enquiry, quotation and sales order. The order links approved design revision, job, bill of materials, material movement, production actuals, inspection and equipment serial. Shipment and invoice link back to the accepted order. Service and calibration use the equipment or instrument identity and customer site. Employee IDs link authorised staff to work and approval records without exposing pay data to production users.')
h('Status and exception rules',2)
para('Use distinct business states such as draft, reviewed, approved, released, in progress, held, accepted, issued, superseded and closed where relevant. Keep the record\'s business state separate from pending sync, synced, failed or conflict. An apparent successful local save must not be reported as confirmed shared storage.')
para('A missing material lot, expired reference standard, failed test, unapproved cost or customer scope mismatch should create an explicit hold with an owner and next action. Deleting the exception or entering a manual Pass must not substitute for resolution evidence.')

for fid in ['WF01','WF02','WF03','WF04','WF05','WF06']:
    rows=[x for x in D['workflows'] if x[0]==fid]
    new('8 '+fid+' '+rows[0][1])
    for row in rows:
        para(f'<b>{row[2]} {escape(row[3])}</b><br/>{escape(row[4])}. Output: {escape(row[5])}. Gate: {escape(row[6])}. Exception: {escape(row[7])}.','feature')
    para('Suggested test: walk one representative case through every step, then repeat with one deliberately missing prerequisite. Confirm the normal record chain and the exception owner remain visible.','small')

new('9 Data architecture and records')
para(f'The companion dictionary contains {len(D["data"])} entries across current form payloads, reading records, backend index columns and proposed department records. Entries describe fields, not populated transaction records. A field may appear in both a form payload and a spreadsheet index because the representations serve different purposes.')
h('Core record relationships',2)
table(['Record group','Required identity and relationships','Owner'],[
['Organisation','Entity, site, department, user and role scope','Management and IT'],
['Commercial','Customer, contact, enquiry, quote revision, order and contract','Sales and Finance'],
['Technical','Product, drawing, BOM, routing, calculation and design revision','Engineering'],
['Supply and stock','Supplier, requisition, PO, receipt, lot, location and movement','Procurement and Stores'],
['Execution','Job, operation, equipment serial, actuals and inspection','Planning Production and Quality'],
['Calibration','Instrument, reference, method, readings, issue and amendment','Calibration and Quality'],
['Financial','Invoice, receipt, payment, account, period and job cost','Finance'],
['People','Candidate, employee, terms, attendance, pay and competence','HR and Payroll']],[104,306,106])
h('Data rules',2)
para('Use stable internal IDs independently from editable document numbers. Store units explicitly, distinguish blank from real zero, validate reference keys and retain effective revisions. Money needs currency and a defined tax basis. Dates need local business meaning, and event timestamps need a recorded time zone. Reject invalid or missing prerequisites rather than silently converting them to successful zero values.')
para('Separate the reference geometry list from live inventory. Track inventory by item, lot, location, status and quantity. Link exact design and master data revisions to issued work so later updates do not change the meaning of a historical result.')
h('Current payload and index design',2)
para('The existing backend uses a searchable sheet row plus JSON payload for each document. That can support the present document register, but a larger system needs validated relationships, revision history, access rules, attachment custody, backup, uniqueness and reconciliation. An approved design should define those requirements before choosing a replacement storage platform.')

new('10 Controls access and recovery')
para('The control register contains 20 requirements with owners, triggers, current evidence and observable acceptance conditions. P0 marks controls to resolve before broader use of sensitive records or controlled issue. This is a proposed implementation priority, not a measured company risk rating.')
for c in D['controls'][:10]:
    para('<b>'+c[0]+' '+escape(c[1])+'</b><br/>'+escape(c[4])+'. Test: '+escape(c[6])+'.','feature')
new('10 Controls continued')
for c in D['controls'][10:]:
    para('<b>'+c[0]+' '+escape(c[1])+'</b><br/>'+escape(c[4])+'. Test: '+escape(c[6])+'.','feature')
h('Suggested access boundaries',2)
para('Operators need released work and their assigned execution records. Engineers need design and technical masters. Calibration staff need instrument and reference data; reviewers need issue authority. HR and payroll need restricted personal and pay records. Finance needs commercial and accounting access. Managers need scoped review views. IT administrators require controlled maintenance access and reviewed activity. Confirm actual roles and segregation with the company.')

new('11 Worked examples and verification cases')
h('Illustrative heater calculation using a live wire value',2)
para('Example inputs are hypothetical: 1200 W, 230 V, heater diameter 14 mm, heater length 500 mm and extra resistance 5 percent. The Nichrome SWG 23 row in the live sheet supplies 3.728 in the ohm column, interpreted by the current code as ohms per metre. These inputs do not represent a customer order. [L03 G01]')
table(['Quantity','Calculation','Result'],[
['Base resistance','230 x 230 / 1200','44.0833 ohm'],
['Adjusted resistance','44.0833 x 1.05','46.2875 ohm'],
['Candidate wire length','46.2875 / 3.728','12.4162 m'],
['Heater area','pi x 14 x 500 / 100','219.9115 cm2'],
['Watt density','1200 / 219.9115','5.4567 W/cm2'],
['Insulation rule','Watt density below 8','1.5 mm in current app logic']],[135,230,151])
para('This example verifies electrical arithmetic only. Final gauge selection still requires the full geometry, pitch, thermal and application checks. The supplied wire master does not include an independently verified material certificate or temperature correction basis.')
h('Illustrative calibration and performance boundaries',2)
table(['Case','Inputs','Expected existing logic'],[
['Calibration within limit','Standard 100; device 100.8; tolerance 1 percent','Error 0.8; allowed 1; Pass'],
['Calibration outside limit','Standard 200; device 202.5; tolerance 1 percent','Error 2.5; allowed 2; Fail row and Review overall'],
['Calibration zero input','Standard 0; device 0.1; tolerance 1 percent','Allowed 0; Fail under current rule'],
['Performance percentage zero','Reference 0 in percentage mode','No calculable percentage; save needs completed valid results'],
['Performance absolute zero','Reference 0; observed 0.2; accuracy 0.5 Celsius','Error 0.2 Celsius; Pass']],[126,205,185])
para('The workbook contains the heater example as editable inputs and formulas. It also includes example input cells for baseline measurement without invented actual savings.')

new('12 Performance measurement and benefits')
para('The 72 proposed metrics cover all 24 functions. The register defines the population, formula, period and cautions. Actual baselines and targets remain Not supplied. Establish them from reconciled company data before reporting improvement.')
h('How to establish the baseline',2)
para('Choose a documented period and comparable product or service cohort. Record counts, actual labour time, elapsed turnaround, error or rework events and customer completion dates. Define start and finish timestamps, planned hold treatment and missing record rules. Preserve the baseline extracts and reconcile totals with the owning register.')
para('For the calculator, measure time from accepted input to reviewed design output, separately from prototype validation. For calibration, separate reading acquisition time, report preparation and independent review. For letters, separate document preparation from recruitment and onboarding lead time. A faster screen interaction is not by itself a shorter complete business cycle.')
h('Benefits calculation',2)
para('Hours released = eligible transaction count multiplied by verified minutes saved per transaction divided by 60. A cash saving requires a documented reduction in paid overtime, outsourced cost or another actual expense. Capacity released can be reported as capacity, with the assumptions and opportunity to use it stated. Do not equate all saved minutes with cash.')
para('Quality benefits should use actual avoided rework or claim cost, including the same cost basis before and after. Delivery improvement should compare matching due date cohorts. Report changes in product mix, staffing, workload and data coverage so the effect of automation is not overstated.')
h('Measurement ownership',2)
para('Process owners validate event definitions and record completeness. Finance validates cost and recognised financial effects. Management approves targets and review cadence. IT validates data refresh and duplicate prevention. Each metric should have an owner who can explain its calculation and missing data.')

new('13 Implementation sequence and acceptance')
para('The phases below are dependency based. No dates, project cost or staffing promise is assumed. Agree duration and resources after validating process variants, source data and deployment constraints.')
for phase in D['rollout']:
    para('<b>'+phase[0]+' '+escape(phase[1])+'</b><br/>Owner: '+escape(phase[2])+'. Work: '+escape(phase[3])+'. Exit evidence: '+escape(phase[4])+'.','feature')
h('Acceptance before expansion',2)
para('Run one custom heater order, one calibration issue, one purchase payment, one employee joining, one service repair and one custom equipment project through the connected record chain. Repeat with missing approvals, failed tests, expired standards, a changed design, a partial delivery and an offline save. The correct owner and hold must remain visible.')
para('For technical release, test simultaneous numbering, altered client payloads, access restrictions, browser upgrades, backup restoration and reconnect conflicts. Reconcile counts, IDs, revisions, values and custody references. An export succeeding or a dashboard showing a total does not prove the workflow is complete.')

new('14 Company data still required')
para('The following records are needed to validate the organisation, complete the actual company dataset and quantify outcomes. The workbook provides 26 requests with an editable owner, due date, evidence reference and collection status. Actual personal and pay records should be restricted to their authorised owners.')
for req in D['requests'][:13]:
    para('<b>'+req[0]+' '+escape(req[2])+'</b> '+escape(req[3])+'. Owner: '+escape(req[1])+'.','feature')
new('14 Company data continued')
for req in D['requests'][13:]:
    para('<b>'+req[0]+' '+escape(req[2])+'</b> '+escape(req[3])+'. Owner: '+escape(req[1])+'.','feature')
h('Completion standard',2)
para('An evidence complete company case study requires the actual structure and process owners, complete current product master, relevant internal registers and measured outcomes. This package provides the full proposed department coverage and all retrieved wire data while keeping outstanding factual records explicit. No claim is made that inaccessible or absent internal company data has been obtained.')

new('15 Sources and audit trail')
para('Public websites were reviewed on 15 October 2026. Company published descriptions are attributed to the company and do not establish independent verification. Local source observations describe the files reviewed on the same date. The live spreadsheet source is a connected read of the two visible tabs, not a modification.')
for s in D['sources']:
    para('<b>'+s[0]+' '+escape(s[1])+'</b> '+escape(s[2])+'.<br/>'+escape(s[3])+'<br/>'+escape(s[4])+'.','small')
para('Excluded identity match: similarly named IT, electrical contracting and overseas businesses were not used as evidence for this Baikampady company. The associated Electro Heat Systems website was included because the two company websites link to each other; ownership remains a data request.','small')

new('Appendix All retrieved wire records')
para('Values below reproduce the connected sheet rows. Thickness is used as millimetres and ohm is used as ohms per metre by the application. The wattage bounds are inclusive. No values have been corrected. Engineering must validate disputed rows before a controlled master revision. [G01 L03]')
table(['Material','ID','SWG','Thickness','ohm','minw W','maxw W'],[row[:-1] for row in D['wire_rows']],[90,37,42,86,83,89,89])
para('The spreadsheet register also contains the complete hardcoded geometry reference options. Those values have no on hand quantity and are not an inventory count.','small')

pdf_path=OUT/'Electro_Group_End_to_End_Case_Study.pdf'
report=Report(pdf_path)
report.multiBuild(story)
reader=PdfReader(str(pdf_path))
texts=[page.extract_text() for page in reader.pages]
info={'pages':len(reader.pages),'characters':sum(map(len,texts)),'text_by_page':[{ 'page':i+1,'characters':len(t),'first_line':t.splitlines()[0] if t else ''} for i,t in enumerate(texts)]}
(WORK/'pdf_qa.json').write_text(json.dumps(info,indent=2),encoding='utf-8')
assert all(len(t)>80 for t in texts),'Unexpected blank page'
for d in D['departments']:
    assert d['name'] in '\n'.join(texts)
print(json.dumps({'pdf':str(pdf_path),'pages':len(reader.pages),'characters':info['characters']}))
