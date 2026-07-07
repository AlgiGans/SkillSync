# services/level_weight.py


# =========================================
# NORMALISASI LEVEL
# =========================================
def normalize_level(level_text):

    if not level_text:
        return "beginner"

    level = str(level_text).lower().strip()

    # =====================================
    # BEGINNER
    # =====================================
    beginner_keywords = [
        "beginner",
        "pemula",
        "dasar",
        "fundamental"
    ]

    # =====================================
    # INTERMEDIATE
    # =====================================
    intermediate_keywords = [
        "intermediate",
        "menengah"
    ]

    # =====================================
    # ADVANCED
    # =====================================
    advanced_keywords = [
        "advanced",
        "mahir",
        "expert"
    ]

    # =====================================
    # DETEKSI LEVEL
    # =====================================
    if any(k in level for k in beginner_keywords):
        return "beginner"

    if any(k in level for k in intermediate_keywords):
        return "intermediate"

    if any(k in level for k in advanced_keywords):
        return "advanced"

    # default
    return "beginner"


# =========================================
# LEVEL WEIGHT MATRIX
# =========================================
DEFAULT_WEIGHTS = {

    ("beginner", "beginner"): 1.00,
    ("beginner", "intermediate"): 0.75,
    ("beginner", "advanced"): 0.45,

    ("intermediate", "beginner"): 0.85,
    ("intermediate", "intermediate"): 1.00,
    ("intermediate", "advanced"): 0.80,

    ("advanced", "beginner"): 0.60,
    ("advanced", "intermediate"): 0.85,
    ("advanced", "advanced"): 1.00
}


# =========================================
# GET LEVEL WEIGHT
# =========================================
def get_level_weight(user_level, course_level):

    user_level = normalize_level(user_level)
    course_level = normalize_level(course_level)

    return DEFAULT_WEIGHTS.get(
        (user_level, course_level),
        1.0
    )