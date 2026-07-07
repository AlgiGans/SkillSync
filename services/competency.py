from services.preprocessing import (
    run_preprocessing_pipeline as preprocess
)

from services.embedding import (
    text_to_vector
)

from services.similarity import (
    get_similarity
)


# ===========================================
# BUILD COMPETENCY TEXT
# ===========================================
def build_competency_text(item):

    return " ".join(filter(None, [

        item.Profesi_Bidang_Usaha or "",

        item.Skill_yang_harus_dikuasai or "",

        item.Detail_Item or "",

        item.Level or ""

    ]))


# ===========================================
# COMPETENCY ↔ COURSE
# ===========================================
def get_competency_similarity(
    competency_guides,
    profession,
    course_vector
):

    if course_vector is None:
        return 0

    competency_documents = []

    for item in competency_guides:

        if (
            (item.Profesi_Bidang_Usaha or "")
            .strip()
            .lower()
            != profession.strip().lower()
        ):
            continue

        competency_documents.append(
            build_competency_text(item)
        )

    if not competency_documents:
        return 0

    competency_text = " ".join(
        competency_documents
    )

    competency_text = preprocess(
        competency_text
    )["normalization"]

    if not competency_text:
        return 0

    competency_vector = text_to_vector(
        competency_text
    )

    return get_similarity(
        competency_vector,
        course_vector
    )