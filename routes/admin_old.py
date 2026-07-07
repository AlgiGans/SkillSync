from flask import Blueprint, render_template, redirect, url_for, flash, request, session    

from models import db, User, Course, Trend, SearchHistory

from services.embedding import text_to_vector, load_or_train
from services.preprocessing import run_preprocessing_pipeline as preprocess
from services.similarity import euclidean, normalize_distance
from services.trend import get_trend_score

import pandas as pd
import numpy as np
import math

from werkzeug.security import check_password_hash

admin_bp = Blueprint('admin', __name__)


# ======================================================
# HELPER : REPRESENTASI COURSE
# ======================================================
def build_course_text(course):

    skills = course.skills or ""
    course_name = course.course_name or ""
    description = course.description or ""

    combined = f"""
    {skills}
    {course_name}
    {description}
    """

    return combined.strip()


# ======================================================
# LOGIN ADMIN
# ======================================================
@admin_bp.route('/login', methods=['GET', 'POST'])
def login():

    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password')

        admin = User.query.filter_by(email=email, role="Admin").first()

        if admin and check_password_hash(admin.password, password):

            session['admin_logged_in'] = True
            session['admin_id'] = admin.id
            session['admin_name'] = admin.username

            flash("Login berhasil sebagai admin", "success")
            return redirect(url_for('admin.dashboard'))

        flash("Email atau password salah", "danger")

    return render_template('admin/login.html')


# ======================================================
# DASHBOARD
# ======================================================
@admin_bp.route('/dashboard')
def dashboard():

    courses_count = Course.query.count()
    trends_count = Trend.query.count()

    return render_template(
        'admin/dashboard.html',
        courses_count=courses_count,
        trends_count=trends_count
    )


# ======================================================
# UPLOAD DATASET
# ======================================================
@admin_bp.route('/upload-dataset', methods=['GET', 'POST'])
def upload_dataset():

    if request.method == 'POST':

        # ======================================================
        # UPLOAD COURSE
        # ======================================================
        if 'file_course' in request.files and request.files['file_course'].filename != '':

            file = request.files['file_course']

            try:

                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                df = df.where(pd.notnull(df), None)

                added_count = 0

                for _, row in df.iterrows():

                    def clean(val):

                        if isinstance(val, float) and math.isnan(val):
                            return None

                        return str(val).strip() if val else None

                    course_name = clean(
                        row.get('nama_course') or
                        row.get('course_name')
                    )

                    skills = clean(
                        row.get('Skill') or
                        row.get('skills')
                    )

                    description = clean(
                        row.get('Deskripsi') or
                        row.get('description')
                    )

                    if not course_name:
                        continue

                    existing = Course.query.filter_by(
                        course_name=course_name
                    ).first()

                    if not existing:

                        new_course = Course(

                            course_name=course_name,
                            skills=skills,
                            description=description,

                            kategori=clean(row.get('Kategori')),
                            harga=clean(row.get('Harga')),
                            pendaftar=clean(row.get('Pendaftar')),
                            durasi=clean(row.get('Durasi')),
                            rating=clean(row.get('Rating')),
                            level=clean(row.get('Level')),
                            mitra=clean(row.get('Mitra')),
                            link=clean(row.get('link'))

                        )

                        db.session.add(new_course)

                        added_count += 1

                db.session.commit()

                flash(
                    f'{added_count} course berhasil ditambahkan',
                    'success'
                )

            except Exception as e:

                db.session.rollback()

                flash(
                    f'Error upload course: {str(e)}',
                    'danger'
                )

        # ======================================================
        # UPLOAD TREND
        # ======================================================
        if 'file_trends' in request.files and request.files['file_trends'].filename != '':

            file = request.files['file_trends']

            try:

                if file.filename.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)

                df = df.where(pd.notnull(df), None)

                added = 0

                for _, row in df.iterrows():

                    keyword = str(
                        row.get('query') or ''
                    ).strip()

                    if not keyword:
                        continue

                    existing = Trend.query.filter_by(
                        keyword=keyword
                    ).first()

                    if not existing:

                        new_trend = Trend(
                            keyword=keyword,
                            value=row.get('search interest'),
                            increase_percent=str(
                                row.get('increase percent') or ''
                            )
                        )

                        db.session.add(new_trend)

                        added += 1

                db.session.commit()

                flash(
                    f'{added} trend berhasil ditambahkan',
                    'success'
                )

            except Exception as e:

                db.session.rollback()

                flash(
                    f'Error upload trend: {str(e)}',
                    'danger'
                )

        return redirect(url_for('admin.upload_dataset'))

    return render_template(
        'admin/upload.html',
        courses_count=Course.query.count(),
        trends_count=Trend.query.count()
    )


# ======================================================
# PREPROCESSING
# ======================================================
@admin_bp.route('/preprocessing')
def preprocessing():

    return render_template(
        'admin/preprocessing.html',
        data=[],
        status=None
    )


@admin_bp.route('/run-preprocessing', methods=['POST'])
def run_preprocessing():

    courses = Course.query.all()

    results = []

    for c in courses:

        course_name = c.course_name or ""
        skills = c.skills or ""
        description = c.description or ""

        combined_text = build_course_text(c)

        processed = preprocess(combined_text)

        case_folding = processed.get("case_folding", "")
        tokens = processed.get("tokens", [])
        filtered = processed.get("filtered_tokens", [])   # ✔ INI YANG BENAR
        normalization = processed.get("normalization", "")

        results.append({
            "course_name": course_name,
            "skills": skills,
            "description": description,
            "combined_text": combined_text,

            "case_folding": case_folding,
            "tokens": tokens,
            "stopword": filtered,   # ✔ FIX
            "normalization": normalization
        })                          

    return render_template(
        'admin/preprocessing.html',
        data=results,
        status="Preprocessing berhasil dijalankan"
    )


# ======================================================
# EMBEDDING VIEW
# ======================================================
@admin_bp.route('/embedding-view')
def embedding_view():

    return render_template(
        'admin/embedding_view.html',
        data=[],
        status=None
    )


@admin_bp.route('/run-embedding', methods=['POST'])
def run_embedding():

    courses = Course.query.all()

    results = []

    sentences = []

    for c in courses:

        raw_text = build_course_text(c)

        clean_text = preprocess(raw_text)["normalization"]

        if clean_text.strip():
            sentences.append(clean_text.split())

    load_or_train(sentences)

    for c in courses:

        raw_text = build_course_text(c)

        clean_text = preprocess(raw_text)["normalization"]

        vector = text_to_vector(clean_text)

        results.append({

            "course": c.course_name,
            "text": clean_text,
            "vector": vector[:8],
            "dimension": len(vector),

            "min_value": round(float(np.min(vector)), 4),
            "max_value": round(float(np.max(vector)), 4),

            "mean_value": round(float(np.mean(vector)), 4)

        })

    return render_template(
        'admin/embedding_view.html',
        data=results,
        status="Embedding berhasil dijalankan"
    )


# ======================================================
# SIMILARITY
# ======================================================
@admin_bp.route('/similarity')
def similarity():

    return render_template(
        'admin/similarity.html',
        data=[],
        status=None
    )


@admin_bp.route('/run-similarity', methods=['POST'])
def run_similarity():

    courses = Course.query.all()
    trends = Trend.query.all()

    results = []
    distances = []

    # =====================================================
    # COURSE ↔ BEST TREND MATCH
    # =====================================================
    for course in courses:

        course_text = preprocess(
            build_course_text(course)
        )["normalization"]

        course_vector = text_to_vector(course_text)

        best_trend = None
        best_distance = None

        # =================================================
        # CARI TREND PALING MIRIP (TOP-1)
        # =================================================
        for trend in trends:

            keyword = str(trend.keyword or "").strip()

            if not keyword:
                continue

            trend_text = preprocess(keyword)["normalization"]
            trend_vector = text_to_vector(trend_text)

            distance = euclidean(course_vector, trend_vector)

            if best_distance is None or distance < best_distance:

                best_distance = distance
                best_trend = keyword

        # simpan hasil terbaik untuk course ini
        if best_trend is not None:

            distances.append(best_distance)

            results.append({
                "course": course.course_name,
                "trend": best_trend,
                "distance": best_distance
            })

    # =====================================================
    # VALIDASI
    # =====================================================
    if not results:
        return render_template(
            'admin/similarity.html',
            data=[],
            status="Data kosong"
        )

    # =====================================================
    # NORMALISASI
    # =====================================================
    d_min = min(distances)
    d_max = max(distances)

    if d_min == d_max:
        d_max = d_min + 1e-9

    final_results = []

    for item in results:

        similarity = normalize_distance(
            item["distance"],
            d_min,
            d_max
        )

        final_results.append({
            "course": item["course"],
            "trend": item["trend"],
            "distance": round(item["distance"], 4),
            "similarity": round(similarity, 4)
        })

    # =====================================================
    # SORTING (TOP COURSE TERBAIK)
    # =====================================================
    final_results = sorted(
        final_results,
        key=lambda x: x["similarity"],
        reverse=True
    )

    return render_template(
        'admin/similarity.html',
        data=final_results,
        status="Course ↔ Trend (Best Match) berhasil dihitung"
    )


# ======================================================
# TREND SCORING
# ======================================================
@admin_bp.route('/trend-scoring')
def trend_scoring():

    return render_template(
        'admin/trend.html',
        data=[],
        status=None
    )


@admin_bp.route('/run-trend-scoring', methods=['POST'])
def run_trend_scoring():

    courses = Course.query.all()

    trends = Trend.query.all()

    results = []

    for c in courses:

        raw_text = build_course_text(c)

        clean_text = preprocess(raw_text)["normalization"]

        course_vector = text_to_vector(
            clean_text
        )

        trend_score = 0

        results.append({

            "course": c.course_name,
            "score": round(trend_score, 4)

        })

    return render_template(
        'admin/trend.html',
        data=results,
        status="Trend scoring berhasil dihitung"
    )


# ======================================================
# RETRAIN MODEL
# ======================================================
@admin_bp.route('/embedding')
def embedding():

    return render_template(
        'admin/embedding.html'
    )


@admin_bp.route('/retrain', methods=['POST'])
def retrain_model():

    try:

        courses = Course.query.all()

        if not courses:

            return render_template(
                'admin/embedding.html',
                success=False,
                error="Database kosong"
            )

        sentences = []

        for c in courses:

            raw_text = build_course_text(c)

            clean_text = preprocess(raw_text)["normalization"]

            if clean_text.strip():

                sentences.append(
                    clean_text.split()
                )

        load_or_train(sentences)

        return render_template(
            'admin/embedding.html',
            success=True
        )

    except Exception as e:

        return render_template(
            'admin/embedding.html',
            success=False,
            error=str(e)
        )

# ======================================================
# USER MANAGEMENT
# ======================================================
@admin_bp.route('/users')
def manage_users():

    users = User.query.all()

    return render_template(
        'admin/users.html',
        users=users
    )

# ======================================================
# EDIT USER (ADMIN)
# ======================================================
@admin_bp.route('/users/edit/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):

    user = User.query.get_or_404(user_id)

    if request.method == 'POST':

        username = request.form.get('username')
        email = request.form.get('email')
        role = request.form.get('role')

        # cek email tidak boleh duplikat
        existing = User.query.filter(
            User.email == email,
            User.id != user_id
        ).first()

        if existing:
            flash("Email sudah digunakan user lain!", "danger")
            return redirect(url_for('admin.edit_user', user_id=user_id))

        user.username = username
        user.email = email
        user.role = role

        db.session.commit()

        flash("User berhasil diupdate!", "success")
        return redirect(url_for('admin.manage_users'))

    return render_template('admin/edit_user.html', user=user)

# ======================================================
# DELETE USER (ADMIN)
# ======================================================
@admin_bp.route('/delete-user/<int:user_id>', methods=['POST'])
def delete_user(user_id):

    user = User.query.get_or_404(user_id)

    SearchHistory.query.filter_by(user_id=user_id).delete()

    db.session.delete(user)
    db.session.commit()

    flash("User berhasil dihapus", "success")
    return redirect(url_for('admin.manage_users'))


# ======================================================
# LOGOUT ADMIN
# ======================================================
@admin_bp.route('/logout')
def logout():

    session.clear()

    flash("Berhasil logout", "success")

    return redirect(url_for('admin.login'))

