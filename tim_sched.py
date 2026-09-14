# https://github.com/imreszakal/volunteer-scheduler

#Download the above repo and replace the `schedule.py` file with this one
#Run according to the volunteer-scheduler readme, with data in the appropriate format.

import calendar
import csv
import datetime
import os
import sys

from lang.language_EN import *
from ortools.sat.python import cp_model


def main():
    f = []
    try:
        with open(l_filename, encoding='UTF8') as data_file:
             reader = csv.reader(data_file, delimiter=',')
             for row in reader:
                 f.append(row)
    except FileNotFoundError:
        print()
        print('Data file "' + l_filename + '" not found.')
        print()
        sys.exit()
    schedule_year = int(f[0][1])
    schedule_month = int(f[1][1])
    month_name = l_month_name_dic[schedule_month]
    data_lines = []
    for line in range(5, len(f)):
        if f[line][3]:
            data_lines.append(line)

    number_of_volunteers = len(data_lines)
    volunteers = [i for i in range(number_of_volunteers)]

    firstday_index, days_in_month = calendar.monthrange(schedule_year,
            schedule_month)

    list_of_days = [i for i in range(1, days_in_month + 1)]

    if firstday_index == 0:
        first_monday = 1
    else:
        first_monday = 8 - firstday_index

    weeks = {}
    m = firstday_index
    week_index = 0
    d = 1
    what_day_dic = {}
    while d <= days_in_month:
        weeks[week_index] = list()
        while d + m - week_index * 7 < 8 and d <= days_in_month:
            weeks[week_index].append(d)
            what_day_dic[d] = d + m - week_index * 7
            d += 1
        week_index += 1

    def certain_weekdays_in_month(list_of_certain_weekdays): # Monday: 1
        days = []
        for c in list_of_certain_weekdays:
            for d in list_of_days:
                if what_day_dic[d] == c:
                    days.append(d)
        return days

    run_days = certain_weekdays_in_month([2, 3, 4, 5])

    # Distance between workdays per person
    distance = 1

    # North : shift 0; South : shift 1
    shifts = [0, 1]

    model = cp_model.CpModel()

    # Creates shift variables.
    # schedule[(v, d, s)]: volunteer 'v' works shift 's' on day 'd'.
    schedule = {}
    for v in volunteers:
        for d in list_of_days:
            for s in shifts:
                i = 'shift_{:_>2}.{:_>2}.{}'.format(v, d, s)
                schedule[(v, d, s)] = model.NewBoolVar(i)

    all_days_available = []
    all_workload = []
    all_cp = []

    def use_data(id, type, days_available, workload):

        all_days_available.append(days_available)

        # Volunteers only doing North run
        if type == l_N:
            for d in list_of_days:
                for s in [1]:
                    model.Add(schedule[(id, d, s)] == False)
                if d in days_available:
                    model.Add(schedule[(id, d, 0)] <= 1)
                else:
                    model.Add(schedule[(id, d, 0)] == False)

        # Volunteers only doing South run
        if type == l_S:
            for d in list_of_days:
                for d in list_of_days:
                    for s in [0]:
                        model.Add(schedule[(id, d, s)] == False)
                    if d in days_available:
                        model.Add(schedule[(id, d, 1)] <= 1)
                    else:
                        model.Add(schedule[(id, d, 1)] == False)

        # Volunteers able to do both runs
        if type == l_NS:
            for d in list_of_days:
                if d in days_available:
                    model.Add(sum(schedule[(id, d, s)] for s in [0, 1]) <= 1)
                else:
                    for s in [0, 1]:
                        model.Add(schedule[(id, d, s)] == False)
            all_cp.append(id)

        # Workload per fortnight
        days = list_of_days
        for day in days:
            a = day - 6
            b = day + 6
            while a < 1:
                a += 1
            while b > days_in_month:
                b -= 1
            model.Add(sum(schedule[(id, d, s)]
                          for s in shifts for d in range(a, b + 1)) <= workload)

    # volunteer_dic = {ID:name}, volunteer_dic_r = {name:ID}
    volunteer_dic = {}
    volunteer_dic_r = {}
    id = 0
    for line in data_lines:
        volunteer_dic[id] = f[line][0]
        volunteer_dic_r[f[line][0]] = id
        id += 1

    # Loads data
    id = 0
    for line in data_lines:
         values = [x for x in f[line]]
         type = values[1]

         days_available = [int(x) for x in values[2].split(',')
                if x.strip().isdigit()]

         workload = int(values[3])

         use_data(id, type, days_available, workload)
         id += 1

    # Maximum one volunteer per shift.
    for d in list_of_days:
        if d in run_days:
            model.Add(sum(schedule[(v, d, 0)] for v in volunteers) <= 1)
            model.Add(sum(schedule[(v, d, 1)] for v in volunteers) <= 1)

    # At least four days between shifts per volunteer
    # for v in volunteers:
    #     days = list_of_days
    #     for day in days:
    #         a = day-distance
    #         b = day+distance
    #         while a < 1:
    #             a += 1
    #         while b > days_in_month:
    #             b -= 1
    #         model.Add(sum(schedule[(v, d, s)]
    #                 for s in shifts for d in range(a, b + 1)) <= 1)

    # OBJECTIVE

    model.Maximize(
            sum(schedule[(v, d, 0)]
                for d in run_days for v in volunteers)
            + sum(schedule[(v, d, 1)]
                for d in run_days for v in volunteers)
    )

    # SOLUTION

    solver = cp_model.CpSolver()
    solver.Solve(model)

    solution_vs_d = {}
    for s in shifts:
        for v in volunteers:
            has = False
            for d in list_of_days:
                if solver.Value(schedule[(v, d, s)]) == 1:
                    if has:
                        solution_vs_d[(v, s)].append(d)
                    else:
                        solution_vs_d[(v, s)] = list()
                        solution_vs_d[(v, s)].append(d)
                    has = True

    solution_v_phonedays = {}
    for v in volunteers:
        tel1 = []
        tel2 = []
        try:
            tel1 = solution_vs_d[(v, 0)]
        except:
            pass
        try:
            tel2 = solution_vs_d[(v, 3)]
        except:
            pass
        solution_v_phonedays[v] = tel1 + tel2

    solution_ds_v = {}
    for v in volunteers:
        for s in shifts:
            try:
                days = solution_vs_d[(v, s)]
                for day in days:
                    solution_ds_v[(day, s)] = v
            except:
                pass

    solution_vd_s = {}
    for v in volunteers:
        for day in list_of_days:
            try:
                if day in solution_v_phonedays[v]:
                    solution_vd_s[(v, day)] = 0
            except:
                pass
            for s in [1, 2]:
                try:
                    if solution_ds_v[(day, s)] == v:
                        solution_vd_s[(v, day)] = s
                except:
                    pass

    needed = {}
    needed[0] = []
    for d in list_of_days:
        try:
            a = solution_ds_v[(d, 0)]
        except:
            needed[0].append(d)
    needed[1] = []
    for d in run_days:
        try:
            a = solution_ds_v[(d, 1)]
        except:
            needed[1].append(d)

    needed_daily = {}
    needed_nextto = {}
    for d in list_of_days:
        need = False
        if d in needed[0]:
            needed_daily[d] = 0
            need = True
        if d in needed[1]:
            try:
                if needed_daily[d] > -1:
                    needed_daily[d] = 2
            except:
                needed_daily[d] = 1
            need = True
        if need == True:
            needed_nextto[d] = []
            for s in shifts:
                try:
                    needed_nextto[d].append(solution_ds_v[(d, s)])
                except:
                    pass


    if not os.path.exists('output'):
        os.makedirs('output')

    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    new_filename = 'output/{}_{}_{}____{}'.format(l_output_filename,
            schedule_year, schedule_month, timestamp)
    txt_file = new_filename + '.txt'
    csv_file = new_filename + '.csv'

    global width
    width = 18 #     minimum 14

    def print_txt(*txt_line):
        try:
            w = txt_line[0]
            print(w)
        except:
            w = '\n'
            print()
        with open(txt_file, 'a', encoding='UTF8') as f:
            f.write(w + '\n')

    def csv_cell(cell_data):
        c = ''
        if cell_data:
            try:
                # number
                if cell_data[0] > 0:
                    if len(cell_data) > 1:
                        c += '"' + str(cell_data[0])
                        for j in cell_data[1:]:
                            c += ',' + str(j)
                        c += '"'
                    else:
                        c += str(cell_data[0])
            except:
                # string
                c = str(cell_data)
        return c

    def print_days(list):
        t = ''
        if list:
            if len(list) > 1:
                t += str(list)
                for j in list[1:]:
                    t += '.,' + str(j)
            else:
                t += str(list[0]) + '.'
        return t

    def print_csv(list):
        # line = ''
        line = ','.join(csv_cell(i) for i in list)
        with open(csv_file, 'a', encoding='UTF8') as f:
            f.write(line + ',\n')

    def calendar_solution(d, l_X, shift, everyday, chatday):
        # txt_item = ''
        # csv_item = ''
        title = l_X + ': '
        try:
            v = solution_ds_v[(d, shift)]
            txt_item = title + vol_l[v] + ' ' * 2
            csv_item = title + volunteer_dic[v]
        except:
            if everyday or chatday and d in run_days:
                csv_item = title + '-'
                txt_item = title + '-' + ' ' * (width - 4)
            else:
                csv_item = ''
                txt_item = ' ' * width
        return txt_item, csv_item

    def daily_txt_solution(day, shift, everyday, chatday):
        has = False
        daily_shift_item = ''
        try:
            v = solution_ds_v[(day, shift)]
            has = True
        except:
            pass
        if has:
            daily_shift_item += ' ' * 5 + vol_r[v]
        elif everyday or chatday and day in run_days:
            daily_shift_item += ' ' * (width - 6) + ' ' * 5 + '-'
        else:
            daily_shift_item += ' ' * width
        return daily_shift_item

    vol_l = {}
    vol_r = {}
    w = width - 5
    for v in volunteers:
        if ord(volunteer_dic[v][0]) < 1000:
            vol_l[v] = volunteer_dic[v].ljust(w)
            vol_r[v] = volunteer_dic[v].rjust(w)
        else:
            length = len(volunteer_dic[v])
            if length in [1, 2, 3]:
                alignment_shift = length
            if length == 4:
                alignment_shift = 3
            if length == 5:
                alignment_shift = 1
            e = l_encoding
            vol_l[v] = volunteer_dic[v].encode(e).ljust(w).decode(e)
            vol_l[v] +=  ' ' * alignment_shift
            vol_r[v] = volunteer_dic[v].encode(e).rjust(w).decode(e)
            vol_r[v] = ' ' * alignment_shift + vol_r[v]

    def horizontal_line():
        print_txt('_' * 7 * width)

    # Calendar
    # TXT and CSV

    print_txt()
    print_txt()
    print_txt(str(schedule_year) + ' ' + month_name)
    print_txt()
    print_txt()
    print_csv([schedule_year, month_name])
    print_csv([])

    txt_weekday_line = ''
    for weekday in l_weekday_name_list:
        txt_weekday_line += '{:<{}}'.format(weekday, width)
    print_txt(txt_weekday_line)
    csv_weekday_line = ['']
    csv_weekday_line.extend([weekday for weekday in l_weekday_name_list])
    print_csv(csv_weekday_line)
    txt_1st_calendar_w_aligner = ' ' * width * firstday_index
    csv_1st_calendar_w_aligner = ',' * firstday_index
    txt_lines = [list() for i in range(5)]
    csv_lines = [list() for i in range(5)]
    for i in weeks:
        horizontal_line()

        for j in range(5):
            txt_lines[j] = ''
        for j in range(5):
            csv_lines[j] = ['']

        if txt_1st_calendar_w_aligner:
            for k in range(5):
                txt_lines[k] = txt_1st_calendar_w_aligner
            txt_1st_calendar_w_aligner = False
        if csv_1st_calendar_w_aligner:
            for k in range(5):
                csv_lines[k].extend(['' for i in csv_1st_calendar_w_aligner])
            csv_1st_calendar_w_aligner = False

        for d in weeks[i]:
            txt_lines[0] += '{:<{}}'.format(d, width)
            csv_lines[0].append(d)

            txt_item, csv_item = calendar_solution(d, l_N, 0, True, False)
            txt_lines[1] += txt_item
            csv_lines[1].append(csv_item)

            txt_item, csv_item = calendar_solution(d, l_E, 3, False, False)
            txt_lines[2] += txt_item
            csv_lines[2].append(csv_item)

            txt_item, csv_item = calendar_solution(d, l_S, 1, False, True)
            txt_lines[3] += txt_item
            csv_lines[3].append(csv_item)

            txt_item, csv_item = calendar_solution(d, l_O, 2, False, False)
            txt_lines[4] += txt_item
            csv_lines[4].append(csv_item)

        for line in txt_lines:
            print_txt(line)
        print_txt()
        print_txt()

        for line in csv_lines:
            print_csv(line)
        print_csv([])

    horizontal_line()
    print_txt()
    print_txt()
    print_txt()
    print_txt()
    print_csv([])


    # By day
    # TXT only
    w = width
    if ord(l_Day[-1]) < 1000:
        print_txt('{:>9}|{:>{}}{:>{}}{:>{}}{:>{}}'.format(l_Day, l_Phone, w,
                l_Extra, w, l_Chat, w, l_Observer, w))
    else:
        print_txt(l_Day + '|' + l_Phone + l_Extra + l_Chat + l_Observer)
    print_txt('_' * 9 + '|' + '_' * 4 * w)

    for d in list_of_days:
         line = ''
         line += '{:>8}.|'.format(d)

         line += daily_txt_solution(d, 0, True, False)
         line += daily_txt_solution(d, 1, False, True)

         print_txt(line)
    print_txt()
    print_txt()

    # # CSV
    print_csv(['', l_Name, l_Phone, l_Chat, l_Observer])
    for v in volunteers:
        line = ['']
        line.append(volunteer_dic[v])
        try:
            line.append(csv_cell(solution_v_phonedays[v]))
        except:
            line.append('')
        for s in [1, 2]:
            try:
                line.append(csv_cell(solution_vs_d[(v, s)]))
            except:
                line.append('')
        print_csv(line)

    # # Needed
    # # 6. hétfő - csetes, Adél mellé
    need_title = False
    for d in certain_weekdays_in_month([2, 3, 4, 5]):
        need = False
        try:
            if needed_daily[d] > -1:
                need = True
        except:
            pass
        if need:
            weekday = l_weekday_name_list[what_day_dic[d]-1]
            needed_shift = needed_daily[d]
            if not need_title:
                print_txt(l_need)
                need_title = True
            if needed_shift == 0:
                needed_shift = l_phone
            if needed_shift == 1:
                needed_shift = l_chat
            if needed_shift == 2:
                needed_shift = l_phone + ' and ' + l_chat
            line = '{:>12}. {:>10}:'.format(d, weekday.lower())
            line += '{:>20}'.format(needed_shift)
            print_txt(line)
    print_txt()
    print_txt()

    # Letter to volunteers
    print_txt()
    print_txt()
    print_txt()

    print(l_created, txt_file)
    print(l_created, csv_file)
    print_txt()
    print_txt()
    print_txt()

    if l_message_1:
        print_txt(' ' * 10 + l_message_1)
        print_txt(' ' * 36 + l_message_2)
        print_txt()
    print_txt()
    print_txt(' ' * 10 + 'Copyright (c) 2019, Imre Szakal (imreszakal.com)')
    print_txt()

if __name__ == '__main__':
    main()
