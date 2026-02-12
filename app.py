from flask import Flask, render_template, request, redirect, url_for
import sqlite3
from datetime import datetime, date

app = Flask(__name__)

DB_NAME = "regulatory.db"


# ---------------------------
# Database Initialization
# ---------------------------
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_name TEXT NOT NULL,
            country TEXT NOT NULL,
            submission_type TEXT NOT NULL,
            deadline_date TEXT NOT NULL
        )
    """)

    conn.commit()
    conn.close()


# ---------------------------
# Status Logic (Enterprise Countdown)
# ---------------------------
def calculate_status(deadline_str):
    deadline = datetime.strptime(deadline_str, "%Y-%m-%d").date()
    today = date.today()
    diff = (deadline - today).days

    if diff < 0:
        countdown = f"Overdue by {abs(diff)} day{'s' if abs(diff) != 1 else ''}"
        return countdown, "Overdue", "danger"

    elif diff == 0:
        return "Due Today", "Due Soon", "warning"

    elif diff == 1:
        return "Due Tomorrow", "Due Soon", "warning"

    elif diff <= 14:
        return f"Due in {diff} days", "Due Soon", "warning"

    else:
        return f"Due in {diff} days", "Upcoming", "success"


# ---------------------------
# Dashboard
# ---------------------------
@app.route("/")
def dashboard():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM submissions ORDER BY deadline_date")
    rows = cursor.fetchall()
    conn.close()

    submissions = []

    # Analytics counters
    total = len(rows)
    upcoming = 0
    due_soon = 0
    overdue = 0

    for row in rows:
        countdown, status, badge = calculate_status(row[4])

        if status == "Upcoming":
            upcoming += 1
        elif status == "Due Soon":
            due_soon += 1
        elif status == "Overdue":
            overdue += 1

        submissions.append({
            "id": row[0],
            "product_name": row[1],
            "country": row[2],
            "submission_type": row[3],
            "deadline_date": row[4],
            "countdown": countdown,
            "status": status,
            "badge": badge
        })

    return render_template(
        "dashboard.html",
        submissions=submissions,
        total=total,
        upcoming=upcoming,
        due_soon=due_soon,
        overdue=overdue
    )


# ---------------------------
# Add Submission
# ---------------------------
@app.route("/add", methods=["GET", "POST"])
def add_submission():
    if request.method == "POST":
        product_name = request.form["product_name"]
        country = request.form["country"]
        submission_type = request.form["submission_type"]
        deadline_date = request.form["deadline_date"]

        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO submissions 
            (product_name, country, submission_type, deadline_date)
            VALUES (?, ?, ?, ?)
        """, (product_name, country, submission_type, deadline_date))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    return render_template("add.html", submission=None)


# ---------------------------
# Edit Submission
# ---------------------------
@app.route("/edit/<int:id>", methods=["GET", "POST"])
def edit_submission(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    if request.method == "POST":
        product_name = request.form["product_name"]
        country = request.form["country"]
        submission_type = request.form["submission_type"]
        deadline_date = request.form["deadline_date"]

        cursor.execute("""
            UPDATE submissions
            SET product_name=?, country=?, submission_type=?, deadline_date=?
            WHERE id=?
        """, (product_name, country, submission_type, deadline_date, id))

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    cursor.execute("SELECT * FROM submissions WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()

    submission = {
        "id": row[0],
        "product_name": row[1],
        "country": row[2],
        "submission_type": row[3],
        "deadline_date": row[4]
    }

    return render_template("add.html", submission=submission)


# ---------------------------
# Delete Submission
# ---------------------------
@app.route("/delete/<int:id>")
def delete_submission(id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM submissions WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


# ---------------------------
# Run App
# ---------------------------
if __name__ == "__main__":
    init_db()
    app.run(debug=True)
