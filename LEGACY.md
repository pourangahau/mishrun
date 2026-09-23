# Running the solver directly (manual / legacy path)

This is the original way to run the scheduler, from before the Google Form
and website existed. Use it if you'd rather skip both and edit
`data/data_EN.csv` by hand.

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

See [`README.md`](README.md) for the recommended workflow (Google Form + the
local website), and [`automation/README.md`](automation/README.md) for the
command-line alternative that still uses the Form but skips the website
(`run_roster.py`).
