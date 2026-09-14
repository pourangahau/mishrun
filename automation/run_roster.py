#!/usr/bin/env python3
"""End-to-end monthly roster run: Google Form CSV export -> data_EN.csv ->
schedule.py -> colorized .xlsx.

Usage (from the volunteer-scheduler directory, with the venv active or using
its python directly):

    .venv/bin/python automation/run_roster.py \
        ~/Downloads/Mish\\ Run\\ Availability\\ Responses.csv \
        --year 2026 --month 9 \
        --out ~/Downloads/"Mish Run September 2026.xlsx"

This replaces: reading WhatsApp messages and hand-typing data_EN.csv, and
hand-colorizing the output into a spreadsheet.
"""
import argparse
import glob
import os
import shutil
import subprocess
import sys

AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(AUTOMATION_DIR)

sys.path.insert(0, AUTOMATION_DIR)
import form_csv_to_data_en  # noqa: E402
import build_colored_roster  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('form_csv', help='CSV exported from the Form responses spreadsheet')
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--month', type=int, required=True, help='1-12')
    ap.add_argument('--out', required=True, help='Path to write the final colorized .xlsx to')
    ap.add_argument('--south-label', default='South', help='Label for the second run, e.g. "City"')
    ap.add_argument('--python', default=sys.executable, help='Python interpreter to run schedule.py with')
    args = ap.parse_args()

    data_en_path = os.path.join(REPO_ROOT, 'data', 'data_EN.csv')
    if os.path.exists(data_en_path):
        backup_path = data_en_path + '.bak'
        shutil.copy2(data_en_path, backup_path)
        print(f'Backed up existing {data_en_path} -> {backup_path}')

    n = form_csv_to_data_en.convert(args.form_csv, args.year, args.month, data_en_path)
    print(f'Wrote {data_en_path} with {n} volunteer(s).')

    before = set(glob.glob(os.path.join(REPO_ROOT, 'output', f'schedule_{args.year}_{args.month}____*.csv')))

    print('Running schedule.py ...')
    result = subprocess.run([args.python, 'schedule.py'], cwd=REPO_ROOT)
    if result.returncode != 0:
        print('schedule.py failed, stopping.', file=sys.stderr)
        sys.exit(1)

    after = set(glob.glob(os.path.join(REPO_ROOT, 'output', f'schedule_{args.year}_{args.month}____*.csv')))
    new_files = sorted(after - before) or sorted(after, key=os.path.getmtime)
    if not new_files:
        print('Could not find schedule.py output CSV for that year/month.', file=sys.stderr)
        sys.exit(1)
    schedule_csv = max(new_files, key=os.path.getmtime)
    print(f'Using scheduler output: {schedule_csv}')

    year, month, assignments = build_colored_roster.parse_schedule_csv(schedule_csv)
    wb = build_colored_roster.build_workbook(year, month, assignments, south_label=args.south_label)
    out_path = os.path.expanduser(args.out)
    wb.save(out_path)
    print(f'Wrote colorized roster: {out_path}')


if __name__ == '__main__':
    main()
