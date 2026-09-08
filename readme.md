# Electro Group of Industries — Operations & Automation

A browser-based engineering and calibration workflow for ELECTRO GROUP OF INDUSTRIES. It combines the existing heater-coil calculator with a pre-built calibration report, editable live preview, report register, and spreadsheet export.

## Features

- Electrical and mechanical heater-coil calculations
- Nichrome and Kanthal D wire databases
- Google Sheets-backed persistent storage
- Admin password validation on the Google Apps Script backend
- Automatic pipe, insulation, core, pitch, and SWG selection
- Responsive desktop and mobile interface
- Calibration report auto-numbering and due-date calculation
- Report numbering continues from the last saved or manually entered sequence
- Automatic observed-error and pass/fail results
- Editable bordered report template based on the supplied certificate
- Browser report register with Google Sheets synchronization
- Linked performance reports with selectable °C/% error, automatic Pass/Fail, shared numbering and customer reuse
- Separate searchable `performance_reports` register with Excel-compatible export
- Excel-compatible CSV export containing report details and all readings
- Live overview metrics for reports, passing records, due dates, and heater calculations
- Offer-letter placeholder filler based on the supplied Electrotech Services format
- Live A4 offer preview, browser PDF printing, confirmation workflow, and searchable offer register
- Confirmed offers synchronized to a separate `offer_letters` Google Sheet tab
- Electro Group red-and-white logo branding and favicon

## Run the app

1. Complete [google-sheets/README.md](google-sheets/README.md).
2. Paste the deployed Google Apps Script `/exec` URL into `GOOGLE_SHEETS_WEB_APP_URL` in `script.js`.
3. Open `index.html` in a browser or publish these static files with any web host.

No Supabase account, SDK, or database is used.

## Project files

```text
index.html                 App interface
styles.css                App styling
script.js                 Calculator and Google Sheets client
google-sheets/Code.gs     Google Apps Script backend
google-sheets/README.md   One-time Google setup guide
```

## Google Sheet columns

Both wire tabs use the same columns:

| id | swg | thickness | ohm | minw | maxw |
|---:|---:|---:|---:|---:|---:|

Do not rename the tabs or column headers. The webpage editor updates complete rows and the backend validates all numeric values before saving.

Calibration reports are stored in `calibration_reports`, linked performance reports in `performance_reports`, and confirmed offer letters in `offer_letters`. The backend creates each tab automatically when its register is first opened or a record is saved. Until the updated Apps Script is deployed, the website keeps all record types safely in that browser and still allows Excel-compatible export.
