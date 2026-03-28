#!/usr/bin/evn python3
# -*- coding: utf-8 -*-
"""
Created on 10/13/25

@author waldo

"""
import csv, sys, os, tempfile
from typing import Any
import pandas as pd

header_row_c = 23

output_header = [
    'PI/Lab',
    'PI Name',
    'Number of Reports',
    'Number of Line Items',
    'Average Lines per Report',
    "Total Expenses",
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
    def __init__(self, report_id, root_num, employee_name, amount, date, description):
        self.report_id = report_id
        self.root_num = root_num
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


# class PI:
#     def __init__(self, pi_id, name, expense):
#         self.pi_id = pi_id
#         self.name = name
#         self.expense_l = [expense]
#
#     def __repr__(self):
#         return (f"PI(pi_id={self.pi_id}, "
#                 f"name='{self.name}', "
#                 f"expenses ='{self.expense_l}')")

class PI_Expense_Summary:
    '''
    Class used to aggregate expense reports for a PI, identified by the root number associated with the PI
    '''
    def __init__(self, root, pi_name, expense):
        self.root = root
        self.pi_name = pi_name
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
        out_line = [self.root,
                    self.pi_name,
                    self.expense_ct,
                    self.lines,
                    "{:.2f}".format(self.lines/self.expense_ct),
                    "{:.2f}".format(self.amount),
                    self.travel_ct,
                    self.catering_ct
                    ]
        return out_line


def extract_name(line):
    """
    Extract name by removing prefix up to first '^' and everything us to the space before the
     first number
    Args:
        line: input string
    Returns:
        processed string
    """
    if not line or '^' not in line:
        return line

    # Find position after second ^
    first_caret = line.find('^')
    if first_caret == -1:
        return line

    # Remove prefix up to second ^
    name = line[first_caret + 1:]

    # Remove everything after the space before the first number
    for i, c in enumerate(name):
        if c.isdigit():
            name = name[:i-1]
            break

    return name.strip()


def make_root_2_pi_d(infile):
    '''
    read a csv file, skipping the first line as a header, then build a dictionary from the root code to the PI name,
    where the code is the first field and the PI name is the second field
    :param infile: path to a csv file
    :return: dictionary with root code as key and PI name as value
    '''
    ret_d = dict()
    with open(infile) as file:
        csv_r = csv.reader(file)
        l = next(csv_r)
        for l in csv_r:
            ret_d[l[0]] = l[1]
    return ret_d

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
    '''
    Create a dictionary, indexed by expense report ID with value and ExpenseReport object, that will
    track the number of lines, the total amount, and whether or not the expense report was a travel expense report.
    :param expenses_line_list:
    :param travel_line_list:
    :return: A dictionary of [expense_id, ExpenseReport]
    '''
    expense_dict: dict[str, ExpenseReport] = {}
    for line in expenses_line_list:
        if line[1] in expense_dict:
            expense = expense_dict[line[1]]
            expense.num_lines += 1
            expense.amount += convert_string_to_float(line[16])

        else:
            expense_dict[line[1]] = ExpenseReport(line[1], line[12], line[4], convert_string_to_float(line[16]), line[0], line[2])
        if line[13] in travel_line_list:
            expense_dict[line[1]].travel = (True)
        if 'Catering' in line[13]:
            expense_dict[line[1]].catering = (True)

    return expense_dict

def process_concur_file(concur_file, travel_file):
   '''
   Read a concur file, and a file with the categories that are considered travel expenses, and
   create a dictionary indexed by expense report number with values ExpenseReports objects
   :param concur_file:
   :param travel_file:
   :return:
   '''
   travel_cat = read_travel_cat(travel_file)
   with open(concur_file) as file:
       csv_r = csv.reader(file)
       skip_headers(csv_r)
       expense_dict= make_expense_dict(csv_r, travel_cat)
       return expense_dict


def make_employee_dict(expense_dict, root_2_pi_dict):
    """Creates a dictionary of expense reports grouped by the root number associated with the PI for whom the
    expense report was submitted.

    Args:
        expense_dict: Dictionary of expense reports indexed by report ID

    Returns:
        Dictionary with employee names as keys and lists of their expense reports as values
    """
    employee_dict: dict[str, PI_Expense_Summary] = {}
    for expense in expense_dict.values():
        if expense.root_num in root_2_pi_dict:
            emp_key = expense.root_num
            pi_name = root_2_pi_dict[expense.root_num]
        else:
            emp_key = expense.root_num + expense.employee_name
            pi_name = expense.employee_name

        if emp_key not in employee_dict:
            employee_dict[emp_key] = PI_Expense_Summary(expense.root_num, pi_name, expense)
        else:
            employee_dict[emp_key].update(expense)

    return employee_dict

def excel_to_csv(excel_path):
    '''Convert an Excel file to a temporary CSV file, returning the temp file path.'''
    df = pd.read_excel(excel_path, header=None)
    tmp = tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False)
    tmp.close()
    df.to_csv(tmp.name, index=False, header=False)
    return tmp.name


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python ExpenseReport.py <concur_file> <travel_file> <root_to_pi_file>")
        sys.exit(1)

    concur_csv = excel_to_csv(sys.argv[1])
    travel_csv = excel_to_csv(sys.argv[2])
    try:
        expense_dict = process_concur_file(concur_csv, travel_csv)
        root_2_pi_d = make_root_2_pi_d(sys.argv[3])
        employee_dict = make_employee_dict(expense_dict, root_2_pi_d)
        summary_l = list(employee_dict.values())

        with open('output.csv', 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            csv_writer.writerow(output_header)
            for summary in summary_l:
                csv_writer.writerow(summary.summary_output())
    finally:
        os.unlink(concur_csv)
        os.unlink(travel_csv)

