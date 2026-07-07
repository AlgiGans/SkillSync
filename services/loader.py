import pandas as pd
import os

def load_courses(path):
    if not os.path.exists(path):
        raise FileNotFoundError(f"File course tidak ditemukan: {path}")

    df = pd.read_excel(path)

    # 🔥 1. NORMALISASI KOLOM
    df.columns = df.columns.str.lower().str.strip()

    # 🔥 2. MAPPING KOLOM (sesuai file kamu)
    df.rename(columns={
        'nama_course': 'course_name',
        'deskripsi': 'description',
        'skill': 'skills',
        'level': 'level'
    }, inplace=True)

    # 🔥 3. HANDLE NULL
    df.fillna("", inplace=True)

    # 🔥 4. VALIDASI KOLOM PENTING
    required_cols = ['course_name', 'description', 'skills']
    for col in required_cols:
        if col not in df.columns:
            raise Exception(f"Kolom {col} tidak ditemukan. Kolom tersedia: {df.columns.tolist()}")

    print("✅ Dataset course siap:", df.shape)

    return df


def load_trends(path):
    df = pd.read_csv(path)

    # rename kolom biar konsisten
    df.rename(columns={
        "search interest": "value",
        "increase percent": "growth"
    }, inplace=True)

    # bersihkan value
    df["value"] = pd.to_numeric(df["value"], errors="coerce")

    # handle growth (optional)
    df["growth"] = df["growth"].astype(str)
    df["growth"] = df["growth"].str.replace("%", "", regex=False)
    df["growth"] = df["growth"].replace("Breakout", "100")
    df["growth"] = pd.to_numeric(df["growth"], errors="coerce")

    df.fillna(0, inplace=True)

    print("📊 Trend setelah cleaning:")
    print(df.head())

    return df