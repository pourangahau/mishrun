#!/usr/bin/env python3
"""Turn schedule.py's raw output CSV into a colorized .xlsx roster, replacing
the manual step of hand-copying names into a spreadsheet and hand-picking
cell colors.

Usage:
    python build_colored_roster.py ../output/schedule_2026_9____20260901_120000.csv \
        -o "~/Downloads/Mish Run September 2026.xlsx"

Each volunteer keeps the same fill color release to release, tracked in
volunteer_colors.json next to this script.
"""
import argparse
import calendar
import csv
import json
import os
import re

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COLORS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'volunteer_colors.json')

# A palette of visually distinct fill colors for volunteers who don't have one yet.
PALETTE = [
    'FFFFE599', 'FF93C47D', 'FF9999FF', 'FF00FFFF', 'FFF1C232', 'FF3399FF',
    'FF66FFCC', 'FF3C78D8', 'FF6AA84F', 'FFFCE5CD', 'FFCC0000', 'FF00FF00',
    'FFFF00FF', 'FFEA9999', 'FFB4A7D6', 'FFD9EAD3', 'FFFFF2CC', 'FFA2C4C9',
    'FFD5A6BD', 'FFB6D7A8', 'FFF9CB9C', 'FF9FC5E8', 'FFD0E0E3', 'FFEAD1DC',
]

# Index into calendar.monthcalendar's Mon..Sun week tuples.
# North only runs Tuesday-Friday; South also runs Mondays.
NORTH_WEEKDAY_ROWS = [
    (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'),
]
SOUTH_WEEKDAY_ROWS = [
    (0, 'Monday'), (1, 'Tuesday'), (2, 'Wednesday'), (3, 'Thursday'), (4, 'Friday'),
]


def load_color_map():
    if os.path.exists(COLORS_FILE):
        with open(COLORS_FILE, encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_color_map(colors):
    with open(COLORS_FILE, 'w', encoding='utf-8') as f:
        json.dump(colors, f, indent=2, sort_keys=True)


def color_for(name, colors):
    if name not in colors:
        used = set(colors.values())
        available = [c for c in PALETTE if c not in used]
        colors[name] = available[0] if available else PALETTE[len(colors) % len(PALETTE)]
    return colors[name]


def parse_schedule_csv(path):
    with open(path, encoding='utf-8') as f:
        rows = list(csv.reader(f))

    year = int(rows[0][0])
    month = _month_number(rows[0][1])

    assignments = {}  # day -> {'N': name, 'S': name}
    for i, row in enumerate(rows):
        cells = (row + [''] * 8)[:8]
        days = cells[1:8]
        # A real calendar date row has, in every one of the 7 weekday cells,
        # either nothing or a bare day number - nothing else (this excludes
        # the volunteer summary table further down, e.g. "Anouk,13,26,,,"
        # which would otherwise look like a date row).
        if not all(c.strip() == '' or c.strip().isdigit() for c in days):
            continue
        if not any(c.strip() for c in days):
            continue
        n_row = (rows[i + 1] + [''] * 8)[1:8] if i + 1 < len(rows) else [''] * 7
        s_row = (rows[i + 3] + [''] * 8)[1:8] if i + 3 < len(rows) else [''] * 7
        for col in range(7):
            day_str = days[col].strip()
            if not day_str.isdigit():
                continue
            day = int(day_str)
            n_name = _strip_prefix(n_row[col], 'N:')
            s_name = _strip_prefix(s_row[col], 'S:')
            assignments[day] = {'N': n_name, 'S': s_name}

    return year, month, assignments


def _strip_prefix(cell, prefix):
    cell = cell.strip()
    if not cell.startswith(prefix):
        return ''
    name = cell[len(prefix):].strip()
    return '' if name == '-' else name


def _month_number(month_name):
    for i in range(1, 13):
        if calendar.month_name[i] == month_name.strip():
            return i
    raise ValueError(f'Unrecognized month name: {month_name!r}')


def ordinal(day):
    if 11 <= day % 100 <= 13:
        suffix = 'th'
    else:
        suffix = {1: 'st', 2: 'nd', 3: 'rd'}.get(day % 10, 'th')
    return f'{day}{suffix}'


def build_workbook(year, month, assignments, south_label='South'):
    colors = load_color_map()
    weeks = calendar.monthcalendar(year, month)  # list of [Mon..Sun], 0 = outside month

    wb = Workbook()
    ws = wb.active
    ws.title = 'Roster'

    bold = Font(bold=True)
    center = Alignment(horizontal='center')

    def write_block(start_row, label, key, weekday_rows):
        ws.cell(row=start_row, column=1, value=f'{label} (week starting)').font = bold

        # A Monday reference row (dates only, no assignee) is only needed when
        # Monday isn't already one of this block's real shift rows below.
        has_monday_row = any(weekday_idx == 0 for weekday_idx, _ in weekday_rows)
        next_row = start_row + 1
        if not has_monday_row:
            ws.cell(row=next_row, column=1, value='Monday')
            for w, week in enumerate(weeks):
                date_col = 2 + 2 * w
                monday = week[0]
                if monday:
                    ws.cell(row=next_row, column=date_col, value=ordinal(monday))
            next_row += 1

        for offset, (weekday_idx, label_text) in enumerate(weekday_rows):
            r = next_row + offset
            ws.cell(row=r, column=1, value=label_text)
            for w, week in enumerate(weeks):
                date_col = 2 + 2 * w
                name_col = date_col + 1
                day = week[weekday_idx]
                if not day:
                    continue
                ws.cell(row=r, column=date_col, value=ordinal(day)).alignment = center
                name = assignments.get(day, {}).get(key, '')
                if name:
                    cell = ws.cell(row=r, column=name_col, value=name)
                    fill = color_for(name, colors)
                    cell.fill = PatternFill(start_color=fill, end_color=fill, fill_type='solid')
        return next_row + len(weekday_rows)

    next_row = write_block(1, 'North', 'N', NORTH_WEEKDAY_ROWS)
    write_block(next_row + 2, south_label, 'S', SOUTH_WEEKDAY_ROWS)

    for col in range(1, 2 + 2 * len(weeks)):
        letter = get_column_letter(col)
        ws.column_dimensions[letter].width = 12 if col == 1 else 9

    save_color_map(colors)
    return wb


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('schedule_csv', help="schedule.py's raw output CSV, e.g. output/schedule_2026_9____....csv")
    ap.add_argument('-o', '--out', required=True, help='Path to write the colorized .xlsx to')
    ap.add_argument('--south-label', default='South', help='Label for the second run, e.g. "City" (default: South)')
    args = ap.parse_args()

    year, month, assignments = parse_schedule_csv(args.schedule_csv)
    wb = build_workbook(year, month, assignments, south_label=args.south_label)
    out_path = os.path.expanduser(args.out)
    wb.save(out_path)
    print(f'Wrote {out_path} ({calendar.month_name[month]} {year}, {len(assignments)} days).')


if __name__ == '__main__':
    main()
