import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session

# --- إعدادات المسارات الصارمة لبيئة Render ---
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
# التأكد من أن Flask يرى مجلدات الـ templates والـ static
app = Flask(__name__, 
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))

app.config["SECRET_KEY"] = "citizen_eye_9988"
DB_PATH = os.path.join(BASE_DIR, "citizen_eye.db")

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
        print(f"DATABASE ERROR: {e}")

# تشغيل القاعدة فوراً
init_db()

@app.route("/")
def index():
    # كود فحص ذكي: لو الملف ناقص هيقلك مكانه فين بدل ما يعلق السيرفر
    t_path = os.path.join(app.template_folder, 'index.html')
    if not os.path.exists(t_path):
        return f"خطأ تقني: السيرفر يبحث عن index.html في المسار التالي ولا يجده: {t_path}. تأكد من وجود مجلد templates وداخله الملف."
    
    return render_template("index.html")

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
        flash("تم استلام شكواك بنجاح!", "success")
    except Exception as e:
        flash(f"فشل الإرسال: {str(e)}", "error")
    return redirect(url_for("index"))

@app.route("/admin")
def admin():
    if not os.path.exists(os.path.join(app.template_folder, 'admin.html')):
        return "خطأ: ملف admin.html مفقود في مجلد templates."
    
    with sqlite3.connect(DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
    return render_template("admin.html", complaints=rows)

if __name__ == "__main__":
    # ريندر يستخدم بورت 10000 غالباً، لكن Gunicorn سيتولى الأمر
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
