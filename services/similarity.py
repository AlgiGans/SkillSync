import numpy as np


# =========================================
# EUCLIDEAN DISTANCE
# =========================================
def euclidean(v1, v2):
    """
    Menghitung jarak Euclidean antara dua vektor.
    Semakin kecil distance, semakin mirip kedua data.
    """

    return np.sqrt(
        np.sum((v1 - v2) ** 2)
    )


# =========================================
# DISTANCE → SIMILARITY
# =========================================
def distance_to_similarity(distance):
    """
    Mengubah nilai distance menjadi similarity.

    Similarity = 1 / (1 + Distance)

    Range:
    0 < similarity <= 1

    Distance = 0
    → Similarity = 1

    Semakin besar distance,
    similarity akan semakin mendekati 0.
    """

    return 1 / (1 + distance)


# =========================================
# PROFILE ↔ COURSE SIMILARITY
# =========================================
def get_similarity(vector1, vector2):
    """
    Menghitung similarity antar dua vektor.

    Langkah:
    1. Euclidean Distance
    2. Distance → Similarity
    """

    distance = euclidean(
        vector1,
        vector2
    )

    similarity = distance_to_similarity(
        distance
    )

    return similarity