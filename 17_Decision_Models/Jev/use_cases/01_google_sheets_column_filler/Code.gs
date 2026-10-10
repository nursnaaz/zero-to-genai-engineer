/**
 * Use case 01 - Jev inside Google Sheets.
 *
 * Install: Extensions > Apps Script, paste this file, then
 * Project Settings > Script Properties > add JEV_KEY.
 * Reload the sheet and use the "Jev" menu.
 *
 * Usage: put your allowed options in row 1 under the new column header,
 * separated by | , e.g.  Category: Groceries|Software|Travel|Other
 */
function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Jev')
    .addItem('Fill active column', 'fillActiveColumn')
    .addToUi();
}

function jevChoice_(state, instructions, options) {
  var criteria = {};
  options.forEach(function (o) { criteria[o] = o; });
  var res = UrlFetchApp.fetch('https://api.typesafe.ai/v1/systemone', {
    method: 'post',
    contentType: 'application/json',
    headers: { Authorization: 'Bearer ' +
      PropertiesService.getScriptProperties().getProperty('JEV_KEY') },
    payload: JSON.stringify({
      state: state,
      model: 'jev-latest',
      questions: { pick: { type: 'choice', instructions: instructions, criteria: criteria } }
    }),
    muteHttpExceptions: true
  });
  if (res.getResponseCode() !== 200) throw new Error(res.getContentText());
  return JSON.parse(res.getContentText()).answers.pick;
}

function fillActiveColumn() {
  var sheet = SpreadsheetApp.getActiveSheet();
  var col = sheet.getActiveCell().getColumn();
  var header = String(sheet.getRange(1, col).getValue());      // "Category: A|B|C"
  var parts = header.split(':');
  var name = parts[0].trim();
  var options = (parts[1] || '').split('|').map(function (s) { return s.trim(); })
                                .filter(String);
  if (options.length < 2) {
    SpreadsheetApp.getUi().alert('Header must be like  Category: Groceries|Software|Other');
    return;
  }

  var lastRow = sheet.getLastRow();
  var headers = sheet.getRange(1, 1, 1, sheet.getLastColumn()).getValues()[0];

  for (var r = 2; r <= lastRow; r++) {
    if (sheet.getRange(r, col).getValue()) continue;           // do not overwrite
    var rowObj = {};
    for (var c = 1; c <= headers.length; c++) {
      if (c === col) continue;
      rowObj[String(headers[c - 1])] = sheet.getRange(r, c).getValue();
    }
    var a = jevChoice_(rowObj, 'Which ' + name + ' fits this row?', options);
    sheet.getRange(r, col).setValue(a.choice);
    sheet.getRange(r, col).setNote('Jev confidence: ' + a.confidence.toFixed(2));
    if (a.confidence < 0.6) sheet.getRange(r, col).setBackground('#fff3cd');  // flag the unsure
  }
}
