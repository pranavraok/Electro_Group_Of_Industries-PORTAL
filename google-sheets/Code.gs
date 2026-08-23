/**
 * Google Sheets backend for the Industrial Heater Coil Calculator.
 * Bind this script to the Google Sheet, set the admin password below, then
 * deploy it as a Web App that executes as you and is accessible to anyone.
 */

const HEADERS = ["id", "swg", "thickness", "ohm", "minw", "maxw"];
const ALLOWED_TABLES = ["nichrome_wires", "kanthal_d_wires"];
const REPORT_SHEET = "calibration_reports";
const REPORT_HEADERS = [
  "id", "report_no", "page_no", "cal_on", "cal_due", "customer_name",
  "device", "serial_no", "equipment", "location", "status", "payload_json", "updated_at"
];
const SPREADSHEET_ID = "1fuzplqthrPBaIbyuaGIOg_n1Z8XnSSdimjJjArl76So";
const ADMIN_PASSWORD = "CHANGE_THIS_TO_YOUR_PASSWORD";

function doGet(event) {
  try {
    const action = String((event.parameter && event.parameter.action) || "");

    if (action === "listReports") {
      return json_({ ok: true, data: listReports_() });
    }

    if (action !== "read") throw new Error("Unsupported request.");

    const table = validateTable_(event.parameter.table);
    return json_({ ok: true, data: readTable_(table) });
  } catch (error) {
    return json_({ ok: false, error: error.message });
  }
}

function doPost(event) {
  try {
    const body = JSON.parse((event.postData && event.postData.contents) || "{}");

    if (body.action === "authenticate") {
      requireAdmin_(body.password);
      return json_({ ok: true });
    }

    if (body.action === "save") {
      requireAdmin_(body.password);
      const table = validateTable_(body.table);
      const rows = validateRows_(body.data);
      saveTable_(table, rows);
      return json_({ ok: true, saved: rows.length });
    }

    if (body.action === "saveReport") {
      const report = validateReport_(body.report);
      saveReport_(report);
      return json_({ ok: true, id: report.id, reportNo: report.reportNo });
    }

    throw new Error("Unsupported request.");
  } catch (error) {
    return json_({ ok: false, error: error.message });
  }
}

function getReportSheet_() {
  const spreadsheet = getSpreadsheet_();
  let sheet = spreadsheet.getSheetByName(REPORT_SHEET);
  if (!sheet) {
    sheet = spreadsheet.insertSheet(REPORT_SHEET);
    sheet.getRange(1, 1, 1, REPORT_HEADERS.length).setValues([REPORT_HEADERS]);
    formatReportSheet_(sheet);
  }
  return sheet;
}

function listReports_() {
  const sheet = getReportSheet_();
  if (sheet.getLastRow() < 2) return [];
  return sheet.getRange(2, 1, sheet.getLastRow() - 1, REPORT_HEADERS.length).getValues()
    .filter(function (row) { return row[0] !== ""; })
    .map(function (row) {
      try { return JSON.parse(String(row[11] || "{}")); }
      catch (_error) { return null; }
    })
    .filter(function (report) { return report && report.id; })
    .sort(function (a, b) { return String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")); });
}

function saveReport_(report) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    const sheet = getReportSheet_();
    const lastRow = sheet.getLastRow();
    let targetRow = lastRow + 1;
    if (lastRow >= 2) {
      const ids = sheet.getRange(2, 1, lastRow - 1, 1).getDisplayValues();
      for (let index = 0; index < ids.length; index++) {
        if (String(ids[index][0]) === report.id) {
          targetRow = index + 2;
          break;
        }
      }
    }
    const values = [[
      report.id, report.reportNo, report.pageNo, report.calOn, report.calDue,
      report.customerName, report.device, report.serialNo, report.equipment,
      report.location, report.status, JSON.stringify(report), report.updatedAt
    ]];
    sheet.getRange(targetRow, 1, 1, REPORT_HEADERS.length).setValues(values);
    formatReportSheet_(sheet);
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
}

function validateReport_(source) {
  if (!source || typeof source !== "object") throw new Error("Calibration report is missing.");
  const report = JSON.parse(JSON.stringify(source));
  ["id", "reportNo", "pageNo", "calOn", "calDue", "customerName"].forEach(function (field) {
    if (!String(report[field] || "").trim()) throw new Error("Missing report field: " + field);
  });
  if (!Array.isArray(report.readings) || report.readings.length === 0 || report.readings.length > 50) {
    throw new Error("Calibration readings are missing or invalid.");
  }
  if (JSON.stringify(report).length > 45000) throw new Error("Calibration report is too large.");
  return report;
}

function formatReportSheet_(sheet) {
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, REPORT_HEADERS.length)
    .setFontWeight("bold")
    .setBackground("#0f766e")
    .setFontColor("#ffffff");
  sheet.getRange("D:E").setNumberFormat("yyyy-mm-dd");
  sheet.autoResizeColumns(1, REPORT_HEADERS.length);
  sheet.setColumnWidth(12, 420);
}

function readTable_(tableName) {
  const sheet = getSpreadsheet_().getSheetByName(tableName);
  if (!sheet || sheet.getLastRow() < 2) return [];

  const values = sheet.getRange(2, 1, sheet.getLastRow() - 1, HEADERS.length).getValues();
  return values
    .filter(function (row) { return row.some(function (value) { return value !== ""; }); })
    .map(function (row) {
      const item = {};
      HEADERS.forEach(function (header, index) { item[header] = Number(row[index]); });
      return item;
    })
    .sort(function (a, b) { return a.swg - b.swg || a.id - b.id; });
}

function saveTable_(tableName, rows) {
  const lock = LockService.getScriptLock();
  lock.waitLock(10000);

  try {
    const sheet = getSpreadsheet_().getSheetByName(tableName);
    if (!sheet) throw new Error("Sheet not found. Run setupDatabase first.");

    const values = rows.map(function (row) {
      return HEADERS.map(function (header) { return row[header]; });
    });
    const rowsToClear = Math.max(sheet.getLastRow() - 1, 0);
    if (rowsToClear) sheet.getRange(2, 1, rowsToClear, HEADERS.length).clearContent();
    if (values.length) sheet.getRange(2, 1, values.length, HEADERS.length).setValues(values);
    formatSheet_(sheet);
    SpreadsheetApp.flush();
  } finally {
    lock.releaseLock();
  }
}

function validateRows_(data) {
  if (!Array.isArray(data) || data.length === 0 || data.length > 500) {
    throw new Error("Database rows are missing or invalid.");
  }

  const ids = {};
  return data.map(function (source, index) {
    const row = {};
    HEADERS.forEach(function (header) { row[header] = Number(source[header]); });

    if (!HEADERS.every(function (header) { return Number.isFinite(row[header]); })) {
      throw new Error("Row " + (index + 1) + " contains a non-numeric value.");
    }
    if (row.id <= 0 || row.swg <= 0 || row.thickness <= 0 || row.ohm <= 0 ||
        row.minw < 0 || row.maxw < row.minw) {
      throw new Error("Row " + (index + 1) + " contains invalid values.");
    }
    if (ids[row.id]) throw new Error("Duplicate row ID: " + row.id);
    ids[row.id] = true;
    return row;
  }).sort(function (a, b) { return a.swg - b.swg || a.id - b.id; });
}

function validateTable_(tableName) {
  const table = String(tableName || "");
  if (ALLOWED_TABLES.indexOf(table) === -1) throw new Error("Unknown wire table.");
  return table;
}

function requireAdmin_(candidate) {
  if (ADMIN_PASSWORD === "CHANGE_THIS_TO_YOUR_PASSWORD" || ADMIN_PASSWORD.length < 8) {
    throw new Error("Set ADMIN_PASSWORD in Code.gs before deploying.");
  }
  if (String(candidate || "") !== ADMIN_PASSWORD) throw new Error("Incorrect password");
}

function getSpreadsheet_() {
  return SpreadsheetApp.openById(SPREADSHEET_ID);
}

function formatSheet_(sheet) {
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, HEADERS.length)
    .setFontWeight("bold")
    .setBackground("#1f4e78")
    .setFontColor("#ffffff");
  sheet.autoResizeColumns(1, HEADERS.length);
}

function json_(value) {
  return ContentService
    .createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
