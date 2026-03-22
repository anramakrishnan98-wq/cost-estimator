import os
from flask import Flask, render_template, request, send_file
import sqlite3
from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

app = Flask(__name__)

rates = {
    "chennai": {"material": 1200, "labor": 400},
    "bangalore": {"material": 1400, "labor": 500},
    "hyderabad": {"material": 1300, "labor": 450}
}

# ✅ Correct DB setup
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(BASE_DIR, "database.db")

def init_db():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS projects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        area REAL,
        floors INTEGER,
        location TEXT,
        total REAL
    )
    """)

    conn.commit()
    conn.close()

init_db()


@app.route("/", methods=["GET", "POST"])
def index():
    result = None

    if request.method == "POST":
        try:
            area = float(request.form.get("area", 0))
            floors = int(request.form.get("floors", 1))
            location = request.form.get("location", "chennai")
        except:
            return "Invalid input"

        base = rates.get(location, rates["chennai"])

        material_cost = area * base["material"] * floors
        labor_cost = area * base["labor"] * floors

        subtotal = material_cost + labor_cost
        gst = subtotal * 0.18
        total_cost = subtotal + gst

        result = {
            "material_cost": material_cost,
            "labor_cost": labor_cost,
            "gst": gst,
            "total_cost": total_cost
        }

        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        c.execute(
            "INSERT INTO projects (area, floors, location, total) VALUES (?, ?, ?, ?)",
            (area, floors, location, total_cost)
        )
        conn.commit()
        conn.close()

    return render_template("index.html", result=result)


@app.route("/admin")
def admin():
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM projects")
    data = c.fetchall()
    conn.close()

    return render_template("admin.html", data=data)


@app.route("/download/<int:id>")
def download(id):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT * FROM projects WHERE id=?", (id,))
    row = c.fetchone()
    conn.close()

    if not row:
        return "No data found"

    file_path = f"project_{id}.pdf"

    doc = SimpleDocTemplate(file_path)
    styles = getSampleStyleSheet()

    content = [
        Paragraph(f"Area: {row[1]}", styles["Normal"]),
        Paragraph(f"Floors: {row[2]}", styles["Normal"]),
        Paragraph(f"Location: {row[3]}", styles["Normal"]),
        Paragraph(f"Total Cost: ₹ {row[4]}", styles["Normal"])
    ]

    doc.build(content)

    return send_file(file_path, as_attachment=True)


if __name__ == "__main__":
    app.run(debug=True, port=5001)