# services/preprocessing.py

import re

# =========================================
# PREPROCESS CACHE
# =========================================
preprocess_cache = {}

# =========================================
# STOPWORDS
# =========================================
# Menghapus kata umum tanpa
# menghilangkan istilah teknis.

STOPWORDS = {

    # Kata umum
    "dan",
    "di",
    "ke",
    "dari",
    "yang",
    "untuk",
    "dengan",
    "pada",
    "adalah",

    # Kata yang sering muncul
    "saya",
    "ingin",
    "mau",
    "belajar",
    "memahami",
    "mempelajari",
    "tentang",
    "agar",
    "bisa",
    "menjadi",
    "sebagai",
    "lebih",
    "dalam",
    "bidang",
    "cara",
    "tutorial",
    "kursus",
    "kelas",

    # Tambahan
    "itu",
    "ini",
    "karena",
    "supaya",
    "buat",
    "nya"
}


# =========================================
# CASE FOLDING
# =========================================
def case_folding(text):

    return str(text).lower()


# =========================================
# CLEAN TEXT
# =========================================
def clean_text(text):

    # Hapus karakter selain huruf,
    # angka, dan spasi.

    text = re.sub(

        r"[^a-z0-9\s]",

        " ",

        text

    )

    # Hapus spasi berlebih

    text = re.sub(

        r"\s+",

        " ",

        text

    ).strip()

    return text


# =========================================
# TOKENIZATION
# =========================================
def tokenization(text):

    return text.split()


# =========================================
# STOPWORD REMOVAL
# =========================================
def stopword_removal(tokens):

    return [

        token

        for token in tokens

        if token not in STOPWORDS

        and len(token) > 1

    ]


# =========================================
# NORMALIZATION
# =========================================
def normalization(tokens):

    # Menghapus token duplikat
    # dengan tetap mempertahankan urutan.

    unique_tokens = list(

        dict.fromkeys(tokens)

    )

    return " ".join(

        unique_tokens

    )


# =========================================
# MAIN PREPROCESSING PIPELINE
# =========================================
def run_preprocessing_pipeline(text):

    original = str(text or "")

    # -------------------------------------
    # CACHE
    # -------------------------------------
    if original in preprocess_cache:
        return preprocess_cache[original]

    # -------------------------------------
    # Case Folding
    # -------------------------------------
    case_text = case_folding(

        original

    )

    # -------------------------------------
    # Cleaning
    # -------------------------------------
    clean = clean_text(

        case_text

    )

    # -------------------------------------
    # Tokenization
    # -------------------------------------
    tokens = tokenization(

        clean

    )

    # -------------------------------------
    # Stopword Removal
    # -------------------------------------
    filtered_tokens = stopword_removal(

        tokens

    )

    # -------------------------------------
    # Normalization
    # -------------------------------------
    normalized = normalization(

        filtered_tokens

    )

    result = {

        "original": original,

        "case_folding": case_text,

        "clean_text": clean,

        "tokens": tokens,

        "filtered_tokens": filtered_tokens,

        "normalization": normalized

    }

    preprocess_cache[original] = result

    return result