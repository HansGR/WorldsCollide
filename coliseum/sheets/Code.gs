/**
 * FF6 Coliseum - Google Sheets vote store (Apps Script web app).
 *
 * Acts as a tiny REST backend over a Google Sheet so the site can store votes
 * with no server/database. Deploy as a Web App (see SETUP.md); the Vercel app
 * talks to it via the SHEETS_WEBAPP_URL / SHEETS_TOKEN environment variables.
 *
 *   POST {action:"vote", token, voter, name, winner, loser}  -> append a row
 *   GET  ?action=votes&token=...                             -> {votes:[...]}
 *
 * Set a shared secret: Project Settings -> Script Properties -> TOKEN = <secret>.
 */
var SHEET_NAME = 'Votes';
var HEADERS = ['ts', 'voter', 'name', 'winner', 'loser'];

function sheet_() {
  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sh = ss.getSheetByName(SHEET_NAME);
  if (!sh) {
    sh = ss.insertSheet(SHEET_NAME);
    sh.appendRow(HEADERS);
  }
  return sh;
}

function token_() {
  return PropertiesService.getScriptProperties().getProperty('TOKEN') || '';
}

function json_(obj) {
  return ContentService.createTextOutput(JSON.stringify(obj))
      .setMimeType(ContentService.MimeType.JSON);
}

function checkToken_(provided) {
  var t = token_();
  return !t || provided === t;   // if no TOKEN set, allow (open mode)
}

function doPost(e) {
  var body = {};
  try { body = JSON.parse(e.postData.contents); } catch (err) {}
  if (!checkToken_(body.token)) return json_({ok: false, error: 'bad token'});
  if (body.action !== 'vote') return json_({ok: false, error: 'unknown action'});

  var winner = String(body.winner || '').slice(0, 64);
  var loser = String(body.loser || '').slice(0, 64);
  if (!winner || !loser || winner === loser) return json_({ok: false, error: 'bad pair'});

  sheet_().appendRow([
    new Date(),
    String(body.voter || 'anon').slice(0, 64),
    String(body.name || '').slice(0, 24),
    winner,
    loser,
  ]);
  return json_({ok: true});
}

function doGet(e) {
  var p = (e && e.parameter) || {};
  if (!checkToken_(p.token)) return json_({ok: false, error: 'bad token'});

  var values = sheet_().getDataRange().getValues();
  var votes = [];
  for (var i = 1; i < values.length; i++) {       // skip header
    var r = values[i];
    if (!r[3] || !r[4]) continue;
    votes.push({voter: String(r[1]), name: String(r[2]), winner: String(r[3]), loser: String(r[4])});
  }
  return json_({votes: votes});
}
