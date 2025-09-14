import os
import tempfile
from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, send_from_directory
import mysql.connector
from config import MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB, FLASK_SECRET_KEY
from utils.auth import hash_password, verify_password, login_required, admin_required
from utils.azure_face import register_face, verify_face
from utils.plagiarism import compute_similarity, check_against_batch, grade_plagiarism

UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

app = Flask(__name__, static_folder='static', template_folder='templates')
app.secret_key = FLASK_SECRET_KEY
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def get_db_connection():
    conn = mysql.connector.connect(
        host=MYSQL_HOST,
        user=MYSQL_USER,
        password=MYSQL_PASSWORD,
        database=MYSQL_DB
    )
    return conn

@app.route('/')
def index():
    return render_template('index.html')

# Register page
@app.route('/register', methods=['GET','POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    # POST: create user
    name = request.form.get('name')
    email = request.form.get('email')
    password = request.form.get('password')
    if not all([name, email, password]):
        return jsonify({'success': False, 'message': 'Missing fields'}), 400
    pw_hash = hash_password(password)
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (name, email, password_hash) VALUES (%s,%s,%s)", (name, email, pw_hash))
        conn.commit()
        user_id = cur.lastrowid
    except mysql.connector.IntegrityError:
        conn.close()
        return jsonify({'success': False, 'message': 'Email already exists'}), 400
    conn.close()
    return jsonify({'success': True, 'user_id': user_id})

# register face
@app.route('/register/face', methods=['POST'])
def register_face_route():
    user_id = request.form.get('user_id')
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image provided'}), 400
    img = request.files['image'].read()
    try:
        person_id = register_face(user_id, img)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    # store person_id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET face_person_id=%s WHERE id=%s", (person_id, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'person_id': person_id})

# register voice sample (save file)
@app.route('/register/voice', methods=['POST'])
def register_voice_route():
    user_id = request.form.get('user_id')
    if 'audio' not in request.files:
        return jsonify({'success': False, 'message': 'No audio provided'}), 400
    f = request.files['audio']
    filename = f"user_{user_id}_voice.wav"
    path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    f.save(path)
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE users SET voice_file_path=%s WHERE id=%s", (path, user_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'path': path})

# login
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    email = request.form.get('email')
    password = request.form.get('password')
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    conn.close()
    if not user or not verify_password(user['password_hash'], password):
        return jsonify({'success': False, 'message': 'Invalid credentials'}), 401
    # Password ok -> set session and require biometrics verification
    session['temp_user_id'] = user['id']
    session['temp_role'] = user['role']
    return jsonify({'success': True, 'next': 'verify-biometrics'})

# face verify endpoint
@app.route('/verify/face', methods=['POST'])
def verify_face_route():
    if 'image' not in request.files:
        return jsonify({'success': False, 'message': 'No image provided'}), 400
    img = request.files['image'].read()
    temp_id = session.get('temp_user_id')
    if not temp_id:
        return jsonify({'success': False, 'message': 'No pending login'}), 400
    # fetch stored person_id
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT face_person_id FROM users WHERE id=%s", (temp_id,))
    row = cur.fetchone()
    conn.close()
    if not row or not row[0]:
        return jsonify({'success': False, 'message': 'User has no face registered'}), 400
    person_id = row[0]
    res = verify_face(person_id, img)
    if res.get('success'):
        # face ok -> complete login
        session['user_id'] = temp_id
        session['role'] = session.get('temp_role', 'student')
        session.pop('temp_user_id', None)
        session.pop('temp_role', None)
        return jsonify({'success': True, 'redirect': url_for('student_dashboard')})
    return jsonify({'success': False, 'message': res.get('message','Face not matched')}), 401

# optional verify voice (fallback: transcribe and compare simple passphrase)
@app.route('/verify/voice', methods=['POST'])
def verify_voice_route():
    # For simplicity we accept passphrase comparison. Real speaker recognition is more complex.
    file = request.files.get('audio')
    temp_id = session.get('temp_user_id')
    if not temp_id:
        return jsonify({'success': False, 'message': 'No pending login'}), 400
    if not file:
        return jsonify({'success': False, 'message': 'No audio sent'}), 400
    # For demo: just accept the voice; in production transcribe and compare to stored voice sample or use speaker verification
    session['user_id'] = temp_id
    session['role'] = session.get('temp_role', 'student')
    session.pop('temp_user_id', None)
    session.pop('temp_role', None)
    return jsonify({'success': True, 'redirect': url_for('student_dashboard')})

@app.route('/logout', methods=['POST','GET'])
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/student/dashboard')
@login_required
def student_dashboard():
    uid = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM exams")
    exams = cur.fetchall()
    conn.close()
    return render_template('student_dashboard.html', exams=exams)

@app.route('/exam/<int:exam_id>/start')
@login_required
def start_exam(exam_id):
    uid = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT * FROM exams WHERE exam_id=%s", (exam_id,))
    exam = cur.fetchone()
    cur.execute("SELECT * FROM questions WHERE exam_id=%s ORDER BY q_id", (exam_id,))
    questions = cur.fetchall()
    conn.close()
    return render_template('exam.html', exam=exam, questions=questions, user_id=uid)

# API to autosave answer
@app.route('/api/exam/save', methods=['POST'])
@login_required
def api_save_answer():
    data = request.get_json()
    q_id = data.get('q_id')
    exam_id = data.get('exam_id')
    answer_text = data.get('answer_text', '')
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    # upsert answer (check existing)
    cur.execute("SELECT answer_id FROM answers WHERE user_id=%s AND q_id=%s AND exam_id=%s", (user_id, q_id, exam_id))
    r = cur.fetchone()
    if r:
        cur.execute("UPDATE answers SET answer_text=%s, saved_at=NOW() WHERE answer_id=%s", (answer_text, r[0]))
    else:
        cur.execute("INSERT INTO answers (user_id,q_id,exam_id,answer_text) VALUES (%s,%s,%s,%s)", (user_id,q_id,exam_id,answer_text))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# submit exam
@app.route('/api/exam/submit', methods=['POST'])
@login_required
def api_submit_exam():
    data = request.get_json()
    exam_id = data.get('exam_id')
    user_id = session['user_id']
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE answers SET submitted=TRUE WHERE user_id=%s AND exam_id=%s", (user_id, exam_id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

# Admin dashboard
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT e.*, COUNT(a.answer_id) as submissions FROM exams e LEFT JOIN answers a ON e.exam_id=a.exam_id GROUP BY e.exam_id")
    exams = cur.fetchall()
    conn.close()
    return render_template('admin_dashboard.html', exams=exams)

# admin get scripts JSON
@app.route('/admin/scripts')
@admin_required
def admin_scripts():
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    cur.execute("SELECT a.*, u.name, q.question_text FROM answers a JOIN users u ON a.user_id=u.id JOIN questions q ON a.q_id=q.q_id")
    rows = cur.fetchall()
    conn.close()
    return jsonify(rows)

# admin evaluate
@app.route('/admin/evaluate', methods=['POST'])
@admin_required
def admin_evaluate():
    data = request.get_json()
    user_id = data.get('user_id')
    exam_id = data.get('exam_id')
    marks_list = data.get('marks')  # list of {q_id, mark}
    # compute total and upsert marks record
    total = sum([float(m.get('mark',0)) for m in marks_list])
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT mark_id, edit_count, is_locked FROM marks WHERE user_id=%s AND exam_id=%s", (user_id, exam_id))
    row = cur.fetchone()
    if row:
        mark_id, edit_count, is_locked = row
        if is_locked:
            conn.close()
            return jsonify({'success': False, 'message': 'Marks locked for editing'}), 403
        edit_count = edit_count + 1
        if edit_count >= 2:
            cur.execute("UPDATE marks SET total_marks=%s, edit_count=%s, is_locked=TRUE WHERE mark_id=%s", (total, edit_count, mark_id))
        else:
            cur.execute("UPDATE marks SET total_marks=%s, edit_count=%s WHERE mark_id=%s", (total, edit_count, mark_id))
    else:
        cur.execute("INSERT INTO marks (user_id, exam_id, total_marks, edit_count, is_locked) VALUES (%s,%s,%s,0,FALSE)", (user_id, exam_id, total))
    conn.commit()
    conn.close()
    return jsonify({'success': True, 'total': total})

# run plagiarism on a specific answer
@app.route('/admin/plagiarism', methods=['POST'])
@admin_required
def admin_plagiarism():
    data = request.get_json()
    target_id = data.get('answer_id')
    conn = get_db_connection()
    cur = conn.cursor(dictionary=True)
    # fetch target text
    cur.execute("SELECT answer_text FROM answers WHERE answer_id=%s", (target_id,))
    target = cur.fetchone()
    if not target:
        conn.close()
        return jsonify({'success': False, 'message': 'Answer not found'}), 404
    cur.execute("SELECT answer_id, answer_text FROM answers WHERE answer_id != %s", (target_id,))
    rows = cur.fetchall()
    texts = [r['answer_text'] for r in rows]
    res = check_against_batch(target['answer_text'], texts)
    conn.close()
    return jsonify(res)

# static route for uploaded files (voice samples, etc.)
@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

if __name__ == '__main__':
    app.run(debug=True)
