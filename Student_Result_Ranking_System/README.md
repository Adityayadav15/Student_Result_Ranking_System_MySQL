# MeritBoard — Student Result Ranking System (MySQL edition)

Full-stack DAA project with HTML/CSS/JavaScript frontend, Flask backend, MySQL database, and Merge Sort / Quick Sort / Python built-in ranking.

## Requirements
- Python 3.10+
- MySQL Server running locally (MySQL Workbench is useful for viewing tables, but Workbench alone is not the database server)

## Setup on Windows / VS Code
1. Extract the ZIP and open the inner `Student_Result_Ranking_System` folder in VS Code.
2. In the project root, copy `.env.example` and rename the copy to `.env`.
3. Open `.env` and replace `YOUR_MYSQL_ROOT_PASSWORD` with your MySQL Server password. Keep the other settings unless you changed the MySQL port/user.
4. Make sure the MySQL Server service is running. In MySQL Workbench, connect to your local MySQL Server.
5. Open VS Code Terminal in the same folder and run:
   ```powershell
   py -m pip install -r requirements.txt
   py app.py
   ```
6. Open `http://127.0.0.1:5001`.
7. In MySQL Workbench refresh Schemas. The app automatically creates database `student_results` and tables `students`, `results`, and `ranking_runs`.

If you already run Maze Runner on port 5000, this app uses port 5001 by default.

## Check the database in MySQL Workbench
After starting `py app.py`, refresh the SCHEMAS panel. Open `student_results` > Tables. To inspect data, right-click a table and choose **Select Rows - Limit 1000**, or run:
```sql
USE student_results;
SELECT * FROM students;
SELECT * FROM results;
SELECT * FROM ranking_runs;
```

## Important about old SQLite data
This version connects to MySQL and will not automatically copy records from an old `student_results.db` SQLite file. If you already entered student records in the SQLite version and want to keep them, ask to migrate those records before deleting or moving the old file. Do not delete the old SQLite database until you have confirmed the MySQL records.

## Features
- Add, edit, search, and delete students.
- Five subject marks out of 100, automatic total, percentage, grade, and pass/fail.
- Rank by Merge Sort, Quick Sort, or Python built-in sort.
- Dashboard metrics, topper, ranking run history, and JSON export.
- Input validation and duplicate roll-number protection.
- Database tables are created automatically on startup.

## Grade policy
A student passes only if every subject has at least 35. Grade policy: A+ >= 90%, A >= 80%, B >= 70%, C >= 60%, D >= 50%, E below 50% if all subjects passed, otherwise F. This is a configurable demo policy, not an official institutional grading rule.

## API
- `GET /` — UI
- `GET /api/students`
- `POST /api/students`
- `PUT /api/students/<id>`
- `DELETE /api/students/<id>`
- `POST /api/rank`
- `GET /api/stats`
- `GET /api/ranking-history`
- `GET /api/export`
- `GET /api/health`

## DAA complexity
- Merge Sort: O(n log n) time, O(n) auxiliary space.
- Quick Sort: average O(n log n), worst O(n²); this educational version uses additional lists.
- Python built-in sort: CPython Timsort.

This is a local academic project and uses Flask's development server. It does not implement user authentication or production security.
