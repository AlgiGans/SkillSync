# services/profile.py


# ===========================================
# BUILD USER PROFILE REPRESENTATION
# ===========================================
def build_profile_text(
    profession,
    selected_competencies
):
    """
    Membangun representasi teks profil pengguna.

    Input:
    - profession
    - selected_competencies

    Output:
    String mentah yang nantinya akan diproses
    pada tahap preprocessing di pipeline.
    """

    profession = profession or ""

    competency_text = " ".join(
        selected_competencies or []
    )

    profile_text = " ".join(
        filter(
            None,
            [
                profession,
                competency_text
            ]
        )
    )

    return profile_text