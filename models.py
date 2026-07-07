from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# TABEL USER (Harus ada karena dipanggil di app.py)
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), default='Regular User')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# TABEL COURSE (Berdasarkan Dicoding.xlsx)
class Course(db.Model):
    __tablename__ = 'course'
    id = db.Column(db.Integer, primary_key=True)
    link = db.Column(db.String(255))
    course_name = db.Column(db.String(255), nullable=False) 
    kategori = db.Column(db.String(100))
    skills = db.Column(db.Text)
    description = db.Column(db.Text) 
    harga = db.Column(db.String(50))
    pendaftar = db.Column(db.String(50))
    durasi = db.Column(db.String(50))
    rating = db.Column(db.String(10))
    level = db.Column(db.String(50))
    mitra = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # runtime only
    embedding = None

# TABEL TREND (Berdasarkan Google Trends CSV)
class Trend(db.Model):
    __tablename__ = 'trend'
    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(255), nullable=False)  # ✅ FIX
    value = db.Column(db.Integer)
    increase_percent = db.Column(db.String(50))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow)

        # runtime only
    embedding = None

# =========================
# SEARCH HISTORY
# =========================
class SearchHistory(db.Model):
    __tablename__ = 'search_history'

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('user.id'),
        nullable=False
    )

    profession = db.Column(
        db.String(255),
        nullable=False
    )

    selected_competencies = db.Column(
        db.Text,
        nullable=False
    )

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # relasi user
    user = db.relationship(
        'User',
        backref='histories'
    )


    # =========================
# TABEL MYTABLE
# =========================
class MyTable(db.Model):
    __tablename__ = 'mytable'

    No = db.Column(db.Float, primary_key=True)

    Profesi_Bidang_Usaha = db.Column(
        db.String(1024)
    )

    Skill_yang_harus_dikuasai = db.Column(
        db.String(1024)
    )

    Detail_Item = db.Column(
        db.String(1024)
    )

    Level = db.Column(
        db.String(255)
    )

        # runtime only
    embedding = None