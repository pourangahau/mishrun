# Roster automation

Replaces two manual steps in the monthly roster process:

1. Reading WhatsApp messages and hand-typing everyone's availability into `data/data_EN.csv`.
2. Hand-copying `schedule.py`'s output into a spreadsheet and hand-picking cell colors.

WhatsApp stays as the reminder channel; the actual availability now comes through a
Google Form so it's typed once, in a fixed format, by each volunteer.

## One-time setup

```
cd ~/volunteer-scheduler
.venv/bin/pip install -r automation/requirements.txt   # openpyxl (already done once for you)
.venv/bin/pip install ortools                          # the solver (already done once for you)
```

## Every month

**1. Create the form** (takes under a minute)

- Go to [script.google.com](https://script.google.com) -> New project.
- Paste in `automation/create_form.gs`.
- Edit `TARGET_YEAR` / `TARGET_MONTH` at the top.
- Run -> `createMonthlyForm` (first time, approve the authorization prompt).
- Open View -> Logs (or Executions -> this run -> Logs) to get the form's public URL.
- Post that URL in the WhatsApp group: *"Please fill in your availability for
  <month>: <link>"*.

**2. Collect responses, then export them**

- Once people have responded, open the linked responses spreadsheet
  (its URL is also in the Apps Script logs).
- File -> Download -> Comma Separated Values (.csv). Save it anywhere, e.g. `~/Downloads`.

**3. Build the roster**

```
cd ~/volunteer-scheduler
.venv/bin/python automation/run_roster.py \
    ~/Downloads/"Mish Run Availability Responses - September 2026 - Form Responses 1.csv" \
    --year 2026 --month 9 \
    --out ~/Downloads/"Mish Run September 2026.xlsx"
```

This will:
- back up the existing `data/data_EN.csv` to `data_EN.csv.bak`
- write a fresh `data/data_EN.csv` from the form responses
- run `schedule.py` (the OR-Tools solver, unchanged)
- write a colorized `.xlsx` to the `--out` path, with the same per-volunteer
  color every month (tracked in `automation/volunteer_colors.json`)

Add `--south-label City` if you want the second run labelled "City" instead of
"South" to match the old spreadsheet's wording.

## Files

| File | Purpose |
|---|---|
| `create_form.gs` | Paste into script.google.com to create the monthly Form + response Sheet |
| `form_csv_to_data_en.py` | Converts a downloaded Form-responses CSV into `data_EN.csv` |
| `build_colored_roster.py` | Converts `schedule.py`'s raw output CSV into a colorized `.xlsx` |
| `run_roster.py` | Runs all of the above in sequence |
| `volunteer_colors.json` | Persistent name -> color map, seeded from the existing "Mish Run" spreadsheet |

## Notes / known limitations

- If someone submits the form twice for the same month, only their **last**
  submission is used (so they can resubmit to correct a mistake).
- Names must be spelled the same way every month, or they'll get treated as
  a new volunteer with a new color.
- The form offers Monday-Friday. North only ever gets scheduled Tuesday-Friday;
  South also runs Mondays. A North-only volunteer ticking a Monday is harmless -
  the solver just never uses it.
- **Fixed while building this**: `data/data_EN.csv` was missing a blank line
  that the scheduler's format expects (compare against any of the older,
  working `data/_EN_*.csv` files). That bug was silently dropping the row
  right after "Legend" - in the live August 2026 file that row was Kate, so
  her availability was never fed to the solver. I've fixed the file's
  formatting; if you want a corrected August roster with Kate included,
  rerun `schedule.py` (it currently still reflects the version without her).
