import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
from functools import wraps

# إعداد المسارات بشكل صارم لـ Render
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
# ملاحظة: سنخزن الصور داخل static لضمان ظهورها
UPLOAD_FOLDER = os.path.join(STATIC_DIR, 'uploads')
DB_PATH = os.path.join(BASE_DIR, "citizen_eye.db")

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)

app.config["SECRET_KEY"] = "super-secret-key-2026"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# التأكد من وجود مجلد الصور
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with app.app_context():
        conn = get_db()
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
        conn.commit()
        conn.close()

# حماية صفحة الإدارة
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/submit", methods=["POST"])
def submit():
    try:
        name = request.form.get("name")
        phone = request.form.get("phone")
        location = request.form.get("location")
        category = request.form.get("category")
        description = request.form.get("description")
        file = request.files.get("image")

        image_path = None
        if file and file.filename != '':
            filename = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
            image_path = "uploads/" + filename

        conn = get_db()
        conn.execute(
            "INSERT INTO complaints (name, phone, location, category, description, image_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, location, category, description, image_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        flash("تم الإرسال بنجاح!", "success")
    except Exception as e:
        flash(f"خطأ: {str(e)}", "error")
    return redirect(url_for("index"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == "admin123":
            session["logged_in"] = True
            return redirect(url_for("admin"))
    return '<h2>دخول الإدارة</h2><form method="post"><input type="password" name="password"><button type="submit">دخول</button></form>'

@app.route("/admin")
@login_required
def admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin.html", complaints=rows)

@app.route("/api/chat", methods=["POST"])
def chat():
    return jsonify({"reply": "أهلاً بك، سأقوم بمساعدتك فوراً!"})

# تشغيل القاعدة تلقائياً
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
