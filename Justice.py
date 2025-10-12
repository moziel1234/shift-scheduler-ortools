import openpyxl
from openpyxl.styles.colors import Color

from collections import defaultdict
import matplotlib.pyplot as plt
import numpy as np

ignore_names = ["אלדד", "אורי", "אליסף", "כוח דדה", "אזרחים", "מאיר\בועז", "הדריאל", "אורי רוזנצוויג", "עמוס"]

# Open the Excel file and select Sheet3
wb = openpyxl.load_workbook(rf"C:\Users\uziki\OneDrive\שולחן העבודה\2שבצק.xlsx", data_only=True)
sheet = wb['Sheet1']


lines_with_yom = []
first_line = "יום ראשון 25.02"
pass_first_line = False
pass_first_black = False
# Iterate over cells in column A
for cell in sheet['A']:
    if cell.fill.start_color.index == Color('FF000000').index:
        pass_first_black = True
    if cell.value and first_line in str(cell.value):
        pass_first_line = True
    if cell.value and "יום" in str(cell.value) and (pass_first_line or not pass_first_black):
        lines_with_yom.append(cell.row)

# Initialize a dictionary to store name counts for each time slot
time_slot_counts = {'2:00-8:00': defaultdict(int), '8:00-14:00': defaultdict(int),
                    '14:00-20:00': defaultdict(int), '20:00-02:00': defaultdict(int)}

# Initialize dictionaries to store name counts for each time slot and total counts
time_slot_counts = defaultdict(int)
total_counts = defaultdict(int)
name_lists = defaultdict(list)

for row_number in lines_with_yom:
    # Iterate over columns B, C, D, E for rows from row_number + 2 to row_number + 5
    for row in range(row_number + 2, row_number + 6):  # 2 to 5 inclusive
        for column in range(2, 7):  # B to F
            name = sheet.cell(row=row, column=column).value
            if name and ":" not in name and name not in ignore_names:
                if "עמוס" in name:
                    a=4
                time_slot_counts[name] += 1 if row ==  row_number + 2 else 0
                total_counts[name] += 1

for name in time_slot_counts:
    name_lists[(time_slot_counts[name], total_counts[name])].append(name[::-1])

# Prepare data for the scatter plot
x_values = [time_slot_counts[name] for name in time_slot_counts]
y_values = [total_counts[name] for name in time_slot_counts]
names = list(time_slot_counts.keys())

yair_index = names.index("יאיר")
or_index = names.index("אור")
alon_index = names.index("אלון")
maayan_index = names.index("מעיין")
asaf_index = names.index("אסף")
israel_index = names.index("ישראל")

x_xvg = int(sum(x_values) / len(x_values)) +1
x_values[yair_index] = x_xvg
name_lists[(x_xvg, y_values[yair_index])].append("יאיר"[::-1])

x_values[or_index] += 3
y_values[or_index] += 9
name_lists[(x_values[or_index], y_values[or_index])].append("אור"[::-1])

x_values[alon_index] += 7
y_values[alon_index] += 18
name_lists[(x_values[alon_index], y_values[alon_index])].append("אלון"[::-1])

x_values[maayan_index] += 5
y_values[maayan_index] += 17
name_lists[(x_values[maayan_index], y_values[maayan_index])].append("מעיין"[::-1])

x_values[asaf_index] += 9
y_values[asaf_index] += 30
name_lists[(x_values[asaf_index], y_values[asaf_index])].append("אסף"[::-1])

x_values[israel_index] += 9
y_values[israel_index] += 30
name_lists[(x_values[israel_index], y_values[israel_index])].append("ישראל"[::-1])

## Plot the scatter plot
plt.figure(figsize=(10, 6))

plt.scatter(x_values, y_values, marker='o', color='b')

# Add labels to the points with aggregated names
for i, (x, y) in enumerate(zip(x_values, y_values)):
    aggregated_names = '\n'.join(name_lists[(x, y)])
    plt.text(x_values[i], y_values[i], aggregated_names, fontsize=9)




plt.xlabel('Frequency in 2:00-8:00')
plt.ylabel('Total Frequency')
plt.title('Frequency of Names')
plt.grid(True)
plt.tight_layout()
plt.show()