# Roster automation

Replaces two manual steps in the monthly roster process:

1. Reading WhatsApp messages and hand-typing everyone's availability into `data/data_EN.csv`.
2. Hand-copying `schedule.py`'s output into a spreadsheet and hand-picking cell colors.

WhatsApp stays as the reminder channel; the actual availability now comes through a
Google Form so it's typed once, in a fixed format, by each volunteer.

## One-time setup

```
cd ~/volunteer-scheduler
.venv/bin/pip install -r automation/requirements.txt   # openpyxl, flask (already done once for you)
.venv/bin/pip install ortools                          # the solver (already done once for you)
```

Also, so the website can find each month's responses sheet on its own instead
of you copying the link by hand every time: in `automation/create_form.gs`,
run `createIndexSheet` once (View -> Logs for its sheet ID), paste that ID
into `INDEX_SHEET_ID` at the top of the script, and paste the index sheet's
URL into the website's "Index sheet link" field once. From then on
`createMonthlyForm` appends a row to it automatically and the website reads
the latest one on startup. Skip this if you'd rather paste the responses
link in by hand each month - everything else still works.

## Every month

**1. Create the form** (takes under a minute)

- Go to [script.google.com](https://script.google.com) -> New project.
- Paste in `automation/create_form.gs`.
- Edit `TARGET_YEAR` / `TARGET_MONTH` at the top.
- Run -> `createMonthlyForm` (first time, approve the authorization prompt).
- Open View -> Logs (or Executions -> this run -> Logs) to get the Form URL.
  Post it in the WhatsApp group: *"Please fill in your availability for
  <month>: <link>"*. The script automatically shares the responses
  spreadsheet as "Anyone with the link can view" so the roster website
  (below) can read it - it's not published or searchable, just accessible
  to anyone who has that exact link.

**2. Once responses are in, build the roster with the website**

```
cd ~/volunteer-scheduler
.venv/bin/python automation/webapp.py
```

Open <http://localhost:5000>. If you set up the index sheet above, the
year/month/responses link are already filled in with the latest month -
otherwise paste in the responses spreadsheet URL yourself. Set South's
label if you want "City" instead, and click Generate. It fetches the
responses, runs `schedule.py`, and shows the colorized roster right on the
page with a download link for the `.xlsx`.

This does everything `run_roster.py` used to require a manual CSV download
for: it backs up the existing `data/data_EN.csv`, writes a fresh one from
the live form responses, runs the solver, and produces the colorized
`.xlsx` - all from one page.

### Command-line alternative

If you'd rather not run a local website, `run_roster.py` still works the
same way it always did - download the responses spreadsheet yourself
(File -> Download -> CSV) and run:

```
.venv/bin/python automation/run_roster.py \
    ~/Downloads/"Mish Run Availability Responses - September 2026 - Form Responses 1.csv" \
    --year 2026 --month 9 \
    --out ~/Downloads/"Mish Run September 2026.xlsx" \
    --south-label City
```

## Files

| File | Purpose |
|---|---|
| `create_form.gs` | Paste into script.google.com to create the monthly Form + response Sheet |
| `webapp.py` | Local website: paste the responses sheet link, get the colorized roster |
| `form_csv_to_data_en.py` | Converts a Form-responses CSV into `data_EN.csv` |
| `build_colored_roster.py` | Converts `schedule.py`'s raw output CSV into a colorized `.xlsx` (and the grid `webapp.py` displays) |
| `run_roster.py` | Command-line version of the same pipeline `webapp.py` runs |
| `volunteer_colors.json` | Persistent name -> color map, seeded from the existing "Mish Run" spreadsheet |

## Notes / known limitations

- If someone submits the form twice for the same month, only their **last**
  submission is used (so they can resubmit to correct a mistake).
- Names must be spelled the same way every month, or they'll get treated as
  a new volunteer with a new color.
- The form offers Monday-Friday. North only ever gets scheduled Tuesday-Friday;
  South also runs Mondays. A North-only volunteer ticking a Monday is harmless -
  the solver just never uses it.
- `webapp.py` fetches the responses sheet via its public CSV export URL, which
  is why `create_form.gs` sets it to "Anyone with the link can view" - the
  website itself has no Google login, so it can only read a sheet that's
  either link-shared like this or accessed via full OAuth (more setup, not
  used here). Each month gets a fresh sheet with its own unguessable link.
- **Fixed while building this**: `data/data_EN.csv` was missing a blank line
  that the scheduler's format expects (compare against any of the older,
  working `data/_EN_*.csv` files). That bug was silently dropping the row
  right after "Legend" - in the live August 2026 file that row was Kate, so
  her availability was never fed to the solver. I've fixed the file's
  formatting; if you want a corrected August roster with Kate included,
  rerun `schedule.py` (it currently still reflects the version without her).
