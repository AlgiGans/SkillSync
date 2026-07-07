# services/course.py

from services.preprocessing import (
    run_preprocessing_pipeline as preprocess
)

# ===========================================
# BUILD COURSE REPRESENTATION
# ===========================================
def build_course_text(course):
    """
    Membangun representasi teks course.

    Representasi terdiri dari:
    - Nama Course
    - Skills
    - Description

    Seluruh teks diproses menggunakan
    preprocessing pipeline sehingga
    konsisten dengan representasi
    profile, competency, dan trend.
    """

    course_name = (
        course.course_name or ""
    ).strip()

    skills = (
        course.skills or ""
    ).strip()

    description = (
        course.description or ""
    ).strip()

    raw_text = " ".join(
        filter(
            None,
            [
                course_name,
                skills,
                description
            ]
        )
    )

    processed = preprocess(raw_text)

    return processed["normalization"]