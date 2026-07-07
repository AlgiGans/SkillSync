# services/adaptive.py


# =========================================
# INTERNAL RELEVANCE
# =========================================
def get_internal_relevance(
    profile_similarity,
    competency_similarity
):
    """
    Internal Relevance

    (Profile Similarity +
     Competency Similarity) / 2
    """

    profile_similarity = float(profile_similarity or 0)
    competency_similarity = float(competency_similarity or 0)

    return (
        profile_similarity +
        competency_similarity
    ) / 2


# =========================================
# ADAPTIVE SCORE
# =========================================
def get_adaptive_score(
    profile_similarity,
    competency_similarity,
    trend_boost,
    beta
):
    """
    Adaptive Score

    Adaptive Score =
    Internal Relevance +
    β × Trend Boost
    """

    internal_relevance = get_internal_relevance(
        profile_similarity,
        competency_similarity
    )

    return (
        internal_relevance +
        (float(beta) * float(trend_boost or 0))
    )