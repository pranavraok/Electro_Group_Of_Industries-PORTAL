/* =========================================================
   GLOBAL STATE
========================================================= */

let activeMaterial = null;
let activeTable = null;
let wireData = [];
let coreODOverridden = false;
let currentScreen = "material";
let currentHistoryIndex = 0;
let loadedTable = null;
let adminPassword = "";
let calibrationReports = [];
let editingReportId = null;

const APP_HISTORY_KEY = "heater-coil-calculator";
const REPORT_STORAGE_KEY = "electrotech-calibration-reports-v1";
const REPORT_SEQUENCE_KEY = "electro-group-calibration-sequence-v1";
const HEATER_CALCULATION_COUNT_KEY = "electro-group-heater-calculation-count-v1";

/* Available standard core diameters (mm) – sorted ascending */
const STANDARD_CORE_SIZES = [
  3.8, 4.1, 4.5, 5, 5.8, 6, 6.5, 7, 7.5, 7.7,
  8, 8.5, 9.2, 10, 10.5, 11, 12, 12.2, 13, 14,
  15.5, 16, 18, 21.3
];

/* Sorted available pipe OD stock sizes (mm) */
const PIPE_OD_SIZES = [
  9.5, 10.5, 11, 12.7, 13.5, 14, 14.5, 15.5, 15.8,
  17.5, 18, 18.5, 18.8, 20, 21.4, 27
];

/* Stock pipe inventory – each entry is { od, thickness } in mm */
const PIPE_INVENTORY = [
  { od: 15.8, thickness: 0.8 },
  { od: 15.5, thickness: 0.8 },
  { od: 14.5, thickness: 1.0 },
  { od: 14,   thickness: 1.0 },
  { od: 13.5, thickness: 0.8 },
  { od: 13.5, thickness: 1.0 },
  { od: 13.5, thickness: 0.7 },
  { od: 11,   thickness: 0.8 },
  { od: 18.8, thickness: 0.8 },
  { od: 18.5, thickness: 1.0 },
  { od: 17.5, thickness: 1.0 },
  { od: 17.5, thickness: 0.8 },
  { od: 18,   thickness: 1.0 },
  { od: 27,   thickness: 1.2 },
  { od: 21.4, thickness: 1.0 },
  { od: 20,   thickness: 1.0 },
  { od: 18,   thickness: 0.8 },
  { od: 14,   thickness: 0.8 },
  { od: 15.5, thickness: 1.0 },
  { od: 12.7, thickness: 0.6 },
  { od: 9.5,  thickness: 0.6 },
  { od: 10.5, thickness: 0.8 }
];

/* =========================================================
   DOM REFERENCES
========================================================= */

const materialSelect = document.getElementById("materialSelect");
const dashboard = document.getElementById("dashboard");
const landing = document.getElementById("landing");
const calculator = document.getElementById("calculator");
const dbEditor = document.getElementById("dbEditor");
const reportBuilder = document.getElementById("reportBuilder");
const recordsView = document.getElementById("recordsView");
const passwordModal = document.getElementById("passwordModal");
const saveModal = document.getElementById("saveModal");
const result = document.getElementById("result");

const wattage = document.getElementById("wattage");
const voltage = document.getElementById("voltage");

const heaterODInput = document.getElementById("heaterOD");
const heaterLengthInput = document.getElementById("heaterLength");
const coreLengthInput = document.getElementById("coreLength");
const pipeThicknessInput = document.getElementById("pipeThickness");
const pipeODInput = document.getElementById("pipeOD");
const coreODInput = document.getElementById("coreOD");

const autoThicknessCheckbox = document.getElementById("autoThickness");
const autoPipeODCheckbox = document.getElementById("autoPipeOD");
const autoCoreODCheckbox = document.getElementById("autoCoreOD");
const coreODStatusEl = document.getElementById("coreODStatus");

const extraInput = document.getElementById("extra");

const materialLabel = document.getElementById("materialLabel");
const materialLabelCalc = document.getElementById("materialLabelCalc");

/* =========================================================
   GOOGLE SHEETS CONNECTION
========================================================= */

// Paste the /exec URL created by deploying google-sheets/Code.gs as a Web App.
const GOOGLE_SHEETS_WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxS99O2UMAulozNxPtyhhlI1qioxrwJxRWdMqSux_FQk-wELsZVWzrOeglKd5_6NNU-XA/exec";

function isGoogleSheetsConfigured() {
  return /^https:\/\/script\.google\.com\/macros\/s\/.+\/exec$/.test(
    GOOGLE_SHEETS_WEB_APP_URL
  );
}

async function sheetsApiRequest(action, payload = {}) {
  if (!isGoogleSheetsConfigured()) {
    throw new Error(
      "Google Sheets is not connected yet. Add the Apps Script Web App URL in script.js."
    );
  }

  const isRead = action === "read" || action === "listReports";
  const options = isRead
    ? { method: "GET", redirect: "follow", cache: "no-store" }
    : {
        method: "POST",
        redirect: "follow",
        headers: { "Content-Type": "text/plain;charset=utf-8" },
        body: JSON.stringify({ action, ...payload })
      };
  const url = isRead
    ? `${GOOGLE_SHEETS_WEB_APP_URL}?action=${encodeURIComponent(action)}${payload.table ? `&table=${encodeURIComponent(payload.table)}` : ""}&t=${Date.now()}`
    : GOOGLE_SHEETS_WEB_APP_URL;

  const response = await fetch(url, options);
  const responseText = await response.text();
  let result;

  try {
    result = JSON.parse(responseText);
  } catch (_error) {
    throw new Error("Google Sheets returned an invalid response. Check the Web App deployment URL and access settings.");
  }

  if (!response.ok || !result.ok) {
    throw new Error(result.error || `Google Sheets request failed (${response.status}).`);
  }

  return result;
}

/* =========================================================
   MATERIAL SELECTION
========================================================= */

function setMaterialContext(type) {
  activeMaterial = type;

  activeTable =
    type === "nichrome"
      ? "nichrome_wires"
      : "kanthal_d_wires";

  const labelText =
    type === "nichrome"
      ? "Material: Nichrome"
      : "Material: Kanthal D";

  materialLabel.innerText = labelText;

  if (materialLabelCalc) {
    materialLabelCalc.innerText = labelText;
  }
}

function renderScreen(screen, material = activeMaterial, options = {}) {
  currentScreen = screen;
  closeMobileSidebar();

  passwordModal.classList.add("hidden");
  saveModal.classList.add("hidden");
  dashboard.classList.add("hidden");
  materialSelect.classList.add("hidden");
  landing.classList.add("hidden");
  calculator.classList.add("hidden");
  dbEditor.classList.add("hidden");
  reportBuilder.classList.add("hidden");
  recordsView.classList.add("hidden");

  document.querySelectorAll(".nav-btn, .nav-subbtn").forEach((button) => {
    const target = button.dataset.screen;
    const activeTarget = ["landing", "calculator", "database"].includes(screen) ? "material" : screen;
    button.classList.toggle("active", target === activeTarget);
  });
  const calibrationGroup = document.querySelector('[data-nav-group="calibration"]');
  const calibrationActive = ["reports", "records"].includes(screen);
  calibrationGroup.classList.toggle("active", calibrationActive);
  if (calibrationActive) calibrationGroup.classList.add("open");
  else calibrationGroup.classList.remove("open");

  const titleMap = {
    dashboard: "Operations & Automation",
    material: "Heater Coil Calculator",
    landing: "Heater Coil Calculator",
    calculator: "Heater Coil Calculator",
    database: "Wire Database",
    reports: "Calibration Report Builder",
    records: "Calibration Report Records"
  };
  const pageTitle = document.getElementById("pageTitle");
  if (pageTitle) pageTitle.textContent = titleMap[screen] || "Operations & Automation";

  if (screen === "dashboard") {
    dashboard.classList.remove("hidden");
    loadLocalReports();
    refreshDashboardMetrics();
    syncReportsFromSheet();
    return;
  }

  if (screen === "reports") {
    reportBuilder.classList.remove("hidden");
    if (!options.keepDraft && !editingReportId) ensureReportDefaults();
    renderCalibrationPreview();
    return;
  }

  if (screen === "records") {
    recordsView.classList.remove("hidden");
    loadLocalReports();
    renderReportRecords();
    syncReportsFromSheet();
    return;
  }

  if (screen === "material") {
    activeMaterial = null;
    activeTable = null;
    currentScreen = "material";
    materialSelect.classList.remove("hidden");
    return;
  }

  if (!material) {
    currentScreen = "material";
    materialSelect.classList.remove("hidden");
    return;
  }

  setMaterialContext(material);

  if (screen === "landing") {
    landing.classList.remove("hidden");
  } else if (screen === "calculator") {
    calculator.classList.remove("hidden");
    if (options.clearResult) result.innerHTML = "";
  } else if (screen === "database") {
    dbEditor.classList.remove("hidden");
    if (activeTable && loadedTable !== activeTable) {
      const table = document.getElementById("dbTable");
      table.innerHTML = "<tr><td>Loading database...</td></tr>";
      loadDatabase().then((loaded) => {
        if (loaded && currentScreen === "database") populateDBTable();
      });
      return;
    }

    populateDBTable();
  }

  if (activeTable && loadedTable !== activeTable) {
    loadDatabase();
  }
}

function saveHistoryState(screen, material = activeMaterial, replace = false) {
  const state = {
    app: APP_HISTORY_KEY,
    screen,
    material: ["material", "dashboard", "reports", "records"].includes(screen) ? null : material,
    index: replace ? currentHistoryIndex : currentHistoryIndex + 1
  };

  if (replace) {
    window.history.replaceState(state, "", window.location.href);
  } else {
    window.history.pushState(state, "", window.location.href);
  }

  currentHistoryIndex = state.index;
}

function navigateTo(screen, material = activeMaterial, options = {}) {
  saveHistoryState(screen, material, Boolean(options.replace));
  renderScreen(screen, material, options);
}

function goBackTo(fallbackScreen) {
  if (currentHistoryIndex > 0) {
    window.history.back();
    return;
  }

  navigateTo(fallbackScreen, activeMaterial, { replace: true });
}

function selectMaterial(type) {
  setMaterialContext(type);
  navigateTo("landing", type);
}

function backToMaterial() {
  goBackTo("material");
}

function openDashboard() {
  navigateTo("dashboard", null);
}

function toggleCalibrationNav() {
  document.querySelector('[data-nav-group="calibration"]').classList.toggle("open");
}

function openHeaterModule() {
  navigateTo("material", null);
}

async function openReportBuilder() {
  editingReportId = null;
  navigateTo("reports", null);
  resetReportForm();
  const provisionalNumber = reportField("reportNo").value;
  await syncReportsFromSheet();
  if (currentScreen === "reports" && !editingReportId && reportField("reportNo").value === provisionalNumber) {
    reportField("reportNo").value = "";
    reportField("pageNo").value = "";
    ensureReportDefaults();
    renderCalibrationPreview();
  }
}

function openReportRecords() {
  navigateTo("records", null);
}

/* =========================================================
   LOAD DATABASE
========================================================= */

async function loadDatabase() {
  const tableToLoad = activeTable;

  try {
    const result = await sheetsApiRequest("read", { table: tableToLoad });

    if (activeTable !== tableToLoad) return false;

    wireData = result.data;
    loadedTable = tableToLoad;
    return true;
  } catch (error) {
    console.error(error);
    showSaveModal("Google Sheets Error", error.message);
    return false;
  }
}

/* =========================================================
   NAVIGATION
========================================================= */

function openCalculator() {
  navigateTo("calculator", activeMaterial, { clearResult: true });
}

function backToLanding() {
  goBackTo("landing");
}

/* =========================================================
   AUTO/MANUAL TOGGLE FUNCTIONS
========================================================= */

function toggleAutoThickness() {
  const isAuto = autoThicknessCheckbox.checked;
  pipeThicknessInput.disabled = isAuto;
  if (isAuto) {
    pipeThicknessInput.value = '';
    pipeThicknessInput.placeholder = 'Auto';
    autoCalculateFields();
  }
}

function toggleAutoPipeOD() {
  const isAuto = autoPipeODCheckbox.checked;
  pipeODInput.disabled = isAuto;
  if (isAuto) {
    pipeODInput.value = '';
    pipeODInput.placeholder = 'Auto';
    autoCalculateFields();
  }
}

function toggleAutoCoreOD() {
  const isAuto = autoCoreODCheckbox.checked;
  if (isAuto) {
    coreODInput.value = '';
    coreODInput.placeholder = 'Auto';
    coreODOverridden = false;
    coreODStatusEl.textContent = '';
    autoCalculateFields();
  } else {
    coreODOverridden = true;
    coreODStatusEl.innerHTML = '<div class="cs-row cs-warn">Manual override active</div>';
  }
}

/* =========================================================
   INSULATION THICKNESS RULE  (based on watt density)
========================================================= */

/**
 * Returns insulation thickness in mm:
 *   wattDensity >= 9  → 2.0 mm
 *   wattDensity <  8  → 1.5 mm
 *   8 ≤ wattDensity < 9 → 1.7 mm (default mid-range)
 */
function getInsulationThickness(wattDensity) {
  if (wattDensity >= 9) return 2.0;
  if (wattDensity < 8)  return 1.5;
  return 1.7;
}

/**
 * Returns the smallest available pipe OD (from PIPE_OD_SIZES) that is
 * >= the required minimum based on heater OD and watt density:
 *   wattDensity >= 9  → pipeRequired = heaterOD + 2
 *   wattDensity <  9  → pipeRequired = heaterOD + 1.5
 * Returns null if no stock size is large enough.
 */
function selectPipeODFromStock(heaterOD, wattDensity) {
  const margin = wattDensity >= 9 ? 2 : 1.5;
  const pipeRequired = heaterOD + margin;
  for (const od of PIPE_OD_SIZES) {
    if (od >= pipeRequired) return od;
  }
  return null;
}

/**
 * From STANDARD_CORE_SIZES, returns the smallest size that is
 * greater than or equal to `theoretical`.
 * Returns null if no standard size fits.
 */
function selectStandardCoreOD(theoretical) {
  for (const size of STANDARD_CORE_SIZES) {
    if (size >= theoretical) return size;
  }
  return null;
}

function calculateCoreForWireThickness(pipeID, wireThickness, insulationThickness) {
  const theoreticalCoreOD = pipeID - (2 * wireThickness) - (2 * insulationThickness);
  if (theoreticalCoreOD <= 0) {
    return { invalidGeometry: true, theoreticalCoreOD, standardCoreOD: null };
  }

  const standardCoreOD = selectStandardCoreOD(theoreticalCoreOD);
  if (standardCoreOD === null) {
    return { invalidGeometry: true, theoreticalCoreOD, standardCoreOD: null };
  }

  return { invalidGeometry: false, theoreticalCoreOD, standardCoreOD };
}

function evaluatePrimarySWGSelection({ W, V, extra, coreLength, pipeID, insulationThickness }) {
  const startIndex = wireData.findIndex(w => W >= w.minw && W <= w.maxw);
  if (startIndex === -1) return null;

  const baseResistance = (V * V) / W;
  const finalResistance = baseResistance * (1 + extra / 100);

  for (let i = startIndex; i < wireData.length; i++) {
    const w = wireData[i];
    const coreCalc = calculateCoreForWireThickness(pipeID, w.thickness, insulationThickness);
    if (coreCalc.invalidGeometry) continue;

    const wireLengthMM = (finalResistance / w.ohm) * 1000;
    const turns = wireLengthMM / (Math.PI * coreCalc.standardCoreOD);
    const pitch = coreLength / turns;
    const idealPitch = 2 * w.thickness;

    let pass = false;
    if (w.swg >= 22 && w.swg <= 32) {
      pass = pitch >= idealPitch * 0.98;
    } else if (w.swg >= 33 && w.swg <= 45) {
      pass = pitch >= idealPitch;
    }

    if (pass) {
      return {
        wire: w,
        theoreticalCoreOD: coreCalc.theoreticalCoreOD,
        standardCoreOD: coreCalc.standardCoreOD
      };
    }
  }

  return null;
}

/* =========================================================
   AUTO-CALCULATE FIELDS IN REAL-TIME
========================================================= */

function autoCalculateFields() {

  const W          = Number(wattage.value);
  const heaterOD   = Number(heaterODInput.value);
  const heaterLength = Number(heaterLengthInput.value);

  // Watt density – needed for both pipe OD margin and insulation rule
  let wattDensity = 0;
  if (W && heaterOD && heaterLength) {
    const surfaceAreaCM2 = (Math.PI * heaterOD * heaterLength) / 100;
    wattDensity = W / surfaceAreaCM2;
  }

  // ── STEP 1: Pipe OD auto-selection ──────────────────────────────────
  // Rule: pipeRequired = heaterOD + 2   (wattDensity >= 9)
  //                    = heaterOD + 1.5  (wattDensity <  9)
  // Pick the smallest OD from PIPE_OD_SIZES that is >= pipeRequired.
  // Manual override: user unchecks Auto checkbox and types a value.
  // ─────────────────────────────────────────────────────────────────────
  if (autoPipeODCheckbox.checked) {
    if (heaterOD && wattDensity) {
      const selectedOD = selectPipeODFromStock(heaterOD, wattDensity);
      if (selectedOD !== null) {
        pipeODInput.value = selectedOD;
      } else {
        pipeODInput.value = '';
      }
    } else {
      pipeODInput.value = '';
    }
  }

  // ── STEP 2: Pipe Thickness auto-selection ───────────────────────────
  // Look up the selected pipe OD in PIPE_INVENTORY to get its thickness.
  // ─────────────────────────────────────────────────────────────────────
  if (autoThicknessCheckbox.checked) {
    const pipeODVal = Number(pipeODInput.value);
    if (pipeODVal > 0) {
      const matchingPipe = PIPE_INVENTORY.find(p => p.od === pipeODVal);
      pipeThicknessInput.value = matchingPipe ? matchingPipe.thickness : '';
    } else {
      pipeThicknessInput.value = '';
    }
  }

  // ── STEP 3: Core OD auto-selection ──────────────────────────────────
  // Uses same SWG loop logic as calculate() so wire thickness comes from
  // the actual selected SWG, not from wattage start-gauge preview.
  // ─────────────────────────────────────────────────────────────────────
  if (autoCoreODCheckbox.checked && wattDensity && wireData.length && W) {

    const pipeThicknessVal = Number(pipeThicknessInput.value);
    const pipeODVal        = Number(pipeODInput.value) || heaterOD;
    const V                = Number(voltage.value);
    const coreLengthVal    = Number(coreLengthInput.value);
    const extraVal         = Number(extraInput.value) || 0;

    if (pipeThicknessVal > 0) {
      const insulationThickness = getInsulationThickness(wattDensity);
      const pipeIDPreview = pipeODVal - (2 * pipeThicknessVal);

      if (!V || !coreLengthVal) {
        coreODInput.value = '';
        coreODStatusEl.innerHTML = '<div class="cs-row cs-note">Enter Voltage and Core Length to auto-calculate Core OD from SWG iteration</div>';
        return;
      }

      const selection = evaluatePrimarySWGSelection({
        W,
        V,
        extra: extraVal,
        coreLength: coreLengthVal,
        pipeID: pipeIDPreview,
        insulationThickness
      });

      if (!selection) {
        coreODInput.value = '';
        coreODStatusEl.innerHTML =
          '<div class="cs-row cs-err">No valid SWG + stock core combination found</div>';
      } else {
        coreODInput.value = selection.standardCoreOD;
        const margin = wattDensity >= 9 ? 2 : 1.5;
        coreODStatusEl.innerHTML =
          `<div class="cs-row"><span class="cs-key">Pipe OD selected</span><span class="cs-val">${pipeODVal} mm (heaterOD + ${margin})</span></div>` +
          `<div class="cs-row"><span class="cs-key">Pipe ID</span><span class="cs-val">${pipeIDPreview.toFixed(2)} mm</span></div>` +
          `<div class="cs-row"><span class="cs-key">SWG used</span><span class="cs-val">${selection.wire.swg} (${selection.wire.thickness.toFixed(3)} mm)</span></div>` +
          `<div class="cs-row"><span class="cs-key">Theoretical Core OD</span><span class="cs-val">${selection.theoreticalCoreOD.toFixed(2)} mm</span></div>` +
          `<div class="cs-row"><span class="cs-key">Insulation</span><span class="cs-val">${insulationThickness.toFixed(1)} mm x 2 sides</span></div>` +
          `<div class="cs-row cs-ok">Standard size selected (${selection.standardCoreOD.toFixed(2)} mm)</div>`;
      }

    } else if (autoPipeODCheckbox.checked && Number(pipeODInput.value) > 0) {
      // Pipe OD found but no matching thickness in inventory
      coreODStatusEl.innerHTML = '<div class="cs-row cs-err">No thickness found in stock for selected pipe OD</div>';
    }
  }
}

/* =========================================================
   ATTACH EVENT LISTENERS FOR REAL-TIME AUTO-FILL
========================================================= */

function setupAutoCalculation() {
  // Trigger auto-calculation when these fields change
  wattage.addEventListener('input', autoCalculateFields);
  voltage.addEventListener('input', autoCalculateFields);
  heaterODInput.addEventListener('input', autoCalculateFields);
  heaterLengthInput.addEventListener('input', autoCalculateFields);
  coreLengthInput.addEventListener('input', autoCalculateFields);
  pipeThicknessInput.addEventListener('input', autoCalculateFields);
  pipeODInput.addEventListener('input', autoCalculateFields);
  extraInput.addEventListener('input', autoCalculateFields);

  // Detect manual override on Core OD field
  coreODInput.addEventListener('input', () => {
    if (autoCoreODCheckbox.checked) {
      // User typed into the field — switch to manual override
      autoCoreODCheckbox.checked = false;
      coreODOverridden = true;
      coreODStatusEl.innerHTML = '<div class="cs-row cs-warn">Manual override active</div>';
    }
  });

  toggleAutoThickness();
  toggleAutoPipeOD();
  toggleAutoCoreOD();
}

// Initialize auto-calculation on page load
setupAutoCalculation();

/* =========================================================
   BROWSER BACK/FORWARD SUPPORT
========================================================= */

function setupHistoryNavigation() {
  const state = window.history.state;

  if (state && state.app === APP_HISTORY_KEY) {
    currentHistoryIndex = state.index || 0;
    renderScreen(state.screen || "dashboard", state.material);
  } else {
    saveHistoryState("dashboard", null, true);
    renderScreen("dashboard", null);
  }

  window.addEventListener("popstate", (event) => {
    const nextState = event.state;

    if (!nextState || nextState.app !== APP_HISTORY_KEY) {
      currentHistoryIndex = 0;
      renderScreen("dashboard");
      return;
    }

    currentHistoryIndex = nextState.index || 0;
    renderScreen(nextState.screen || "dashboard", nextState.material);
  });
}

setupHistoryNavigation();

function showResultError(message) {
  result.innerHTML = `<div class="alert">${message}</div>`;
}

function setupModalShortcuts() {
  const dbPasswordInput = document.getElementById("dbPassword");

  dbPasswordInput.addEventListener("keydown", (event) => {
    if (event.key === "Enter") checkPassword();
  });

  document.addEventListener("keydown", (event) => {
    if (event.key !== "Escape") return;
    closeMobileSidebar();
    if (!passwordModal.classList.contains("hidden")) closePassword();
    if (!saveModal.classList.contains("hidden")) closeSaveModal();
  });

  passwordModal.addEventListener("click", (event) => {
    if (event.target === passwordModal) closePassword();
  });

  saveModal.addEventListener("click", (event) => {
    if (event.target === saveModal) closeSaveModal();
  });
}

function toggleMobileSidebar() {
  const sidebar = document.querySelector(".sidebar");
  const overlay = document.getElementById("sidebarOverlay");
  const shouldOpen = !sidebar.classList.contains("mobile-open");

  sidebar.classList.toggle("mobile-open", shouldOpen);
  overlay.classList.toggle("visible", shouldOpen);
  document.body.classList.toggle("menu-open", shouldOpen);
}

function closeMobileSidebar() {
  document.querySelector(".sidebar")?.classList.remove("mobile-open");
  document.getElementById("sidebarOverlay")?.classList.remove("visible");
  document.body.classList.remove("menu-open");
}

window.addEventListener("resize", () => {
  if (window.innerWidth > 900) closeMobileSidebar();
});

setupModalShortcuts();

/* =========================================================
   MAIN CALCULATION
========================================================= */

function calculate() {

  const W = Number(wattage.value);
  const V = Number(voltage.value);
  const heaterOD = Number(heaterODInput.value);
  const heaterLength = Number(heaterLengthInput.value);
  const coreLength = Number(coreLengthInput.value);
  const extra = Number(extraInput.value) || 0;

  /* ---------------- VALIDATION ---------------- */

  if (!wireData.length) {
    showResultError("Database not loaded.");
    return;
  }

  if (!W || !V || !heaterOD || !heaterLength || !coreLength) {
    showResultError("Fill all required inputs.");
    return;
  }

  const coreOD = Number(coreODInput.value);

  if (!coreOD || coreOD <= 0) {
    if (autoCoreODCheckbox && autoCoreODCheckbox.checked) {
      showResultError("No valid stock pipe + core combination found.");
    } else {
      showResultError("Enter Core OD or enable Auto mode.");
    }
    return;
  }

  /* =====================================================
     STEP 1: WATT DENSITY (USING HEATER OD + HEATER LENGTH)
  ===================================================== */

  const heaterCircumference = Math.PI * heaterOD; // mm
  const surfaceAreaMM2 = heaterCircumference * heaterLength; // mm²
  const surfaceAreaCM2 = surfaceAreaMM2 / 100; // convert to cm²
  const wattDensity = W / surfaceAreaCM2;

  /* =====================================================
     STEP 1b: INSULATION THICKNESS (from watt density rule)
  ===================================================== */

  const insulationThickness = getInsulationThickness(wattDensity);
  const isCoreODAuto = autoCoreODCheckbox && autoCoreODCheckbox.checked;

  // Minimum pipe OD required by the insulation clearance rule
  const pipeODMargin   = wattDensity >= 9 ? 2 : 1.5;
  const pipeODRequired = heaterOD + pipeODMargin;

  /* =====================================================
     STEP 2: GET PIPE THICKNESS (ALREADY AUTO-FILLED OR MANUAL)
  ===================================================== */

  const pipeThickness = Number(pipeThicknessInput.value);
  
  if (!pipeThickness) {
    showResultError(
      autoThicknessCheckbox.checked
        ? "No valid stock pipe found."
        : "Enter pipe thickness."
    );
    return;
  }

  /* =====================================================
     STEP 3: GET PIPE OD (ALREADY AUTO-FILLED OR MANUAL)
  ===================================================== */

  const pipeOD = Number(pipeODInput.value);
  
  if (!pipeOD) {
    showResultError(
      autoPipeODCheckbox.checked
        ? "No valid stock pipe found."
        : "Enter pipe OD."
    );
    return;
  }

  /* =====================================================
     STEP 3b: PIPE ID CALCULATION
  ===================================================== */
  // Pipe ID = Pipe OD − (2 × Pipe Thickness)
  // In auto mode pipeOD comes from the stock inventory selection.
  const pipeID = pipeOD - (2 * pipeThickness);

  // Resolve the matching stock pipe entry ONCE – used for display and per-SWG core calc.
  // The pipe never changes during SWG iteration.
  const autoSelectedPipe = PIPE_INVENTORY.find(p => p.od === pipeOD) || null;

  /* =====================================================
     STEP 4: RESISTANCE CALCULATION
  ===================================================== */

  const baseResistance = (V * V) / W;
  const finalResistance = baseResistance * (1 + extra / 100);

  /* =====================================================
     STEP 5: FIND STARTING GAUGE FROM WATTAGE RANGE
  ===================================================== */

  const startIndex = wireData.findIndex(
    w => W >= w.minw && W <= w.maxw
  );

  if (startIndex === -1) {
    showResultError("No wire found for this wattage range.");
    return;
  }

  let results = [];
  let primaryIndex = -1;
  let found = false;

  /* =====================================================
     STEP 6: ITERATE GAUGE LOGIC
  ===================================================== */

  for (let i = startIndex; i < wireData.length; i++) {

    const w = wireData[i];

    /* ---- PER-SWG CORE SELECTION ──────────────────────────────────────
       Auto mode : pipe is FIXED (selected once via selectPipeODFromStock
                   before this loop). Only the core OD is re-snapped per
                   SWG because wire thickness varies between gauges.
       Manual mode: use the user-entered pipe OD / Core OD unchanged.
    ─────────────────────────────────────────────────────────────────── */
    // Pipe is fixed for ALL SWG iterations – selected once via selectPipeODFromStock()
    let effectiveCoreOD;
    let selectedPipe = isCoreODAuto ? autoSelectedPipe : null;
    let invalidGeometry = false;

    if (isCoreODAuto) {

      // Fixed pipe geometry – pipeOD and pipeThickness never change between iterations
      const coreCalc = calculateCoreForWireThickness(pipeID, w.thickness, insulationThickness);

      if (!autoSelectedPipe || coreCalc.invalidGeometry) {
        invalidGeometry = true;
        effectiveCoreOD = 0;
      } else {
        effectiveCoreOD = coreCalc.standardCoreOD;
      }

    } else {
      effectiveCoreOD = coreOD;
    }

    /* ---- SAFETY VALIDATION: skip turns/pitch for invalid geometry ---- */
    if (invalidGeometry) {
      results.push({
        swg: w.swg,
        thickness: w.thickness,
        ohm: w.ohm,
        wireLengthMeters: 0,
        turns: 0,
        pitch: 0,
        idealPitch: 2 * w.thickness,
        effectiveCoreOD: 0,
        selectedPipe: null,
        pass: false,
        invalidGeometry: true
      });
      if (!found) continue;  // try a thinner gauge – a different pipe may fit
      else break;
    }

    const wireLengthMeters = finalResistance / w.ohm;
    const wireLengthMM = wireLengthMeters * 1000;

    /* -------- TURNS CALCULATION (USING EFFECTIVE CORE OD) -------- */
    const circumferencePerTurn = Math.PI * effectiveCoreOD;
    const turns = wireLengthMM / circumferencePerTurn;

    /* -------- PITCH: SPACING BETWEEN TURNS (USING CORE LENGTH) -------- */
    const pitch = coreLength / turns;
    const idealPitch = 2 * w.thickness;

    let pass = false;

    if (w.swg >= 22 && w.swg <= 32) {
      pass = pitch >= idealPitch * 0.98;
    } else if (w.swg >= 33 && w.swg <= 45) {
      pass = pitch >= idealPitch;
    }

    results.push({
      swg: w.swg,
      thickness: w.thickness,
      ohm: w.ohm,
      wireLengthMeters,
      turns,
      pitch,
      idealPitch,
      effectiveCoreOD,
      selectedPipe,
      pass,
      invalidGeometry: false
    });

    if (pass && !found) {
      primaryIndex = results.length - 1;
      found = true;
    } else if (found) {
      break;
    }
  }

  /* ---- All evaluated gauges have invalid geometry → hard stop ---- */
  if (!found && results.length > 0 && results.every(r => r.invalidGeometry)) {
    showResultError("No valid stock pipe + core combination found.");
    return;
  }

  /* =====================================================
     FINAL OUTPUT
  ===================================================== */

  // Resolve display values for the summary
  const primaryResult = primaryIndex >= 0 ? results[primaryIndex] : null;
  const primaryPipe   = (isCoreODAuto && primaryResult) ? primaryResult.selectedPipe : null;

  const displayPipeOD        = primaryPipe ? primaryPipe.od        : pipeOD;
  const displayPipeThickness = primaryPipe ? primaryPipe.thickness : pipeThickness;
  const displayPipeID        = displayPipeOD - 2 * displayPipeThickness;
  const displayCoreOD        = (isCoreODAuto && primaryResult) ? primaryResult.effectiveCoreOD : coreOD;

  incrementHeaterCalculationCount();

  result.innerHTML = `
    <div class="result-stack">
      <div class="result-grid">
      <div class="info-grid">
        <div class="info-grid-header">Geometry</div>
        <div class="info-row"><div class="info-label">Material</div><div class="info-value">${(activeMaterial || '-').toUpperCase()}</div></div>
        <div class="info-row"><div class="info-label">Heater OD</div><div class="info-value">${heaterOD.toFixed(2)} mm</div></div>
        <div class="info-row"><div class="info-label">Pipe OD</div><div class="info-value">${displayPipeOD.toFixed(2)} mm <span class="info-tag">${isCoreODAuto ? 'Stock' : 'Manual'}</span></div></div>
        <div class="info-row"><div class="info-label">Pipe Wall</div><div class="info-value">${displayPipeThickness.toFixed(2)} mm</div></div>
        <div class="info-row"><div class="info-label">Pipe ID</div><div class="info-value">${displayPipeID.toFixed(2)} mm</div></div>
        <div class="info-row"><div class="info-label">Core OD</div><div class="info-value">${displayCoreOD > 0 ? displayCoreOD.toFixed(2) + ' mm' : '-'} ${!isCoreODAuto ? '<span class="info-tag info-tag--warn">Manual</span>' : '<span class="info-tag">Auto</span>'}</div></div>
        <div class="info-row"><div class="info-label">Core Length</div><div class="info-value">${coreLength.toFixed(2)} mm</div></div>
        <div class="info-row"><div class="info-label">Insulation</div><div class="info-value">${insulationThickness.toFixed(1)} mm x 2</div></div>
      </div>

      <div class="info-grid">
        <div class="info-grid-header">Electrical</div>
        <div class="info-row"><div class="info-label">Wattage</div><div class="info-value">${W.toFixed(2)} W</div></div>
        <div class="info-row"><div class="info-label">Voltage</div><div class="info-value">${V.toFixed(2)} V</div></div>
        <div class="info-row"><div class="info-label">Surface Area</div><div class="info-value">${surfaceAreaCM2.toFixed(2)} cm2</div></div>
        <div class="info-row"><div class="info-label">Watt Density</div><div class="info-value">${wattDensity.toFixed(2)} W/cm2</div></div>
        <div class="info-row"><div class="info-label">Base Resistance</div><div class="info-value">${baseResistance.toFixed(2)} Ohm</div></div>
        <div class="info-row"><div class="info-label">Final Resistance</div><div class="info-value">${finalResistance.toFixed(2)} Ohm</div></div>
        <div class="info-row"><div class="info-label">Extra</div><div class="info-value">${extra.toFixed(2)}%</div></div>
      </div>
      </div>
    </div>

    <div class="table-wrapper">
      <table>
        <tr>
          <th>SWG</th>
          <th>Thickness (mm)</th>
          <th>Ohm / m</th>
          <th>Wire Length (m)</th>
          ${isCoreODAuto ? '<th>Pipe OD (mm)</th><th>Core OD (mm)</th>' : ''}
          <th>Turns</th>
          <th>Pitch (mm)</th>
          <th>2 x Thickness</th>
          <th>Status</th>
        </tr>

        ${results.map((r, i) => `
          <tr class="${
            i === primaryIndex
              ? "primary"
              : r.pass
              ? "secondary"
              : "fail"
          }">
            <td>${r.swg}</td>
            <td>${r.thickness.toFixed(3)}</td>
            <td>${r.ohm.toFixed(3)}</td>
            <td>${r.invalidGeometry ? '-' : r.wireLengthMeters.toFixed(2)}</td>
            ${isCoreODAuto ? `
              <td>${r.invalidGeometry || !r.selectedPipe ? '-' : r.selectedPipe.od.toFixed(1) + ' / ' + r.selectedPipe.thickness.toFixed(1)}</td>
              <td>${r.invalidGeometry ? '-' : r.effectiveCoreOD.toFixed(2)}</td>
            ` : ''}
            <td>${r.invalidGeometry ? '-' : r.turns.toFixed(0)}</td>
            <td>${r.invalidGeometry ? '-' : r.pitch.toFixed(3)}</td>
            <td>${r.idealPitch.toFixed(3)}</td>
            <td>${
              r.invalidGeometry
                ? '<span class="status-pill status-pill--warn">NO FIT</span>'
                : r.pass
                ? '<span class="status-pill status-pill--ok">PASS</span>'
                : '<span class="status-pill status-pill--fail">FAIL</span>'
            }</td>
          </tr>
        `).join("")}
      </table>
    </div>
  `;
}

/* =========================================================
   PASSWORD MODAL FUNCTIONS
========================================================= */

function openPassword() {
  passwordModal.classList.remove("hidden");
  document.getElementById("dbPassword").value = "";
  document.getElementById("passError").innerText = "";
  setTimeout(() => document.getElementById("dbPassword").focus(), 0);
}

function closePassword() {
  passwordModal.classList.add("hidden");
}

async function checkPassword() {
  const pass = document.getElementById("dbPassword").value;
  const passError = document.getElementById("passError");
  const enterButton = passwordModal.querySelector(".primary-action");

  if (!pass) {
    passError.innerText = "Enter the admin password";
    return;
  }

  enterButton.disabled = true;
  enterButton.innerText = "Checking...";
  passError.innerText = "";

  try {
    await sheetsApiRequest("authenticate", { password: pass });
    adminPassword = pass;
    closePassword();
    openDatabase();
  } catch (error) {
    console.error(error);
    passError.innerText = error.message;
  } finally {
    enterButton.disabled = false;
    enterButton.innerText = "Enter";
  }
}

/* =========================================================
   DATABASE EDITOR FUNCTIONS
========================================================= */

function openDatabase() {
  navigateTo("database", activeMaterial);
}

function populateDBTable() {
  const table = document.getElementById("dbTable");
  
  if (!wireData.length) {
    table.innerHTML = "<tr><td>No data loaded</td></tr>";
    return;
  }

  let html = `
    <thead>
      <tr>
        <th>SWG</th>
        <th>Thickness (mm)</th>
        <th>Ohm / m</th>
        <th>Min Wattage</th>
        <th>Max Wattage</th>
      </tr>
    </thead>
    <tbody>
  `;

  wireData.forEach((wire, idx) => {
    html += `
      <tr>
        <td><input type="number" value="${wire.swg}" data-idx="${idx}" data-field="swg"></td>
        <td><input type="number" step="0.001" value="${wire.thickness}" data-idx="${idx}" data-field="thickness"></td>
        <td><input type="number" step="0.001" value="${wire.ohm}" data-idx="${idx}" data-field="ohm"></td>
        <td><input type="number" value="${wire.minw}" data-idx="${idx}" data-field="minw"></td>
        <td><input type="number" value="${wire.maxw}" data-idx="${idx}" data-field="maxw"></td>
      </tr>
    `;
  });

  html += `</tbody>`;
  table.innerHTML = html;

  // Add event listeners to update wireData when inputs change
  table.querySelectorAll("input").forEach(input => {
    input.addEventListener("input", (e) => {
      const idx = parseInt(e.target.dataset.idx);
      const field = e.target.dataset.field;
      const value = parseFloat(e.target.value) || 0;
      wireData[idx][field] = value;
    });
  });
}

async function saveDatabase() {
  const saveBtn = document.getElementById("saveBtn");
  const invalidRow = wireData.find((wire) =>
    !Number.isFinite(Number(wire.swg)) ||
    !Number.isFinite(Number(wire.thickness)) ||
    !Number.isFinite(Number(wire.ohm)) ||
    !Number.isFinite(Number(wire.minw)) ||
    !Number.isFinite(Number(wire.maxw)) ||
    Number(wire.swg) <= 0 ||
    Number(wire.thickness) <= 0 ||
    Number(wire.ohm) <= 0 ||
    Number(wire.minw) < 0 ||
    Number(wire.maxw) < Number(wire.minw)
  );

  if (invalidRow) {
    showSaveModal("Check Values", "Fix database values before saving.");
    return;
  }

  saveBtn.disabled = true;
  saveBtn.innerText = "Saving...";

  try {
    await sheetsApiRequest("save", {
      table: activeTable,
      password: adminPassword,
      data: wireData
    });

    showSaveModal("Saved", "Google Sheet saved successfully.");
  } catch (err) {
    console.error(err);
    showSaveModal("Google Sheets Error", err.message);
  } finally {
    saveBtn.disabled = false;
    saveBtn.innerText = "Save Changes";
  }
}

/* =========================================================
   SAVE STATUS MODAL
========================================================= */

function showSaveModal(title, message) {
  document.getElementById("saveTitle").innerText = title;
  document.getElementById("saveMessage").innerText = message;
  document.getElementById("saveModal").classList.remove("hidden");
}

function closeSaveModal() {
  document.getElementById("saveModal").classList.add("hidden");
}

/* =========================================================
   CALIBRATION REPORT AUTOMATION
========================================================= */

function reportField(name) {
  return document.querySelector(`[data-report-field="${name}"]`);
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function toInputDate(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function formatReportDate(value) {
  if (!value) return "—";
  const [year, month, day] = String(value).split("-");
  return year && month && day ? `${day}-${month}-${year}` : value;
}

function calculateDueDate(calibrationDate) {
  const date = calibrationDate ? new Date(`${calibrationDate}T12:00:00`) : new Date();
  date.setFullYear(date.getFullYear() + 1);
  date.setDate(date.getDate() - 1);
  return toInputDate(date);
}

function getFinancialYearCode(date = new Date()) {
  const startYear = date.getMonth() >= 3 ? date.getFullYear() : date.getFullYear() - 1;
  return `${String(startYear).slice(-2)}-${String(startYear + 1).slice(-2)}`;
}

function loadLocalReports() {
  try {
    const saved = JSON.parse(localStorage.getItem(REPORT_STORAGE_KEY) || "[]");
    calibrationReports = Array.isArray(saved) ? saved : [];
  } catch (_error) {
    calibrationReports = [];
  }
  return calibrationReports;
}

function persistLocalReports() {
  localStorage.setItem(REPORT_STORAGE_KEY, JSON.stringify(calibrationReports));
}

function extractReportSequence(reportNumber) {
  const match = String(reportNumber || "").match(/(?:ETS|EGI)\/CAL\/(\d+)/i);
  return match ? Number(match[1]) : null;
}

function readReportSequenceState() {
  try {
    const value = JSON.parse(localStorage.getItem(REPORT_SEQUENCE_KEY) || "null");
    return value && Number.isFinite(Number(value.sequence)) ? value : null;
  } catch (_error) {
    return null;
  }
}

function rememberReportSequence(reportNumber, updatedAt = new Date().toISOString()) {
  const sequence = extractReportSequence(reportNumber);
  if (!Number.isFinite(sequence)) return;
  localStorage.setItem(REPORT_SEQUENCE_KEY, JSON.stringify({ sequence, updatedAt }));
}

async function syncReportsFromSheet() {
  try {
    const response = await sheetsApiRequest("listReports");
    if (!Array.isArray(response.data)) return;
    const combined = new Map(calibrationReports.map((report) => [report.id, report]));
    response.data.forEach((remoteReport) => {
      const localReport = combined.get(remoteReport.id);
      if (!localReport || String(remoteReport.updatedAt || "") > String(localReport.updatedAt || "")) {
        combined.set(remoteReport.id, remoteReport);
      }
    });
    calibrationReports = Array.from(combined.values()).sort((a, b) => String(b.updatedAt || "").localeCompare(String(a.updatedAt || "")));
    persistLocalReports();
    const newestReport = calibrationReports[0];
    const sequenceState = readReportSequenceState();
    if (newestReport && (!sequenceState || String(newestReport.updatedAt || "") > String(sequenceState.updatedAt || ""))) {
      rememberReportSequence(newestReport.reportNo, newestReport.updatedAt);
    }
    if (currentScreen === "records") renderReportRecords();
    if (currentScreen === "dashboard") refreshDashboardMetrics();
  } catch (error) {
    console.info("Shared report register is waiting for the updated Apps Script deployment.");
  }
}

function nextReportSequence() {
  loadLocalReports();
  const sequenceState = readReportSequenceState();
  if (sequenceState) return Number(sequenceState.sequence) + 1;
  const newestSequence = calibrationReports.length ? extractReportSequence(calibrationReports[0].reportNo) : null;
  if (Number.isFinite(newestSequence)) return newestSequence + 1;
  const highest = calibrationReports.reduce((max, report) => Math.max(max, extractReportSequence(report.reportNo) || 0), 0);
  return highest + 1;
}

function getHeaterCalculationCount() {
  return Number(localStorage.getItem(HEATER_CALCULATION_COUNT_KEY) || 0);
}

function incrementHeaterCalculationCount() {
  localStorage.setItem(HEATER_CALCULATION_COUNT_KEY, String(getHeaterCalculationCount() + 1));
}

function refreshDashboardMetrics() {
  const total = calibrationReports.length;
  const passed = calibrationReports.filter((report) => report.status === "Pass").length;
  const today = new Date();
  today.setHours(0, 0, 0, 0);
  const thirtyDays = 30 * 24 * 60 * 60 * 1000;
  const dueSoon = calibrationReports.filter((report) => {
    if (!report.calDue) return false;
    const due = new Date(`${report.calDue}T00:00:00`);
    const difference = due.getTime() - today.getTime();
    return difference >= 0 && difference <= thirtyDays;
  }).length;

  document.getElementById("dashboardTotalReports").textContent = total;
  document.getElementById("dashboardPassedReports").textContent = passed;
  document.getElementById("dashboardDueSoon").textContent = dueSoon;
  document.getElementById("dashboardHeaterRuns").textContent = getHeaterCalculationCount();

  const recentList = document.getElementById("dashboardRecentReports");
  const recent = calibrationReports.slice(0, 5);
  recentList.innerHTML = recent.length
    ? recent.map((report) => `<button class="recent-report" onclick="editCalibrationReport('${escapeHtml(report.id)}')"><span><strong>${escapeHtml(report.reportNo)}</strong><small>${escapeHtml(report.customerName || "No customer")}</small></span><span><small>${formatReportDate(report.calOn)}</small><b class="status-dot ${report.status === "Pass" ? "pass" : "review"}"></b></span></button>`).join("")
    : `<div class="dashboard-empty">No calibration reports yet.</div>`;
}

function ensureReportDefaults() {
  if (!document.getElementById("calibrationForm")) return;
  const today = new Date();
  const sequence = String(nextReportSequence()).padStart(3, "0");
  if (!reportField("calOn").value) reportField("calOn").value = toInputDate(today);
  if (!reportField("calDue").value) reportField("calDue").value = calculateDueDate(reportField("calOn").value);
  if (!reportField("reportNo").value) reportField("reportNo").value = `EGI/CAL/${sequence}/${getFinancialYearCode(today)}`;
  if (!reportField("pageNo").value) reportField("pageNo").value = sequence;
  if (!document.querySelector("#readingsBody tr")) {
    [0, 50, 100, 175, 250, 400].forEach((standard, index) => addReadingRow({ standard, duc: [0, 50, 100, 176, 249, 400][index] }, false));
  }
}

function addReadingRow(reading = {}, shouldRender = true) {
  const body = document.getElementById("readingsBody");
  if (!body) return;
  const row = document.createElement("tr");
  row.innerHTML = `
    <td class="reading-number"></td>
    <td><input type="number" step="0.01" data-reading-field="standard" value="${escapeHtml(reading.standard ?? "")}"></td>
    <td><input type="number" step="0.01" data-reading-field="duc" value="${escapeHtml(reading.duc ?? "")}"></td>
    <td class="calculated-value" data-reading-output="error">0</td>
    <td class="calculated-value pass" data-reading-output="remark">Pass</td>
    <td><button type="button" class="remove-reading" aria-label="Remove reading" onclick="removeReadingRow(this)">×</button></td>`;
  body.appendChild(row);
  renumberReadingRows();
  if (shouldRender) renderCalibrationPreview();
}

function removeReadingRow(button) {
  const body = document.getElementById("readingsBody");
  if (body.rows.length <= 1) return;
  button.closest("tr").remove();
  renumberReadingRows();
  renderCalibrationPreview();
}

function renumberReadingRows() {
  document.querySelectorAll("#readingsBody tr").forEach((row, index) => {
    row.querySelector(".reading-number").textContent = `${index + 1}.`;
  });
}

function getReadingRows() {
  const tolerance = Math.abs(Number(reportField("claimedError")?.value) || 0);
  return Array.from(document.querySelectorAll("#readingsBody tr")).map((row, index) => {
    const standardValue = row.querySelector('[data-reading-field="standard"]').value;
    const ducValue = row.querySelector('[data-reading-field="duc"]').value;
    const standard = Number(standardValue);
    const duc = Number(ducValue);
    const complete = standardValue !== "" && ducValue !== "";
    const error = complete ? duc - standard : 0;
    const allowedError = Math.abs(standard) * tolerance / 100;
    const pass = complete && Math.abs(error) <= allowedError + 0.000001;
    const errorOutput = row.querySelector('[data-reading-output="error"]');
    const remarkOutput = row.querySelector('[data-reading-output="remark"]');
    errorOutput.textContent = complete ? Number(error.toFixed(2)).toString() : "—";
    remarkOutput.textContent = complete ? (pass ? "Pass" : "Fail") : "—";
    remarkOutput.classList.toggle("pass", pass);
    remarkOutput.classList.toggle("fail", complete && !pass);
    return { index: index + 1, standard: complete ? standard : "", duc: complete ? duc : "", error: complete ? Number(error.toFixed(2)) : "", remark: complete ? (pass ? "Pass" : "Fail") : "" };
  });
}

function collectReportData() {
  const report = {};
  document.querySelectorAll("[data-report-field]").forEach((field) => {
    report[field.dataset.reportField] = field.value.trim();
  });
  report.readings = getReadingRows();
  report.status = report.readings.length && report.readings.every((reading) => reading.remark === "Pass") ? "Pass" : "Review";
  report.id = editingReportId || `CAL-${Date.now()}-${Math.random().toString(16).slice(2)}`;
  report.updatedAt = new Date().toISOString();
  return report;
}

function renderCalibrationPreview() {
  const preview = document.getElementById("calibrationPreview");
  if (!preview) return;
  const data = collectReportData();
  const address = escapeHtml(data.customerAddress || "Customer address").replaceAll("\n", "<br>");
  const readings = data.readings.length ? data.readings : [{ index: 1, standard: "", duc: "", error: "", remark: "" }];
  preview.innerHTML = `
    <div class="certificate-brand"><img class="certificate-service-logo" src="assets/electrotech-services-logo.png" alt="Electrotech Services"></div>
    <div class="certificate-title">CALIBRATION REPORT</div>
    <div class="certificate-customer"><strong>CUSTOMER'S NAME &amp; ADDRESS</strong><div class="certificate-address">${escapeHtml(data.customerName || "M/s. Customer name")}<br>${address}</div></div>
    <table class="certificate-control"><thead><tr><th>CAL. REPORT NO.</th><th>CAL. ON</th><th>CAL. DUE</th><th>PAGE NO.</th></tr></thead><tbody><tr><td>${escapeHtml(data.reportNo)}</td><td>${formatReportDate(data.calOn)}</td><td>${formatReportDate(data.calDue)}</td><td>${escapeHtml(data.pageNo)}</td></tr></tbody></table>
    <div class="certificate-equipment">
      <div class="line"><span><b>Device:</b> ${escapeHtml(data.device || "—")}</span><span><b>Make:</b> ${escapeHtml(data.make || "—")}</span><span><b>Sl No:</b> ${escapeHtml(data.serialNo || "—")}</span></div>
      <div class="line"><span><b>Equipment:</b> ${escapeHtml(data.equipment || "—")}</span><span><b>Location:</b> ${escapeHtml(data.location || "—")}</span><span></span></div>
      <div class="line"><span><b>Environment Condition:</b> ${escapeHtml(data.environment || "—")}</span><span><b>Room Temp.:</b> ± ${escapeHtml(data.roomTemp || "—")}°C</span><span><b>Humidity:</b> ${escapeHtml(data.humidity || "—")}</span></div>
    </div>
    <table class="certificate-readings"><thead><tr><th>Sl.<br>No</th><th>Parameter / Range<br>Temp/Ambt.</th><th>STD<br>Input</th><th>DUC<br>Reading</th><th>DUC error<br>claimed</th><th>DUC error<br>observed</th><th>Remarks</th></tr></thead><tbody>${readings.map((reading, index) => `<tr><td>${reading.index}.</td><td>${index === 0 ? `${escapeHtml(data.parameter || "—")}<br>(${escapeHtml(data.range || "—")})` : ""}</td><td>${reading.standard === "" ? "—" : escapeHtml(reading.standard) + "°C"}</td><td>${reading.duc === "" ? "—" : escapeHtml(reading.duc) + "°C"}</td><td>±${escapeHtml(data.claimedError || "0")}%</td><td>${reading.error === "" ? "—" : escapeHtml(reading.error)}</td><td>${escapeHtml(reading.remark || "—")}</td></tr>`).join("")}</tbody></table>
    <div class="certificate-standard"><strong>PRIMARY STANDARD USED :</strong><div class="standard-details"><span>${escapeHtml(data.standardName || "—")}</span><span>Make: ${escapeHtml(data.standardMake || "—")} &nbsp;&nbsp; SL.NO: ${escapeHtml(data.standardSerial || "—")}</span><span>Report No. ${escapeHtml(data.standardReportNo || "—")}</span><span>Cal. Validity: ${formatReportDate(data.standardValidity)}</span></div></div>
    <div class="certificate-notes"><div class="certificate-note"><b>TRACEABLE TO</b><span>:</span><span>${escapeHtml(data.traceableTo || "—")}</span></div><div class="certificate-note"><b>METHOD</b><span>:</span><span>${escapeHtml(data.method || "—")}</span></div><div class="certificate-note"><b>CONDITION</b><span>:</span><span>${escapeHtml(data.condition || "—")}</span></div></div>
    <div class="certificate-signatures"><div class="signature-block"><strong>CALIBRATED BY</strong><div><div class="signature-name">${escapeHtml(data.calibratedBy || "—")}</div><div class="signature-role">(Calibration Engineer)</div></div></div><div class="signature-block"><strong>CHECKED BY</strong><div><div class="signature-name">${escapeHtml(data.checkedBy || "—")}</div><div class="signature-role">(Sr. Calibration Engineer)</div></div></div><div class="signature-block"><strong>For ELECTRO GROUP OF INDUSTRIES</strong><div><div class="signature-name">[${escapeHtml(data.authorisedBy || "—")}]</div></div></div></div>`;
}

function resetReportForm() {
  editingReportId = null;
  const form = document.getElementById("calibrationForm");
  form.reset();
  document.getElementById("readingsBody").innerHTML = "";
  reportField("reportNo").value = "";
  reportField("pageNo").value = "";
  reportField("calOn").value = "";
  reportField("calDue").value = "";
  document.getElementById("reportFormTitle").textContent = "New calibration report";
  ensureReportDefaults();
  renderCalibrationPreview();
}

function validateCalibrationReport(report) {
  if (!report.customerName || !report.reportNo || !report.calOn || !report.calDue) return "Complete the report number, dates and customer name.";
  if (!report.readings.length || report.readings.some((reading) => reading.standard === "" || reading.duc === "")) return "Complete all calibration reading rows.";
  return "";
}

async function saveCalibrationReport() {
  const report = collectReportData();
  const validationError = validateCalibrationReport(report);
  if (validationError) {
    showSaveModal("Check report", validationError);
    return;
  }

  loadLocalReports();
  const existingIndex = calibrationReports.findIndex((item) => item.id === report.id);
  const reportNumberChanged = existingIndex >= 0 && calibrationReports[existingIndex].reportNo !== report.reportNo;
  if (existingIndex >= 0) calibrationReports[existingIndex] = report;
  else calibrationReports.unshift(report);
  if (existingIndex < 0 || reportNumberChanged) rememberReportSequence(report.reportNo, report.updatedAt);
  persistLocalReports();
  editingReportId = report.id;
  document.getElementById("reportFormTitle").textContent = `Edit ${report.reportNo}`;

  try {
    await sheetsApiRequest("saveReport", { report });
    showSaveModal("Report saved", `${report.reportNo} is stored in the report register and Google Sheet.`);
  } catch (error) {
    console.warn(error);
    showSaveModal("Report saved locally", `${report.reportNo} is available in this browser. Deploy the updated Google Apps Script to also sync it to the shared spreadsheet.`);
  }
}

function setReportFormData(report) {
  editingReportId = report.id;
  document.querySelectorAll("[data-report-field]").forEach((field) => {
    const value = report[field.dataset.reportField];
    if (value !== undefined) field.value = value;
  });
  const body = document.getElementById("readingsBody");
  body.innerHTML = "";
  (report.readings || []).forEach((reading) => addReadingRow(reading, false));
  document.getElementById("reportFormTitle").textContent = `Edit ${report.reportNo}`;
  renderCalibrationPreview();
}

function editCalibrationReport(id) {
  loadLocalReports();
  const report = calibrationReports.find((item) => item.id === id);
  if (!report) return;
  navigateTo("reports", null, { keepDraft: true });
  setReportFormData(report);
}

function renderReportRecords() {
  const table = document.getElementById("recordsTable");
  const search = (document.getElementById("recordsSearch")?.value || "").toLowerCase().trim();
  const filtered = calibrationReports.filter((report) => [report.reportNo, report.customerName, report.device, report.serialNo, report.equipment].join(" ").toLowerCase().includes(search));
  document.getElementById("recordCount").textContent = `${filtered.length} report${filtered.length === 1 ? "" : "s"}`;
  table.innerHTML = `<thead><tr><th>Report no.</th><th>Customer</th><th>Calibration on</th><th>Device / serial</th><th>Status</th><th>Updated</th><th>Actions</th></tr></thead><tbody>${filtered.length ? filtered.map((report) => `<tr><td>${escapeHtml(report.reportNo)}</td><td>${escapeHtml(report.customerName)}</td><td>${formatReportDate(report.calOn)}</td><td>${escapeHtml(report.device || "—")}<br><small>${escapeHtml(report.serialNo || "")}</small></td><td><span class="status-pill ${report.status === "Pass" ? "status-pill--ok" : "status-pill--warn"}">${escapeHtml(report.status || "Review")}</span></td><td>${new Date(report.updatedAt).toLocaleDateString()}</td><td><div class="record-actions"><button onclick="editCalibrationReport('${escapeHtml(report.id)}')">View / edit</button></div></td></tr>`).join("") : `<tr><td colspan="7" class="empty-state">No saved reports yet. Create the first calibration report to start the register.</td></tr>`}</tbody>`;
}

function csvCell(value) {
  return `"${String(value ?? "").replaceAll('"', '""')}"`;
}

function exportReportsCsv() {
  loadLocalReports();
  if (!calibrationReports.length) {
    showSaveModal("Nothing to export", "Create and save at least one calibration report first.");
    return;
  }
  const maxReadings = Math.max(...calibrationReports.map((report) => (report.readings || []).length));
  const baseHeaders = ["Report No", "Page No", "Calibration On", "Calibration Due", "Customer", "Address", "Device", "Make", "Serial No", "Equipment", "Location", "Environment", "Room Temp C", "Humidity", "Parameter", "Range", "Claimed Error %", "Primary Standard", "Standard Make", "Standard Serial", "Standard Report No", "Standard Validity", "Traceable To", "Method", "Condition", "Calibrated By", "Checked By", "Authorised By", "Status", "Updated At"];
  const readingHeaders = Array.from({ length: maxReadings }, (_, index) => [`Reading ${index + 1} STD`, `Reading ${index + 1} DUC`, `Reading ${index + 1} Error`, `Reading ${index + 1} Remark`]).flat();
  const lines = [[...baseHeaders, ...readingHeaders].map(csvCell).join(",")];
  calibrationReports.forEach((report) => {
    const base = [report.reportNo, report.pageNo, report.calOn, report.calDue, report.customerName, report.customerAddress, report.device, report.make, report.serialNo, report.equipment, report.location, report.environment, report.roomTemp, report.humidity, report.parameter, report.range, report.claimedError, report.standardName, report.standardMake, report.standardSerial, report.standardReportNo, report.standardValidity, report.traceableTo, report.method, report.condition, report.calibratedBy, report.checkedBy, report.authorisedBy, report.status, report.updatedAt];
    const readings = Array.from({ length: maxReadings }, (_, index) => {
      const reading = (report.readings || [])[index] || {};
      return [reading.standard, reading.duc, reading.error, reading.remark];
    }).flat();
    lines.push([...base, ...readings].map(csvCell).join(","));
  });
  const blob = new Blob(["\ufeff" + lines.join("\r\n")], { type: "text/csv;charset=utf-8" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = `Electro_Group_Calibration_Reports_${toInputDate(new Date())}.csv`;
  link.click();
  URL.revokeObjectURL(link.href);
}

function printCalibrationReport() {
  renderCalibrationPreview();
  window.print();
}

function setupCalibrationAutomation() {
  loadLocalReports();
  ensureReportDefaults();
  const form = document.getElementById("calibrationForm");
  form.addEventListener("input", (event) => {
    if (event.target === reportField("calOn")) reportField("calDue").value = calculateDueDate(event.target.value);
    if (event.target === reportField("reportNo")) rememberReportSequence(event.target.value);
    renderCalibrationPreview();
  });
  document.getElementById("recordsSearch").addEventListener("input", renderReportRecords);
  renderCalibrationPreview();
}

setupCalibrationAutomation();
