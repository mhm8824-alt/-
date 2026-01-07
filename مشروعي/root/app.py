import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, send_from_directory
from werkzeug.utils import secure_filename

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "citizen_eye.db")
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif"}

app = Flask(__name__)
app.config["SECRET_KEY"] = "change-me-in-production"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024  # 5MB

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

def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route("/")
def index():
    return render_template("index")

@app.route("/submit", methods=["POST"])
def submit():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    location = request.form.get("location", "").strip()
    category = request.form.get("category", "").strip()
    description = request.form.get("description", "").strip()

    if not name or not location or not category or not description:
        flash("يرجى ملء الحقول المطلوبة.", "error")
        return redirect(url_for("index"))

    image_path = None
    file = request.files.get("image")
    if file and file.filename:
        if not allowed_file(file.filename):
            flash("صيغة الصورة غير مدعومة. الصيغ المسموح بها: png, jpg, jpeg, gif", "error")
            return redirect(url_for("index"))
        filename = secure_filename(f"{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{file.filename}")
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(save_path)
        image_path = f"/uploads/{filename}"

    conn = get_db()
    conn.execute("""
        INSERT INTO complaints (name, phone, location, category, description, image_path, status, created_at)
        VALUES (?, ?, ?, ?, ?, ?, 'جديدة', ?)
    """, (name, phone, location, category, description, image_path, datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()

    flash("تم استلام الشكوى بنجاح. شكرًا لمساهمتك.", "success")
    return redirect(url_for("index"))

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# دردشة إرشادية بدون نموذج خارجي (منطق قواعد بسيط)
@app.route("/api/chat", methods=["POST"])
def chat():
    user_msg = (request.json.get("message") or "").strip().lower()

    response = "مرحبًا! اكتب: موقع المشكلة، نوعها، وصفًا مختصرًا، وإذا عندك صورة إرفقها قبل الإرسال."
    rules = [
        (["مرحبا", "السلام", "اهلا"], "أهلًا في منصة عين المواطن. لرفع شكوى: اكتب الموقع، النوع (مياه/كهرباء/طرق/نظافة)، وصف مختصر، ثم أرفق صورة إن وُجدت."),
        (["كيف", "طريقة", "أقدم", "تقديم"], "الطريقة: أدخل الموقع، اختر الفئة، اكتب وصف دقيق (مثال: حفرة كبيرة أمام مدرسة كذا)، وأرفق صورة، ثم اضغط إرسال."),
        (["صورة", "ارفاق", "رفع", "upload"], "للصورة: اضغط زر اختيار ملف، الصيغ المسموحة PNG/JPG/JPEG/GIF، حجم حتى 5MB."),
        (["مكان", "موقع", "عنوان"], "رجاءً حدد العنوان بدقة: الحي، الشارع، أقرب معلم (مثال: قرب جامع...)."),
        (["نوع", "فئة", "تصنيف"], "الأنواع: مياه، كهرباء، طرق، نظافة، أخرى. اختر الأقرب لحالتك."),
        (["وصف", "أصف", "تفاصيل"], "اكتب وصفًا واضحًا: ما المشكلة، تأثيرها، منذ متى؟ مثال: انقطاع مياه منذ يومين في حي..."),
        (["تأكيد", "تم", "استلام"], "بعد الإرسال يظهر تنبيه 'تم استلام الشكوى بنجاح'. ستُسجل في النظام مع الوقت والتفاصيل."),
    ]

    for keys, msg in rules:
        if any(k in user_msg for k in keys):
            response = msg
            break

    return jsonify({"reply": response})

# لوحة إدارة
@app.route("/admin")
def admin():
    conn = get_db()
    rows = conn.execute("SELECT * FROM complaints ORDER BY created_at DESC").fetchall()
    conn.close()
    return render_template("admin.html", complaints=rows)

@app.route("/admin/update_status", methods=["POST"])
def update_status():
    cid = request.form.get("id")
    status = request.form.get("status")
    if cid and status in {"جديدة", "قيد المعالجة", "منتهية"}:
        conn = get_db()
        conn.execute("UPDATE complaints SET status=? WHERE id=?", (status, cid))
        conn.commit()
        conn.close()
        flash("تم تحديث الحالة.", "success")
    else:
        flash("طلب غير صالح.", "error")
    return redirect(url_for("admin"))

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)

