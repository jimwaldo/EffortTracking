#!/usr/bin/evn python3
# -*- coding: utf-8 -*-
"""
Created on 10/13/25

@author waldo

"""
import csv, sys
from typing import Any

header_row_c = 23

output_header = [
    'PI/Lab',
    'Number of Reports',
    'Number of Line Items',
    'Average Lines per Report',
    'Number of Travel Reports',
    'Number of Catering Reports'
]

def skip_headers(csv_file):
    #l = next(csv_file)
    for _ in range(header_row_c):
        l = next(csv_file)
    return l

def read_travel_cat(csv_file):
    ret_set = set()
    with open(csv_file) as file:
        csv_r = csv.reader(file)
        for l in csv_r:
            ret_set.add(l[0])
    return ret_set

class ExpenseReport:
    def __init__(self, report_id, employee_name, amount, date, description):
        self.report_id = report_id
        self.employee_name = employee_name
        self.amount = amount
        self.date = date
        self.description = description
        self.num_lines = 1  # Default value
        self.travel = False
        self.catering = False

    def __repr__(self):
        return (f"ExpenseReport(report_id={self.report_id}, "
                f"employee_name='{self.employee_name}', "
                f"amount={self.amount}, "
                f"date='{self.date}', "
                f"description='{self.description}')")


class PI:
    def __init__(self, pi_id, name, expense):
        self.pi_id = pi_id
        self.name = name
        self.expense_l = [expense]

    def __repr__(self):
        return (f"PI(pi_id={self.pi_id}, "
                f"name='{self.name}', "
                f"expenses ='{self.expense_l}')")

class PI_Expense_Summary:
    def __init__(self, name, expense):
        self.name = name
        self.expense_ct = 1
        self.lines = expense.num_lines
        self.amount = expense.amount
        if expense.travel:
            self.travel_ct = 1
        else:
            self.travel_ct = 0
        if expense.catering:
            self.catering_ct = 1
        else:
            self.catering_ct = 0

    def update(self, expense ):
        self.expense_ct += 1
        self.lines += expense.num_lines
        self.amount += expense.amount
        if expense.travel:
            self.travel_ct += 1
        if expense.catering:
            self.catering_ct += 1
        return None

    def summary_output(self):
        out_line = [self.name,
                    self.expense_ct,
                    self.lines,
                    self.lines/self.expense_ct,
                    self.travel_ct,
                    self.catering_ct
                    ]
        return out_line




def convert_string_to_float(num_string):
    '''takes a string that might contain commas and converts to a float
    numbers in parentheses are treated as negative'''
    # Check if the number is in parentheses
    if not num_string or not isinstance(num_string, str):
        return 0
    num_string = num_string.strip()
    if num_string.startswith('(') and num_string.endswith(')'):
        # Remove parentheses and commas, then convert to negative float
        return -float(num_string[1:-1].replace(',', ''))
    else:
        # Remove commas and convert to float
        return float(num_string.replace(',', ''))

def make_expense_dict(expenses_line_list, travel_line_list):
    expense_dict: dict[str, ExpenseReport] = {}
    for line in expenses_line_list:
        if line[1] in expense_dict:
            expense = expense_dict[line[1]]
            expense.num_lines += 1
            expense.amount += convert_string_to_float(line[16])

        else:
            expense_dict[line[1]] = ExpenseReport(line[1], line[4], convert_string_to_float(line[16]), line[0], line[2])
        if line[13] in travel_line_list:
            expense_dict[line[1]].travel = (True)
        if 'Catering' in line[13]:
            expense_dict[line[1]].catering = (True)

    return expense_dict

def process_concur_file(concur_file, travel_file):
   travel_cat = read_travel_cat(travel_file)
   with open(concur_file) as file:
       csv_r = csv.reader(file)
       skip_headers(csv_r)
       expense_dict= make_expense_dict(csv_r, travel_cat)
       return expense_dict


def make_employee_dict(expense_dict):
    """Creates a dictionary of expense reports grouped by employee name.

    Args:
        expense_dict: Dictionary of expense reports indexed by report ID

    Returns:
        Dictionary with employee names as keys and lists of their expense reports as values
    """
    employee_dict: dict[str, PI_Expense_Summary] = {}
    for expense in expense_dict.values():
        if expense.employee_name not in employee_dict:
            employee_dict[expense.employee_name] = PI_Expense_Summary(expense.employee_name, expense)
        else:
            employee_dict[expense.employee_name].update(expense)

    return employee_dict

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python ExpenseReport.py <concur_file> <travel_file>")
        sys.exit(1)

    expense_dict = process_concur_file(sys.argv[1], sys.argv[2])
    employee_dict = make_employee_dict(expense_dict)
    summary_l = list(employee_dict.values())

    with open('output.csv', 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerow(output_header)
        for summary in summary_l:
            csv_writer.writerow(summary.summary_output())

