# services/embedding.py

import os
import numpy as np
from gensim.models import FastText

from config import (
    BASE_DIR,
    FASTTEXT_VECTOR_SIZE
)

# =========================================
# MODEL PATH
# =========================================
MODEL_DIR = os.path.join(
    BASE_DIR,
    "models"
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "fasttext_model.model"
)

model = None

# =========================================
# VECTOR CACHE
# =========================================
vector_cache = {}


# =========================================
# LOAD ATAU TRAIN MODEL
# =========================================
def load_or_train(sentences):

    global model
    if model is not None:
        return

    os.makedirs(
        MODEL_DIR,
        exist_ok=True
    )

    # ==============================
    # LOAD MODEL
    # ==============================
    if os.path.exists(MODEL_PATH):

        try:

            model = FastText.load(
                MODEL_PATH
            )

            print("✅ FastText model loaded")

            return

        except Exception as e:

            print(
                f"❌ Gagal load model : {e}"
            )

    # ==============================
    # TRAIN MODEL BARU
    # ==============================
    print("🧠 Training FastText...")

    model = FastText(

        sentences=sentences,

        vector_size=FASTTEXT_VECTOR_SIZE,

        window=5,

        min_count=1,

        workers=4,

        sg=1

    )

    model.save(MODEL_PATH)

    print("✅ FastText model saved")


# =========================================
# TEXT → VECTOR
# =========================================
def text_to_vector(text):

    global model
    global vector_cache

    if model is None:
        return np.zeros(
            FASTTEXT_VECTOR_SIZE,
            dtype=np.float32
        )

    if text is None:
        return np.zeros(
            model.vector_size,
            dtype=np.float32
        )

    text = str(text).strip().lower()

    if text in vector_cache:
        return vector_cache[text]

    words = [
        w.strip()
        for w in text.split()
        if w.strip()
    ]

    vectors = []

    for word in words:

        try:
            vectors.append(model.wv[word])

        except KeyError:
            continue

    if vectors:

        vector = np.mean(
            vectors,
            axis=0
        )

    else:

        vector = np.zeros(
            model.vector_size,
            dtype=np.float32
        )

    vector_cache[text] = vector

    return vector
