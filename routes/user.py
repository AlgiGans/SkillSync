from flask import Blueprint, render_template, request, session, redirect, url_for, flash

from models import (
    db,
    User,
    Course,
    Trend,
    SearchHistory,
    MyTable
)

from services.pipeline import pipeline

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from config import BETA
from flask import jsonify


user_bp = Blueprint('user', __name__)


# =========================
# REGISTER
# =========================
@user_bp.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")

        user_exists = User.query.filter_by(email=email).first()

        if user_exists:
            flash("Email sudah digunakan!", "danger")
            return redirect(url_for('user.register'))

        hashed_password = generate_password_hash(password)

        new_user = User(
            username=username,
            email=email,
            password=hashed_password
        )

        db.session.add(new_user)
        db.session.commit()

        flash("Registrasi berhasil! Silakan login.", "success")

        return redirect(url_for('user.login'))

    return render_template("user/register.html")


# =========================
# LOGIN
# =========================
@user_bp.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email")
        password = request.form.get("password")

        user = User.query.filter_by(email=email).first()

        if user and check_password_hash(user.password, password):

            session['user_logged_in'] = True
            session['user_id'] = user.id
            session['username'] = user.username
            session['email'] = user.email

            flash(f"Selamat datang kembali, {user.username}!", "success")

            return redirect(url_for('user.dashboard'))

        else:
            flash("Email atau password salah.", "danger")

    return render_template("user/login.html")


# =========================
# LOGOUT
# =========================
@user_bp.route("/logout")
def logout():

    session.clear()
    flash("Anda telah keluar.", "info")

    return redirect(url_for('user.index'))


#===== LANDING PAGE
# =========================
# LANDING PAGE
# =========================
@user_bp.route("/")
def index():

    return render_template("user/landingpage.html")

# =========================
# DASHBOARD
# =========================
@user_bp.route("/get-skills/<path:profesi>")
def get_skills(profesi):

    rows = MyTable.query.filter_by(
        Profesi_Bidang_Usaha=profesi
    ).all()

    skills = []

    for row in rows:

        if row.Skill_yang_harus_dikuasai:

            skills.append({
                "skill": row.Skill_yang_harus_dikuasai,
                "detail": row.Detail_Item,
            })

    return jsonify(skills)

@user_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard():

    if not session.get('user_logged_in'):
        return redirect(url_for('user.login'))

    user_data = {
        "username": session.get("username"),
        "email": session.get("email")
    }

    courses = Course.query.all()
    trends = Trend.query.all()
    competency_guides = MyTable.query.all()

    profesi_list = (
        db.session.query(MyTable.Profesi_Bidang_Usaha)
        .distinct()
        .order_by(MyTable.Profesi_Bidang_Usaha)
        .all()
    )

    profesi_list = [p[0] for p in profesi_list if p[0]]

    skill_reference = MyTable.query.all()

    history_list = SearchHistory.query.filter_by(
        user_id=session.get('user_id')
    ).order_by(
        SearchHistory.created_at.desc()
    ).all()

    results = None

    selected_competencies = []

    trend_insight = []

    profession = ""

    if request.method == "POST":

        profession = request.form.get(
            "profession",
            ""
        ).strip()

        selected_competencies = request.form.get(
            "selected_skills",
            ""
        )

        selected_competencies = [
            s.strip()
            for s in selected_competencies.split("|")
            if s.strip()
        ]


        if profession and selected_competencies:

            results, selected_competencies, trend_insight = pipeline(
                    courses,
                    trends,
                    competency_guides,
                    profession,
                    selected_competencies
                )
            

            for r in results:
                print(r)


            new_history = SearchHistory(

                user_id=session.get("user_id"),

                profession=profession,

                selected_competencies="|".join(
                    selected_competencies
                )

            )

            db.session.add(new_history)
            db.session.commit()

            history_list = SearchHistory.query.filter_by(
                user_id=session.get('user_id')
            ).order_by(
                SearchHistory.created_at.desc()
            ).all()

        else:

            if not profession:

                flash(
                    "Silakan pilih profesi.",
                    "warning"
                )

            elif not selected_competencies:

                flash(
                    "Silakan pilih minimal satu kompetensi.",
                    "warning"
                )
                

    return render_template(
    "user/dashboard.html",
    skill_reference=skill_reference,
    results=results,
    selected_competencies=selected_competencies,
    profession=profession,
    trend_insight=trend_insight,
    history=history_list,
    user=user_data,
    profesi_list=profesi_list,
    beta=BETA
)


# =========================
# HISTORY DETAIL
# =========================
@user_bp.route("/history/<int:history_id>")
def history_detail(history_id):

    if not session.get('user_logged_in'):
        return redirect(url_for('user.login'))

    history = SearchHistory.query.filter_by(
        id=history_id,
        user_id=session.get('user_id')
    ).first()

    if not history:
        flash("Riwayat tidak ditemukan.", "danger")
        return redirect(url_for('user.index'))

    courses = Course.query.all()
    trends = Trend.query.all()
    competency_guides = MyTable.query.all()

    selected_competencies = (
        history.selected_competencies.split("|")
        if history.selected_competencies
        else []
    )

    results, selected_competencies, trend_insight = pipeline(
        courses,
        trends,
        competency_guides,
        history.profession,
        selected_competencies
    )

    user_data = {
        "username": session.get("username"),
        "email": session.get("email")
    }

    history_list = SearchHistory.query.filter_by(
        user_id=session.get('user_id')
    ).order_by(
        SearchHistory.created_at.desc()
    ).all()

    profesi_list = (
        db.session.query(MyTable.Profesi_Bidang_Usaha)
        .distinct()
        .order_by(MyTable.Profesi_Bidang_Usaha)
        .all()
    )

    profesi_list = [p[0] for p in profesi_list if p[0]]

    skill_reference = MyTable.query.all()

    return render_template(
    "user/dashboard.html",
    skill_reference=skill_reference,
    results=results,
    selected_competencies=selected_competencies,
    profession=history.profession,
    trend_insight=trend_insight,
    history=history_list,
    user=user_data,
    profesi_list=profesi_list,
    beta=BETA
)

# =========================
# DELETE HISTORY
# =========================
@user_bp.route("/history/delete/<int:history_id>", methods=["POST"])
def delete_history(history_id):

    if not session.get('user_logged_in'):
        return redirect(url_for('user.login'))

    history = SearchHistory.query.filter_by(
        id=history_id,
        user_id=session.get('user_id')
    ).first()

    if not history:
        flash("Riwayat tidak ditemukan.", "danger")
        return redirect(url_for('user.index'))

    db.session.delete(history)
    db.session.commit()

    flash("Riwayat berhasil dihapus.", "success")

    return redirect(url_for('user.dashboard'))