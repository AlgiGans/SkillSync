from config import ALPHA, BETA

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    session
)

from werkzeug.security import check_password_hash

from models import (
    db,
    User,
    Course,
    Trend,
    MyTable,
    SearchHistory
)

from werkzeug.security import (
    check_password_hash,
    generate_password_hash
)

from services.preprocessing import (
    run_preprocessing_pipeline as preprocess
)

from services.embedding import (
    load_or_train,
    text_to_vector
)

from services.similarity import (
    get_similarity
)
from services.evaluation.precision import evaluate_precision
from functools import wraps

import pandas as pd
import numpy as np
import math

admin_bp = Blueprint(
    "admin",
    __name__
)

# ==========================================================
# COURSE REPRESENTATION
# ==========================================================

def build_course_text(course):

    return " ".join([

        str(course.course_name or ""),

        str(course.skills or ""),

        str(course.description or "")

    ])


# ==========================================================
# TREND REPRESENTATION
# ==========================================================

def build_trend_text(trend):

    return str(
        trend.keyword or ""
    )


# ==========================================================
# COMPETENCY REPRESENTATION
# ==========================================================

def build_competency_text(item):

    return " ".join([

        str(item.Profesi_Bidang_Usaha or ""),

        str(item.Skill_yang_harus_dikuasai or ""),

        str(item.Detail_Item or ""),

        str(item.Level or "")

    ])

# ==========================================================
# REGISTER ADMIN
# ==========================================================
@admin_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm = request.form.get("confirm_password")

        # validasi
        if not username or not email or not password:

            flash("Semua field wajib diisi.", "danger")
            return redirect(url_for("admin.register"))

        if password != confirm:

            flash("Konfirmasi password tidak sama.", "danger")
            return redirect(url_for("admin.register"))

        if User.query.filter_by(email=email).first():

            flash("Email sudah digunakan.", "danger")
            return redirect(url_for("admin.register"))

        if User.query.filter_by(username=username).first():

            flash("Username sudah digunakan.", "danger")
            return redirect(url_for("admin.register"))

        admin = User(

            username=username,

            email=email,

            password=generate_password_hash(password),

            role="Admin"

        )

        db.session.add(admin)
        db.session.commit()

        flash(
            "Admin berhasil dibuat. Silakan login.",
            "success"
        )

        return redirect(
            url_for("admin.login")
        )

    return render_template(
        "admin/register.html"
    )

# ==========================================================
# LOGIN
# ==========================================================

@admin_bp.route("/login", methods=["GET","POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")

        password = request.form.get("password")

        admin = User.query.filter_by(

            email=email,

            role="Admin"

        ).first()

        if admin and check_password_hash(

            admin.password,

            password

        ):

            session["admin_logged_in"] = True

            session["admin_id"] = admin.id

            session["admin_name"] = admin.username

            flash(

                "Login berhasil.",

                "success"

            )

            return redirect(

                url_for("admin.dashboard")

            )

        flash(

            "Email atau password salah.",

            "danger"

        )

    return render_template(

        "admin/login.html"

    )

# ==========================================================
# LOGOUT
# ==========================================================

@admin_bp.route("/logout")
def logout():

    session.clear()

    flash(

        "Logout berhasil",

        "success"

    )

    return redirect(

        url_for("admin.login")

    )

# ==========================================================
# DASHBOARD
# ==========================================================

@admin_bp.route("/dashboard")
def dashboard():

    return render_template(

        "admin/dashboard.html",

        total_course=Course.query.count(),

        total_trend=Trend.query.count(),

        total_competency=MyTable.query.count(),

        total_user=User.query.count()

    )


# ======================================================
# DATASET HOME
# ======================================================
@admin_bp.route("/dataset")
def dataset():

    return render_template(
        "admin/dataset/index.html",
        course_count=Course.query.count(),
        trend_count=Trend.query.count(),
        competency_count=MyTable.query.count()
    )

# ======================================================
# COURSE DATASET
# ======================================================
@admin_bp.route("/dataset/course")
def dataset_course():

    courses = Course.query.order_by(
        Course.course_name.asc()
    ).all()

    return render_template(
        "admin/dataset/course.html",
        courses=courses
    )

@admin_bp.route(
    "/dataset/course/upload",
    methods=["POST"]
)
def upload_course_dataset():

    file = request.files.get("file")

    if not file:

        flash("File tidak ditemukan", "danger")
        return redirect(
            url_for("admin.dataset_course")
        )

    try:

        if file.filename.endswith(".csv"):
            df = pd.read_csv(file)
        else:
            df = pd.read_excel(file)

        df = df.where(
            pd.notnull(df),
            None
        )

        added = 0

        for _, row in df.iterrows():

            def clean(value):

                if isinstance(value, float):

                    if math.isnan(value):
                        return None

                return str(value).strip() if value else None

            course_name = clean(
                row.get("nama_course")
                or row.get("course_name")
            )

            if not course_name:
                continue

            exists = Course.query.filter_by(
                course_name=course_name
            ).first()

            if exists:
                continue

            db.session.add(

                Course(

                    course_name=course_name,

                    kategori=clean(
                        row.get("Kategori")
                    ),

                    skills=clean(
                        row.get("Skill")
                        or row.get("skills")
                    ),

                    description=clean(
                        row.get("Deskripsi")
                        or row.get("description")
                    ),

                    harga=clean(
                        row.get("Harga")
                    ),

                    pendaftar=clean(
                        row.get("Pendaftar")
                    ),

                    durasi=clean(
                        row.get("Durasi")
                    ),

                    rating=clean(
                        row.get("Rating")
                    ),

                    level=clean(
                        row.get("Level")
                    ),

                    mitra=clean(
                        row.get("Mitra")
                    ),

                    link=clean(
                        row.get("link")
                    )

                )

            )

            added += 1

        db.session.commit()

        flash(
            f"{added} Course berhasil ditambahkan",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        flash(
            str(e),
            "danger"
        )

    return redirect(
        url_for("admin.dataset_course")
    )

@admin_bp.route(
    "/dataset/course/delete/<int:id>",
    methods=["POST"]
)
def delete_course(id):

    course = Course.query.get_or_404(id)

    db.session.delete(course)

    db.session.commit()

    flash(
        "Course berhasil dihapus",
        "success"
    )

    return redirect(
        url_for("admin.dataset_course")
    )



# ======================================================
# TREND DATASET
# ======================================================
@admin_bp.route("/dataset/trend")
def dataset_trend():

    trends = Trend.query.order_by(
        Trend.keyword.asc()
    ).all()

    return render_template(
        "admin/dataset/trend.html",
        trends=trends
    )

# ======================================================
# UPLOAD TREND
# ======================================================
@admin_bp.route(
    "/dataset/trend/upload",
    methods=["POST"]
)
def upload_trend_dataset():

    file = request.files.get("file")

    if not file:

        flash(
            "File tidak ditemukan",
            "danger"
        )

        return redirect(
            url_for("admin.dataset_trend")
        )

    try:

        if file.filename.endswith(".csv"):

            df = pd.read_csv(file)

        else:

            df = pd.read_excel(file)

        df = df.where(
            pd.notnull(df),
            None
        )

        added = 0

        for _, row in df.iterrows():

            keyword = str(
                row.get("query") or ""
            ).strip()

            if not keyword:
                continue

            exists = Trend.query.filter_by(
                keyword=keyword
            ).first()

            if exists:
                continue

            trend = Trend(

                keyword=keyword,

                value=row.get(
                    "search interest"
                ),

                increase_percent=str(
                    row.get(
                        "increase percent"
                    ) or ""
                )

            )

            db.session.add(
                trend
            )

            added += 1

        db.session.commit()

        flash(
            f"{added} Trend berhasil ditambahkan",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        flash(
            str(e),
            "danger"
        )

    return redirect(
        url_for("admin.dataset_trend")
    )

# ======================================================
# DELETE TREND
# ======================================================
@admin_bp.route(
    "/dataset/trend/delete/<int:id>",
    methods=["POST"]
)
def delete_trend(id):

    trend = Trend.query.get_or_404(id)

    db.session.delete(trend)

    db.session.commit()

    flash(
        "Trend berhasil dihapus",
        "success"
    )

    return redirect(
        url_for("admin.dataset_trend")
    )

# ======================================================
# CLEAR TREND
# ======================================================
@admin_bp.route(
    "/dataset/trend/clear",
    methods=["POST"]
)
def clear_trend():

    Trend.query.delete()

    db.session.commit()

    flash(
        "Seluruh Trend berhasil dihapus",
        "success"
    )

    return redirect(
        url_for("admin.dataset_trend")
    )




# ======================================================
# COMPETENCY DATASET
# ======================================================
@admin_bp.route("/dataset/competency")
def dataset_competency():

    competencies = MyTable.query.order_by(
        MyTable.Profesi_Bidang_Usaha.asc()
    ).all()

    return render_template(
        "admin/dataset/competency.html",
        competencies=competencies
    )

# ======================================================
# UPLOAD COMPETENCY DATASET
# ======================================================
@admin_bp.route(
    "/dataset/competency/upload",
    methods=["POST"]
)
def upload_competency_dataset():

    file = request.files.get("file")

    if not file:

        flash(
            "File tidak ditemukan",
            "danger"
        )

        return redirect(
            url_for("admin.dataset_competency")
        )

    try:

        if file.filename.lower().endswith(".csv"):

            df = pd.read_csv(file)

        else:

            df = pd.read_excel(file)

        df = df.where(
            pd.notnull(df),
            None
        )

        added = 0

        def clean(value):

            if value is None:
                return None

            if isinstance(value, float):

                if math.isnan(value):
                    return None

                if value.is_integer():
                    value = int(value)

            return str(value).strip()

        for _, row in df.iterrows():

            profesi = clean(
                row.get("Profesi_Bidang_Usaha")
            )

            skill = clean(
                row.get("Skill_yang_harus_dikuasai")
            )

            detail = clean(
                row.get("Detail_Item")
            )

            level = clean(
                row.get("Level")
            )

            if not profesi:
                continue

            exists = MyTable.query.filter_by(
                Profesi_Bidang_Usaha=profesi,
                Skill_yang_harus_dikuasai=skill,
                Detail_Item=detail,
                Level=level
            ).first()

            if exists:
                continue

            competency = MyTable(

                Profesi_Bidang_Usaha=profesi,

                Skill_yang_harus_dikuasai=skill,

                Detail_Item=detail,

                Level=level

            )

            db.session.add(
                competency
            )

            added += 1

        db.session.commit()

        flash(
            f"{added} data kompetensi berhasil ditambahkan.",
            "success"
        )

    except Exception as e:

        db.session.rollback()

        flash(
            str(e),
            "danger"
        )

    return redirect(
        url_for("admin.dataset_competency")
    )

# ======================================================
# DELETE COMPETENCY
# ======================================================
@admin_bp.route(
    "/dataset/competency/delete/<int:id>",
    methods=["POST"]
)
def delete_competency(id):

    competency = MyTable.query.get_or_404(id)

    db.session.delete(
        competency
    )

    db.session.commit()

    flash(
        "Data kompetensi berhasil dihapus",
        "success"
    )

    return redirect(
        url_for("admin.dataset_competency")
    )

# ======================================================
# CLEAR COMPETENCY DATASET
# ======================================================
@admin_bp.route(
    "/dataset/competency/clear",
    methods=["POST"]
)
def clear_competency():

    MyTable.query.delete()

    db.session.commit()

    flash(
        "Seluruh data kompetensi berhasil dihapus",
        "success"
    )

    return redirect(
        url_for("admin.dataset_competency")
    )





# ======================================================
# PREPROCESSING
# ======================================================
@admin_bp.route("/method/preprocessing")
def method_preprocessing():

    courses = Course.query.order_by(
        Course.course_name.asc()
    ).all()

    results = []

    for course in courses:

        raw_text = build_course_text(
            course
        )

        process = preprocess(
            raw_text
        )

        results.append({

            "course": course.course_name,

            "original": raw_text,

            "case_folding": process["case_folding"],

            "clean_text": process["clean_text"],

            "tokens": process["tokens"],

            "filtered_tokens": process["filtered_tokens"],

            "normalization": process["normalization"]

        })

    return render_template(

        "admin/method/preprocessing.html",

        results=results,

        total=len(results)

    )





# ======================================================
# EMBEDDING
# ======================================================
@admin_bp.route("/method/embedding")
def method_embedding():

    courses = Course.query.order_by(
        Course.course_name.asc()
    ).all()

    # ---------------------------------------------
    # Train / Load FastText
    # ---------------------------------------------
    sentences = []

    # Menyimpan hasil preprocessing setiap course
    course_texts = {}

    for course in courses:

        text = preprocess(
            build_course_text(course)
        )["normalization"]

        # simpan hasil preprocessing
        course_texts[course.id] = text

        if text.strip():

            sentences.append(
                text.split()
            )

    load_or_train(sentences)

    results = []

    for course in courses:

        text = course_texts.get(course.id, "")

        vector = text_to_vector(text)

        results.append({

            "course": course.course_name,

            "text": text,

            "dimension": len(vector),

            "vector_preview": [
                round(float(v),4)
                for v in vector[:10]
            ],

            "min": round(float(np.min(vector)),4),

            "max": round(float(np.max(vector)),4),

            "mean": round(float(np.mean(vector)),4)

        })

    return render_template(

        "admin/method/embedding.html",

        results=results,

        total=len(results)

    )




# ======================================================
# SIMILARITY
# ======================================================
@admin_bp.route("/method/similarity")
def method_similarity():

    courses = Course.query.order_by(
        Course.course_name.asc()
    ).all()

    trends = Trend.query.order_by(
        Trend.keyword.asc()
    ).all()

    competencies = MyTable.query.all()

    # --------------------------------------------------
    # memastikan model FastText tersedia
    # --------------------------------------------------
    corpus = []

    for c in courses:

        text = preprocess(
            build_course_text(c)
        )["normalization"]

        if text.strip():

            corpus.append(
                text.split()
            )

    load_or_train(corpus)

    # --------------------------------------------------
    # contoh profile admin
    # hanya untuk validasi metode
    # --------------------------------------------------
    sample_profile = """
    Software Engineer
    Python
    Machine Learning
    Data Analysis
    SQL
    """

    profile_text = preprocess(
        sample_profile
    )["normalization"]

    profile_vector = text_to_vector(
        profile_text
    )
    
    # ==========================================
    # PREPARE COURSE VECTORS
    # ==========================================
    course_vectors = {}

    for course in courses:

        course_text = preprocess(
            build_course_text(course)
        )["normalization"]

        course_vectors[course.id] = {
            "text": course_text,
            "vector": text_to_vector(course_text)
        }

    # ==========================================
    # PREPARE TREND VECTORS
    # ==========================================
    trend_vectors = []

    for trend in trends:

        trend_text = preprocess(
            build_trend_text(trend)
        )["normalization"]

        trend_vectors.append({

            "trend": trend,

            "vector": text_to_vector(
                trend_text
            )

        })

    # ==========================================
    # PREPARE COMPETENCY VECTORS
    # ==========================================
    competency_vectors = []

    for item in competencies:

        competency_text = preprocess(
            build_competency_text(item)
        )["normalization"]

        competency_vectors.append({

            "item": item,

            "vector": text_to_vector(competency_text)

        })

    results = []
    
    # ==================================================
    # setiap course
    # ==================================================
    for course in courses:

        course_vector = course_vectors[
            course.id
        ]["vector"]

        # ----------------------------------------------
        # Profile -> Course
        # ----------------------------------------------
        sim_profile_course = get_similarity(

            profile_vector,

            course_vector

        )

        # ----------------------------------------------
        # Trend terbaik
        # ----------------------------------------------
        best_trend = None
        best_trend_similarity = 0

        for trend_data in trend_vectors:

            trend = trend_data["trend"]

            trend_vector = trend_data["vector"]

            sim_profile_trend = get_similarity(

                profile_vector,

                trend_vector

            )

            if sim_profile_trend > best_trend_similarity:

                best_trend_similarity = sim_profile_trend

                best_trend = trend

        # ----------------------------------------------
        # Trend -> Course
        # ----------------------------------------------
        trend_course_similarity = 0

        if best_trend:

            trend_vector = next(

            t["vector"]

            for t in trend_vectors

            if t["trend"] == best_trend

        )

            trend_course_similarity = get_similarity(

                trend_vector,

                course_vector

            )

        # ----------------------------------------------
        # Competency -> Course
        # ----------------------------------------------
        competency_similarity = 0

        for competency_data in competency_vectors:

            competency_vector = competency_data[
                "vector"
            ]

            sim = get_similarity(

                competency_vector,

                course_vector

            )

            if sim > competency_similarity:

                competency_similarity = sim

        results.append({

            "course": course.course_name,

            "profile_course":
                round(sim_profile_course,4),

            "profile_trend":
                round(best_trend_similarity,4),

            "trend":

                best_trend.keyword
                if best_trend else "-",

            "trend_course":
                round(trend_course_similarity,4),

            "competency_course":
                round(competency_similarity,4)

        })

    return render_template(

        "admin/method/similarity.html",

        results=results,

        total=len(results)

    )

# ======================================================
# TREND BOOST
# ======================================================
@admin_bp.route("/method/trend-boost")
def method_trend_boost():

    courses = Course.query.order_by(
        Course.course_name.asc()
    ).all()

    trends = Trend.query.all()

    # ---------------------------------------------
    # memastikan model FastText tersedia
    # ---------------------------------------------
    corpus = []

    for c in courses:

        text = preprocess(
            build_course_text(c)
        )["normalization"]

        if text.strip():

            corpus.append(
                text.split())

    load_or_train(corpus)

    # ==========================================
    # PREPARE COURSE VECTORS
    # ==========================================
    course_vectors = {}

    for course in courses:

        course_text = preprocess(
            build_course_text(course)
        )["normalization"]

        course_vectors[course.id] = {

            "text": course_text,

            "vector": text_to_vector(
                course_text
            )

        }

    # ==========================================
    # PREPARE TREND VECTORS
    # ==========================================
    trend_vectors = []

    for trend in trends:

        trend_text = preprocess(
            build_trend_text(trend)
        )["normalization"]

        trend_vectors.append({

            "trend": trend,

            "vector": text_to_vector(
                trend_text
            )

        })
        
    results = []

    # =============================================
    # Hitung Trend Boost tiap Course
    # =============================================
    for course in courses:

        course_vector = course_vectors[
            course.id
        ]["vector"]

        best_trend = None

        best_similarity = 0

        best_popularity = 0

        best_boost = 0

        for trend_data in trend_vectors:

            trend = trend_data["trend"]

            trend_vector = trend_data["vector"]

            similarity = get_similarity(

                trend_vector,

                course_vector

            )

            try:

                popularity = float(
                    trend.value or 0
                ) / 100

            except:

                popularity = 0

            trend_boost = (

                ALPHA * similarity +

                (1 - ALPHA) * popularity

            )

            if trend_boost > best_boost:

                best_boost = trend_boost

                best_similarity = similarity

                best_popularity = popularity

                best_trend = trend

        results.append({

            "course": course.course_name,

            "trend":

                best_trend.keyword
                if best_trend else "-",

            "similarity":

                round(best_similarity,4),

            "popularity":

                round(best_popularity,4),

            "trend_boost":

                round(best_boost,4)

        })

    results = sorted(

        results,

        key=lambda x: x["trend_boost"],

        reverse=True

    )

    return render_template(

        "admin/method/trend_boost.html",

        results=results,

        alpha=ALPHA,

        total=len(results)

    )



# ======================================================
# ADAPTIVE SCORE
# ======================================================
@admin_bp.route("/method/adaptive-score")
def method_adaptive_score():

    courses = Course.query.order_by(
        Course.course_name.asc()
    ).all()

    trends = Trend.query.all()

    competencies = MyTable.query.all()

    # --------------------------------------------
    # memastikan model FastText tersedia
    # --------------------------------------------
    corpus = []

    for c in courses:

        text = preprocess(
            build_course_text(c)
        )["normalization"]

        if text.strip():

            corpus.append(
                text.split()
            )

    load_or_train(corpus)

    # --------------------------------------------
    # sample profile
    # --------------------------------------------
    sample_profile = """
    Software Engineer
    Python
    Machine Learning
    SQL
    Data Analysis
    """

    profile_text = preprocess(
        sample_profile
    )["normalization"]

    profile_vector = text_to_vector(
        profile_text
    )

    # ==========================================
    # PREPARE COURSE VECTORS
    # ==========================================
    course_vectors = {}

    for course in courses:

        course_text = preprocess(
            build_course_text(course)
        )["normalization"]

        course_vectors[course.id] = {

            "text": course_text,

            "vector": text_to_vector(
                course_text
            )

        }

        

    # ==========================================
    # PREPARE TREND VECTORS
    # ==========================================
    trend_vectors = []

    for trend in trends:

        trend_text = preprocess(
            build_trend_text(trend)
        )["normalization"]

        trend_vectors.append({

            "trend": trend,

            "vector": text_to_vector(
                trend_text
            )

        })

    # ==========================================
    # PREPARE COMPETENCY VECTORS
    # ==========================================
    competency_vectors = []

    for competency in competencies:

        competency_text = preprocess(

            build_competency_text(
                competency
            )

        )["normalization"]

        competency_vectors.append({

            "competency": competency,

            "vector": text_to_vector(
                competency_text
            )

        })
    results = []

    # ============================================
    # setiap course
    # ============================================
    for course in courses:

        # ----------------------------------------
        # Course
        # ----------------------------------------
        course_vector = course_vectors[
        course.id
    ]["vector"]

        # ----------------------------------------
        # Profile -> Course
        # ----------------------------------------
        sim_profile_course = get_similarity(

            profile_vector,

            course_vector

        )

        # ----------------------------------------
        # Competency -> Course
        # ----------------------------------------
        competency_similarity = 0

        for competency_data in competency_vectors:

            competency_vector = competency_data[
                "vector"
            ]
            sim = get_similarity(

                competency_vector,

                course_vector

            )

            if sim > competency_similarity:

                competency_similarity = sim

        # ----------------------------------------
        # Trend Boost
        # ----------------------------------------
        best_boost = 0

        best_trend = "-"

        for trend_data in trend_vectors:

            trend = trend_data["trend"]

            trend_vector = trend_data[
                "vector"
            ]

            similarity = get_similarity(

                trend_vector,

                course_vector

            )

            try:

                popularity = float(
                    trend.value or 0
                ) / 100

            except:

                popularity = 0

            boost = (

                ALPHA * similarity +

                (1 - ALPHA) * popularity

            )

            if boost > best_boost:

                best_boost = boost

                best_trend = trend.keyword

        # ----------------------------------------
        # Internal Relevance
        # ----------------------------------------
        internal_relevance = (

            sim_profile_course +

            competency_similarity

        ) / 2

        # ----------------------------------------
        # Adaptive Score
        # ----------------------------------------
        adaptive_score = (

            internal_relevance +

            (BETA * best_boost)

        )

        results.append({

            "course": course.course_name,

            "trend": best_trend,

            "profile_course":
                round(sim_profile_course,4),

            "competency_course":
                round(competency_similarity,4),

            "internal_relevance":
                round(internal_relevance,4),

            "trend_boost":
                round(best_boost,4),

            "adaptive_score":
                round(adaptive_score,4)

        })

    results = sorted(

        results,

        key=lambda x: x["adaptive_score"],

        reverse=True

    )

    return render_template(

        "admin/method/adaptive_score.html",

        results=results,

        beta=BETA,

        total=len(results)

    )


# ======================================================
# USERS
# ======================================================
@admin_bp.route("/users")
def users():

    users = User.query.order_by(
        User.username.asc()
    ).all()

    return render_template(

        "admin/users/index.html",

        users=users

    )

@admin_bp.route(
    "/users/edit/<int:id>",
    methods=["GET","POST"]
)
def edit_user(id):

    user = User.query.get_or_404(id)

    if request.method == "POST":

        user.username = request.form.get("username")

        user.email = request.form.get("email")

        user.role = request.form.get("role")

        db.session.commit()

        flash(
            "User berhasil diperbarui.",
            "success"
        )

        return redirect(
            url_for("admin.users")
        )

    return render_template(

        "admin/users/edit.html",

        user=user

    )

@admin_bp.route(
    "/users/delete/<int:id>",
    methods=["POST"]
)
def delete_user(id):

    user = User.query.get_or_404(id)

    SearchHistory.query.filter_by(
        user_id=id
    ).delete()

    db.session.delete(user)

    db.session.commit()

    flash(
        "User berhasil dihapus.",
        "success"
    )

    return redirect(
        url_for("admin.users")
    )







from flask import request, render_template
import os

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

ground_truth_path = os.path.join(
    BASE_DIR,
    "dataset",
    "ground truth 1.xlsx"
)
@admin_bp.route("/evaluation/precision", methods=["GET", "POST"])
def evaluation_precision():

    courses = Course.query.all()
    trends = Trend.query.all()
    competency_guides = MyTable.query.all()

    evaluation = None

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    ground_truth_path = os.path.join(
        BASE_DIR,
        "dataset",
        "ground truth 1.xlsx"
    )

    if request.method == "POST":

        mode = request.form.get("mode", "global")
        selected_professions = request.form.getlist("professions")[:5]

        evaluation = evaluate_precision(
            courses=courses,
            trends=trends,
            competency_guides=competency_guides,
            ground_truth_path=ground_truth_path,
            mode=mode,
            selected_professions=selected_professions
        )

    return render_template(
        "admin/evaluation/precision.html",
        evaluation=evaluation,
        competency_guides=competency_guides
    )


@admin_bp.route("/get-skills/<path:profesi>")
def get_skills(profesi):

    rows = MyTable.query.filter_by(
        Profesi_Bidang_Usaha=profesi
    ).all()

    skills=[]

    for row in rows:

        if row.Skill_yang_harus_dikuasai:

            skills.append({

                "skill":row.Skill_yang_harus_dikuasai,

                "detail":row.Detail_Item

            })

    return jsonify(skills)

@admin_bp.route("/evaluation/pembobotan", methods=["GET", "POST"])
def evaluation_pembobotan():

    courses = Course.query.all()
    trends = Trend.query.all()
    competency_guides = MyTable.query.all()

    alphas_betas = [
        (0.2, 0.8),
        (0.3, 0.7),
        (0.4, 0.6),
        (0.5, 0.5)
    ]

    results = []

    best = None
    best_score = -1

    if request.method == "POST":

        for alpha, beta in alphas_betas:

            # override config sementara (penting)
            eval_result = evaluate_precision(
                courses=courses,
                trends=trends,
                competency_guides=competency_guides,
                ground_truth_path=ground_truth_path,
                mode="global",
                selected_professions=[],
                alpha=alpha,
                beta=beta
            )

            avg = (
                eval_result["avg_precision1"] +
                eval_result["avg_precision5"] +
                eval_result["avg_precision10"]
            ) / 3

            row = {
                "alpha": alpha,
                "beta": beta,
                "precision_at_1": eval_result["avg_precision1"],
                "precision_at_5": eval_result["avg_precision5"],
                "precision_at_10": eval_result["avg_precision10"],
                "avg": round(avg, 4)
            }

            results.append(row)

            if avg > best_score:
                best_score = avg
                best = row

    return render_template(
        "admin/evaluation/pembobotan.html",
        results=results,
        best=best
    )