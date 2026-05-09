// ============================================================
// QR Attendance System — Google Apps Script
// ============================================================
// Deploy as Web App:
//   Execute as: Me
//   Who has access: Anyone
//
// Then paste the Web App URL into server.py
// ============================================================

const SHEET_ID     = "YOUR_GOOGLE_SHEET_ID_HERE";
const SECRET_TOKEN = "YOUR_SECRET_TOKEN_HERE"; // must match server.py
const TIMEZONE     = "Asia/Riyadh";            // change to your timezone

function doGet(e) {
  // ── Token validation ─────────────────────────────────────
  if (e.parameter.token !== SECRET_TOKEN) {
    return respond("unauthorized");
  }

  // ── Rate limiting (max 30 requests per minute) ───────────
  const cache   = CacheService.getScriptCache();
  const rateKey = "rate_" + new Date().toISOString().slice(0, 16);
  const count   = parseInt(cache.get(rateKey) || "0");
  if (count > 30) return respond("rate_limited");
  cache.put(rateKey, count + 1, 120);

  // ── Parameters ───────────────────────────────────────────
  const { id, name, type, time, device } = e.parameter;
  if (!id || !name || !type || !time) return respond("missing_params");

  const ss         = SpreadsheetApp.openById(SHEET_ID);
  const attendance = ss.getSheetByName("Attendance");
  const audit      = ss.getSheetByName("Attendance");
  const now        = new Date();
  const date       = Utilities.formatDate(now, TIMEZONE, "dd/MM/yyyy");
  const timestamp  = Utilities.formatDate(now, TIMEZONE, "dd/MM/yyyy hh:mm a");
  const deviceName = device || "Unknown";
  const lastRow    = attendance.getLastRow();

  // ── CHECK IN ─────────────────────────────────────────────
  if (type.toUpperCase() === "IN") {
    if (lastRow > 1) {
      const data = attendance.getRange(2, 1, lastRow - 1, 5).getValues();
      for (let i = 0; i < data.length; i++) {
        if (String(data[i][2]).trim() == id &&
            String(data[i][0]).trim() == date &&
            String(data[i][4]).trim() == "IN") {
          audit.appendRow([timestamp, deviceName, id, name, "CHECK IN"]);
          return respond("duplicate");
        }
      }
    }
    // Write as plain text strings to avoid date object issues
    const newRow = attendance.getLastRow() + 1;
    attendance.getRange(newRow, 1).setValue(date);
    attendance.getRange(newRow, 2).setValue(time);
    attendance.getRange(newRow, 3).setValue(id);
    attendance.getRange(newRow, 4).setValue(name);
    attendance.getRange(newRow, 5).setValue("IN");
    audit.appendRow([timestamp, deviceName, id, name, "CHECK IN"]);

  // ── CHECK OUT ────────────────────────────────────────────
  } else {
    if (lastRow > 1) {
      const data = attendance.getRange(2, 1, lastRow - 1, 6).getValues();
      for (let i = 0; i < data.length; i++) {
        if (String(data[i][2]).trim() == id &&
            String(data[i][0]).trim() == date &&
            String(data[i][4]).trim() == "IN") {
          if (String(data[i][5]).trim() == "OUT") {
            audit.appendRow([timestamp, deviceName, id, name, "CHECK OUT"]);
            return respond("duplicate");
          }
          attendance.getRange(i + 2, 6).setValue("OUT");
          attendance.getRange(i + 2, 7).setValue(time);
          audit.appendRow([timestamp, deviceName, id, name, "CHECK OUT"]);
          return respond("ok");
        }
      }
    }
    // No check-in found — log it and return ok
    audit.appendRow([timestamp, deviceName, id, name, "CHECK OUT"]);
    return respond("ok");
  }

  return respond("ok");
}

function respond(status) {
  return ContentService
    .createTextOutput(JSON.stringify({ status }))
    .setMimeType(ContentService.MimeType.JSON);
}
