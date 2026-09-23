#!/usr/bin/env python3
"""A small local website that ties the whole roster pipeline together:
paste in this month's Form responses sheet link, click Generate, and it
fetches the responses, runs the OR-Tools solver, and shows the colorized
roster right in the browser (plus a download link for the .xlsx).

Run it with:
    .venv/bin/python automation/webapp.py

Then open http://localhost:5000 in a browser.

Requires the response spreadsheet to be shared as "Anyone with the link
can view" - create_form.gs sets that automatically. Nothing here needs
Google API credentials; it just fetches the sheet's public CSV export.
"""
import calendar
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from datetime import datetime

from flask import Flask, redirect, render_template_string, request, send_from_directory, url_for

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(AUTOMATION_DIR)
GENERATED_DIR = os.path.join(AUTOMATION_DIR, 'generated')
STATE_FILE = os.path.join(AUTOMATION_DIR, 'webapp_state.json')

sys.path.insert(0, AUTOMATION_DIR)
import form_csv_to_data_en  # noqa: E402
import build_colored_roster  # noqa: E402

app = Flask(__name__)

SHEET_URL_RE = re.compile(r'/d/([a-zA-Z0-9-_]+)')


def extract_sheet_id(text):
    text = text.strip()
    m = SHEET_URL_RE.search(text)
    return m.group(1) if m else text


def fetch_sheet_csv(sheet_id, dest_path):
    export_url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv'
    req = urllib.request.Request(export_url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
    except urllib.error.HTTPError as e:
        raise RuntimeError(
            f'Google returned HTTP {e.code} fetching the sheet. Make sure it is shared '
            f'as "Anyone with the link - Viewer" (create_form.gs sets this automatically).'
        ) from e
    if b'<html' in data[:200].lower():
        raise RuntimeError(
            'Got an HTML page instead of a CSV, which usually means the sheet is not '
            'shared as "Anyone with the link can view". Check its sharing settings.'
        )
    with open(dest_path, 'wb') as f:
        f.write(data)


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, encoding='utf-8') as f:
            return json.load(f)
    now = datetime.now()
    return {'year': now.year, 'month': now.month, 'sheet_url': '', 'south_label': 'South'}


def save_state(state):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(state, f, indent=2)


def parse_still_need(txt_path):
    if not os.path.exists(txt_path):
        return []
    with open(txt_path, encoding='utf-8') as f:
        text = f.read()
    marker = 'We still need people for these shifts:'
    if marker not in text:
        return []
    tail = text.split(marker, 1)[1]
    lines = []
    for line in tail.splitlines():
        line = line.strip()
        if not line:
            if lines:
                break
            continue
        lines.append(line)
    return lines


PAGE = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>Mish Run roster</title>
<style>
  body { font-family: -apple-system, Helvetica, Arial, sans-serif; max-width: 900px; margin: 2rem auto; padding: 0 1rem; color: #222; }
  h1 { font-size: 1.4rem; }
  form { display: grid; grid-template-columns: auto 1fr; gap: 0.6rem 1rem; align-items: center; margin-bottom: 1.5rem; }
  form label { font-weight: 600; }
  input, button { font-size: 1rem; padding: 0.35rem; }
  button { grid-column: 2; justify-self: start; padding: 0.5rem 1.2rem; cursor: pointer; }
  .error { background: #fde8e8; border: 1px solid #e5a0a0; padding: 0.8rem; border-radius: 4px; margin-bottom: 1rem; white-space: pre-wrap; }
  .block-title { font-weight: 700; margin: 1.5rem 0 0.4rem; }
  table { border-collapse: collapse; margin-bottom: 0.5rem; }
  td { border: 1px solid #ccc; padding: 4px 8px; text-align: center; font-size: 0.9rem; }
  td.rowlabel { text-align: left; font-weight: 600; background: #f5f5f5; min-width: 90px; }
  td.date { color: #666; font-size: 0.8rem; background: #fafafa; min-width: 40px; border-right: none; }
  td.namecell { min-width: 80px; border-left: none; font-weight: 600; }
  .download { display: inline-block; margin: 1rem 0; padding: 0.5rem 1rem; background: #2563eb; color: white; text-decoration: none; border-radius: 4px; }
  .needed { background: #fff8e1; border: 1px solid #ffe08a; padding: 0.8rem; border-radius: 4px; margin-top: 1.5rem; }
  .needed ul { margin: 0.4rem 0 0; padding-left: 1.2rem; }
</style>
</head>
<body>
<h1>Mish Run roster generator</h1>

{% if error %}<div class="error">{{ error }}</div>{% endif %}

<form method="post" action="{{ url_for('generate') }}">
  <label>Year</label><input type="number" name="year" value="{{ state.year }}" required>
  <label>Month (1-12)</label><input type="number" name="month" min="1" max="12" value="{{ state.month }}" required>
  <label>Responses sheet link</label><input type="text" name="sheet_url" value="{{ state.sheet_url }}" placeholder="https://docs.google.com/spreadsheets/d/..." style="width:100%" required>
  <label>South run label</label><input type="text" name="south_label" value="{{ state.south_label }}">
  <button type="submit">Generate roster</button>
</form>

{% if result %}
  <a class="download" href="{{ url_for('download', filename=result.filename) }}">Download {{ result.filename }}</a>

  {% for block in result.blocks %}
    <div class="block-title">{{ block.title }}</div>
    <table>
      {% for row in block.rows %}
        <tr>
          <td class="rowlabel">{{ row.label }}</td>
          {% for cell in row.cells %}
            <td class="date">{{ cell.date or '' }}</td>
            <td class="namecell" style="{% if cell.color %}background:#{{ cell.color[2:] }};{% endif %}">{{ cell.name or '' }}</td>
          {% endfor %}
        </tr>
      {% endfor %}
    </table>
  {% endfor %}

  {% if result.needed %}
    <div class="needed">
      <strong>Still need people for these shifts:</strong>
      <ul>{% for line in result.needed %}<li>{{ line }}</li>{% endfor %}</ul>
    </div>
  {% endif %}
{% endif %}

</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(PAGE, state=load_state(), result=None, error=None)


@app.route('/generate', methods=['POST'])
def generate():
    state = {
        'year': int(request.form['year']),
        'month': int(request.form['month']),
        'sheet_url': request.form['sheet_url'].strip(),
        'south_label': request.form.get('south_label', 'South').strip() or 'South',
    }
    save_state(state)

    os.makedirs(GENERATED_DIR, exist_ok=True)
    responses_csv = os.path.join(GENERATED_DIR, 'form_responses.csv')

    try:
        sheet_id = extract_sheet_id(state['sheet_url'])
        fetch_sheet_csv(sheet_id, responses_csv)

        data_en_path = os.path.join(REPO_ROOT, 'data', 'data_EN.csv')
        if os.path.exists(data_en_path):
            os.replace(data_en_path, data_en_path + '.bak')
        form_csv_to_data_en.convert(responses_csv, state['year'], state['month'], data_en_path)

        result = subprocess.run(
            [sys.executable, 'schedule.py'], cwd=REPO_ROOT,
            capture_output=True, text=True,
        )
        if result.returncode != 0:
            raise RuntimeError('schedule.py failed:\n' + result.stdout[-2000:] + result.stderr[-2000:])

        prefix = f"schedule_{state['year']}_{state['month']}____"
        output_dir = os.path.join(REPO_ROOT, 'output')
        candidates = [f for f in os.listdir(output_dir) if f.startswith(prefix) and f.endswith('.csv')]
        if not candidates:
            raise RuntimeError('schedule.py ran but produced no output for that year/month.')
        latest = max(candidates, key=lambda f: os.path.getmtime(os.path.join(output_dir, f)))
        schedule_csv = os.path.join(output_dir, latest)
        schedule_txt = schedule_csv[:-4] + '.txt'

        year, month, assignments = build_colored_roster.parse_schedule_csv(schedule_csv)
        colors = build_colored_roster.load_color_map()
        weeks, blocks = build_colored_roster.compute_blocks(year, month, assignments, state['south_label'], colors)
        build_colored_roster.save_color_map(colors)

        wb = build_colored_roster.build_workbook(year, month, assignments, south_label=state['south_label'])
        xlsx_name = f"Mish Run {calendar.month_name[month]} {year}.xlsx"
        wb.save(os.path.join(GENERATED_DIR, xlsx_name))

        result_data = {
            'filename': xlsx_name,
            'blocks': blocks,
            'needed': parse_still_need(schedule_txt),
        }
        return render_template_string(PAGE, state=state, result=result_data, error=None)

    except Exception as e:
        return render_template_string(PAGE, state=state, result=None, error=str(e))


@app.route('/download/<path:filename>')
def download(filename):
    return send_from_directory(GENERATED_DIR, filename, as_attachment=True)


if __name__ == '__main__':
    app.run(debug=False, port=5000)
