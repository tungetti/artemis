# Import the necessary libraries
import openpyxl
import pandas as pd


def update_workbook(workbook_name, data, sheet):
    workbook = openpyxl.load_workbook('./source/template_entraid.xlsx')
    # Add data to the Excel sheet
    data = data #[
    #     ["Name", "Age", "City"],
    #     ["John", 28, "New York"],
    #     ["Alice", 24, "San Francisco"],
    #     ["Bob", 32, "Los Angeles"]
    # ]

    test_sheet = workbook[sheet]
    for row in data:
        test_sheet.append(row)
    # Save the workbook to a file
    workbook.save(f"{workbook_name}.xlsx")

update_workbook()