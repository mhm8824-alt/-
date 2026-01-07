import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory

app = Flask(__name__)
app.config["SECRET_KEY"] = "dev_key_123"

# إعداد المسارات لتناسب سيرفر ريندر
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
DB_PATH = os.path.join(BASE_DIR, "citizen_eye.db")

# إنشاء المجلدات إذا لم تكن موجودة لمنع الخطأ
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def init_db():
    try:
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
    except Exception as e:
        print(f"Database error: {e}")

# التأكد من عمل قاعدة البيانات عند التشغيل
with app.app_context():
    init_db()

@app.route("/")
def index():
    # هذا السطر للتأكد من وجود ملف index.html ومنع الـ Error 500
    try:
        return render_template("index.html")
    except Exception as e:
        return f"خطأ: ملف index.html غير موجود في مجلد templates. التفاصيل: {str(e)}"

@app.route("/submit", methods=["POST"])
def submit():
    try:
        name = request.form.get("name")
        location = request.form.get("location")
        category = request.form.get("category")
        description = request.form.get("description")
        
        with sqlite3.connect(DB_PATH) as conn:
            conn.execute(
                "INSERT INTO complaints (name, location, category, description, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, location, category, description, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
        flash("تم الإرسال بنجاح!", "success")
    except Exception as e:
        flash(f"حدث خطأ: {str(e)}", "error")
    return redirect(url_for("index"))

@app.route("/admin")
def admin():
    try:
        with sqlite3.connect(DB_PATH) as conn:
            conn.row_factory = sqlite3.Row
            rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
        return render_template("admin.html", complaints=rows)
    except Exception as e:
        return f"خطأ في لوحة الإدارة: {str(e)}"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
