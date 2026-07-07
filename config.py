import os

# =========================================
# BASE DIRECTORY
# =========================================
BASE_DIR = os.path.dirname(
    os.path.abspath(__file__)
)

# =========================================
# FASTTEXT
# =========================================
FASTTEXT_VECTOR_SIZE = 100

# =========================================
# RECOMMENDATION PARAMETERS
# =========================================

# Trend Boost
# TrendBoost =
# α × SemanticSimilarity +
# (1-α) × Popularity
ALPHA = 0.6

# Adaptive Score
# AdaptiveScore =
# InternalRelevance +
# β × TrendBoost
BETA = 0.4

# Jumlah trend yang dipilih
TOP_K = 5

# Jumlah rekomendasi course
TOP_N = 5