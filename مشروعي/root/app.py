import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory, session
from werkzeug.utils import secure_filename
from functools import wraps

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "citizen_eye.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
# تغيير المفتاح السري ضروري للأمان
app.config["SECRET_KEY"] = "citizen_eye_secure_key_2024"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

# إعداد كلمة مرور بسيطة للوحة الإدارة
ADMIN_PASSWORD = "admin123"  # يمكنك تغييرها لما تريد

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
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

# وظيفة لحماية مسارات الإدارة
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated_function

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

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
    if file and allowed_file(file.filename):
        filename = datetime.now().strftime("%Y%m%d%H%M%S_") + secure_filename(file.filename)
        file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        image_path = "/uploads/" + filename

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
        flash(f"حدث خطأ أثناء الإرسال: {e}", "error")

    return redirect(url_for("index"))

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

@app.route("/api/chat", methods=["POST"])
def chat():
    user_msg = request.json.get("message", "").lower()
    response = "شكرًا لتواصلك. يمكنك البدء بتعبئة النموذج أعلاه وسأقوم بمساعدتك إذا واجهت أي مشكلة."
    
    rules = [
        (["مرحبا", "أهلا", "سلام"], "أهلاً بك في نظام عين المواطن. كيف يمكنني مساعدتك اليوم؟"),
        (["صورة", "صور", "أرفق"], "يمكنك إرفاق صورة واحدة توضح المشكلة بصيغة JPG أو PNG وحجم أقل من 5 ميجابايت."),
        (["مكان", "موقع", "عنوان"], "يرجى تحديد موقع المشكلة بدقة (الحي، الشارع) ليسهل علينا الوصول إليها."),
        (["نوع", "فئة"], "نوفر تصنيفات مثل: مياه، كهرباء، طرق، ونظافة. اختر الأنسب لمشكلتك."),
    ]

    for keys, msg in rules:
        if any(k in user_msg for k in keys):
            response = msg
            break
    return jsonify({"reply": response})

# --- صفحات الإدارة مع الحماية ---

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
                <input type="password" name="password" placeholder="أدخل كلمة المرور" required>
                <button type="submit">دخول</button>
            </form>
        </div>
    '''

@app.route("/logout")
def logout():
    session.pop("logged_in", None)
    return redirect(url_for("index"))

@app.route("/admin")
@login_required
def admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin.html", complaints=rows)

@app.route("/admin/update_status", methods=["POST"])
@login_required
def update_status():
    cid = request.form.get("id")
    status = request.form.get("status")
    if cid and status in {"جديدة", "قيد المعالجة", "منتهية"}:
        conn = get_db()
        conn.execute("UPDATE complaints SET status = ? WHERE id = ?", (status, cid))
        conn.commit()
        conn.close()
        flash("تم تحديث الحالة بنجاح", "success")
    return redirect(url_for("admin"))

# ضمان تشغيل قاعدة البيانات على Render
with app.app_context():
    init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
