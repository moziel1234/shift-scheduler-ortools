"""Nurse scheduling problem with shift requests."""
from ortools.sat.python import cp_model


def main():
    # This program tries to find an optimal assignment of nurses to shifts
    # (3 shifts per day, for 7 days), subject to some constraints (see below).
    # Each nurse can request to be assigned to specific shifts.
    # The optimal assignment maximizes the number of fulfilled shift requests.

    num_shifts = 4
    min_nights = 0
    max_nights = 2
    min_shifts = 3
    max_shifts = 5
    max_6_12 = 10

    names = ["מני", "גבי", "אריה", "יונתן", "מימון", "אפשטיין", "יעקב",
             "עמר", "עקיבא", "משה", "אור", "רזיאל", "אלון", "אסף", "ישראל"]

    num_nurses = len(names)
    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)


    nurses_per_shift = [
        [3, 3, 3, 2], # חמישי
        [4, 2, 2, 3],  # שישי
        [4, 3, 3, 2],  # שבת
        [2, 2, 3, 3],  # ראשון
        [4, 3, 3, 2],  # שני

    ]
    total_sum = sum(sum(shift) for shift in nurses_per_shift)
    print("Total sum of numbers in the list:", total_sum)

    num_days = len(nurses_per_shift)
    all_days = range(num_days)

    shift_requests = [
        [[0, 1, -1, -1], [0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0], [0, 1, 0, 0]],  # מני
        [[-1, -1, -1, -1], [0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 1]],  # גבי
        [[-1,-1, 0, 0], [0, 0, -1, -1], [-1, -1, -1, -1], [0, 0, 0, 0], [0, 0, 0, 0]],  # אריה
        [[-1, -1, -1, -1], [-1, -1, -1, -1], [-1, -1, -1, -1], [0, 0, 0, 0], [0, 0, 0, 0]],  # יונתן
        [[-1, -1, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # מימון
        [[-1, 0, 0, 1], [0, 0, 0, 0], [1, 0, 0, 0], [1, 0, -1, -1], [-1, -1, -1, -1]],  # אפשטיין
        [[-1, -1, -1, -1], [-1, -1, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # יעקב
        [[-1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [-1, -1, -1, -1], [-1, -1, -1, -1]],  # עמר
        [[0, 0, 0, 0], [0, 0, -1, -1], [-1, -1, -1, -1], [0, 0, 0, 0], [0, 0, 0, 0]],  # עקיבא
        [[-1, -1, -1, -1], [0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # משה
        [[-1, -1, -1, -1], [-1, -1, -1, -1], [-1, 0, 0, 0], [0, 0, 0, 0], [0, 1, 0, 0]],  # אור
        [[0, 0, -1, 0], [0, 1, 0, -1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # רזיאל
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 1, -1, -1], [-1, -1, -1, -1]],  # אלון
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [-1, -1, -1, -1], [-1, -1, -1, -1]],  # אסף
        [[-1, 0, 0, 0], [0, 0, -1, -1], [-1, -1, -1, -1], [0, 0, 0, -1], [-1, 0, 0, 0]],  # ישראל
    ]


    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: nurse 'n' works shift 's' on day 'd'.
    shifts = {}
    conseq_shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar(f"shift_n{n}_d{d}_s{s}")
                conseq_shifts[(n, d, s)] = model.NewIntVar(0, 100, f"conseq_shifts_n{n}_d{d}_s{s}")


    '''
    # Each shift is assigned to exactly one nurse in .
    for d in all_days:
        for s in all_shifts:
            model.AddExactlyOne(shifts[(n, d, s)] for n in all_nurses)
    '''


    for d in range(num_days):
        for s in range(num_shifts):
            model.Add(sum(shifts[(n, d, s)] for n in range(num_nurses)) == nurses_per_shift[d][s])

    # Constraint: Minimum gap of 2 shifts between shifts of the same nurse.
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                next_day = d
                next_next_day = d
                next_shift = s + 1
                next_next_shift = s + 2

                if s+1 == all_shifts[-1]+1:
                    next_day += 1
                    next_shift = 0
                if s+1 == all_shifts[-1]+2:
                    next_day += 1
                    next_shift = 1

                if s + 2 == all_shifts[-1] + 1:
                    next_next_day += 1
                    next_next_shift = 0
                if s + 2 == all_shifts[-1] + 2:
                    next_next_day += 1
                    next_next_shift = 1

                if next_day <= all_days[-1] and next_next_day <= all_days[-1]:
                    model.Add(shifts[(n, d, s)] +
                              shifts[(n, next_day, next_shift)] +
                              shifts[(n, next_next_day, next_next_shift)] <= 1)

    '''
    # Each nurse works at most one shift per day.
    for n in all_nurses:
        for d in all_days:
            model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)
    '''



    # Try to distribute the shifts evenly, so that each nurse works
    # min_shifts_per_nurse shifts. If this is not possible, because the total
    # number of shifts is not divisible by the number of nurses, some nurses will
    # be assigned one more shift.
    min_shifts_per_nurse = (num_shifts * num_days) // num_nurses
    if num_shifts * num_days % num_nurses == 0:
        max_shifts_per_nurse = min_shifts_per_nurse
    else:
        max_shifts_per_nurse = min_shifts_per_nurse + 1
    for n in all_nurses:
        num_shifts_worked = 0
        for d in all_days:
            for s in all_shifts:
                num_shifts_worked += shifts[(n, d, s)]
        # model.Add(min_shifts_per_nurse <= num_shifts_worked)
        # model.Add(num_shifts_worked <= max_shifts_per_nurse)

        model.Add(num_shifts_worked >= min_shifts)
        model.Add(num_shifts_worked <= max_shifts)

    '''
    # pylint: disable=g-complex-comprehension
    model.Maximize(
        sum(
            shift_requests[n][d][s] * shifts[(n, d, s)]
            for n in all_nurses
            for d in all_days
            for s in all_shifts
        )
    )
    '''
    # negative and positive request
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                if shift_requests[n][d][s] == -1:
                    model.Add(shifts[(n, d, s)] == 0)
                if shift_requests[n][d][s] == 1:
                    model.Add(shifts[(n, d, s)] == 1)

    for n in all_nurses:
        model.Add(
            sum(shifts[(n, day, 0)] for day in all_days) >= min_nights
        )  # At least one first shift day
        model.Add(
            sum(shifts[(n, day, 0)] for day in all_days) <= max_nights
        )  # At most two first shift days

    for nurse in all_nurses:
        for day in all_days:
            model.Add(sum(shifts[(nurse, day, shift)] for shift in all_shifts) <= 1).OnlyEnforceIf(
                model.NewBoolVar(f'nurse_{nurse}_works_at_most_one_shift_on_day_{day}')
            )

    model.Add(sum(shifts[(names.index("עמר"), day, shift)] for day in all_days for shift in all_shifts) == 4)
    model.Add(sum(shifts[(names.index("מימון"), day, 0)] for day in all_days ) == 1)
    '''model.Add(sum(shifts[(names.index("עקיבא"), day, shift)] for day in all_days for shift in all_shifts) == 5)
    model.Add(sum(shifts[(names.index("משה"), day, shift)] for day in all_days for shift in all_shifts) == 5)
    model.Add(sum(shifts[(names.index("עמר"), day, shift)] for day in all_days for shift in all_shifts) == 6)
    model.Add(sum(shifts[(names.index("גבי"), day, shift)] for day in all_days for shift in all_shifts) == 6)
    model.Add(sum(shifts[(names.index("יונתן"), day, shift)] for day in all_days for shift in all_shifts) == 6)
    model.Add(sum(shifts[(names.index("ויקטור"), day, shift)] for day in all_days for shift in all_shifts) == 6)
    model.Add(sum(shifts[(names.index("אסף"), day, shift)] for day in all_days for shift in all_shifts) == 6)
    model.Add(sum(shifts[(names.index("אריה"), day, shift)] for day in all_days for shift in all_shifts) == 6)
    model.Add(sum(shifts[(names.index("מימון"), day, shift)] for day in all_days for shift in all_shifts) == 5)
    model.Add(sum(shifts[(names.index("יעקב"), day, shift)] for day in all_days for shift in all_shifts) == 5)
    # model.Add(sum(shifts[(names.index("מימון"), day, 0)] for day in all_days) == 1)'''

    # Creates the solver and solve.

    solver = cp_model.CpSolver()
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL:
        print("Solution:")
        for d in all_days:
            # print("Day", d)
            for s in all_shifts:
                for n in all_nurses:
                    if solver.Value(shifts[(n, d, s)]) == 1:
                        print(names[n], end=", ")
                print()

            # print()
        print(
            f"Number of shift requests met = {solver.ObjectiveValue()}",
            f"(out of {num_nurses * min_shifts_per_nurse})",
        )

    else:
        print("No optimal solution found !")

    # Statistics.
    print("\nStatistics")
    print(f"  - conflicts: {solver.NumConflicts()}")
    print(f"  - branches : {solver.NumBranches()}")
    print(f"  - wall time: {solver.WallTime()}s")


if __name__ == "__main__":
    main()