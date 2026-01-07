import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
from functools import wraps

# إعداد المسارات الأساسية لضمان عملها على السيرفر
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
STATIC_DIR = os.path.join(BASE_DIR, 'static')
UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static/uploads')
DB_PATH = os.path.join(BASE_DIR, "citizen_eye.db")

app = Flask(__name__, 
            template_folder=TEMPLATE_DIR,
            static_folder=STATIC_DIR)

app.config["SECRET_KEY"] = "citizen_eye_secret_2026"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5 ميجابايت

# كلمة مرور لوحة الإدارة (يمكنك تغييرها)
ADMIN_PASSWORD = "admin123"

# التأكد من وجود مجلد الرفع
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

# وظيفة حماية المسارات
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

    try:
        conn = get_db()
        conn.execute(
            "INSERT INTO complaints (name, phone, location, category, description, image_path, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (name, phone, location, category, description, image_path, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()
        flash("تم استلام الشكوى بنجاح. شكرًا لمساهمتك!", "success")
    except Exception as e:
        flash(f"حدث خطأ: {e}", "error")

    return redirect(url_for("index"))

@app.route("/api/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()
    response = "شكرًا لتواصلك. يمكنك تعبئة النموذج وسنقوم بمتابعة شكواك."
    
    rules = [
        (["مرحبا", "أهلا"], "أهلاً بك في عين المواطن، كيف يمكنني مساعدتك؟"),
        (["صورة", "صور"], "يمكنك إرفاق صورة واحدة واضحة للمشكلة."),
        (["مكان", "موقع"], "يرجى كتابة العنوان بدقة لسهولة الوصول."),
    ]

    for keys, msg in rules:
        if any(k in user_msg for k in keys):
            response = msg
            break
    return jsonify({"reply": response})

# --- صفحات الإدارة ---

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("admin"))
        else:
            flash("كلمة المرور خاطئة!", "error")
    return '''
        <div style="text-align:center; margin-top:100px; font-family:sans-serif;" dir="rtl">
            <h2>دخول الإدارة</h2>
            <form method="post">
                <input type="password" name="password" placeholder="أدخل كلمة المرور" required style="padding:10px;">
                <button type="submit" style="padding:10px; cursor:pointer;">دخول</button>
            </form>
            <p><a href="/">العودة للرئيسية</a></p>
        </div>
    '''

@app.route("/admin")
@login_required
def admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin.html", complaints=rows)

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

# تشغيل قاعدة البيانات تلقائياً
init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
