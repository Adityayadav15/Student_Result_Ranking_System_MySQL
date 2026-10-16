import os
from pathlib import Path
from datetime import datetime

import mysql.connector
from mysql.connector import IntegrityError
from dotenv import load_dotenv
from flask import Flask, render_template, request, jsonify

from ranking import rank_students, validate_student

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

app = Flask(__name__)

DB_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "localhost"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "user": os.getenv("MYSQL_USER", "root"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
}
DB_NAME = os.getenv("MYSQL_DATABASE", "student_results")


def get_db():
    """Open a MySQL connection to the project's database."""
    return mysql.connector.connect(database=DB_NAME, **DB_CONFIG)


def init_db():
    # Create the database first, without selecting it.
    conn = mysql.connector.connect(**DB_CONFIG)
    try:
        cur = conn.cursor()
        cur.execute(
            f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
        )
        cur.close()
    finally:
        conn.close()

    with get_db() as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS students (
                id INT AUTO_INCREMENT PRIMARY KEY,
                roll_no VARCHAR(30) NOT NULL UNIQUE,
                name VARCHAR(100) NOT NULL,
                class_name VARCHAR(60) NOT NULL,
                department VARCHAR(60) NOT NULL DEFAULT 'CSE',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS results (
                id INT AUTO_INCREMENT PRIMARY KEY,
                student_id INT NOT NULL UNIQUE,
                subject1 DECIMAL(5,2) NOT NULL,
                subject2 DECIMAL(5,2) NOT NULL,
                subject3 DECIMAL(5,2) NOT NULL,
                subject4 DECIMAL(5,2) NOT NULL,
                subject5 DECIMAL(5,2) NOT NULL,
                total DECIMAL(6,2) NOT NULL,
                percentage DECIMAL(5,2) NOT NULL,
                grade VARCHAR(2) NOT NULL,
                status VARCHAR(10) NOT NULL,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                    ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT fk_results_student FOREIGN KEY (student_id)
                    REFERENCES students(id) ON DELETE CASCADE,
                CONSTRAINT chk_subject1 CHECK (subject1 BETWEEN 0 AND 100),
                CONSTRAINT chk_subject2 CHECK (subject2 BETWEEN 0 AND 100),
                CONSTRAINT chk_subject3 CHECK (subject3 BETWEEN 0 AND 100),
                CONSTRAINT chk_subject4 CHECK (subject4 BETWEEN 0 AND 100),
                CONSTRAINT chk_subject5 CHECK (subject5 BETWEEN 0 AND 100)
            ) ENGINE=InnoDB
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS ranking_runs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                algorithm VARCHAR(20) NOT NULL,
                student_count INT NOT NULL,
                elapsed_ms DECIMAL(10,3) NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            ) ENGINE=InnoDB
        """)
        conn.commit()
        cur.close()


def calculate_result(marks):
    total = sum(marks)
    percentage = total / 5
    passed = all(mark >= 35 for mark in marks)
    if not passed:
        return total, percentage, "F", "Fail"
    if percentage >= 90:
        grade = "A+"
    elif percentage >= 80:
        grade = "A"
    elif percentage >= 70:
        grade = "B"
    elif percentage >= 60:
        grade = "C"
    elif percentage >= 50:
        grade = "D"
    else:
        grade = "E"
    return total, percentage, grade, "Pass"


def student_payload(row):
    return {
        "id": row["id"],
        "roll_no": row["roll_no"],
        "name": row["name"],
        "class_name": row["class_name"],
        "department": row["department"],
        "marks": [float(row[f"subject{i}"]) for i in range(1, 6)],
        "total": float(row["total"]),
        "percentage": float(row["percentage"]),
        "grade": row["grade"],
        "status": row["status"],
        "updated_at": str(row["updated_at"])
    }


def fetch_students():
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT s.id, s.roll_no, s.name, s.class_name, s.department,
                   r.subject1, r.subject2, r.subject3, r.subject4, r.subject5,
                   r.total, r.percentage, r.grade, r.status, r.updated_at
            FROM students s JOIN results r ON r.student_id = s.id
        """)
        rows = cur.fetchall()
        cur.close()
        return [student_payload(row) for row in rows]
    finally:
        conn.close()


@app.route("/")
def index():
    return render_template("index.html")


@app.get("/api/students")
def api_students():
    return jsonify(rank_students(fetch_students(), "merge"))


@app.post("/api/students")
def api_add_student():
    data = request.get_json(silent=True) or {}
    error = validate_student(data)
    if error:
        return jsonify({"error": error}), 400

    marks = [float(data[f"subject{i}"]) for i in range(1, 6)]
    total, percentage, grade, status = calculate_result(marks)
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO students (roll_no, name, class_name, department)
            VALUES (%s, %s, %s, %s)
        """, (
            data["roll_no"].strip().upper(), data["name"].strip(),
            data["class_name"].strip(), data.get("department", "CSE").strip() or "CSE"
        ))
        student_id = cur.lastrowid
        cur.execute("""
            INSERT INTO results
            (student_id, subject1, subject2, subject3, subject4, subject5,
             total, percentage, grade, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (student_id, *marks, total, percentage, grade, status))
        conn.commit()
        cur.close()
    except IntegrityError as exc:
        conn.rollback()
        if getattr(exc, "errno", None) == 1062:
            return jsonify({"error": "That roll number already exists. Use a unique roll number."}), 409
        return jsonify({"error": "Could not save student. Check the entered details."}), 400
    finally:
        conn.close()
    return jsonify({"ok": True, "message": "Student result saved successfully."}), 201


@app.put("/api/students/<int:student_id>")
def api_update_student(student_id):
    data = request.get_json(silent=True) or {}
    error = validate_student(data)
    if error:
        return jsonify({"error": error}), 400
    marks = [float(data[f"subject{i}"]) for i in range(1, 6)]
    total, percentage, grade, status = calculate_result(marks)
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM students WHERE id=%s", (student_id,))
        if cur.fetchone() is None:
            cur.close()
            return jsonify({"error": "Student not found."}), 404
        cur.execute("""
            UPDATE students SET roll_no=%s, name=%s, class_name=%s, department=%s
            WHERE id=%s
        """, (data["roll_no"].strip().upper(), data["name"].strip(),
              data["class_name"].strip(), data.get("department", "CSE").strip() or "CSE",
              student_id))
        cur.execute("""
            UPDATE results SET subject1=%s, subject2=%s, subject3=%s, subject4=%s,
                subject5=%s, total=%s, percentage=%s, grade=%s, status=%s
            WHERE student_id=%s
        """, (*marks, total, percentage, grade, status, student_id))
        conn.commit()
        cur.close()
    except IntegrityError as exc:
        conn.rollback()
        if getattr(exc, "errno", None) == 1062:
            return jsonify({"error": "That roll number is already used by another student."}), 409
        return jsonify({"error": "Could not update student."}), 400
    finally:
        conn.close()
    return jsonify({"ok": True, "message": "Student result updated successfully."})


@app.delete("/api/students/<int:student_id>")
def api_delete_student(student_id):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM students WHERE id=%s", (student_id,))
        deleted = cur.rowcount
        conn.commit()
        cur.close()
    finally:
        conn.close()
    if not deleted:
        return jsonify({"error": "Student not found."}), 404
    return jsonify({"ok": True, "message": "Student deleted."})


@app.post("/api/rank")
def api_rank():
    data = request.get_json(silent=True) or {}
    algorithm = str(data.get("algorithm", "merge")).lower()
    if algorithm not in {"merge", "quick", "builtin"}:
        return jsonify({"error": "Choose merge, quick, or builtin."}), 400
    result = rank_students(fetch_students(), algorithm)
    elapsed_ms = result.pop("elapsed_ms")
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO ranking_runs (algorithm, student_count, elapsed_ms)
            VALUES (%s, %s, %s)
        """, (algorithm.upper(), len(result["students"]), elapsed_ms))
        conn.commit()
        cur.close()
    finally:
        conn.close()
    return jsonify({
        "students": result["students"],
        "algorithm": algorithm.upper(),
        "student_count": len(result["students"]),
        "elapsed_ms": elapsed_ms,
        "message": f"Ranked {len(result['students'])} students using {algorithm.upper()} sort."
    })


@app.get("/api/stats")
def api_stats():
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT COUNT(*) AS n FROM students")
        student_count = cur.fetchone()["n"]
        cur.execute("SELECT COUNT(*) AS n FROM results WHERE status='Pass'")
        pass_count = cur.fetchone()["n"]
        cur.execute("SELECT AVG(percentage) AS n FROM results")
        avg = cur.fetchone()["n"] or 0
        cur.execute("""
            SELECT s.name, s.roll_no, r.percentage, r.grade
            FROM students s JOIN results r ON s.id=r.student_id
            ORDER BY r.percentage DESC, r.total DESC, s.roll_no ASC LIMIT 1
        """)
        top = cur.fetchone()
        cur.execute("SELECT COUNT(*) AS n FROM ranking_runs")
        ranking_count = cur.fetchone()["n"]
        cur.close()
    finally:
        conn.close()
    if top:
        top["percentage"] = float(top["percentage"])
    return jsonify({
        "student_count": student_count,
        "pass_count": pass_count,
        "pass_rate": round(pass_count / student_count * 100, 1) if student_count else 0,
        "average_percentage": round(float(avg), 2),
        "ranking_runs": ranking_count,
        "top_student": top
    })


@app.get("/api/ranking-history")
def api_ranking_history():
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT id, algorithm, student_count, elapsed_ms, created_at
            FROM ranking_runs ORDER BY id DESC LIMIT 10
        """)
        rows = cur.fetchall()
        cur.close()
        for row in rows:
            row["elapsed_ms"] = float(row["elapsed_ms"])
            row["created_at"] = str(row["created_at"])
        return jsonify(rows)
    finally:
        conn.close()


@app.get("/api/export")
def api_export():
    students = rank_students(fetch_students(), "merge")
    return jsonify({
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "students": students["students"]
    })


@app.get("/api/health")
def api_health():
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        cur.close()
        return jsonify({"ok": True, "database": DB_NAME, "engine": "MySQL"})
    finally:
        conn.close()


# Creates the database and tables when the application starts.
try:
    init_db()
except mysql.connector.Error as exc:
    raise RuntimeError(
        "Could not connect to MySQL. Check that MySQL Server is running and "
        "MYSQL_HOST, MYSQL_PORT, MYSQL_USER, and MYSQL_PASSWORD in .env are correct."
    ) from exc


if __name__ == "__main__":
    app.run(debug=True, port=int(os.getenv("APP_PORT", "5001")))
