import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config["SECRET_KEY"] = "any-secret-key-here"
# تحديد المسار بشكل يوافق سيرفر ريندر
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
app.config["UPLOAD_FOLDER"] = os.path.join(BASE_DIR, "uploads")
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

# التأكد من وجود مجلد الصور وقاعدة البيانات
if not os.path.exists(app.config["UPLOAD_FOLDER"]):
    os.makedirs(app.config["UPLOAD_FOLDER"])

DB_PATH = os.path.join(BASE_DIR, "citizen_eye.db")

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS complaints (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            phone TEXT,
            location TEXT NOT NULL,
            category TEXT NOT NULL,
            description TEXT NOT NULL,
            image_path TEXT,
            status TEXT NOT NULL DEFAULT 'جديدة',
            created_at TEXT NOT NULL
        )
        """)

# تشغيل قاعدة البيانات فوراً عند بدء التطبيق
init_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    try:
        name = request.form.get("name")
        location = request.form.get("location")
        category = request.form.get("category")
        description = request.form.get("description")
        file = request.files.get("image")
        
        image_path = None
        if file and file.filename != '':
            filename = datetime.now().strftime("%Y%m%d%H%M%S") + "_" + secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = "/uploads/" + filename

        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO complaints (name, location, category, description, image_path, created_at) VALUES (?, ?, ?, ?, ?, ?)",
                (name, location, category, description, image_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
        flash("تم الإرسال بنجاح", "success")
    except Exception as e:
        flash(f"خطأ: {str(e)}", "error")
    return redirect(url_for("index"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/admin")
def admin():
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
    return render_template("admin.html", complaints=rows)

@app.route("/api/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()
    return jsonify({"reply": "أهلاً بك، يمكنك تعبئة النموذج وسنتابع شكواك فوراً."})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
