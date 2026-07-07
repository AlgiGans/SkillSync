# services/trend.py

from config import ALPHA

from services.embedding import (
    text_to_vector
)

from services.similarity import (
    get_similarity
)


# =========================================
# PROFILE ↔ TREND
# =========================================
def get_relevant_trends(
    trends,
    profile_vector,
    top_k
):
    """
    Mengambil Top-K trend
    yang paling relevan
    terhadap profil pengguna.
    """

    if profile_vector is None:
        return []

    scored_trends = []

    for trend in trends:

        keyword = str(
            trend.keyword or ""
        ).strip()

        if not keyword:
            continue

        trend_vector = text_to_vector(
            keyword
        )

        similarity = get_similarity(
            profile_vector,
            trend_vector
        )

        scored_trends.append({

            "trend_obj": trend,

            "keyword": keyword,

            "similarity": similarity

        })

    scored_trends.sort(

        key=lambda x: x["similarity"],

        reverse=True

    )

    return scored_trends[:top_k]


# =========================================
# TREND BOOST
# =========================================
def get_trend_boost(
    relevant_trends,
    course_vector
):
    """
    Trend Boost

    α × Sim(Trend, Course)
    +
    (1-α) × Popularity
    """

    if course_vector is None:
        return 0

    boosts = []

    for item in relevant_trends:

        trend = item["trend_obj"]

        keyword = str(
            trend.keyword or ""
        ).strip()

        if not keyword:
            continue

        trend_vector = text_to_vector(
            keyword
        )

        trend_similarity = get_similarity(
            trend_vector,
            course_vector
        )

        popularity = float(
            trend.value or 0
        ) / 100

        trend_boost = (

            ALPHA *
            trend_similarity

            +

            (1 - ALPHA) *
            popularity

        )

        boosts.append(trend_boost)

    if not boosts:
        return 0

    return max(boosts)