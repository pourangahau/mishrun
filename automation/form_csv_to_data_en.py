#!/usr/bin/env python3
"""Convert a raw Google Form responses CSV export into the data_EN.csv
format that schedule.py expects.

Usage:
    python form_csv_to_data_en.py responses.csv --year 2026 --month 9 -o ../data/data_EN.csv

The input is whatever you get from the Form's response spreadsheet via
File -> Download -> Comma Separated Values, with the questions created by
create_form.gs:
    Timestamp, Your name, Which run(s) can you do?,
    How many shifts can you do per fortnight?, Which days are you available?
"""
import argparse
import csv
import re
import sys

NAME_COL = 'Your name'
RUN_COL = 'Which run(s) can you do?'
WORKLOAD_COL = 'How many shifts can you do per fortnight?'
DAYS_COL = 'Which days are you available?'
TIMESTAMP_COL = 'Timestamp'

RUN_CODE_RE = re.compile(r'\(([A-Za-z]+)\)')
TRAILING_NUMBER_RE = re.compile(r'(\d+)\s*$')


def parse_run_type(raw):
    m = RUN_CODE_RE.search(raw or '')
    if not m:
        raise ValueError(f'Could not parse run type from {raw!r}')
    return m.group(1).upper()


def parse_days(raw):
    days = []
    for label in (raw or '').split(','):
        label = label.strip()
        if not label:
            continue
        m = TRAILING_NUMBER_RE.search(label)
        if not m:
            raise ValueError(f'Could not parse a day number from {label!r}')
        days.append(int(m.group(1)))
    return sorted(set(days))


def read_responses(form_csv_path):
    with open(form_csv_path, encoding='utf-8-sig', newline='') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    if not rows:
        raise ValueError(f'No responses found in {form_csv_path}')
    missing = [c for c in (NAME_COL, RUN_COL, WORKLOAD_COL, DAYS_COL) if c not in rows[0]]
    if missing:
        raise ValueError(
            'Missing expected column(s) ' + ', '.join(missing) +
            ' - was this exported from the form created by create_form.gs?')
    return rows


def dedupe_latest_per_name(rows):
    """If someone submitted more than once, keep only their last submission
    (rows are assumed to be in submission order, which is how Google Forms
    appends them)."""
    latest = {}
    for row in rows:
        name = row[NAME_COL].strip()
        if name:
            latest[name] = row
    return list(latest.values())


def build_data_en_rows(rows, year, month):
    out = [
        ['Year:', str(year), '', ''],
        ['Month (number):', str(month), '', '', '', '', ''],
        ['', '', '', ''],
        ['Real name', 'Type', 'Available days', 'Workload (per fortnight)'],
        ['Legend (/ = OR)', 'N/S/NS', '1,2,3', '6'],
    ]
    for row in rows:
        name = row[NAME_COL].strip()
        run_type = parse_run_type(row[RUN_COL])
        workload = row[WORKLOAD_COL].strip()
        days = parse_days(row[DAYS_COL])
        if not days:
            print(f'Warning: {name} selected no available days, skipping.', file=sys.stderr)
            continue
        out.append([name, run_type, ','.join(str(d) for d in days), workload])
    return out


def convert(form_csv_path, year, month, out_path):
    rows = read_responses(form_csv_path)
    rows = dedupe_latest_per_name(rows)
    data_en_rows = build_data_en_rows(rows, year, month)
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data_en_rows)
    return len(data_en_rows) - 5  # number of volunteers written


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('form_csv', help='CSV exported from the Form responses spreadsheet')
    ap.add_argument('--year', type=int, required=True)
    ap.add_argument('--month', type=int, required=True, help='1-12')
    ap.add_argument('-o', '--out', default='data/data_EN.csv')
    args = ap.parse_args()

    n = convert(args.form_csv, args.year, args.month, args.out)
    print(f'Wrote {args.out} with {n} volunteer(s).')


if __name__ == '__main__':
    main()
