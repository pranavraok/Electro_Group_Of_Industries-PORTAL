# Google Sheets backend setup

1. Create a blank Google Sheet.
2. In that sheet, open **Extensions > Apps Script**.
3. Replace the editor contents with `Code.gs` from this folder.
4. Near the top of the code, replace `CHANGE_THIS_TO_YOUR_PASSWORD` with a private admin password of at least 8 characters.
5. Save the script. Do not run a setup function; the verified Spreadsheet ID is already configured. The `calibration_reports`, `performance_reports`, `offer_letters`, and `appointment_letters` tabs are created automatically on first use.
6. Click **Deploy > New deployment > Web app**.
7. Set **Execute as** to **Me** and **Who has access** to **Anyone**.
8. Deploy, approve Google's permission request, and copy the URL ending in `/exec`.
9. Paste that URL into `GOOGLE_SHEETS_WEB_APP_URL` near the top of the website's `script.js`.

The spreadsheet already contains these two wire-data tabs:

- `nichrome_wires`
- `kanthal_d_wires`

The updated backend also creates and maintains:

- `calibration_reports` — one searchable row per report, with the complete editable report stored in the `payload_json` column
- `performance_reports` — one searchable row per linked performance report, including calculated readings and results in `payload_json`
- `offer_letters` — one searchable row per confirmed offer, with every editable placeholder stored in the `payload_json` column
- `appointment_letters` — one searchable row per issued appointment letter, stored independently from offers with the complete four-page letter data in `payload_json`

Reads are public so the calculator can load. Writes require the admin password stored privately in Apps Script properties. After changing `Code.gs`, create a new Web App version from **Deploy > Manage deployments** so the live backend receives the change.

Calibration, performance-report, offer-letter, and appointment-letter saves are designed for this internal operations interface and do not use the wire-database admin password. If the site will be public, restrict the Web App deployment to your organisation before using shared record storage.
