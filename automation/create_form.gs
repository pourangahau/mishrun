// Mish Run availability form generator.
//
// One-time setup:
//   1. Go to https://script.google.com -> New project.
//   2. Delete the placeholder code and paste this whole file in.
//   3. Run menu -> select "createIndexSheet" -> click Run (first time, approve the
//      authorization prompt). Open View -> Logs and copy the sheet ID it prints into
//      INDEX_SHEET_ID below. This lets the roster website auto-detect the latest
//      month's responses sheet on startup - do this once and never again.
//   4. Edit TARGET_YEAR / TARGET_MONTH below for the month you're collecting availability for.
//   5. Run menu -> select "createMonthlyForm" -> click Run.
//   6. Open "View -> Logs" (or Executions) to get the Form URL. Post it in the
//      WhatsApp group instead of asking people to type their availability as free text.
//      (You no longer need to copy the responses spreadsheet URL by hand - the
//      website picks it up from the index sheet automatically.)
//
// Each new month: change TARGET_YEAR / TARGET_MONTH and run createMonthlyForm again.
// It creates a brand new form + response spreadsheet each time, so old months' responses
// are never mixed with the new ones.

var TARGET_YEAR = 2026;
var TARGET_MONTH = 9; // 1-12

// Paste the ID that createIndexSheet() logs, once. Leave blank to skip this feature -
// createMonthlyForm() still works fine, you'll just paste the responses URL by hand.
var INDEX_SHEET_ID = '';

// One-time setup: creates a small permanent sheet that createMonthlyForm() appends a
// row to every month, so the roster website can look up the latest month's responses
// sheet on its own. Run this once, then paste its ID into INDEX_SHEET_ID above.
function createIndexSheet() {
  var ss = SpreadsheetApp.create('Mish Run Form Index');
  ss.getSheets()[0].appendRow(['Year', 'Month', 'Form URL', 'Responses URL', 'Created']);
  DriveApp.getFileById(ss.getId())
      .setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);
  Logger.log('Index sheet created: ' + ss.getUrl());
  Logger.log('Paste this ID into INDEX_SHEET_ID at the top of this script: ' + ss.getId());
}

function createMonthlyForm() {
  var monthName = Utilities.formatDate(
      new Date(TARGET_YEAR, TARGET_MONTH - 1, 1),
      Session.getScriptTimeZone(), 'MMMM');

  var form = FormApp.create('Mish Run Availability - ' + monthName + ' ' + TARGET_YEAR);
  form.setDescription(
      'Let us know what shifts you can help with this month. ' +
      'One shift = one hour in the morning. North runs Tuesday-Friday; ' +
      'South also runs Mondays.');
  form.setCollectEmail(false);

  form.addTextItem()
      .setTitle('Your name')
      .setHelpText('Please use the same spelling every month so your color on the roster stays consistent.')
      .setRequired(true);

  form.addMultipleChoiceItem()
      .setTitle('Which run(s) can you do?')
      .setChoiceValues(['North (N)', 'South (S)', 'Both (NS)'])
      .setRequired(true);

  var workloadChoices = [];
  for (var w = 1; w <= 10; w++) workloadChoices.push(String(w));
  form.addListItem()
      .setTitle('How many shifts can you do per fortnight?')
      .setChoiceValues(workloadChoices)
      .setRequired(true);

  var dayChoices = availableDayLabels(TARGET_YEAR, TARGET_MONTH);
  form.addCheckboxItem()
      .setTitle('Which days are you available?')
      .setHelpText('Mondays are South only - if you only do North, no need to pick a Monday.')
      .setChoiceValues(dayChoices)
      .setRequired(true);

  var ss = SpreadsheetApp.create(
      'Mish Run Availability Responses - ' + monthName + ' ' + TARGET_YEAR);
  form.setDestination(FormApp.DestinationType.SPREADSHEET, ss.getId());

  // Let the roster website read this sheet's CSV export directly, without
  // needing Google API credentials. Only people with this exact link can
  // view it - it's not published or searchable.
  DriveApp.getFileById(ss.getId())
      .setSharing(DriveApp.Access.ANYONE_WITH_LINK, DriveApp.Permission.VIEW);

  if (INDEX_SHEET_ID) {
    try {
      SpreadsheetApp.openById(INDEX_SHEET_ID).getSheets()[0]
          .appendRow([TARGET_YEAR, TARGET_MONTH, form.getPublishedUrl(), ss.getUrl(), new Date()]);
    } catch (e) {
      Logger.log('Could not write to the index sheet - check INDEX_SHEET_ID is correct. ' + e);
    }
  } else {
    Logger.log(
        'INDEX_SHEET_ID is not set, so the website will not auto-detect this month. ' +
        'Run createIndexSheet() once and paste its ID in to fix that.');
  }

  Logger.log('Form URL (share this in WhatsApp): ' + form.getPublishedUrl());
  Logger.log('Editor URL: ' + form.getEditUrl());
  Logger.log('Responses spreadsheet: ' + ss.getUrl());
}

// Builds ['Mon 1', 'Tue 2', ...] for every Monday-Friday in the given month
// (Monday is South-only, but offered to everyone - see the help text above).
function availableDayLabels(year, month) {
  var labels = [];
  var abbrev = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];
  var daysInMonth = new Date(year, month, 0).getDate();
  for (var d = 1; d <= daysInMonth; d++) {
    var date = new Date(year, month - 1, d);
    var dow = date.getDay(); // 0=Sun..6=Sat
    if (dow >= 1 && dow <= 5) { // Mon-Fri
      labels.push(abbrev[dow] + ' ' + d);
    }
  }
  return labels;
}
