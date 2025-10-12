# 🧠 Smart Shift Scheduler  
### Automated Staff Scheduling with Google OR-Tools

**Smart Shift Scheduler** is a Python-based tool for optimizing team shift assignments using **Google OR-Tools (CP-SAT solver)**.  
It automatically builds fair, compliant, and preference-based schedules — perfect for healthcare teams, operations centers, or any multi-shift environment.

---

## 🚀 Features

- 🧩 **Constraint Optimization** – Uses OR-Tools to solve the Nurse Scheduling Problem efficiently.  
- 🙋 **Employee Preferences** – Supports “yes / no / neutral” availability for each shift.  
- ⏰ **Rest-Time Rules** – Enforces minimum rest hours between consecutive shifts.  
- ⚖️ **Fairness Control** – Balances workloads using min/max shift limits per person.  
- 📊 **Excel Integration** – Reads preferences and outputs final schedules directly to Excel.  
- ✅ **Validation Tools** – Checks generated schedules for violations or inconsistencies.

---

## 🧱 Repository Structure

| File | Description |
|------|--------------|
| **`V2_CreateTable.py`** | Reads the Excel file of staff preferences (`העדפות שמירה.xlsx`) and converts it into Python structures (`names`, `shift_requests`). |
| **`V2_NurseProblem.py`** | Core solver – defines and solves the scheduling optimization problem using OR-Tools. Produces a valid shift schedule and exports to Excel. |
| **`V2_checkResultsNew.py`** | Validates the generated schedule (`plan.xlsx` or `schedule.xlsx`) by checking for rule violations (e.g. rest < 8h, overlapping shifts, or forbidden assignments). |

---

## ⚙️ Requirements

Make sure you have Python 3.9+ installed.

Install dependencies:
```bash
pip install ortools openpyxl


