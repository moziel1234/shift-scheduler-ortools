# shift_planner_cp_sat.py
from ortools.sat.python import cp_model
from typing import Dict, List, Tuple, Union
from openpyxl import Workbook
from openpyxl.styles import Font, Alignment

# --------------------------
# Helper functions
# --------------------------
def intervals_overlap(a: Tuple[float, float], b: Tuple[float, float]) -> bool:
    return max(a[0], b[0]) < min(a[1], b[1])

def shift_intervals_overlap_any(assigned_intervals: List[Tuple[float, float]],
                                forbidden_intervals: List[Tuple[float, float]]) -> bool:
    for a in assigned_intervals:
        for b in forbidden_intervals:
            if intervals_overlap(a, b):
                return True
    return False

def hours_between_intervals(day_a: int, interval_a: Tuple[float, float],
                            day_b: int, interval_b: Tuple[float, float]) -> float:
    end_a = day_a * 24.0 + interval_a[1]
    start_b = day_b * 24.0 + interval_b[0]
    return start_b - end_a

def shifts_violate_rest(day_a: int, intervals_a: List[Tuple[float, float]],
                        day_b: int, intervals_b: List[Tuple[float, float]],
                        min_rest_hours: float) -> bool:
    for ia in intervals_a:
        for ib in intervals_b:
            if hours_between_intervals(day_a, ia, day_b, ib) < min_rest_hours:
                return True
    return False

# --------------------------
# Core function
# --------------------------
def plan_shifts(
    names: List[str],
    shift_requests: List[List[List[int]]],     # shape: [persons][days][4 standard shifts]
    STANDARD_SHIFTS: List[str],                # ordered 4 standard shift names
    shift_time_map: Dict[str, List[Tuple[float, float]]],  # shift_name -> list of (start_hr, end_hr)
    target_shifts: Dict[str, int],
    num_days: int = None,
    shift_requirements: Union[int, Dict[str, Union[int, List[int]]]] = 1,
    min_shifts_per_person: Union[int, List[int]] = 0,
    max_shifts_per_person: Union[int, List[int]] = 999,
    min_rest_hours: float = 8.0,
    time_limit_seconds: int = 20
):
    P = len(names)
    if num_days is None:
        num_days = len(shift_requests[0])

    # normalize min/max per person
    if isinstance(min_shifts_per_person, int):
        min_shifts = [min_shifts_per_person] * P
    else:
        min_shifts = list(min_shifts_per_person)

    if isinstance(max_shifts_per_person, int):
        max_shifts = [max_shifts_per_person] * P
    else:
        max_shifts = list(max_shifts_per_person)

    # requirement accessor
    def req_for(shift_name: str, day: int) -> int:
        if isinstance(shift_requirements, int):
            return shift_requirements
        if isinstance(shift_requirements, dict):
            v = shift_requirements.get(shift_name, None)
            if v is None:
                return 1
            if isinstance(v, int):
                return v
            else:
                return v[day]
        return 1

    model = cp_model.CpModel()

    # decision vars
    assign = {}
    shift_names = list(shift_time_map.keys())

    for p in range(P):
        for d in range(num_days):
            for s in shift_names:
                assign[(p, d, s)] = model.NewBoolVar(f"assign_p{p}_d{d}_s_{s}")

    # 1) coverage constraints
    for d in range(num_days):
        for s in shift_names:
            req = req_for(s, d)
            model.Add(sum(assign[(p, d, s)] for p in range(P)) == req)

    # 2) forbid assignments marked -1
    std_intervals_map = {std: shift_time_map[std] for std in STANDARD_SHIFTS}
    for p in range(P):
        for d in range(num_days):
            for std_idx, std_name in enumerate(STANDARD_SHIFTS):
                if shift_requests[p][d][std_idx] == -1:
                    forbidden_intervals = std_intervals_map[std_name]
                    for s in shift_names:
                        assigned_intervals = shift_time_map[s]
                        if shift_intervals_overlap_any(assigned_intervals, forbidden_intervals):
                            model.Add(assign[(p, d, s)] == 0)

    # 3) min/max shifts per person
    for p in range(P):
        total = [assign[(p, d, s)] for d in range(num_days) for s in shift_names]
        model.Add(sum(total) >= min_shifts[p])
        model.Add(sum(total) <= max_shifts[p])

    # 4) min rest constraints
    for p in range(P):
        person_shifts = [(d, s, shift_time_map[s]) for d in range(num_days) for s in shift_names]
        N = len(person_shifts)
        for i in range(N):
            d1, s1, intervals1 = person_shifts[i]
            for j in range(i+1, N):
                d2, s2, intervals2 = person_shifts[j]
                if d1 == d2 and s1 == s2:
                    continue
                '''if shifts_violate_rest(d1, intervals1, d2, intervals2, min_rest_hours) \
                   or shifts_violate_rest(d2, intervals2, d1, intervals1, min_rest_hours):
                    model.Add(assign[(p, d1, s1)] + assign[(p, d2, s2)] <= 1)'''
                if shifts_violate_rest(d1, intervals1, d2, intervals2, min_rest_hours):
                    model.Add(assign[(p, d1, s1)] + assign[(p, d2, s2)] <= 1)

    # 5) preferences
    preference_terms = []
    for p in range(P):
        for d in range(num_days):
            for std_idx, std_name in enumerate(STANDARD_SHIFTS):
                if shift_requests[p][d][std_idx] == 1:
                    pref_intervals = shift_time_map[std_name]
                    for s in shift_names:
                        intervals = shift_time_map[s]
                        if shift_intervals_overlap_any(intervals, pref_intervals):
                            preference_terms.append(assign[(p, d, s)])


    # 6) force number of shifts per person
    for p, person_name in enumerate(names):
        if person_name in target_shifts:
            total_shifts = sum(assign[(p, d, s)] for d in range(num_days) for s in shift_names)
            model.Add(total_shifts == target_shifts[person_name])

    # balancing term
    max_shifts_var = model.NewIntVar(0, num_days * len(shift_names), "max_shifts")
    for p in range(P):
        model.Add(sum(assign[(p, d, s)] for d in range(num_days) for s in shift_names) <= max_shifts_var)

    # objective: maximize preferences, then balance
    model.Maximize(1000 * sum(preference_terms) - max_shifts_var)

    # solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit_seconds
    solver.parameters.num_search_workers = 8
    result = solver.Solve(model)

    if result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        solution = {}
        shift_counts = {names[p]: 0 for p in range(P)}
        for p in range(P):
            for d in range(num_days):
                for s in shift_names:
                    if solver.Value(assign[(p, d, s)]):
                        solution[(names[p], d, s)] = 1
                        shift_counts[names[p]] += 1
        return {
            "status": solver.StatusName(result),
            "solution": solution,
            "shift_counts": shift_counts,
            "objective": solver.ObjectiveValue()
        }
    else:
        return None


def check_solution(
    solution: Dict[Tuple[str,int,str], int],
    names: List[str],
    shift_requests: List[List[List[int]]],
    STANDARD_SHIFTS: List[str],
    shift_time_map: Dict[str, List[Tuple[float, float]]],
    shift_requirements,
    min_shifts_per_person=0,
    max_shifts_per_person=999,
    min_rest_hours=8.0
):
    violations = []
    P = len(names)
    name_to_idx = {n: i for i,n in enumerate(names)}
    num_days = len(shift_requests[0])
    shift_names = list(shift_time_map.keys())

    # normalize min/max
    if isinstance(min_shifts_per_person, int):
        min_shifts = [min_shifts_per_person] * P
    else:
        min_shifts = list(min_shifts_per_person)

    if isinstance(max_shifts_per_person, int):
        max_shifts = [max_shifts_per_person] * P
    else:
        max_shifts = list(max_shifts_per_person)

    # requirement accessor
    def req_for(shift_name: str, day: int) -> int:
        if isinstance(shift_requirements, int):
            return shift_requirements
        if isinstance(shift_requirements, dict):
            v = shift_requirements.get(shift_name, None)
            if v is None:
                return 1
            if isinstance(v, int):
                return v
            else:
                return v[day]
        return 1

    # 1) Coverage check
    for d in range(num_days):
        for s in shift_names:
            assigned = [pname for (pname, dd, ss), v in solution.items() if v and dd == d and ss == s]
            req = req_for(s, d)
            if len(assigned) != req:
                violations.append(f"[Coverage] Day {d}, shift {s}: assigned={len(assigned)}, required={req}")

    # 2) Forbidden shifts (-1)
    for (pname, d, s), v in solution.items():
        if v:
            p = name_to_idx[pname]
            for std_idx,std_name in enumerate(STANDARD_SHIFTS):
                if shift_requests[p][d][std_idx] == -1:
                    forbidden_intervals = shift_time_map[std_name]
                    if shift_intervals_overlap_any(shift_time_map[s], forbidden_intervals):
                        violations.append(f"[Forbidden] {pname} assigned to {s} on day {d} but marked -1 for {std_name}")

    # 3) Min/max per person
    for p, pname in enumerate(names):
        total = sum(v for (pp,_,_),v in solution.items() if v and pp==pname)
        if total < min_shifts[p]:
            violations.append(f"[Min shifts] {pname}, has {total}, min {min_shifts[p]}")
        if total > max_shifts[p]:
            violations.append(f"[Max shifts] {pname}, has {total}, max {max_shifts[p]}")

    # 4) Rest violations (with debug info)
    for p, pname in enumerate(names):
        assigned_shifts = [(d,s,shift_time_map[s]) for (pp,d,s),v in solution.items() if v and pp==pname]
        assigned_shifts.sort(key=lambda x:(x[0],x[2][0][0]))
        for i in range(len(assigned_shifts)):
            d1,s1,intervals1 = assigned_shifts[i]
            for j in range(i+1,len(assigned_shifts)):
                d2,s2,intervals2 = assigned_shifts[j]
                # check both directions (since intervals may cross midnight)
                for ia in intervals1:
                    for ib in intervals2:
                        diff = hours_between_intervals(d1, ia, d2, ib)
                        if diff < min_rest_hours:
                            violations.append(
                                f"[Rest] {pname} between {s1}(day{d1}, {ia}) "
                                f"and {s2}(day{d2}, {ib}), rest={diff:.1f}h < {min_rest_hours}h"
                            )
                '''for ia in intervals2:
                    for ib in intervals1:
                        diff = hours_between_intervals(d2, ia, d1, ib)
                        if diff < min_rest_hours:
                            violations.append(
                                f"[Rest] {pname} between {s2}(day{d2}, {ia}) "
                                f"and {s1}(day{d1}, {ib}), rest={diff:.1f}h < {min_rest_hours}h"
                            )'''

    return violations


def build_solution_dict(names: list,
                        days_shifts: list) -> dict:
    solution = {}
    num_days = len(days_shifts)

    for d in range(num_days):
        day = days_shifts[d]
        for shift_name, assigned_people in day.items():
            for person in assigned_people:
                if person not in names:
                    raise ValueError(f"Person {person} not in names list")
                solution[(person, d, shift_name)] = 1
    return solution


def save_solution_to_excel(solution, shift_requirements, num_days, filename="schedule.xlsx"):
    """
    Save the shift assignment solution to an Excel file.

    Each day is a separate sheet.
    Each row is a shift.
    Each assigned person appears in a separate column.
    """

    wb = Workbook()

    for d in range(num_days):
        # Create or select sheet for this day
        if d == 0:
            ws = wb.active
            ws.title = f"Day {d}"
        else:
            ws = wb.create_sheet(title=f"Day {d}")

        # Title
        ws["A1"] = f"Day {d}"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A1"].alignment = Alignment(horizontal="center")

        row = 3
        ws.column_dimensions['A'].width = 25
        for c in range(2, 10):
            ws.column_dimensions[chr(64 + c)].width = 20

        for shift_name, req_list in shift_requirements.items():
            # Only include shifts required for this day
            if d < len(req_list) and req_list[d] > 0:
                # Find assigned people
                assigned = [p for (p, dd, s), v in solution.items()
                            if v and dd == d and s == shift_name]

                if assigned:
                    ws.cell(row=row, column=1, value=shift_name).font = Font(bold=True)

                    for i, person in enumerate(assigned, start=2):
                        ws.cell(row=row, column=i, value=person)

                    row += 1

    wb.save(filename)
    print(f"✅ Schedule saved to '{filename}'")

def print_solution_by_day(solution, shift_requirements, num_days):
    """
    Pretty-print the solution using shift_requirements of form:
      {shift_name: [required_day0, required_day1, ...]}
    Only prints shifts with required > 0.
    """
    for d in range(num_days):
        print(f"\nDay {d}")
        for shift_name, req_list in shift_requirements.items():
            if d < len(req_list) and req_list[d] > 0:
                assigned = [p for (p, dd, s), v in solution.items()
                            if v and dd == d and s == shift_name]
                if assigned:  # print only if names assigned
                    print(f"  {shift_name}: {', '.join(assigned)}")


# --------------------------
# Example usage
# --------------------------
if __name__ == "__main__":
    names = ['אביב ברזל', 'אברהם דיאמנד', 'אהרון רוטנברג', 'אוהד אלקיים', 'אור חבזה', 'משה עוזיאל', 'אלעד מאיר',
             'אסף ברזיס', 'דביר רוזנברג', 'דין קרמזין', 'יאיר בן יוסף', 'יאיר מימון', 'יואל שפץ', 'יובל ברוכיאן',
             'יונתן פרידלנדר', 'יפתח בן זמרה', 'מאיר סמסון', 'משה וילנסקי', 'משה ליפן', 'עודד טובולסקי', 'עקיבא עמיאל',
             'רונן איזיק', 'רזיאל זקבך ']
    shift_requests = [
        [[-1, -1, -1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, -1, 0], [0, -1, -1, 0], [-1, -1, -1, -1]],  # אביב ברזל
        [[0, 0, -1, -1], [0, -1, -1, 0], [0, 0, 0, 0], [0, 0, -1, 0], [0, -1, 0, 0], [0, 0, 0, 0]],  # אברהם דיאמנד
        [[-1, 0, -1, -1], [-1, -1, -1, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # אהרון רוטנברג
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # אוהד אלקיים
        [[0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1]],  # אור חבזה
        [[0, 0, 0, 1], [0, 0, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1], [1, 0, 0, 0], [0, 0, 1, 0]],  # משה עוזיאל
        [[0, 0, 0, 0], [0, 0, 0, 0], [-1, -1, -1, -1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # אלעד מאיר
        [[1, 0, 0, 0], [-1, -1, -1, -1], [1, 0, 0, 0], [1, 0, 0, 0], [-1, -1, -1, -1], [1, 0, 0, 0]],  # אסף ברזיס
        [[-1, 0, 0, 0], [0, 0, 0, 0], [-1, -1, -1, -1], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # דביר רוזנברג
        [[-1, 0, 0, 0], [0, 0, 0, 0], [-1, -1, -1, -1], [1, 0, -1, 0], [0, 0, 0, 0], [1, 0, -1, 1]],  # דין קרמזין
        [[0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0], [0, 1, 0, 0], [-1, -1, -1, -1], [0, 0, 0, 1]],  # יאיר בן יוסף
        [[-1, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # יאיר מימון
        [[1, 0, -1, -1], [-1, -1, 1, 0], [0, 0, 1, 1], [1, 0, -1, -1], [0, -1, -1, -1], [0, -1, 0, 0]],  # יואל שפץ
        [[-1, 1, -1, -1], [-1, -1, -1, 0], [0, 0, 1, 0], [0, 1, -1, 0], [0, -1, 1, 0], [-1, -1, 1, 0]],  # יובל ברוכיאן
        [[0, 0, 0, 0], [0, 0, 1, 0], [-1, -1, -1, -1], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0]],  # יונתן פרידלנדר
        [[0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1], [0, 0, 0, 1]],  # יפתח בן זמרה
        [[0, 1, 0, -1], [0, 0, 0, 1], [0, -1, 1, 0], [0, 0, 0, 1], [0, 0, 0, 0], [0, 0, 0, 0]],  # מאיר סמסון
        [[0, 1, -1, -1], [-1, -1, -1, -1], [0, 0, 1, 0], [0, 0, -1, -1], [0, -1, 1, 0], [0, 1, 0, 0]],  # משה וילנסקי
        [[1, -1, -1, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0], [1, 0, 0, 0]],  # משה ליפן
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [1, 0, 0, 0], [0, 0, 0, 0]],  # עודד טובולסקי
        [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],  # עקיבא עמיאל
        [[-1, 0, 0, 0], [0, 0, 0, 0], [-1, -1, -1, -1], [0, 0, 0, 0], [0, -1, 0, 0], [0, -1, -1, -1]],  # רונן איזיק
        [[1, 0, 0, -1], [0, -1, 0, 0], [0, -1, -1, -1], [-1, 0, 0, -1], [0, 0, 0, 1], [0, 0, 0, 0]],  # רזיאל זקבך
    ]

    num_days = 6
    '''cols_to_keep = [0, 1]  # indices of columns you want to keep
    shift_requests = [[row[i] for i in cols_to_keep] for row in shift_requests]'''


    STANDARD_SHIFTS = ["03:00-09:00","09:00-15:00","15:00-21:00","21:00-03:00"]
    shift_time_map = {
        "03:00-09:00": [(3,9)],
        "09:00-15:00": [(9,15)],
        "15:00-21:00": [(15,21)],
        "21:00-03:00": [(21,27)],
        "יזומה 149 בוקר": [(6,9),(17,18.5)],
        "יזומה 149 בוקר ק": [(6,9)],
        "יזומה 149 ערב": [(18.5,23)],
        "דרום 18-24": [(18,24)],
        "הורדיון 09-13": [(9,13)],
        "הורדיון 13-17": [(13,17)],
    }


    shift_requirements = {
        "03:00-09:00":      [2, 4, 2, 2, 4, 2],  # Day0 → 2 persons, Day1 → 1 person, Day2 → 2 persons
        "09:00-15:00":      [2, 4, 2, 2, 4, 2],
        "15:00-21:00":      [4, 4, 2, 4, 4, 2],
        "21:00-03:00":      [4, 2, 2, 4, 2, 2],
        "יזומה 149 בוקר ק":  [3, 0, 0, 3, 0, 0],
        "יזומה 149 בוקר":    [0, 0, 3, 0, 0, 3],
        "יזומה 149 ערב":     [0, 0, 3, 0, 0, 3],
        "דרום 18-24":        [0, 0, 1, 0, 0, 1],
        "הורדיון 09-13":     [3, 0, 0, 0, 0, 0],
        "הורדיון 13-17":     [3, 0, 0, 0, 0, 0],
    }


    '''# Build nested dict per day
    days_shifts = [
        # Day 0
        {
            "03:00-09:00": ["אסף ברזיס", "דין קרמזין"],
            "יזומה 149 בוקר": ["אוהד אלקיים", "אברהם דיאמנד", "רזיאל זקבך"],
            "09:00-15:00": ["יואל שפץ", "עודד טובולסקי"],
            "15:00-21:00": ["יונתן פרידלנדר", "מאיר סמסון"],
            "יזומה 149 ערב": ["דביר רוזנברג", "אביב ברזל", "משה עוזיאל"],
            "דרום 18-24": ["אהרון רוטנברג"],
            "21:00-03:00": ["רונן איזיק", "יפתח בן זמרה"]
        },
        # Day 1
        {
            "03:00-09:00": ["משה וילנסקי", "דין קרמזין"],
            "09:00-15:00": ["יובל ברוכיאן", "אביב ברזל"],
            "15:00-21:00": ["יאיר מימון", "אסף ברזיס", "אור חבזה"],
            "דרום 18-24": ["אלעד מאיר"],
            "21:00-03:00": ["יואל שפץ", "עקיבא עמיאל"]
        }
    ]

    # Convert to solution dict
    solution = build_solution_dict(names, days_shifts)

    violations = check_solution(
        solution=solution,
        names=names,
        shift_requests=shift_requests,
        STANDARD_SHIFTS=STANDARD_SHIFTS,
        shift_time_map=shift_time_map,
        shift_requirements=shift_requirements,
        min_shifts_per_person=0,
        max_shifts_per_person=3,
        min_rest_hours=8
    )

    if violations:
        print("❌ Violations found:")
        for v in violations:
            print(" -", v)
    else:
        print("✅ Solution is valid")
    '''

    target_shifts = {
        "משה ליפן" : 5,
        "אהרון רוטנברג" : 3,
        "אוהד אלקיים" : 3,
        "דין קרמזין" : 3,
        "רזיאל זקבך" : 3,
        "משה עוזיאל" : 4,
    }

    out = plan_shifts(
        names=names,
        shift_requests=shift_requests,
        STANDARD_SHIFTS=STANDARD_SHIFTS,
        shift_time_map=shift_time_map,
        target_shifts=target_shifts,
        num_days=num_days,
        shift_requirements=shift_requirements,
        min_shifts_per_person=3,
        max_shifts_per_person=5,
        min_rest_hours=8,
        time_limit_seconds=100
    )

    if out:
        print("Status:", out["status"])
        print("Objective:", out["objective"])
        print("Shift counts:", out["shift_counts"])
        print("Assignments:")
        '''for (p,d,s),v in out["solution"].items():
            print(f" Day {d}, {s} -> {p}")'''
        print_solution_by_day(out["solution"], shift_requirements, num_days)
        save_solution_to_excel(out["solution"], shift_requirements, num_days, filename="schedule.xlsx")
    else:
        print("No feasible solution")
