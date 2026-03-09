from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import pandas as pd
from datetime import datetime

app = Flask(__name__)

DATABASE = "database.db"


# -------------------------
# DATABASE CONNECTION
# -------------------------
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


# -------------------------
# INITIALIZE DATABASE
# -------------------------
def init_db():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tasks(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        description TEXT,
        due_date TEXT,
        priority TEXT,
        status TEXT DEFAULT 'pending',
        created_at TEXT DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.commit()
    conn.close()


init_db()


# -------------------------
# HOME PAGE
# -------------------------
@app.route('/')
def index():

    conn = get_db_connection()

    tasks = conn.execute(
        "SELECT * FROM tasks ORDER BY created_at DESC"
    ).fetchall()

    # Dashboard stats
    total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
    completed = conn.execute("SELECT COUNT(*) FROM tasks WHERE status='completed'").fetchone()[0]
    pending = conn.execute("SELECT COUNT(*) FROM tasks WHERE status!='completed'").fetchone()[0]

    conn.close()

    today = datetime.today().date()

    return render_template(
        "index.html",
        tasks=tasks,
        total=total,
        completed=completed,
        pending=pending,
        today=today
    )


# -------------------------
# ADD TASK
# -------------------------
@app.route('/add', methods=('GET', 'POST'))
def add_task():

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        priority = request.form['priority']
        status = request.form['status']

        conn = get_db_connection()

        conn.execute(
            """INSERT INTO tasks
            (title, description, due_date, priority, status)
            VALUES (?, ?, ?, ?, ?)""",
            (title, description, due_date, priority, status)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    return render_template("add_task.html")


# -------------------------
# EDIT TASK
# -------------------------
@app.route('/edit/<int:id>', methods=('GET', 'POST'))
def edit_task(id):

    conn = get_db_connection()

    task = conn.execute(
        "SELECT * FROM tasks WHERE id=?",
        (id,)
    ).fetchone()

    if request.method == 'POST':

        title = request.form['title']
        description = request.form['description']
        due_date = request.form['due_date']
        priority = request.form['priority']
        status = request.form['status']

        conn.execute(
            """UPDATE tasks
            SET title=?, description=?, due_date=?, priority=?, status=?
            WHERE id=?""",
            (title, description, due_date, priority, status, id)
        )

        conn.commit()
        conn.close()

        return redirect(url_for('index'))

    conn.close()

    return render_template("edit_task.html", task=task)


# -------------------------
# DELETE TASK
# -------------------------
@app.route('/delete/<int:id>')
def delete_task(id):

    conn = get_db_connection()

    conn.execute(
        "DELETE FROM tasks WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


# -------------------------
# COMPLETE TASK
# -------------------------
@app.route('/complete/<int:id>')
def complete_task(id):

    conn = get_db_connection()

    conn.execute(
        "UPDATE tasks SET status='completed' WHERE id=?",
        (id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for('index'))


# -------------------------
# ANALYTICS PAGE
# -------------------------
@app.route('/analytics')
def analytics():

    conn = get_db_connection()

    df = pd.read_sql_query("SELECT * FROM tasks", conn)

    conn.close()

    if df.empty:
        status_counts = {}
        due_counts = {}

    else:

        status_counts = df['status'].value_counts().to_dict()

        df['due_date'] = pd.to_datetime(df['due_date'], errors='coerce')

        due_counts = df.groupby(df['due_date'].dt.date).size().to_dict()

        due_counts = {str(k): v for k, v in due_counts.items()}

    return render_template(
        "analytics.html",
        status_counts=status_counts,
        due_counts=due_counts
    )


# -------------------------
# SEARCH TASKS
# -------------------------
@app.route('/search')
def search():

    keyword = request.args.get("keyword")

    conn = get_db_connection()

    tasks = conn.execute(
        "SELECT * FROM tasks WHERE title LIKE ?",
        ('%' + keyword + '%',)
    ).fetchall()

    conn.close()

    return render_template("index.html", tasks=tasks)


# -------------------------
# RUN APP
# -------------------------
if __name__ == "__main__":
    app.run(debug=True)