from ortools.linear_solver import pywraplp

# Define your data
num_employees = 17
num_days = 9
#                        0  1  2  3  4  5  6  7  8
#                        M  T  W  T  F  S   S  M  T
#                        4  5  6  7  8  9  10 11 12
max_vacations_per_day = [4, 4, 4, 4, 4, 4, 4, 5, 5]  # Maximum vacations allowed per day
splited = [1, 0, 1]
# Example: employee_preferences[employee_id][day_id] = priority
employee_preferences = [
    [9, 9, 9, 1, 9, 9, 0, 9, 9], # יעקב
    [0, 0, 0, 0, 0, 0, 0, 0, 0], # עמר
    [0, 0, 0, 0, 0, 0, 0, 0, 0], # יונתן
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0, 0],

]

# Initialize the solver
solver = pywraplp.Solver.CreateSolver('CBC')

# Define variables
vacations = {}
for employee in range(num_employees):
    for day in range(num_days):
        vacations[(employee, day)] = solver.BoolVar(f'Employee_{employee}_Day_{day}')

# Define constraints
for day in range(num_days):
    solver.Add(sum(vacations[employee, day] for employee in range(num_employees)) <= max_vacations_per_day[day])

# Each employee should get 2 days off
for employee in range(num_employees):
    solver.Add(sum(vacations[employee, day] for day in range(num_days)) == 2)


# Define the objective function: minimize total penalty
total_penalty = solver.Sum(
    employee_preferences[employee][day] * vacations[(employee, day)]
    for employee in range(num_employees)
    for day in range(num_days)
)

solver.Minimize(total_penalty)

# Solve the problem
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL:
    print('Optimal Solution:')
    for employee in range(num_employees):
        for day in range(num_days):
            if vacations[employee, day].solution_value() == 1:
                print(f'Employee {employee} takes vacation on Day {day}')
else:
    print('No optimal solution found.')
