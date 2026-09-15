// Mish Run availability form generator.
//
// One-time setup:
//   1. Go to https://script.google.com -> New project.
//   2. Delete the placeholder code and paste this whole file in.
//   3. Edit TARGET_YEAR / TARGET_MONTH below for the month you're collecting availability for.
//   4. Run menu -> select "createMonthlyForm" -> click Run. First run asks you to authorize
//      access to your own Forms/Sheets/Drive - that's expected, approve it.
//   5. Open "View -> Logs" (or Executions) to get the Form URL. Post that link in the
//      WhatsApp group instead of asking people to type their availability as free text.
//
// Each new month: change TARGET_YEAR / TARGET_MONTH and run createMonthlyForm again.
// It creates a brand new form + response spreadsheet each time, so old months' responses
// are never mixed with the new ones.

var TARGET_YEAR = 2026;
var TARGET_MONTH = 9; // 1-12

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

  Logger.log('Form URL (share this in WhatsApp): ' + form.getPublishedUrl());
  Logger.log('Editor URL: ' + form.getEditUrl());
  Logger.log('Responses spreadsheet: ' + ss.getUrl());
  Logger.log(
      'When it is time to build the roster: open the responses spreadsheet, ' +
      'File -> Download -> Comma Separated Values (.csv), then feed that file ' +
      'to run_roster.py on your computer.');
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
