# Mish Run roster scheduler

Builds the monthly volunteer roster for the Mish Run (North and South, one
morning shift = one hour, North Tuesday-Friday and South Monday-Friday).
Given each volunteer's availability
and how many shifts they can do, [OR-Tools](https://developers.google.com/optimization)
solves for a fair assignment, and a colorized spreadsheet is produced for
sharing.

This repo has two parts:

- **`schedule.py`** - the original solver (a customized fork of
  [imreszakal/volunteer-scheduler](https://github.com/imreszakal/volunteer-scheduler)).
  Unchanged; still does all the actual scheduling.
- **`automation/`** - a Google Form + a local website + scripts that replace
  the old manual steps: reading availability off WhatsApp and hand-typing it
  in, and hand-colorizing the output into a spreadsheet. See
  [`automation/README.md`](automation/README.md) for the full monthly
  workflow - this file is the overview and one-time setup.

## One-time setup

```bash
git clone https://github.com/pourangahau/mishrun.git volunteer-scheduler
cd volunteer-scheduler
python3 -m venv .venv
.venv/bin/pip install -r automation/requirements.txt   # openpyxl, flask
.venv/bin/pip install ortools                          # the solver
```

You'll also need a `data/` folder (gitignored - it holds real volunteers'
names and availability, so it's never committed). Either:
- run the automation pipeline once (it creates `data/data_EN.csv` for you), or
- create `data/data_EN.csv` by hand in the format below.

## Monthly workflow (recommended)

Full instructions: [`automation/README.md`](automation/README.md). In short:

1. Create this month's Google Form by pasting `automation/create_form.gs`
   into [script.google.com](https://script.google.com) and running it.
2. Post the form link in WhatsApp instead of asking people to type their
   availability as free text.
3. Once responses are in, run the local website:
   ```bash
   .venv/bin/python automation/webapp.py
   ```
   Open <http://localhost:5000> and click Generate. It fetches the
   responses, writes `data/data_EN.csv`, runs the solver, and shows the
   colorized roster right on the page with a download link for the `.xlsx`
   - no manual CSV download, typing, or coloring required.

   The year/month/responses-link fields auto-fill with the latest month if
   you've set up the one-time "index sheet" (see
   [`automation/README.md`](automation/README.md)); otherwise paste in the
   responses spreadsheet link from step 1 yourself.

## Running the solver directly (manual / legacy path)

If you'd rather skip the Form and edit `data/data_EN.csv` by hand:

```
Year:,2026,,
Month (number):,9,,,,,
,,,
Real name,Type,Available days,Workload (per fortnight)
Legend (/ = OR),N/S/NS,"1,2,3",6
Tim,N,"5,6,13,14,19,20",2
Delia,S,"19,21,27",1
Anouk,NS,"13,19,20,26,27",1
```

- **Type**: `N` (North only), `S` (South only), or `NS` (either)
- **Available days**: comma-separated day-of-month numbers
- **Workload**: max shifts per fortnight
- The blank line after the `Month` row is required - without it, the row
  immediately after the `Legend` row is silently dropped by the solver. (This
  bit a real volunteer once; see git history / commit notes for the fix.)

Then:

```bash
cd volunteer-scheduler
.venv/bin/python schedule.py
```

Output goes to `output/schedule_<year>_<month>____<timestamp>.{csv,txt}`.
From there you can either colorize it by hand as before, or run it through
`automation/build_colored_roster.py` to get the `.xlsx` automatically:

```bash
.venv/bin/python automation/build_colored_roster.py \
    output/schedule_2026_9____20260901_120000.csv \
    -o ~/Downloads/"Mish Run September 2026.xlsx"
```

## Repo layout

| Path | What it is |
|---|---|
| `schedule.py`, `lang/`, `config.py` | The solver (unchanged) |
| `automation/` | Form creation, local website, CSV conversion, colorized roster builder |
| `data/`, `output/` | Gitignored - real volunteer data, local only |
| `volunteer-availability/` | An earlier, unfinished attempt at a web-based availability calendar (Flask + JS). Superseded by `automation/`, kept for reference. |
