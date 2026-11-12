from pathlib import Path
import json,re,math,hashlib
from html.parser import HTMLParser

ROOT=Path(__file__).resolve().parents[1]
WORK=Path(__file__).resolve().parent
DATE='15 October 2026'
html=(ROOT/'index.html').read_text(encoding='utf-8')
js=(ROOT/'script.js').read_text(encoding='utf-8')
backend=(ROOT/'google-sheets/Code.gs').read_text(encoding='utf-8')
class FieldsParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.fields=[]; self.label=''; self.in_label=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=='label': self.in_label=True; self.label=''
        if any(k.startswith('data-') and k.endswith('-field') for k in a):
            self.fields.append((tag,a,self.label.strip()))
    def handle_endtag(self,tag):
        if tag=='label': self.in_label=False
    def handle_data(self,text):
        if self.in_label: self.label+=text
parser=FieldsParser(); parser.feed(html)

sources=[
['S01','Company business profile','Public company statement','https://electrotechind.in/','Heating and packaging activities; not audited performance'],
['S02','Electrotech about','Public company statement','https://electrotechind.in/about/','Manufacturing and testing statements; no independent certification verification'],
['S03','Electrotech services','Public company statement','https://electrotechind.in/our-services/','Repair and calibration; website says servicing since 1995'],
['S04','Electrotech contact','Public company statement','https://electrotechind.in/contact-us/','Baikampady address, public business phone and email'],
['S05','Packaging machinery catalogue','Public catalogue','https://electrotechind.in/product-category/packaging-machineries/','12 of 14 listed items accessible; page two unavailable'],
['S06','Plastic processing catalogue','Public catalogue','https://electrotechind.in/product-category/plastic-processing-equipment/','Three catalogue entries'],
['S07','Heating equipment catalogue','Public catalogue','https://electrotechind.in/product-category/heating-equipment/','Seven catalogue entries'],
['S08','Controllers and panels catalogue','Public catalogue','https://electrotechind.in/product-category/temperature-controllers-panel-box/','Three catalogue entries'],
['S09','Sensors catalogue','Public catalogue','https://electrotechind.in/product-category/thermocouples-sensors/','One category entry; not a complete sensor SKU list'],
['S10','Packaging materials catalogue','Public catalogue','https://electrotechind.in/product-category/packaging-materials/','Three catalogue entries'],
['S11','Customized machines catalogue','Public catalogue','https://electrotechind.in/product-category/customized-machines/','Six catalogue entries'],
['S12','Electro Heat Systems profile','Public company statement','https://electroheatsystems.in/','Reciprocal website links establish association, not legal ownership'],
['S13','Electro Heat Systems about','Public company statement','https://electroheatsystems.in/about/','Manufacturing since 1998 and listed test types are company claims'],
['S14','Electro Heat Systems catalogue','Public catalogue','https://electroheatsystems.in/products/','15 catalogue entries; no prices or capacity verified'],
['L01','Project overview','Local source review','readme.md','Source inventory; not a live deployment test'],
['L02','Application interface','Local source review','index.html','Navigation, form fields and defaults'],
['L03','Application logic','Local source review','script.js','Calculation rules, registers, exports and local storage'],
['L04','Spreadsheet backend','Local source review','google-sheets/Code.gs','Routes, table headers, validation and locking'],
['L05','Backend setup guide','Local source review','google-sheets/README.md','Deployment instructions and access limitations'],
['L06','Installable application','Local source review','service-worker.js and manifest.webmanifest','App shell caching and install settings'],
['A01','Operating model recommendations','Analysis','Case study department and workflow design','Proposed functions; actual organisation and policies require validation'],
]

# Feature syntax: label | expected behavior | evidence status | evidence source
departments=[]
def dept(code,name,purpose,workflow,features,fields,kpis,handoffs,control,acceptance):
    parsed=[]
    for line in features.strip().split('\n'):
        bits=line.strip().split('|')
        label,behavior=bits[:2]
        status=bits[2] if len(bits)>2 else 'Proposed'
        source=bits[3] if len(bits)>3 else 'A01'
        parsed.append({'id':f'{code}-{len(parsed)+1:02d}','department':name,'feature':label.strip(),'behavior':behavior.strip(),'status':status.strip(),'source':source.strip(),'priority':'P0' if label.startswith(('Identity','Access','Release','Traceability','Approval')) else 'P1','owner':name+' lead','acceptance':acceptance})
    departments.append(dict(code=code,name=name,purpose=purpose,workflow=workflow,features=parsed,fields=fields.split(';'),kpis=kpis.split(';'),handoffs=handoffs,control=control,acceptance=acceptance))

dept('GOV','Management and strategy','Own business priorities, accountability, budgets and review decisions across the confirmed study scope.',
'Set plan, approve resources, review exceptions, assign actions and verify closure.',
'''Operations dashboard|Display calibration counts, passes, due soon, heater runs and HR/performance counts.|Present in source|L02 L03
Business unit register|Separate legal entities, sites, business lines, authorised signatories and intercompany relationships.
Annual operating plan|Record sales, margin, production capacity and cash assumptions with accountable owners.
Budget approvals|Route spending and capital requests against a documented authority matrix.
Balanced performance review|Compare agreed targets with reconciled actuals and show period and data coverage.
Action register|Track decisions, owners, target dates, dependencies and closure evidence.
Risk register|Maintain operational, customer, supplier, safety and technology risks with mitigations.
Management review pack|Compile overdue commitments, quality trends, cash exposure and improvement decisions.''',
'entity_id;site_id;business_line;period;budget_version;target_value;actual_value;action_owner;action_due_date;risk_owner;decision_reference',
'Action closure on time;Budget variance;Operating margin',
'Finance supplies reconciled results; all department leads own action closure.',
'Reviewers approve changes to targets and retain the previous plan version.',
'A period review names a single owner for every unresolved action and links each displayed actual to its source.')

dept('MKT','Marketing and business development','Connect the published product and service portfolio to qualified enquiries and repeat business.',
'Maintain product content, record campaign response, qualify demand and hand accepted leads to sales.',
'''Product content library|Maintain approved product families, specifications, application notes, images and revision owners.
Enquiry capture|Capture web, telephone, walk in, dealer and event enquiries with consent and source.
Campaign register|Record channel, audience, spend, response and qualified enquiry outcome.
Lead qualification|Classify application, location, estimated need and purchase timing before assignment.
Customer segmentation|Group accounts by application, service needs, geography and purchasing history.
Demonstration planning|Schedule equipment demonstrations and record requirements and follow up.
Partner register|Maintain dealer, referral and industry partner contacts and agreed responsibilities.
Content approval|Check claims, specifications and image rights before material is published.''',
'campaign_id;lead_id;lead_source;product_family;application;region;consent_status;campaign_cost;qualified_date;assigned_salesperson;content_revision',
'Qualified lead conversion;Cost per qualified lead;Enquiry response time',
'Sales accepts qualified leads; engineering approves technical content; finance verifies campaign costs.',
'Use approved performance claims and keep a recorded basis for public product specifications.',
'A new enquiry retains its source and owner through qualification and appears once in the sales handoff.')

dept('SAL','Sales and customer relationship management','Own customer requirements and commercial commitments from enquiry to accepted order.',
'Register enquiry, assess application, obtain technical costing, issue quotation, negotiate and confirm order.',
'''Customer reuse|Reuse customer names and addresses across calibration and performance forms.|Present in source|L03
Customer account master|Use stable customer IDs, contacts, billing and delivery addresses and account status.
Opportunity pipeline|Track stage, next action, expected value, product line and loss reason.
Requirement capture|Record voltage, power, temperature, dimensions, environment, throughput and service scope as applicable.
Quotation follow up|Manage quotation revisions, expiry, negotiation and promised response dates.
Sales order review|Compare customer purchase order with accepted technical and commercial terms.
Credit and advance check|Obtain finance clearance or approved exception before order release.
Customer commitment history|Record changes to quantity, specification, price and delivery promise with approval.''',
'customer_id;contact_id;enquiry_id;opportunity_id;quotation_id;quotation_revision;customer_po;order_id;delivery_commitment;payment_terms;credit_clearance',
'Quote win rate;Enquiry to quotation time;On time customer commitment',
'Engineering checks feasibility; estimation owns cost; planning receives approved order; finance clears credit.',
'Do not convert an unapproved specification or quotation into a production instruction.',
'One accepted order links the customer requirement, quotation revision, purchase order and finance clearance.')

dept('EST','Estimation and commercial costing','Produce traceable costs and prices for custom heaters, machines, service work and consumables.',
'Receive scope, choose costing basis, price material and labour, review margin and release quotation.',
'''Material costing|Calculate cost from approved bill of materials, units, scrap allowance and supplier price date.
Labour costing|Estimate operation hours and approved labour rates by work centre or service skill.
Overhead allocation|Apply an approved basis and keep overhead separate from direct cost.
Outsourcing estimates|Include machining, treatment, bought out panels or other subcontract scope.
Service estimate|Separate diagnosis, travel, spares, labour and exclusions.
Margin review|Show net sales and cost basis before discount approval.
Quotation revision control|Keep superseded prices and scope changes attached to the opportunity.
Estimate versus actual|Compare completed job material, labour and rework with the accepted estimate.''',
'estimate_id;revision;order_id;bom_revision;material_cost;labour_hours;labour_rate;overhead_basis;subcontract_cost;quoted_net_value;discount_approval',
'Estimate variance;Quoted gross margin;Quotation turnaround time',
'Procurement supplies prices; engineering supplies design; finance approves rates and commercial exceptions.',
'Use dated rate versions and disclose exclusions; approved price cannot be silently replaced.',
'A reviewer can reconstruct a quotation from its quantities, rates, version and approved margin.')

dept('ENG','Engineering and research development','Turn customer needs into approved and repeatable designs across heater and equipment applications.',
'Review specification, calculate design, verify constraints, release drawing and revise through change control.',
'''Heater electrical calculation|Calculate base resistance and adjusted resistance from wattage, voltage and extra resistance.|Present in source|L03
Material selection|Choose Nichrome or Kanthal D and load the corresponding wire data.|Present in source|L02 L03
Geometry and gauge selection|Evaluate pipe, insulation, core diameter, wire length, turns and pitch against implemented rules.|Present in source|L03
Manual design overrides|Allow manual pipe and core inputs alongside automatic selections.|Present in source|L02 L03
Wire master editing|Validate numeric wire rows and require backend administrator validation for writes.|Present in source|L03 L04
Design package release|Link calculation snapshot, drawing, bill of materials and approved revision to a job.
Engineering change control|Assess stock, work in progress, customer approval and cost impact before changing a released design.
Prototype validation|Record thermal, electrical, mechanical and application test evidence against an agreed plan.''',
'design_id;design_revision;material;wattage_W;voltage_V;heater_od_mm;heater_length_mm;core_length_mm;pipe_od_mm;pipe_wall_mm;core_od_mm;extra_resistance_pct;swg;wire_ohm_per_m;wire_length_m;turns;pitch_mm;watt_density_W_cm2;approved_by',
'Design release lead time;Design change after release;Prototype first pass rate',
'Sales supplies operating conditions; procurement confirms available material; planning uses released revision.',
'Application rules are company logic and require engineering validation for actual operating conditions.',
'A released design reproduces its inputs, wire master version, calculation results, assumptions and reviewer approval.')

dept('PPC','Production planning and control','Translate accepted demand into feasible jobs, material availability and dated work.',
'Check order and design readiness, explode materials, allocate capacity, schedule operations and monitor completion.',
'''Order readiness check|Verify accepted specification, approved drawing, credit clearance and promised date.
Job creation|Assign a unique production or service job ID linked to the sales order.
Material requirements|Calculate component demand from approved quantities, yield and available stock.
Capacity planning|Reserve work centres, skills and bottleneck time using current calendars.
Operation scheduling|Sequence winding, fabrication, assembly and testing with due dates.
Work in progress visibility|Show job status, completed quantity, waiting reason and responsible department.
Shortage escalation|Assign purchase, substitution or rescheduling actions with approval.
Completion reconciliation|Close only after material, labour, inspection and finished quantity reconcile.''',
'job_id;order_id;design_revision;planned_quantity;route_id;work_centre;planned_start;planned_finish;capacity_hours;material_shortage;completed_quantity;closure_date',
'Schedule adherence;Work in progress age;Material ready at planned start',
'Stores reserves stock; procurement resolves shortages; production reports actual progress; QA releases output.',
'Changes to priority must show their effect on other committed orders.',
'A planner can identify the current operation, shortage owner and next promised event for each open job.')

dept('WND','Heater production and winding','Execute approved heater designs with lot traceability, measured geometry and accountable production records.',
'Receive job and materials, verify setup, wind coil, assemble heater, inspect and transfer with recorded actuals.',
'''Calculation use|View calculated wire gauge, length, turns, pitch and selected geometry.|Present in source|L02 L03
Controlled job traveller|Record job, drawing revision, operation sequence and required inspection points.
Wire lot issue|Link issued alloy, SWG, supplier lot, length and unused return to the job.
Setup verification|Record machine, mandrel, core, pitch setting and first piece approval.
Winding progress|Record operator, quantity, start and finish times and interruptions.
In process inspection|Record resistance, dimensions and other approved checks with instrument identity.
Scrap and rework|Capture rejected quantity, recoverable material, reason and authorised disposition.
Production transfer|Move accepted quantities to assembly or QA with traceable acceptance.''',
'job_id;wire_lot;wire_swg;wire_length_issued_m;operator_id;machine_id;setup_revision;actual_turns;actual_pitch_mm;actual_resistance_ohm;scrap_quantity;inspection_reference',
'First pass yield;Wire utilisation;Winding cycle time',
'Engineering owns design; stores owns issue and return; QA owns acceptance.',
'A calculator result supports setup; manufacturing release needs a reviewed design and inspection evidence.',
'One finished heater traces back to its design revision, wire lot, operator and actual inspection results.')

dept('FAB','Mechanical fabrication and assembly','Build frames, ovens, furnaces, conveyors and custom equipment against controlled drawings.',
'Release fabrication drawings, cut and form parts, join and finish, assemble and inspect.',
'''Drawing distribution|Make the current approved fabrication revision available at the work centre.
Material identity|Track sheet, tube and bought out part specifications and supplier evidence.
Cutting and forming records|Record sizes, work orders and material utilisation where needed.
Joining process records|Record applicable joining procedure, person and inspection evidence.
Assembly bill of materials|Verify fitted components against the approved assembly list.
Dimensional inspection|Record critical fits, enclosure dimensions and assembly clearances.
Subcontract tracking|Track material sent out, expected return and inspection on receipt.
Assembly release|Record incomplete items and prevent transfer before accepted closure.''',
'fabrication_job_id;drawing_revision;material_grade;material_lot;part_id;assembly_id;subcontract_reference;critical_dimension;inspection_result;fitment_check;release_reference',
'Fabrication rework rate;Assembly completion on time;Subcontract turnaround',
'Engineering releases drawings; procurement buys parts; QA signs inspection; projects receives finished equipment.',
'Approved substitutions and drawing revisions must reach every affected assembly.',
'The assembled equipment matches its bill of materials and has recorded results for all mandatory inspection points.')

dept('CTL','Electrical controls and automation','Manage electrical panels, temperature controls, sensors and process automation deliverables.',
'Define control philosophy, approve schematics, build panel, configure software and verify operation.',
'''Electrical drawing control|Version schematics, wiring schedules and panel layout against the equipment job.
Panel component register|Record controller, relay, switchgear and sensor part numbers and ratings.
Software configuration|Version PLC, HMI or controller configuration when used in the project.
Sensor specification|Record thermocouple or RTD type, range, construction and connection requirements.
Wiring inspection|Verify terminations, identification and schematic compliance with recorded results.
Functional sequence test|Test interlocks, alarms and operating modes against an approved procedure.
Configuration backup|Retain released firmware, parameters and recovery instructions with access control.
Panel handover|Provide approved drawings, test records, manuals and spare parts information.''',
'panel_id;job_id;schematic_revision;controller_model;sensor_type;sensor_range;configuration_version;software_backup_ref;test_procedure;alarm_test_result;handover_revision',
'Panel first pass acceptance;Configuration revision defects;Functional test closure time',
'Engineering approves logic; stores issues components; QA reviews tests; commissioning verifies on site.',
'Safety functions and electrical ratings require the assigned qualified engineering reviewer.',
'The delivered panel has an approved schematic and recoverable configuration matching the tested version.')

dept('BUY','Procurement and vendor management','Acquire approved materials and services with traceable price, quality, lead time and receipt controls.',
'Receive requisition, obtain quotations, select approved supplier, approve order, expedite and resolve receipt issues.',
'''Supplier master|Maintain supplier identity, contacts, approved categories and assessment evidence.
Purchase requisition|Link requested material and need date to job, stock policy or approved expense.
Supplier quotation comparison|Compare price, specification, lead time, tax basis and payment terms.
Purchase order approval|Route commitment by value and authority before issue.
Delivery follow up|Track supplier confirmations, partial deliveries and revised dates.
Supplier quality actions|Link rejected receipts to replacement, credit and corrective action.
Subcontract purchase|Specify supplied material, expected work, inspection and return obligations.
Supplier performance|Review on time delivery, accepted quantity and unresolved corrective actions.''',
'supplier_id;requisition_id;job_id;rfq_id;quotation_reference;purchase_order_id;item_id;quantity;unit;promised_date;approved_price;supplier_lot',
'Supplier on time delivery;Supplier rejection rate;Purchase cycle time',
'Planning requests quantities; engineering approves specifications; stores receives; finance matches invoices.',
'Separate requisition, purchase approval, receipt and payment responsibilities where staffing permits.',
'A purchase invoice can be traced to approved order, actual receipt and accepted or rejected quantity.')

dept('INV','Stores and inventory','Protect material identity and maintain quantities by item, location, lot and stock status.',
'Receive, inspect or quarantine, locate, reserve, issue, return, count and reconcile stock.',
'''Pipe and core reference lists|Use hardcoded stock size options to guide heater geometry selection.|Present in source|L03
Item master|Assign item IDs, specifications, units, conversion rules and purchasing/stock categories.
Goods receipt|Record supplier delivery, purchase order, quantity and lot evidence.
Quarantine control|Keep uninspected, rejected and usable quantities distinct.
Material reservation|Allocate quantities to jobs without silently reducing physical stock.
Issue and return|Post material transactions with job, person, time and reason.
Cycle counting|Record counted quantity, difference and independent adjustment approval.
Reorder planning|Use approved lead time, safety stock and demand assumptions for replenishment.''',
'item_id;warehouse_id;bin_id;lot_id;stock_status;receipt_id;movement_id;job_id;quantity;unit;reservation_id;count_reference;adjustment_approval',
'Inventory record accuracy;Stockout incidents;Slow moving stock value',
'Procurement owns order; QA releases quarantined stock; production acknowledges issue; finance reconciles value.',
'Hardcoded size lists describe options; they do not prove available quantities or a warehouse balance.',
'For each lot, opening quantity plus receipts and returns less issues and approved adjustments equals closing stock.')

dept('QUA','Quality assurance and inspection','Control product conformance, nonconformities and release using approved plans and retained evidence.',
'Define inspection plan, inspect incoming and in process work, test finished output, resolve deviations and approve release.',
'''Inspection plan|Define characteristics, method, sample basis and acceptance rule by product and revision.
Incoming inspection|Record material checks and supplier evidence before stock release.
In process hold points|Require approved checks before irreversible or downstream operations.
Final test record|Record resistance, insulation, electrical and dimensional tests applicable to the approved product plan.
Nonconformity register|Capture requirement, observed condition, affected lots and immediate containment.
Corrective action|Assign root cause, action, verification and effectiveness review.
Release authorisation|Keep final acceptance distinct from data entry and production completion.
Quality document control|Retain approved procedures, revisions and product release evidence.''',
'inspection_id;job_id;product_id;plan_revision;characteristic;measured_value;unit;acceptance_limit;instrument_id;ncr_id;disposition;release_authoriser',
'First pass yield;Cost of poor quality;Corrective action overdue',
'Engineering sets requirements; production contains defects; stores controls status; dispatch checks release.',
'Published test descriptions are company statements; actual procedures, limits and records need company validation.',
'Dispatch is blocked when a mandatory characteristic fails or a required inspection record is missing.')

dept('CAL','Calibration and metrology','Manage traceable instrument and equipment results, review and recalibration commitments.',
'Identify instrument and method, confirm reference validity, record readings, evaluate, review and issue controlled report.',
'''Calibration report builder|Capture customer, instrument, conditions, reference standard, readings and signatory fields.|Present in source|L02 L03
Automatic error evaluation|Calculate observed minus standard and compare absolute error with percentage based allowed error.|Present in source|L03
Report numbering and due date|Generate sequence and default annual due date while permitting relevant edits.|Present in source|L03
Calibration register and export|Search, view, edit, print and export stored reports to CSV.|Present in source|L03
Linked performance report|Reuse calibration context and evaluate error in Celsius or percentage with separate register.|Present in source|L03 L04
Reference standard register|Manage standard identity, certificate, scope, expiry and out of tolerance impact.
Report review and revision|Add independent authorisation, issued version retention and superseded report status.
Uncertainty and decision rule|Record applicable uncertainty, tolerance basis and agreed conformity decision rule.''',
'instrument_id;report_id;report_no;customer_id;calibration_date;due_date;standard_id;standard_certificate;standard_validity;method_revision;reference_value;observed_value;error;error_unit;tolerance_basis;uncertainty;decision_rule;reviewer;issued_revision',
'Calibration turnaround;Overdue instruments;Report amendment rate',
'Service receives equipment; sales agrees scope; QA reviews method; finance invoices accepted work.',
'Traceability wording on the public website does not establish the company is an accredited laboratory.',
'A report links valid reference evidence, complete readings, the chosen decision rule and its authorised issued revision.')

dept('PRJ','Projects installation and commissioning','Deliver approved equipment and custom projects through site readiness, installation and customer acceptance.',
'Confirm scope, plan milestones, check site readiness, install, test, resolve punch items and obtain handover.',
'''Project register|Link equipment, customer, order, project owner, milestones and budget.
Scope baseline|Record deliverables, exclusions, interfaces and customer responsibilities.
Site readiness|Confirm utilities, access, foundations and agreed operating conditions.
Resource scheduling|Assign competent people, travel, tools and required test equipment.
Installation checklist|Record installation observations and completion against the approved plan.
Commissioning results|Capture operating tests, settings and deviations using the agreed acceptance procedure.
Change and punch list|Approve additional scope and record remaining issues before handover.
Customer acceptance pack|Retain signed acceptance, training, manuals, spares and warranty start reference.''',
'project_id;order_id;site_id;equipment_serial;project_owner;milestone;planned_date;actual_date;site_readiness;punch_item;change_order;customer_acceptance',
'Milestone adherence;Project cost variance;Punch list closure time',
'Sales owns scope; engineering owns drawings; dispatch moves equipment; service receives the installed base.',
'Customer acceptance and commercial closure require explicit evidence for agreed conditions.',
'The project closes only when acceptance requirements and authorised residual actions are recorded.')

dept('SRV','Service repair and annual maintenance','Maintain the customer installed base and turn service requests into diagnosed, repaired and accepted work.',
'Log complaint, triage, schedule, diagnose, estimate, authorise repair, test and close with customer acknowledgement.',
'''Installed equipment register|Maintain model, serial, customer site, commissioning and warranty references.
Service ticket|Record reported symptom, urgency, contact, application and safe access needs.
Technician assignment|Match skill, location, availability and tool or spare requirements.
Diagnosis record|Record observed failure, evidence, suspected cause and recommended work.
Repair authorisation|Obtain customer approval or approved warranty decision before chargeable work.
Spares and labour capture|Post consumed parts, travel and actual hours to the service job.
Repair test and closure|Record post repair checks and customer acknowledgement.
Maintenance contracts|Schedule agreed visits, entitlements, renewal dates and excluded work.''',
'ticket_id;equipment_serial;customer_site;reported_symptom;priority;technician_id;diagnosis;repair_approval;spare_issue;labour_hours;warranty_decision;closure_ack;contract_id',
'First response time;First visit fix rate;Repeat complaint rate',
'Sales confirms contract; stores supplies spares; calibration handles reports; finance bills authorised work.',
'Keep warranty entitlement and chargeable scope visible before technician work is invoiced.',
'A closed ticket contains diagnosis, approved scope, actual work, test evidence and customer acknowledgement.')

dept('LOG','Dispatch logistics and delivery','Move released goods with the correct documents, packaging, custody and delivery evidence.',
'Confirm release and commercial clearance, pack, prepare documents, dispatch, obtain delivery and resolve discrepancies.',
'''Dispatch readiness|Check quality release, customer address, quantity and required finance clearance.
Packing checklist|Verify product protection, identification, accessories and document pack.
Shipment identity|Assign shipment ID and link every package to job or equipment serial.
Delivery documentation|Prepare delivery note and required transport and tax references after applicability review.
Carrier allocation|Record vehicle or carrier, booking, promised transit and charges.
Dispatch acknowledgement|Record handed over quantity, date and custody evidence.
Proof of delivery|Attach recipient acknowledgement and delivery date to the order.
Returns handling|Log shortages, transit damage, returned goods and credit or replacement decision.''',
'shipment_id;order_id;job_id;equipment_serial;package_count;dispatch_date;delivery_note;invoice_reference;carrier;tracking_reference;delivery_date;proof_of_delivery;return_id',
'On time in full delivery;Transit damage rate;Proof of delivery completion',
'QA releases; finance checks commercial documents; stores posts stock issue; service receives installed asset details.',
'Dispatch must use the approved destination and match invoice and delivery quantities.',
'A delivered order reconciles released, dispatched and received quantities and preserves supporting documents.')

dept('FIN','Finance accounts and treasury','Own the financial record from customer invoice and supplier payment through job margin, cash and period close.',
'Maintain accounts, post approved transactions, reconcile balances, collect/pay, close period and review financial results.',
'''Customer billing|Link invoice lines to order, dispatch or accepted service and approved price.
Receivable control|Track due dates, receipts, credit notes, disputes and collection actions.
Supplier invoice matching|Compare order, accepted receipt and invoice before payment approval.
Payable scheduling|Prioritise due payments with approved bank details and authority.
Bank reconciliation|Match bank transactions to receipts, payments and journals with unresolved item ownership.
Job cost and margin|Reconcile material, labour, subcontract and relevant overhead costs to completed jobs.
Fixed assets and expenses|Record capitalisation decisions, depreciation basis and approved employee expenses.
Period close and reporting|Close reconciled ledgers and produce profit, balance sheet and cash reports for the defined entity.''',
'entity_id;account_code;period;invoice_id;order_id;tax_code;net_amount;tax_amount;gross_amount;due_date;receipt_id;payment_id;bank_reference;job_cost;asset_id',
'Receivable days;Gross margin;Close completion time',
'Sales supplies terms; procurement and stores support matching; HR supplies approved payroll; management reviews results.',
'Tax rates, filing duties and payroll deductions must come from validated applicability and current approved configuration.',
'A period report reconciles to the ledger, and every payment has approved supplier identity and supporting transaction evidence.')

dept('HR','Human resources recruitment and onboarding','Manage approved vacancies and employee entry using controlled documents and retained acceptance.',
'Approve vacancy, screen and interview, approve terms, issue offer, confirm acceptance, appoint and complete onboarding.',
'''Offer letter generation|Fill editable employment terms and produce live A4 preview and print output.|Present in source|L02 L03
Offer confirmation and register|Confirm offers, maintain searchable records and export them to CSV.|Present in source|L03 L04
Appointment letter generation|Create the four page appointment format and compensation annexure from entered values.|Present in source|L02 L03
Appointment register|Issue, search, edit, print and export appointments in a separate register.|Present in source|L03 L04
Vacancy approval|Record business need, approved headcount, role and salary range before recruitment.
Candidate and interview tracking|Maintain application, evaluation and selection evidence with restricted access.
Offer acceptance and onboarding|Track accepted terms, start date, required documents and joining checklist.
Employee master and lifecycle|Assign employee ID and manage role, reporting line, confirmation, transfer and exit.''',
'vacancy_id;candidate_id;offer_no;offer_date;candidate_name;designation;joining_date;appointment_no;employee_id;employee_address;gross_salary_monthly;probation_months;notice_months;accepted_at;hr_approver',
'Time to fill;Offer acceptance rate;Onboarding completed on time',
'Management approves vacancy and pay; IT provisions access; payroll receives approved employee and pay details.',
'Generated terms and gross amounts are document values; they do not demonstrate payroll execution or signed acceptance.',
'An employee file links approved vacancy, accepted offer, issued appointment and completed joining requirements.')

dept('PAY','Attendance payroll and employee development','Convert approved attendance and compensation into controlled pay and maintain competence and employee lifecycle records.',
'Capture time, approve exceptions, process payroll, review, pay, reconcile and maintain training and performance records.',
'''Attendance and shifts|Record actual attendance, shift calendar and approved corrections.
Leave management|Maintain entitlements, applications, approval, balances and effective dates.
Overtime approval|Link additional work hours to authorisation before pay calculation.
Payroll components|Version effective salary components and deductions by employee and period.
Payroll review and payment|Reconcile gross to net, obtain approval and record payment reference.
Payslip and statutory outputs|Generate outputs from validated jurisdiction and applicability settings.
Competence and training|Track job skills, completed training, assessment and authorisation expiry.
Performance and exit|Record agreed objectives, review outcomes, clearance and final settlement checks.''',
'employee_id;pay_period;attendance_date;shift_id;leave_type;leave_balance;overtime_hours;salary_revision;gross_pay;deductions;net_pay;pay_approval;bank_payment_reference;training_id',
'Payroll correction rate;Absence rate;Required training current',
'HR owns employee master; supervisors approve time; finance approves payments; quality owns technical authorisations.',
'Restrict personal and bank details; use effective dates and retain approved payroll versions.',
'A paid period reconciles approved attendance, pay inputs, deductions, net pay and payment totals without duplicates.')

dept('ADM','Administration and facilities','Support daily operations through controlled facility services, records, visitors and shared resources.',
'Receive request, approve cost or access, assign service, verify completion and retain evidence.',
'''Facility request register|Track housekeeping, repairs, office support and responsible service owner.
Visitor and contractor entry|Record host, purpose, approved access and exit according to company policy.
Travel and accommodation|Approve employee travel and link bookings and claims to jobs or cost centres.
Office procurement|Track approved consumables and administrative service purchases.
Document correspondence|Maintain incoming and outgoing official correspondence and response owners.
Asset custody|Assign shared equipment and record issue, return and condition.
Insurance and renewals|Track policy, service agreement and licence renewal dates after owner validation.
Facility service review|Monitor recurring provider obligations, unresolved requests and service cost.''',
'request_id;facility_id;service_provider;visitor_id;host_id;travel_request;cost_centre;asset_custodian;renewal_reference;renewal_date;completion_evidence',
'Facility request closure time;Renewals overdue;Administrative cost variance',
'Procurement contracts services; finance pays verified costs; EHS manages required safety conditions.',
'Access, cost and renewal approvals must be identifiable and time bounded.',
'Each open facility request has an owner, agreed completion date and visible evidence when closed.')

dept('MNT','Maintenance and utilities','Keep production machines, tools and utilities available through planned maintenance and accountable repairs.',
'Register asset, assess criticality, plan maintenance, execute work, verify restoration and analyse repeat failures.',
'''Equipment asset register|Identify machines, location, responsible owner and required maintenance information.
Preventive maintenance|Schedule tasks by approved calendar or operating usage.
Breakdown request|Record symptom, equipment, downtime start and production impact.
Maintenance work order|Assign competent staff, spare needs, permits and completion checks.
Spare parts planning|Reserve critical spares and record actual consumption and return.
Restoration verification|Record functional checks and hand back equipment to production.
Utilities monitoring|Capture electricity and other relevant utility meter readings and abnormal consumption.
Failure improvement|Review repeat faults and approve replacement or reliability improvement actions.''',
'asset_id;criticality;maintenance_plan;work_order_id;failure_code;downtime_start;downtime_end;repair_hours;spares_consumed;restoration_check;meter_id;utility_quantity',
'Unplanned downtime;Preventive maintenance compliance;Repair turnaround time',
'Production reports failures; stores supplies spares; EHS controls permits; finance records asset spending.',
'Return equipment to use only after required checks and release by the responsible owner.',
'A completed work order includes fault, actual work, consumed spares, downtime and verified return to service.')

dept('EHS','Environment health and safety','Manage actual workplace hazards, incidents and environmental obligations through named controls and evidence.',
'Identify hazards, assess risk, authorise work, inspect conditions, investigate events and verify corrective actions.',
'''Hazard and risk register|Record equipment, task, hazard, affected people, controls and review date.
Work authorisation|Use company approved permits and isolation checks for tasks requiring them.
Safety induction|Record employee and contractor induction and relevant training.
Inspection actions|Track workplace inspections, unsafe conditions and corrective action ownership.
Incident and near miss|Capture event, immediate action, investigation and verified closure.
Protective equipment|Record required equipment, issue, inspection and replacement.
Emergency readiness|Maintain responsibilities, equipment checks, drill records and follow up.
Waste and environmental records|Track applicable waste, contractor evidence and resource use against validated obligations.''',
'hazard_id;task_id;risk_assessment;control_owner;permit_id;isolation_check;training_record;incident_id;corrective_action;ppe_issue;waste_record;emergency_drill',
'Safety actions overdue;Induction completion;Incident investigation closure',
'Every operating department owns task controls; HR owns training records; facilities and maintenance close physical actions.',
'Confirm which legal and site requirements apply before configuring permits, reporting or retention periods.',
'Work requiring a permit cannot be marked ready while its specified prerequisites are incomplete.')

dept('ITS','Information technology data and security','Protect access, source data and recoverability as the existing operations app expands.',
'Provision identity, approve role, control changes, monitor sync and incidents, back up and demonstrate recovery.',
'''Spreadsheet integration|Read and save the configured wire and document registers through Apps Script.|Present in source|L03 L04
Local save fallback|Keep supported document records in browser local storage when shared save fails.|Present in source|L03
Installable application shell|Cache same origin application assets and offer supported browser installation.|Present in source|L03 L06
Identity and access roles|Apply individual accounts and least privilege to every record and write operation.
Audit and document retention|Record actor, action, before and after revision and retention owner.
Reliable synchronisation|Provide visible sync states, idempotent retries, conflict handling and reconciliation.
Backup and restore|Back up shared records and prove restoration against agreed recovery objectives.
Release and incident management|Test changes, version deployments and record service incidents with recovery actions.''',
'user_id;role_id;entity_scope;record_id;record_version;created_by;updated_by;sync_status;request_id;audit_event_id;backup_id;restore_result;deployment_version',
'Failed sync unresolved;Restore success;Access reviews overdue',
'Department owners approve access; finance and HR restrict sensitive records; management owns recovery priorities.',
'Local storage is browser specific; cached app assets do not prove an offline database or safe multiuser conflict handling.',
'An unauthorised user cannot read restricted HR data or submit writes, and an approved restore recovers the tested records.')

dept('AUD','Compliance audit and document control','Maintain the approved obligation register, controlled records and independent assurance over department processes.',
'Confirm applicability, assign owner, control document revision, gather evidence, audit exceptions and verify closure.',
'''Obligation register|Record legal, contractual, customer and certification requirements with applicability evidence.
Controlled document library|Version policies, procedures, drawings, formats and approved effective dates.
Record retention schedule|Define retention and disposal from actual legal and business requirements.
Internal audit plan|Schedule independent checks by process, risk and agreed scope.
Evidence and findings|Link each finding to a requirement, record sample and responsible process owner.
Corrective action follow up|Verify completion and effectiveness with evidence separate from action entry.
Contract and certification tracking|Retain signed terms, actual certificates, scope, validity and renewal ownership.
Change impact review|Assess process, regulatory, customer and record consequences before major changes.''',
'obligation_id;applicability_basis;process_owner;document_id;revision;effective_date;approval;retention_rule;audit_id;finding_id;evidence_reference;corrective_action_id;certificate_scope',
'Audit findings overdue;Controlled document current;Obligation evidence complete',
'Department leads supply records; management approves policy; qualified advisers validate legal and certification applicability.',
'No registration, accreditation, statutory status or compliance claim is assumed from website wording.',
'An audit finding links a specific requirement and evidence, then closes only after independent verification.')

features=[f for d in departments for f in d['features']]

products=[]
def product_rows(brand,category,names,source):
    for name in names.split(';'):
        products.append([f'PROD-{len(products)+1:03d}',brand,category,name,'Public catalogue entry','Not supplied','Not supplied',source])
product_rows('Electrotech Services','Packaging machinery','Automatic cup filling and sealing machine;Continuous band sealer;Dry ink coding machine;Form fill seal machine;Foil cup sealer;Foot sealer;Gravimetric weigh dispenser;Hand sealer;Induction sealer;Paste and liquid filler;Shrink tunnel;Solenoid sealer','S05')
product_rows('Electrotech Services','Plastic processing','Hopper dryer;Hopper loader and static discharger;Pneumatic loop handle machine','S06')
product_rows('Electrotech Services','Heating equipment','Furnace;HDPE pipe welding mirrors;Heating vessel;Hot air generator;Hot plate;Online heaters;Ovens and dryers','S07')
product_rows('Electrotech Services','Controls and panels','Digital timers and counters;Panel boxes for various applications;Temperature controllers','S08')
product_rows('Electrotech Services','Sensors','Thermocouples and sensors','S09')
product_rows('Electrotech Services','Packaging materials','Polyolefin shrink film;Strapping rolls;Stretch wrapping film','S10')
product_rows('Electrotech Services','Custom machines','Chemical stirrer;Coding conveyor;Custom floor top pneumatic sealer;Custom industrial ovens;Height adjustable truck loading conveyor;Hot air generator','S11')
product_rows('Electro Heat Systems','Heaters and controls','Mica band heater;Ceramic band heater;Strip and flat heater;Low density cartridge heater;Split type cartridge heater;High density cartridge heater;Ceramic cartridge and bobbin heater;Tubular heaters;Cast in heaters;Hot runner bushes and manifold heaters;Jacket heaters pads and heating tape;Thermocouples and sensors;Temperature controllers and timers;Ceramic infrared heaters;Infrared heaters','S14')

data=[]
def field_row(entity,name,label,typ,unit,required,status,source,owner,validation):
    data.append([f'DATA-{len(data)+1:04d}',entity,name,label,typ,unit,required,status,owner,validation,source])
for attr,entity,owner in [('report','Calibration report','Calibration'),('performance','Performance report','Calibration'),('offer','Offer letter','HR'),('appointment','Appointment letter','HR')]:
    for tag,el,lastlabel in parser.fields:
        if f'data-{attr}-field' not in el: continue
        name=el.get(f'data-{attr}-field')
        label=lastlabel or name
        typ=el.get('type','text') if tag=='input' else ('enum' if tag=='select' else 'text')
        options=''
        unit='INR' if re.search('salary|basic|allowance|gross',name,re.I) else ('percent' if name=='claimedError' else 'As entered')
        field_row(entity,name,label,typ,unit,'Form required' if 'required' in el else 'Not required in form','Present in source','L02 L03',owner,('Allowed options: '+options) if options else 'See form and save validation; proposed release controls are additional')
    for name,typ in [('id','identifier'),('status','enum'),('updatedAt','timestamp')]:
        field_row(entity,name,name,typ,'n.a.','Generated','Present in source','L03',owner,'Application generated; identifier is not an issued document revision')
for entity,names in [('Calibration reading','index;standard;duc;error;remark'),('Performance reading','index;reference;observed;error;remark')]:
    for name in names.split(';'):
        field_row(entity,name,name,'number' if name!='remark' else 'enum','Celsius or selected error unit' if name not in ('index','remark') else 'n.a.','Required reading values','Present in source','L03','Calibration','Full precision comparison precedes display rounding; blank and zero differ')
for name,label,unit in [('wattage','Wattage','W'),('voltage','Voltage','V'),('heaterOD','Heater outside diameter','mm'),('heaterLength','Heater length','mm'),('coreLength','Core winding length','mm'),('pipeThickness','Pipe wall thickness','mm'),('pipeOD','Pipe outside diameter','mm'),('coreOD','Core outside diameter','mm'),('extra','Extra resistance','percent')]:
    field_row('Heater input',name,label,'number',unit,'Required or auto selected','Present in source','L02 L03','Engineering','Positive engineering inputs and valid geometry need independent review')
for const,entity in [('HEADERS','Wire table'),('REPORT_HEADERS','Calibration sheet index'),('PERFORMANCE_REPORT_HEADERS','Performance sheet index'),('OFFER_HEADERS','Offer sheet index'),('APPOINTMENT_HEADERS','Appointment sheet index')]:
    m=re.search(r'const '+const+r'\s*=\s*\[(.*?)\];',backend,re.S)
    for name in re.findall(r'"([^"]+)"',m.group(1)):
        field_row(entity,name,name,'JSON' if name=='payload_json' else 'Column','See payload or wire units','Backend schema','Present in source','L04','IT and record owner','Spreadsheet index plus complete JSON payload; not a normalised enterprise data model')
for d in departments:
    for name in d['fields']:
        typ='date' if re.search('date|_start|_finish',name) else ('decimal' if re.search('amount|cost|value|quantity|hours|_mm|_ohm|_pct|_m$|_W|_V',name) else 'text or reference')
        unit='INR' if re.search('cost|amount|pay$|value|salary',name) else ('mm' if name.endswith('_mm') else 'Define in configuration')
        field_row(d['name'],name,name.replace('_',' '),typ,unit,'Confirm with process owner','Proposed','A01',d['name']+' lead','Validate unit, reference key, applicability and effective revision before release')

workflows=[]
def flow(fid,title,steps):
    for n,(owner,action,record,gate,exception) in enumerate(steps,1):
        workflows.append([fid,title,n,owner,action,record,gate,exception,'Proposed operating flow'])
flow('WF01','Enquiry to cash for custom heater',[
('Sales','Capture customer application and requirement','Enquiry and requirement revision','Application inputs complete','Return incomplete scope to customer'),
('Engineering','Check feasibility and calculate winding','Design and calculation revision','Engineer approves design basis','Revise specification or decline infeasible scope'),
('Estimation','Build cost and issue approved quotation','Estimate and quotation revision','Margin and discount approved','Escalate price or scope exception'),
('Sales and Finance','Accept order and check credit or advance','Order and commercial clearance','PO matches accepted quotation','Resolve mismatch or hold order'),
('Planning','Release job and material requirement','Job traveller and approved BOM','Design and material readiness confirmed','Assign shortage action'),
('Procurement and Stores','Receive, inspect, reserve and issue material','Receipt, lot and issue records','Only accepted lot issued','Quarantine or approved substitution'),
('Production','Wind and assemble to approved revision','Operation and consumption records','First piece and in process checks accepted','Record rework or scrap'),
('Quality','Perform required final checks','Inspection and release record','Mandatory tests complete and accepted','NCR and release hold'),
('Dispatch','Pack and dispatch approved goods','Shipment and delivery note','QA and finance clearance obtained','Hold incomplete shipment'),
('Finance','Invoice and collect payment','Invoice receipt and bank reconciliation','Invoice and delivered quantity reconcile','Dispute and collection ownership'),
('Service','Maintain installed base and warranty','Equipment and service history','Acceptance and warranty basis recorded','Route complaint to service ticket')])
flow('WF02','Calibration request to issued report',[
('Service or Sales','Agree scope, method and customer acceptance needs','Service request and quotation','Instrument and required scope identified','Clarify unsupported range or method'),
('Calibration','Receive and identify item and condition','Instrument receipt and condition record','Unique identity and condition accepted','Hold damaged or unidentified item'),
('Calibration','Confirm standard validity and method competence','Standard certificate and authorisation','Standard valid for date range and method','Use approved alternate standard or reschedule'),
('Calibration','Capture conditions and raw readings','Calibration readings','Mandatory readings complete','Keep draft status'),
('Calibration','Evaluate error and conformity rule','Calculation and decision record','Units, tolerance basis and decision rule agreed','Investigate zero reference and invalid input'),
('Quality reviewer','Review report and authorise release','Reviewed issued revision','Independent approval and evidence complete','Correct and retain prior draft history'),
('Calibration','Issue report and communicate next due date','Issued certificate and acknowledgement','Issued copy matches reviewed version','Amend through controlled revision'),
('Finance and Service','Bill, return item and schedule agreed recall','Invoice, return acknowledgement and recall','Commercial and custody records reconcile','Assign dispute or overdue action')])
flow('WF03','Purchase request to payment',[
('Requesting department','Raise defined need and required date','Purchase requisition','Budget and specification approved','Return incomplete request'),
('Procurement','Obtain comparable supplier offers','RFQ comparison','Supplier and technical requirements accepted','Escalate sole source exception'),
('Approver','Approve commitment and order','Purchase order','Authority and spend limit met','Hold for higher approval'),
('Stores and Quality','Receive and inspect delivered material','Receipt and inspection','Accepted quantity and lot identified','Quarantine discrepancy'),
('Finance','Match supplier invoice','Three way match evidence','Order, accepted receipt and invoice reconcile','Resolve mismatch before payment'),
('Finance approver','Authorise and execute payment','Approved payment and bank reference','Bank identity checked and payment approved','Hold suspicious or changed bank details'),
('Finance','Reconcile supplier and bank balances','Reconciliation','No duplicate invoice or payment','Investigate reconciling item')])
flow('WF04','Recruitment to employee exit',[
('Management and HR','Approve vacancy and terms','Vacancy and pay approval','Headcount and pay approved','Revise or reject request'),
('HR and Hiring manager','Evaluate candidate','Interview record','Selection and reference process complete','Record rejection or further assessment'),
('HR','Issue offer and obtain acceptance','Offer and acceptance','Terms approved and acceptance recorded','Revise offer or close vacancy'),
('HR','Issue appointment and complete joining','Appointment and joining checklist','Required documents and employee ID complete','Track outstanding requirements'),
('IT and Department lead','Provision access and training','Access and training record','Role approved and competence requirements met','Limit access until approved'),
('Payroll and Finance','Process approved time and pay','Payroll and payment evidence','Independent review and totals reconcile','Correct input before pay'),
('HR and Department lead','Manage confirmation, review and changes','Lifecycle and effective pay revisions','Authorised changes with effective dates','Escalate unresolved review'),
('HR IT and Finance','Complete exit clearance','Access revocation and final settlement','Assets, access and balances reconciled','Retain documented open item owner')])
flow('WF05','Complaint to repair and maintenance renewal',[
('Service','Log issue and identify equipment','Ticket and installed asset','Customer and entitlement identified','Clarify equipment identity'),
('Service scheduler','Assign technician and plan visit','Visit plan','Skills, tools and access ready','Reschedule with customer'),
('Technician','Diagnose and recommend work','Diagnosis and estimate','Cause evidence and scope recorded','Escalate technical uncertainty'),
('Customer or Warranty approver','Approve repair scope','Approval or warranty decision','Chargeable work authorised','Hold unapproved work'),
('Technician and Stores','Execute repair and post actuals','Labour spares and repair record','Approved parts and procedure used','Record extra scope for approval'),
('Quality or Service reviewer','Verify operation and close','Post repair test and acknowledgement','Required checks and customer acceptance complete','Reopen unresolved issue'),
('Finance and Service','Bill and schedule future service','Invoice and contract reminder','Actuals and entitlement reconcile','Dispute or renewal follow up')])
flow('WF06','Custom machine project to handover',[
('Sales and Projects','Confirm project scope and milestones','Scope baseline','Customer scope and interfaces accepted','Record exclusion or change request'),
('Engineering','Release mechanical electrical and control designs','Approved design package','Cross discipline review complete','Resolve interface conflict'),
('Planning and Procurement','Plan manufacture and long lead items','Schedule and purchase plans','Capacity and supplier commitments feasible','Approve schedule revision'),
('Production and Quality','Build assemble and test','Build and factory test evidence','Agreed factory acceptance complete','Punch list and repair'),
('Projects','Verify customer site readiness','Readiness checklist','Required utilities and access ready','Delay installation with documented reason'),
('Projects and Customer','Install commission and train','Commissioning and training records','Agreed site acceptance complete','Approved residual punch list'),
('Projects Finance and Service','Handover bill and activate support','Acceptance pack and equipment record','Commercial and technical deliverables reconciled','Assign remaining obligation owner')])

controls=[
['C01','Individual access and entity scope','IT','All reads and writes','Restrict HR/pay and approve each role','Present source has wire admin check only; broader roles proposed','Unauthorised user cannot list HR records or save documents','P0','L04 L05 A01'],
['C02','Reference validity and method scope','Calibration','Before calibration','Verify standard identity certificate range and validity','Proposed release control','Expired or out of scope reference blocks issue','P0','L02 L03 A01'],
['C03','Conformity decision rule','Quality','Before report issue','Agree error unit tolerance basis uncertainty and decision rule','Partial calculation exists','Boundary and zero reference examples produce agreed results','P0','L03 A01'],
['C04','Server validation of calculations','IT and Quality','Every document save','Revalidate numeric readings, status and permissible payload','Current backend validates required fields and size, not full result logic','Altered client result is rejected or recomputed','P0','L04 A01'],
['C05','Issued document immutability','Quality and HR','After issue','Retain issued revision and supersede through controlled amendment','Proposed','Editing an issued record creates a traceable new revision','P0','L03 A01'],
['C06','Unique numbering and concurrent use','IT','Create or issue','Allocate controlled number per entity type and period','Client sequences and backend locks exist; global uniqueness not established','Two simultaneous issuers receive different valid numbers','P0','L03 L04 A01'],
['C07','Sync and conflict management','IT','Save and retry','Separate pending synced failed and conflict with idempotent requests','Local fallback exists; durable retry and conflict handling unverified','Offline then reconnect preserves both users records once','P0','L03 A01'],
['C08','Backup and restore','IT','Scheduled and after release','Prove shared record and attachment restoration','Proposed','Restore sample reconstructs counts IDs payloads and attachments','P0','A01'],
['C09','Released design revision','Engineering','Job release','Approve calculation drawing BOM and master version','Proposed','Job cannot use superseded revision without authorised exception','P0','A01'],
['C10','Material lot status','Stores and Quality','Receipt and issue','Separate accepted quarantined rejected and reserved','Proposed','Quarantined stock cannot be issued to production','P1','A01'],
['C11','Production and quality release','Quality','Dispatch','Complete mandatory inspection and resolve failed characteristics','Proposed','Failed mandatory check blocks shipment release','P0','A01'],
['C12','Purchase payment segregation','Finance','Purchase to pay','Approve order accepted receipt and invoice match before pay','Proposed','Receipt or price mismatch remains visible and blocks payment','P1','A01'],
['C13','Commercial change control','Sales and Finance','Order change','Approve cost price delivery and customer changes','Proposed','Changed scope updates version and linked commitments','P1','A01'],
['C14','Employee pay effective dates','HR and Payroll','Employee change','Version authorised terms and retain approval evidence','Letter generation exists; payroll control proposed','New pay takes effect in approved period only','P1','L03 A01'],
['C15','Record retention and restricted export','Record owner and IT','Export and disposal','Apply approved retention and protect HR exports and shared files','Proposed','Role limits and disposal evidence match approved schedule','P0','A01'],
['C16','Deployment and cache version','IT','Application release','Version assets, test upgrade and maintain rollback evidence','App shell exists; release discipline proposed','Returning user receives compatible app and backend version','P1','L06 A01'],
['C17','Numeric and geometry boundaries','Engineering and IT','Calculation','Reject nonfinite or nonpositive inputs and invalid geometry','Partial checks in source; comprehensive validation proposed','Negative zero missing and infeasible geometry have defined outcomes','P0','L03 A01'],
['C18','CSV export safety','IT','Export','Prevent spreadsheet formula interpretation of user text','CSV escaping exists; formula neutralisation not verified','Text starting with equals remains literal in exported workbook','P1','L03 A01'],
['C19','Obligation applicability','Compliance owner','Configuration and review','Validate registrations, thresholds, due dates and legal requirements','Proposed','Each configured obligation has an applicability basis and owner','P1','A01'],
['C20','Customer owned property','Service and Stores','Receipt through return','Identify custody condition accessory and return evidence','Proposed','Receipt and return reconcile each instrument and accessory','P1','A01']]

kpis=[]
definitions={
'First pass yield':('Units accepted without rework / units first submitted','percent','Use first submission cohorts; exclude reinspection duplicates'),
'Quoted gross margin':('(Net quoted value - estimated direct cost) / net quoted value','percent','Define treatment of overhead and exclude taxes'),
'Gross margin':('(Net recognised revenue - agreed cost of sales) / net recognised revenue','percent','Use finance approved recognition and matched cost basis'),
'Inventory record accuracy':('Counted item location lots within approved tolerance / counted item location lots','percent','Keep quantity and value accuracy separate'),
'Calibration turnaround':('Issue timestamp minus accepted receipt timestamp','hours or days','Report median and tail; disclose agreed customer holds'),
'Overdue instruments':('Active instruments due before reporting date and not validly recalibrated','count','Exclude formally retired equipment; define date basis'),
'Quote win rate':('Won quotations / closed quotations in defined cohort','percent','Separate open quotations and define win/loss population'),
'Supplier on time delivery':('Receipts on or before agreed promise / receipts due in period','percent','Define line or quantity basis and revised promise policy'),
'On time in full delivery':('Orders delivered complete by committed date / orders due','percent','Freeze commitment revision and define partial delivery treatment'),
'Receivable days':('Average eligible trade receivables / matching credit sales x period days','days','Use consistent tax and sales scope; do not use unrelated sales'),
'First visit fix rate':('Eligible service tickets resolved on first visit / eligible completed visit tickets','percent','Define repeat fault window and remote only exclusions'),
'Absence rate':('Unplanned absent scheduled hours / scheduled work hours','percent','Separate planned leave and approved overtime'),
'Wire utilisation':('Approved wire in accepted output / total wire consumed','percent','Use one unit and record returned material separately'),
'Schedule adherence':('Jobs completed by approved planned finish / jobs due','percent','Define freeze point and approved reschedule treatment'),
'Required training current':('People meeting required current training / people requiring it','percent','Use role and authorisation validity on reporting date')}
extra_definitions={
'Action closure on time':'Actions closed by agreed due date / actions due in period',
'Budget variance':'Actual amount minus approved budget for matching entity period and scope',
'Operating margin':'Finance approved operating profit / matching net recognised revenue',
'Qualified lead conversion':'Sales accepted qualified leads / marketing leads qualified in the cohort',
'Cost per qualified lead':'Attributable campaign cost / qualified leads from the matching campaign cohort',
'Enquiry response time':'First substantive response timestamp minus enquiry receipt timestamp',
'Enquiry to quotation time':'First approved quotation timestamp minus complete enquiry timestamp',
'On time customer commitment':'Commitments fulfilled by accepted due date / commitments due in period',
'Estimate variance':'Actual completed job cost minus matching approved estimated job cost',
'Quotation turnaround time':'Approved quotation issue timestamp minus complete estimation request timestamp',
'Design release lead time':'Approved design release timestamp minus accepted design request timestamp',
'Design change after release':'Released designs changed after job release / designs released in cohort',
'Prototype first pass rate':'Prototypes meeting all mandatory tests on first submission / first submissions',
'Work in progress age':'Reporting date minus actual job start date for open jobs',
'Material ready at planned start':'Jobs with all required material ready by frozen start / jobs due to start',
'Winding cycle time':'Winding finish timestamp minus start timestamp using agreed downtime treatment',
'Fabrication rework rate':'Fabrication units requiring rework / fabricated units first submitted',
'Assembly completion on time':'Assemblies completed by approved finish date / assemblies due',
'Subcontract turnaround':'Accepted return timestamp minus material despatch timestamp',
'Panel first pass acceptance':'Panels meeting required tests on first submission / panels first submitted',
'Configuration revision defects':'Confirmed defects caused by incorrect released configuration in the period',
'Functional test closure time':'Final mandatory functional test acceptance minus first test start timestamp',
'Supplier rejection rate':'Rejected received units / inspected received units on matching unit basis',
'Purchase cycle time':'Approved purchase order timestamp minus approved requisition timestamp',
'Stockout incidents':'Distinct production or service shortages blocking planned work during the period',
'Slow moving stock value':'Stock value with no qualifying issue within an approved age threshold',
'Cost of poor quality':'Recorded scrap rework warranty and approved failure cost in the period',
'Corrective action overdue':'Open corrective actions with due date before reporting date',
'Report amendment rate':'Issued reports amended for internal error / reports issued in matching cohort',
'Milestone adherence':'Milestones accepted by baseline due date / milestones due in period',
'Project cost variance':'Actual project cost minus approved baseline cost for matching completed scope',
'Punch list closure time':'Verified closure timestamp minus punch item creation timestamp',
'First response time':'First substantive service response minus ticket receipt timestamp',
'Repeat complaint rate':'Closed service tickets with repeat same fault within approved window / eligible closed tickets',
'Transit damage rate':'Shipments with confirmed transit damage / shipments delivered in period',
'Proof of delivery completion':'Delivered shipments with valid delivery evidence / shipments delivered',
'Close completion time':'Approved financial close timestamp minus reporting period end',
'Time to fill':'Accepted offer date minus approved vacancy release date',
'Offer acceptance rate':'Offers accepted / offers decided in matching candidate cohort',
'Onboarding completed on time':'Joiners meeting mandatory checklist by agreed deadline / joiners due',
'Payroll correction rate':'Employees requiring post approval payroll correction / employees paid',
'Facility request closure time':'Verified facility completion timestamp minus accepted request timestamp',
'Renewals overdue':'Required active renewals whose due date precedes reporting date without renewal evidence',
'Administrative cost variance':'Actual administrative cost minus approved budget for matching period and scope',
'Unplanned downtime':'Sum of nonoverlapping equipment unavailable time caused by unplanned failures',
'Preventive maintenance compliance':'Planned tasks completed by due time / planned tasks due in period',
'Repair turnaround time':'Verified restoration timestamp minus accepted breakdown timestamp',
'Safety actions overdue':'Open safety actions with due date before reporting date',
'Induction completion':'People with mandatory completed induction / people requiring induction',
'Incident investigation closure':'Investigations verified closed within agreed time / investigations due',
'Failed sync unresolved':'Records in failed or conflict sync state without confirmed resolution at reporting time',
'Restore success':'Restore exercises meeting all approved record and recovery checks / restore exercises run',
'Access reviews overdue':'Required access reviews due before reporting date without completed evidence',
'Audit findings overdue':'Open audit findings whose approved due date precedes reporting date',
'Controlled document current':'Active controlled documents with approved current revision / active documents requiring review',
'Obligation evidence complete':'Applicable obligations with current required evidence / obligations due for evidence review'}
for metric,definition in extra_definitions.items():
    unit='percent' if ' / ' in definition else ('count' if any(x in metric.lower() for x in ['overdue','defects','incidents','unresolved']) else ('INR' if any(x in metric.lower() for x in ['cost variance','budget variance','estimate variance','quality','stock value','cost per']) else 'elapsed time or defined unit'))
    definitions[metric]=(definition,unit,'Confirm period, event timestamps, permitted exclusions, zero denominator treatment and target with the process owner')
for metric in ['Enquiry response time','Enquiry to quotation time','Quotation turnaround time','Design release lead time','Winding cycle time','Subcontract turnaround','Functional test closure time','First response time','Close completion time','Facility request closure time','Unplanned downtime','Repair turnaround time']:
    definition,unit,note=definitions[metric];definitions[metric]=(definition,'hours',note)
for metric in ['Work in progress age','Punch list closure time','Time to fill']:
    definition,unit,note=definitions[metric];definitions[metric]=(definition,'days',note)
definition,unit,note=definitions['Cost per qualified lead'];definitions['Cost per qualified lead']=(definition,'INR per qualified lead',note)
for d in departments:
    for metric in d['kpis']:
        definition,unit,note=definitions.get(metric,('Define exact numerator denominator event and population with process owner','To define','Agree period, exclusions, source completeness and target before use'))
        kpis.append([f'KPI-{len(kpis)+1:03d}',d['name'],metric,definition,unit,'Monthly or operational review','Not supplied','Not supplied',note,'Proposed metric'])

requests=[]
request_groups=[
('Management','Legal entity and group structure','Registration documents, sites, authorised signatories and entity relationships','Entity identity and scope'),
('Management','Actual organisation chart','Departments, reporting lines, role owners and delegation limits','Map proposed functions to real owners'),
('Finance','Financial statements and trial balances','Latest approved periods, ledger mapping and entity scope','Revenue profitability and financial case'),
('Sales','Customer and order registers','Customer IDs, enquiries, quotes, orders, dates, values and status history','Sales funnel and order cycle baseline'),
('Engineering','Approved specifications and design history','Drawings, design calculations, BOMs, revisions and engineering approvals','Product scope and design validation'),
('Engineering','Wire master and material evidence','Actual wire rows, alloy certification, resistance units and master revisions','Validate gauge logic and assumptions'),
('Planning','Jobs routes and capacity','Production schedule, work centre calendars, routing and actual progress','Capacity and delivery baseline'),
('Production','Production actuals','Operation time, output, rework, scrap and job material consumption','Yield cycle time and cost'),
('Stores','Inventory and movement history','Opening balances, receipts, issues, returns, lots, locations and count results','Stock accuracy and traceability'),
('Procurement','Suppliers and purchasing','Vendor approvals, requisitions, quotes, POs, receipts and invoice links','Supplier quality lead time and spend'),
('Quality','Inspection and nonconformity records','Plans, measured results, release evidence, NCRs and corrective actions','Conformance and improvement evidence'),
('Calibration','Actual report and standard records','Registers, raw readings, issued revisions, reference certificates, scope and validity','Calibration volume traceability and report quality'),
('Projects','Project and acceptance records','Scope, milestones, budgets, actuals, commissioning and customer signoff','Project outcomes and acceptance'),
('Service','Installed base service and contracts','Equipment serials, tickets, diagnosis, parts, labour, warranty and AMC terms','Reliability and service baseline'),
('Dispatch','Shipment and delivery records','Delivery notes, invoice links, carrier, dates, POD and damage claims','On time delivery and custody'),
('Finance','Cost and cash records','Rates, job costing, invoices, ageing, receipts, payments and bank reconciliations','Margin cash and verified benefits'),
('HR','Restricted employee lifecycle records','Approved vacancies, accepted offers, appointments, joins, changes and exits','HR process evidence and headcount'),
('Payroll','Restricted attendance and pay evidence','Time, leave, overtime approvals, pay components, deductions and payments','Payroll reconciliation and labour cost'),
('Maintenance','Assets and downtime','Asset list, preventive plans, breakdowns, repairs, spares and meter readings','Availability and utility efficiency'),
('Administration','Facility services and renewals','Supplier contracts, assigned assets, travel and renewal calendar','Administrative obligations'),
('EHS','Applicable safety and environment records','Risk assessments, permits, training, incidents, inspections and waste records','Actual controls and incident history'),
('IT','Deployment access and storage evidence','Hosting version, Apps Script deployment access, user roles and record counts','Live behaviour and exposure assessment'),
('IT','Backup restore and sync evidence','Backup jobs, restore results, failed sync history and conflict resolutions','Recovery and shared data reliability'),
('Compliance','Registration certification and obligation evidence','Actual certificates, accreditation scope, applicability register and audit results','Support exact compliance claims'),
('Marketing','Catalogue completeness','Current full catalogue, discontinued items, SKU IDs and missing web pages','Complete company product master'),
('All department owners','Baseline and target definitions','Measured volumes, elapsed time, error rates, date window and approved targets','Validate improvement business case')]
for i,(owner,area,items,use) in enumerate(request_groups,1):
    requests.append([f'REQ-{i:03d}',owner,area,items,use,'Not supplied',None,'Not received','Restricted' if owner in ('HR','Payroll','Finance','IT') else 'Internal'])

rollout=[
['PH0','Validate scope and evidence','Management and department leads','Confirm entities, owners, process variants and baseline; fill data requests','Approved scope, owners and evidence register','P0','Not started'],
['PH1','Protect existing records','IT and record owners','Individual access, server validation, versioning, unique numbers and restore','Access, concurrency, tamper and restore acceptance pass','P0','Not started'],
['PH2','Control engineering and quality','Engineering Quality and Calibration','Approve design history, standards, decision rules and controlled report release','Representative design and calibration journeys pass','P0','Not started'],
['PH3','Connect demand material and production','Sales Planning Procurement Stores Production','Create order job BOM material movements and production inspection links','One heater order reconciles from requirement to delivery','P1','Not started'],
['PH4','Connect finance projects and service','Finance Projects Service Dispatch','Link accepted output to invoices cost receipts warranty and installed base','Invoice and job cost reconcile; project/service acceptance captured','P1','Not started'],
['PH5','Complete employee and support processes','HR Payroll Admin Maintenance EHS Compliance','Approved employee lifecycle, pay, assets, maintenance and obligation workflows','Restricted payroll trial and applicable support workflows pass','P1','Not started'],
['PH6','Measure and improve','Management and process owners','Compare approved baseline with complete operating periods','Measured benefits reconciled and improvement owners named','P2','Not started']]

payload={'date':DATE,'departments':departments,'features':features,'products':products,'data':data,'workflows':workflows,'controls':controls,'kpis':kpis,'requests':requests,'rollout':rollout,'sources':sources}
live=json.loads((WORK/'live_wire.json').read_text(encoding='utf-8'))
wire_rows=[]
for alloy in ['nichrome','kanthal']:
    for row in live[alloy]['values'][1:]:
        wire_rows.append([alloy]+row+['G01'])
payload['wire_rows']=wire_rows
payload['sources'].append(['G01','Live wire master','Connected Google Sheets read',live['url'],'Read both visible tabs A1:F1000 on 15 October 2026; 23 Nichrome and 9 Kanthal rows; no document register tabs visible'])
geometry=[]
for name,kind in [('STANDARD_CORE_SIZES','Core diameter option'),('PIPE_OD_SIZES','Pipe outside diameter option')]:
    block=re.search(r'const '+name+r'\s*=\s*\[(.*?)\];',js,re.S).group(1)
    for size in re.findall(r'\d+(?:\.\d+)?',block): geometry.append([kind,float(size),None,'mm','Hardcoded reference option','L03'])
block=re.search(r'const PIPE_INVENTORY\s*=\s*\[(.*?)\];',js,re.S).group(1)
for od,wall in re.findall(r'od:\s*([\d.]+),\s*thickness:\s*([\d.]+)',block):geometry.append(['Pipe geometry reference',float(od),float(wall),'mm','Hardcoded geometry; no stock quantity','L03'])
payload['geometry']=geometry
payload['requests'][5][5]='32 live wire rows retrieved; certificates and revision history missing'
payload['requests'][5][7]='Part received'
(WORK/'case_data.json').write_text(json.dumps(payload,indent=2,ensure_ascii=False),encoding='utf-8')
inventory={name:{'sha256':hashlib.sha256((ROOT/name).read_bytes()).hexdigest(),'lines':len((ROOT/name).read_text(encoding='utf-8').splitlines())} for name in ['index.html','script.js','readme.md','google-sheets/Code.gs','google-sheets/README.md','service-worker.js','manifest.webmanifest']}
(WORK/'source_inventory.json').write_text(json.dumps(inventory,indent=2),encoding='utf-8')
print(json.dumps({'departments':len(departments),'features':len(features),'current_features':sum(f['status']=='Present in source' for f in features),'data_fields':len(data),'product_entries':len(products),'workflow_steps':len(workflows),'controls':len(controls),'kpis':len(kpis),'data_requests':len(requests)}))
