# services/pipeline.py

from config import (
    ALPHA,
    BETA,
    TOP_K,
    TOP_N
)

from services.preprocessing import (
    run_preprocessing_pipeline as preprocess
)

from services.embedding import (
    text_to_vector
)

from services.profile import (
    build_profile_text
)

from services.course import (
    build_course_text
)

from services.similarity import (
    get_similarity
)

from services.trend import (
    get_relevant_trends,
    get_trend_boost
)

from services.competency import (
    get_competency_similarity
)

from services.adaptive import (
    get_adaptive_score
)


# =====================================================
# MAIN PIPELINE
# =====================================================
def pipeline(
    courses,
    trends,
    competency_guides,
    profession,
    selected_competencies,
    alpha=None,
    beta=None
):
    
    if alpha is None:
        alpha = ALPHA

    if beta is None:
            beta = BETA
    # =====================================================
    # 1. BUILD USER PROFILE
    # =====================================================
    profile_raw = build_profile_text(
        profession,
        selected_competencies
    )

    profile_text = preprocess(
        profile_raw
    )["normalization"]

    if not profile_text.strip():
        return [], [], []

    # =====================================================
    # 2. PROFILE EMBEDDING
    # =====================================================
    profile_vector = text_to_vector(
        profile_text
    )

    # =====================================================
    # 3. PROFILE ↔ TREND
    # =====================================================
    relevant_trends = get_relevant_trends(
        trends,
        profile_vector,
        TOP_K
    )

    # =====================================================
    # 4. COURSE SCORING
    # =====================================================
    results = []

    for course in courses:

        # ---------------------------------------------
        # Course Representation
        # ---------------------------------------------
        course_text = build_course_text(course)

        if not course_text.strip():
            continue

        # ---------------------------------------------
        # Course Embedding
        # ---------------------------------------------
        course_vector = text_to_vector(
            course_text
        )

        # ---------------------------------------------
        # Profile ↔ Course Similarity
        # ---------------------------------------------
        profile_similarity = get_similarity(
            profile_vector,
            course_vector
        )

        # ---------------------------------------------
        # Competency Guide ↔ Course Similarity
        # ---------------------------------------------
        competency_similarity = get_competency_similarity(
            competency_guides,
            profession,
            course_vector
        )

        # ---------------------------------------------
        # Internal Relevance
        # ---------------------------------------------
        internal_relevance = (
            profile_similarity +
            competency_similarity
        ) / 2

        # ---------------------------------------------
        # Trend Boost
        # ---------------------------------------------
        trend_boost = get_trend_boost(
            relevant_trends,
            course_vector
        )

        # ---------------------------------------------
        # Adaptive Score
        # ---------------------------------------------
        adaptive_score = get_adaptive_score(
            profile_similarity,
            competency_similarity,
            trend_boost,
            BETA
        )

        # ---------------------------------------------
        # Store Result
        # ---------------------------------------------
        results.append({

            "course": course.course_name,

            "description": course.description,

            "skills": course.skills,

            "mitra": course.mitra,

            "url": getattr(
                course,
                "link",
                "#"
            ),

            "profile_similarity": round(
                profile_similarity,
                4
            ),

            "competency_similarity": round(
                competency_similarity,
                4
            ),

            "internal_relevance": round(
                internal_relevance,
                4
            ),

            "trend_boost": round(
                trend_boost,
                4
            ),

            "adaptive_score": round(
                adaptive_score,
                4
            ),

            # digunakan untuk proses ranking
            "score": round(
                adaptive_score,
                4
            )

        })

    # =====================================================
    # 5. RANKING
    # =====================================================
    results.sort(
        key=lambda item: item["adaptive_score"],
        reverse=True
    )

    results = results[:TOP_N]

    # =====================================================
    # 6. TREND INSIGHT
    # =====================================================
    trend_insight = []

    for item in relevant_trends:

        trend = item["trend_obj"]

        popularity = trend.value or 0

        if popularity >= 80:
            level = "Sangat Tinggi"
        elif popularity >= 60:
            level = "Tinggi"
        elif popularity >= 40:
            level = "Sedang"
        else:
            level = "Rendah"

        trend_insight.append({

            "skill": trend.keyword,

            "popularity": popularity,

            "similarity": round(
                item["similarity"],
                4
            ),

            "level": level

        })

    # =====================================================
    # OUTPUT
    # =====================================================
    return (
        results,
        selected_competencies,
        trend_insight
    )