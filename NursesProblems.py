"""Nurse scheduling problem with shift requests."""
from ortools.sat.python import cp_model


def main():
    num_shifts = 3
    # min_shifts = 5
    max_shifts = 6

    names = ['יאיר מימון', 'אסף ברזיס', 'רזיאל זקבך', 'איתן אברהמי', 'אלי בוימל', 'מרדכי יצהר', 'אהרון רוטנברג',
             'ישראל מלכיאל', 'יוני סרוסי', 'נעם לוי']
    shift_requests = [
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # יאיר מימון
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # אסף ברזיס
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # רזיאל זקבך
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # איתן אברהמי
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # אלי בוימל
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # אלי בוימל
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # אלי בוימל
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # אלי בוימל
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # אלי בוימל
        [[1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1], [1, 1, 1]],  # אלי בוימל

    ]

    num_nurses = len(names)
    all_nurses = range(num_nurses)
    all_shifts = range(num_shifts)

    nurses_per_shift = [
        [2, 2, 2],  # שישי
        [2, 2, 2],  # שבת
        [2, 2, 2],  # ראשון
        [2, 2, 2],  # שני
        [2, 2, 2],  # שלישי
        [2, 2, 2],  # רביעי
        [2, 2, 2],  # חמישי
    ]

    total_sum = sum(sum(shift) for shift in nurses_per_shift)
    print("Total sum of numbers in the list:", total_sum)

    num_days = len(nurses_per_shift)
    all_days = range(num_days)

    # Creates the model.
    model = cp_model.CpModel()

    # Creates shift variables.
    # shifts[(n, d, s)]: nurse 'n' works shift 's' on day 'd'.
    shifts = {}
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                shifts[(n, d, s)] = model.NewBoolVar(f"shift_n{n}_d{d}_s{s}")

    for d in range(num_days):
        for s in range(num_shifts):
            model.Add(sum(shifts[(n, d, s)] for n in range(num_nurses)) == nurses_per_shift[d][s])

    # Each nurse works at most one shift per day.
    for n in all_nurses:
        for d in all_days:
            model.AddAtMostOne(shifts[(n, d, s)] for s in all_shifts)

    # min max shifts
    for n in all_nurses:
        num_shifts_worked = 0
        for d in all_days:
            for s in all_shifts:
                num_shifts_worked += shifts[(n, d, s)]
        # model.Add(num_shifts_worked >= min_shifts)
        model.Add(num_shifts_worked <= max_shifts)

    # Constraint: can't do morning after night
    for n in all_nurses:
        for d in range(num_days-1):
            model.Add(shifts[(n, d, 2)] + shifts[(n, d+1, 0)] <= 1)

    # negative and positive request
    for n in all_nurses:
        for d in all_days:
            for s in all_shifts:
                if shift_requests[n][d][s] == -1:
                    model.Add(shifts[(n, d, s)] == 0)
                '''if shift_requests[n][d][s] == 1:
                    model.Add(shifts[(n, d, s)] == 1)'''

    objective = [  # Use model.Sum to define the objective
        ((shift_requests[n][d][s] == 1) * shifts[(n, d, s)])  # Use default weight of 1 if not specified
        for n in all_nurses
        for d in all_days
        for s in all_shifts
    ]
    model.Maximize(sum(objective))


    afters = [6, 6, 2, 6, 2, 5, 5, 2, 6, 3, 4, 4, 4, 4, 4,]
    for name_ind, name in enumerate(names):
        model.Add(sum(shifts[(names.index(name), day, shift)] for day in all_days for shift in all_shifts) <=
                  afters[name_ind])

    nights = [2, 1, 1, 1, 1, 1, 1, 1, 2, 1, 2, 1, 1, 3, 2,]
    for name_ind, name in enumerate(names):
        model.Add(sum(shifts[(names.index(name), day, 2)] for day in all_days) <= nights[name_ind])





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
            f"(out of {num_nurses * 4})",
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