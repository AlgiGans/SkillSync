import os

from flask import Flask

from werkzeug.security import generate_password_hash

from config import *

from models import (
    db,
    User,
    Course,
    Trend,
    SearchHistory,
    MyTable
)

from services.preprocessing import (
    run_preprocessing_pipeline as preprocess
)

from services.embedding import (
    load_or_train
)

from routes.user import user_bp
from routes.admin import admin_bp


app = Flask(__name__)

app.secret_key = "skripsi_rahasia_123"


# =====================================================
# DATABASE CONFIGURATION
# =====================================================
import os

import os

app.config["SQLALCHEMY_DATABASE_URI"] = (
    f"mysql+pymysql://"
    f"{os.getenv('MYSQLUSER')}:"
    f"{os.getenv('MYSQLPASSWORD')}@"
    f"{os.getenv('MYSQLHOST')}:"
    f"{os.getenv('MYSQLPORT')}/"
    f"{os.getenv('MYSQLDATABASE')}"
)

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False



db.init_app(app)



# =====================================================
# FASTTEXT INITIALIZATION
# =====================================================
def initialize_ai_model():

    """
    Training FastText menggunakan
    seluruh dataset sistem.
    """

    try:

        courses = Course.query.all()

        trends = Trend.query.all()

        competency_guides = MyTable.query.all()

        if not courses:

            print("⚠️ Course database kosong")

            return

        print(
            f"🧠 Training FastText dengan {len(courses)} course..."
        )

        sentences = []

        # =================================================
        # COURSE DATASET
        # =================================================
        for c in courses:

            text = f"""
            {c.course_name or ""}
            {c.description or ""}
            {c.skills or ""}
            """

            processed = preprocess(text)

            tokens = processed["filtered_tokens"]

            if tokens:

                sentences.append(tokens)

        # =================================================
        # GOOGLE TRENDS
        # =================================================
        for t in trends:

            text = f"""
            {t.keyword or ""}
            """

            processed = preprocess(text)

            tokens = processed["filtered_tokens"]

            if tokens:

                sentences.append(tokens)

        # =================================================
        # COMPETENCY GUIDE
        # =================================================
        for item in competency_guides:

            text = f"""
            {item.Profesi_Bidang_Usaha or ""}
            {item.Skill_yang_harus_dikuasai or ""}
            {item.Detail_Item or ""}
            {item.Level or ""}
            """

            processed = preprocess(text)

            tokens = processed["filtered_tokens"]

            if tokens:

                sentences.append(tokens)

        # =================================================
        # TRAIN / LOAD MODEL
        # =================================================
        if sentences:

            load_or_train(sentences)

            print("✅ FastText Model Ready!")

        else:

            print("⚠️ Corpus kosong.")

    except Exception as e:

        print(f"❌ Error training FastText : {e}")


# =====================================================
# INITIALIZE DATABASE
# =====================================================
with app.app_context():

    db.create_all()

    print(
        "✅ Database SkillSync Connected!"
    )

    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":

        initialize_ai_model()


# =====================================================
# REGISTER BLUEPRINT
# =====================================================
app.register_blueprint(user_bp)

app.register_blueprint(

    admin_bp,

    url_prefix="/admin"

)


# =====================================================
# ERROR HANDLER
# =====================================================
@app.errorhandler(404)
def page_not_found(e):

    return (

        "Halaman tidak ditemukan. "
        "Kembali ke <a href='/'>Dashboard</a>",

        404

    )


# =====================================================
# RUN
# =====================================================
if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8080)),
        debug=False
    )