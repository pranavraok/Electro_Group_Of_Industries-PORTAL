import fs from 'node:fs/promises';
import path from 'node:path';
import { Workbook, SpreadsheetFile } from '@oai/artifact-tool';

const root=path.resolve(import.meta.dirname,'..');
const work=import.meta.dirname;
const d=JSON.parse(await fs.readFile(path.join(work,'case_data.json'),'utf8'));
const out=path.join(root,'outputs','electro-group-case-study');
await fs.mkdir(out,{recursive:true});
const wb=Workbook.create();
const sheets={};
const red='#A91830', dark='#363A40';
const names=['Coverage','Features','Data dictionary','Workflows','Controls','KPIs','Data requests','Rollout','Worked examples','Product catalogue','Wire master','Geometry reference','Sources'];
for(const name of names){sheets[name]=wb.worksheets.add(name);sheets[name].showGridLines=false;}
function col(n){let s='';for(n++;n>0;n=Math.floor((n-1)/26)){s=String.fromCharCode(65+(n-1)%26)+s;}return s;}
function make(name,title,note,headers,rows,widths){
 const sh=sheets[name],last=col(headers.length-1),end=5+rows.length;
 sh.getRange(`A1:${last}${Math.max(end,7)}`).format.font={name:'Arial',size:10,color:'#202124'};
 sh.getRange('A2').values=[[title]];sh.getRange('A2').format.font={name:'Arial',size:15,bold:true,color:'#000000'};
 sh.getRange('A3').values=[[note]];sh.getRange('A3').format.font={name:'Arial',size:10,italic:true,color:'#5B6067'};
 sh.getRange('A3').format.wrapText=false;
 sh.getRange(`A5:${last}5`).values=[headers];
 sh.getRange(`A5:${last}5`).format={fill:dark,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:32,wrapText:true,horizontalAlignment:'center',verticalAlignment:'center'};
 sh.getRange(`A6:${last}${end}`).values=rows;
 sh.getRange(`A6:${last}${end}`).format.verticalAlignment='center';
 sh.getRange(`A6:${last}${end}`).format.wrapText=true;
 widths.forEach((w,i)=>sh.getRange(`${col(i)}1:${col(i)}${end}`).format.columnWidth=w);
 for(let i=0;i<rows.length;i++){
  const lines=Math.max(...rows[i].map((v,j)=>Math.ceil(String(v??'').length/Math.max(8,(widths[j]??20)-2))));
  sh.getRange(`A${i+6}:${last}${i+6}`).format.rowHeight=Math.max(25,Math.min(112,lines*13+10));
  if(i%2===1)sh.getRange(`A${i+6}:${last}${i+6}`).format.fill='#F5F6F8';
 }
 const tab=sh.tables.add(`A5:${last}${end}`,true,name.replaceAll(' ','')+'Table');
 tab.showFilterButton=true;
 sh.freezePanes.freezeRows(5);
 sh.freezePanes.freezeColumns(name==='Coverage'?2:1);
 return sh;
}
const featRows=d.features.map(f=>[f.id,f.department,f.feature,f.behavior,f.status,f.priority,f.owner,'Verify: '+f.behavior,f.source]);
make('Features','Department feature register','Present in source describes code presence. Proposed features require owner validation.',['Feature ID','Department','Feature','Expected behavior','Evidence status','Priority','Proposed owner','Acceptance scenario','Source IDs'],featRows,[14,43,34,64,23,11,43,64,18]);
const dictRows=d.data.map(row=>row);
make('Data dictionary','Current and proposed data fields','Field entries describe structure, not populated company transactions. Current and proposed records are distinct.',['Field ID','Entity or function','Field key','Business label','Data type','Unit','Required rule','Evidence status','Owner','Validation or interpretation','Source IDs'],dictRows,[16,43,31,34,22,31,32,23,43,68,16]);
make('Workflows','End to end operating workflows','All steps are proposed operating flow. Output, gate and exception must remain linked to the case ID.',['Flow ID','Workflow','Step','Responsible function','Action','Output record','Completion gate','Exception route','Status'],d.workflows,[12,39,9,29,55,42,48,46,28]);
make('Controls','Controls and acceptance tests','P0 requires resolution before broader controlled issue or sensitive record use. Priority is proposed.',['Control ID','Control','Owner','Trigger','Required behavior','Current evidence','Acceptance test','Priority','Source IDs'],d.controls,[14,35,27,26,57,60,60,11,22]);
make('KPIs','Department performance measures','Baselines and targets are not supplied. Define the period, exclusions and matching population before use.',['Metric ID','Department','Metric','Definition','Unit','Review cadence','Actual baseline','Approved target','Interpretation','Status'],d.kpis,[15,43,35,76,30,30,23,23,70,24]);
const requestRows=d.requests.map(r=>[...r.slice(0,6),'','',r[7],r[8]]);
make('Data requests','Company data collection register','Amber cells are editable owner, evidence, due date and status fields. Missing actuals have not been replaced with zeros.',['Request ID','Requested owner','Data area','Records needed','Purpose','Evidence received','Assigned owner','Due date','Collection status','Access class'],requestRows,[15,25,39,73,47,57,29,17,25,18]);
sheets['Data requests'].getRange(`F6:I${5+requestRows.length}`).format.fill='#FFF2CC';
sheets['Data requests'].getRange(`H6:H${5+requestRows.length}`).setNumberFormat('dd-mmm-yyyy');
sheets['Data requests'].getRange(`I6:I${5+requestRows.length}`).dataValidation={rule:{type:'list',values:['Not received','In progress','Part received','Received','Validated','Not applicable']}};
make('Rollout','Implementation phases and exit evidence','No schedule, project cost or staffing commitment is assumed. Assign after process and source validation.',['Phase','Scope','Proposed owner','Work','Exit evidence','Priority','Status'],d.rollout,[11,43,48,78,76,11,22]);
make('Product catalogue','Retrieved public catalogue entries','Entries may overlap across brands or categories. Not a complete current SKU or stock list.',['Entry ID','Published business','Category','Catalogue entry','Evidence type','Current price','Stock quantity','Source ID'],d.products,[15,27,28,54,29,22,22,15]);
make('Wire master','All retrieved live wire rows','Connected Google Sheet read on 15 Oct 2026. Preserve original values pending engineering review.',['Material','Row ID','SWG','Thickness mm','ohm column','Minimum W','Maximum W','Source ID'],d.wire_rows,[20,12,12,21,20,20,20,14]);
sheets['Wire master'].getRange('D6:E37').setNumberFormat('0.000');
const wire=sheets['Wire master'];
wire.getRange('A40').values=[['Engineering review findings']];wire.getRange('A40').format.font={name:'Arial',size:12,bold:true};
wire.getRange('A42:D42').values=[['Finding','Affected values','Interpretation','Action owner']];
wire.getRange('A42:D42').format={fill:dark,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:35,wrapText:true};
wire.getRange('A43:D48').values=[
 ['Repeated technical rows','Nichrome SWG 32, 36, 42, 44','Same technical values with different IDs; preserve until reviewed','Engineering'],
 ['Different same gauge resistance','Nichrome SWG 38 and 40','Confirm intended alloy supplier tolerance or variant key','Engineering'],
 ['Overlapping wattage bands','Nichrome SWG 24 and 25 overlap 900 to 1049 W','Initial selection uses first matching row; precedence matters','Engineering'],
 ['Uncovered wattage interval','Kanthal D 1591 to 1599 W','No initial matching row in live master','Engineering'],
 ['Pitch acceptance coverage','Kanthal D SWG 20 and 21','Code acceptance branches start at SWG 22; validate intended behavior','Engineering and IT'],
 ['Document register evidence','Only two wire tabs visible in connected sheet','Report and HR code exist; shared transaction data not established','IT and record owners']];
wire.getRange('A43:D48').format.wrapText=true;wire.getRange('A43:D48').format.rowHeight=140;
make('Geometry reference','Hardcoded engineering reference options','These options have no stock quantity and do not establish available inventory.',['Reference type','Outside diameter','Wall thickness','Unit','Interpretation','Source ID'],d.geometry,[37,23,23,12,57,15]);
sheets['Geometry reference'].getRange(`B6:C${5+d.geometry.length}`).setNumberFormat('0.0##');
make('Sources','Evidence and source register','Public sources and local project files reviewed on 15 Oct 2026. Live sheet scope is recorded separately.',['Source ID','Source','Type','Location','Coverage and limitations'],d.sources,[15,39,29,83,85]);

const cov=sheets.Coverage;
const summaryRows=d.departments.map(x=>[x.code,x.name,null,null,null,x.name+' lead','Awaiting owner confirmation']);
make('Coverage','Electro Group and Electrotech Services','24 functional areas. Source presence is distinct from live adoption. Data assessed as of 15 Oct 2026.',['Code','Department function','Features','In source','Proposed','Proposed owner','Organisation validation'],summaryRows,[12,49,14,14,14,49,38]);
cov.tabColor=red;
const fend=5+featRows.length;
cov.getRange('C6:E29').formulas=d.departments.map((x,i)=>[
`=COUNTIFS('Features'!$B$6:$B$${fend},B${i+6})`,
`=COUNTIFS('Features'!$B$6:$B$${fend},B${i+6},'Features'!$E$6:$E$${fend},"Present in source")`,
`=COUNTIFS('Features'!$B$6:$B$${fend},B${i+6},'Features'!$E$6:$E$${fend},"Proposed")`]);
cov.getRange('B31:E31').values=[['Total',null,null,null]];
cov.getRange('C31:E31').formulas=[['=SUM(C6:C29)','=SUM(D6:D29)','=SUM(E6:E29)']];
cov.getRange('B31:E31').format.font={name:'Arial',size:10,bold:true};
cov.getRange('C6:E31').setNumberFormat('0');
cov.getRange('C6:E31').format.horizontalAlignment='right';
cov.getRange('A34').values=[['Companion report covers the current app, proposed departments, workflows, controls, gaps and evidence.']];
cov.getRange('A35').values=[['Company revenue, headcount, operating volumes and achieved savings require internal records.']];
cov.getRange('A36').values=[['Live sheet: 23 Nichrome rows and 9 Kanthal D rows. Only two wire tabs were visible.']];

const ex=sheets['Worked examples'];
ex.getRange('A1:F45').format.font={name:'Arial',size:10};ex.getRange('A1:A45').format.columnWidth=43;ex.getRange('B1:B45').format.columnWidth=23;ex.getRange('C1:C45').format.columnWidth=17;ex.getRange('D1:D45').format.columnWidth=65;
ex.getRange('A2').values=[['Illustrative calculations and baseline measurement']];ex.getRange('A2').format.font={name:'Arial',size:15,bold:true};
ex.getRange('A3').values=[['Hypothetical heater inputs use a live wire resistance. This is not a released customer design.']];
ex.getRange('A5:D5').values=[['Input or result','Value','Unit','Interpretation']];
ex.getRange('A6:D11').values=[['Input power',1200,'W','Hypothetical'],['Input voltage',230,'V','Hypothetical'],['Heater diameter',14,'mm','Hypothetical'],['Heater length',500,'mm','Hypothetical'],['Extra resistance',0.05,'percent','Hypothetical'],['Candidate wire resistance',null,'ohm/m','Nichrome row ID 2, SWG 23 in live sheet']];
// Source order: row 1 of data is Excel row 6, so Nichrome ID 2 is row 7.
ex.getRange('B11').formulas=[["='Wire master'!E7"]];
ex.getRange('A13:D18').values=[['Base resistance',null,'ohm','Voltage squared divided by power'],['Adjusted resistance',null,'ohm','Base multiplied by one plus extra resistance'],['Candidate wire length',null,'m','Adjusted resistance divided by resistance per metre'],['Heater surface area',null,'cm2','Pi times diameter times length divided by 100'],['Watt density',null,'W/cm2','Power divided by surface area'],['App insulation rule',null,'mm','Below 8: 1.5; 8 to below 9: 1.7; 9 or more: 2']];
ex.getRange('B13:B18').formulas=[['=B7^2/B6'],['=B13*(1+B10)'],['=B14/B11'],['=PI()*B8*B9/100'],['=B6/B16'],['=IF(B17>=9,2,IF(B17<8,1.5,1.7))']];
ex.getRange('B10').setNumberFormat('0.0%');ex.getRange('B11:B18').setNumberFormat('0.0000');
ex.getRange('A21:D21').values=[['Baseline input or result','Value','Unit','Interpretation']];
ex.getRange('A22:D28').values=[['Eligible transaction count',null,'count','Enter actual count for the defined cohort'],['Baseline preparation time',null,'minutes/transaction','Enter measured actual; excludes unrelated waiting time'],['New preparation time',null,'minutes/transaction','Enter measured actual for comparable work'],['Net minutes released',null,'minutes/transaction','Negative value means time increased'],['Hours released',null,'hours','Capacity measure; does not automatically equal cash saving'],['Baseline cohort and period','','text','Describe matching population and data coverage'],['Validation owner','','text','Process owner who validates the evidence']];
ex.getRange('B25').formulas=[['=IF(OR(B23="",B24=""),"Not supplied",B23-B24)']];
ex.getRange('B26').formulas=[['=IF(OR(B22="",B23="",B24=""),"Not supplied",B22*B25/60)']];
ex.getRange('B22:B24').format.fill='#FFF2CC';ex.getRange('B27:B28').format.fill='#FFF2CC';
for(const r of [5,21])ex.getRange(`A${r}:D${r}`).format={fill:dark,font:{name:'Arial',size:10,bold:true,color:'#FFFFFF'},rowHeight:30,wrapText:true};
ex.getRange('A5:D28').format.wrapText=true;ex.getRange('A6:D28').format.rowHeight=34;

// Reader editable statuses, priorities and evidence remain ordinary cells.
sheets.Features.getRange(`E6:E${fend}`).dataValidation={rule:{type:'list',values:['Present in source','Proposed']}};
sheets.Features.getRange(`F6:F${fend}`).dataValidation={rule:{type:'list',values:['P0','P1','P2']}};
wb.recalculate();
console.log((await wb.inspect({kind:'table',range:'Coverage!B31:E31',include:'values,formulas',tableMaxRows:1,tableMaxCols:4,maxChars:1000})).ndjson);
console.log((await wb.inspect({kind:'match',searchTerm:'#REF!|#DIV/0!|#VALUE!|#NAME\\?|#N/A|#NUM!|#NULL!|#SPILL!|#CALC!',options:{useRegex:true,maxResults:20},maxChars:1000})).ndjson);
const sums=cov.getRange('C31:E31').values[0];
if(sums[0]!==192||sums[1]!==21||sums[2]!==171)throw Error('Coverage count reconciliation failed: '+JSON.stringify(sums));
const vals=ex.getRange('B13:B18').values.flat();
if(Math.abs(vals[0]-44.0833333333)>1e-7||Math.abs(vals[2]-46.2875/3.728)>1e-7)throw Error('Heater example did not reconcile');
if(ex.getRange('B26').values[0][0]!=='Not supplied')throw Error('Missing baseline must remain unavailable');
// Change inputs, verify dependency recalculation, then restore to original values.
ex.getRange('B22:B24').values=[[100],[20],[15]];
if(Math.abs(ex.getRange('B26').values[0][0]-100*5/60)>1e-9)throw Error('Baseline calculation response failed');
ex.getRange('B22:B24').values=[[null],[null],[null]];
ex.getRange('B6').values=[[1000]];
if(Math.abs(ex.getRange('B13').values[0][0]-52.9)>1e-8)throw Error('Electrical dependency response failed');
ex.getRange('B6').values=[[1200]];
wb.recalculate();
const previewFiles=[];
const selectedPreviews=process.env.CASE_QA_SHEETS?process.env.CASE_QA_SHEETS.split(','):names;
for(const name of selectedPreviews){
 const sh=sheets[name];const n=name==='Worked examples'?4:(name==='Coverage'?7:sh.getUsedRange().values[4].length);
 const range=name==='Worked examples'?'A1:D28':name==='Coverage'?'A1:G36':`A1:${col(n-1)}12`;
 const img=await wb.render({sheetName:name,range,scale:1,format:'png'});
 const filename=path.join(work,'preview_'+name.replaceAll(' ','_')+'.png');
 await fs.writeFile(filename,new Uint8Array(await img.arrayBuffer()));previewFiles.push(filename);
}
if(selectedPreviews.includes('Wire master')){
 const findingsImage=await wb.render({sheetName:'Wire master',range:'A40:D48',scale:1,format:'png'});
 await fs.writeFile(path.join(work,'wire_findings.png'),new Uint8Array(await findingsImage.arrayBuffer()));
}
const result=await SpreadsheetFile.exportXlsx(wb);
await result.save(path.join(out,'Electro_Group_Department_Features_and_Data.xlsx'));
await fs.writeFile(path.join(work,'workbook_qa.json'),JSON.stringify({sheets:names.length,featureTotal:sums[0],sourceFeatures:sums[1],proposedFeatures:sums[2],heaterValues:vals,previewFiles},null,2));
console.log(JSON.stringify({workbook:path.join(out,'Electro_Group_Department_Features_and_Data.xlsx'),sheets:names.length,features:d.features.length,dataFields:d.data.length}));
