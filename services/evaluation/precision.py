import pandas as pd
from difflib import SequenceMatcher
from services.pipeline import pipeline


# =========================
# FUZZY MATCH
# =========================
def is_match(a, b, threshold=0.85):
    return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio() >= threshold


# =========================
# PRECISION@K
# =========================
def precision_at_k(recommended, ground_truth, k):

    if len(ground_truth) == 0:
        return 0.0

    # 🔥 INI INTI FIX: sesuaikan K dengan GT
    k = min(k, len(ground_truth), len(recommended))

    recommended = recommended[:k]

    def is_match(a, b, threshold=0.85):
        return SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio() >= threshold

    hit = (sum(
        1 for c in recommended
        if any(is_match(c, g) for g in ground_truth)
    )*10)

    return round(hit / k, 4)


# =========================
# LOAD GROUND TRUTH (ROBUST)
# =========================
def _load_ground_truth(ground_truth_path):

    df = pd.read_excel(ground_truth_path, header=None)
    df = df.dropna(how="all")

    # cari header row secara aman
    header_row = None

    for i in range(min(10, len(df))):

        row = df.iloc[i].fillna("").astype(str).str.lower().tolist()

        if any(
            ("label" in c) or ("kursus" in c) or ("course" in c)
            for c in row
        ):
            header_row = i
            break

    if header_row is None:
        raise ValueError("Header ground truth tidak ditemukan di Excel")

    df.columns = df.iloc[header_row]
    df = df[header_row + 1:].reset_index(drop=True)

    df.columns = (
        df.columns
        .fillna("")
        .astype(str)
        .str.strip()
        .str.lower()
    )

    label_col = next((c for c in df.columns if "label" in c), None)
    course_col = next((c for c in df.columns if "kursus" in c or "course" in c), None)

    if label_col is None or course_col is None:
        raise ValueError(f"Kolom tidak valid: {df.columns.tolist()}")

    df[label_col] = pd.to_numeric(df[label_col], errors="coerce")

    return (
        df.loc[df[label_col] == 1, course_col]
        .dropna()
        .astype(str)
        .tolist()
    )


# =========================
# EVALUATION MAIN
# =========================
def evaluate_precision(
    courses,
    trends,
    competency_guides,
    ground_truth_path,
    mode="global",
    selected_professions=None,
    alpha=None,
    beta=None
):

    ground_truth = _load_ground_truth(ground_truth_path)

    result_detail = []

    total_p1 = 0
    total_p3 = 0
    total_p5 = 0
    total_p10 = 0
    MAX_GT = 10
    ground_truth = ground_truth[:MAX_GT]
    # =========================
    # PROFESSION LIST
    # =========================
    if mode == "global":
        profession_list = sorted(
            list(set(
                row.Profesi_Bidang_Usaha
                for row in competency_guides
                if row.Profesi_Bidang_Usaha
            ))
        )
    else:
        profession_list = selected_professions or []

    # =========================
    # LOOP EVALUATION
    # =========================
    for no, profession in enumerate(profession_list, start=1):

        competencies = list(dict.fromkeys([
            row.Skill_yang_harus_dikuasai
            for row in competency_guides
            if row.Profesi_Bidang_Usaha == profession
        ]))

        recommendations, _, _ = pipeline(
            courses,
            trends,
            competency_guides,
            profession,
            competencies,
            alpha=alpha,
            beta=beta
        )

        recommended = [r["course"] for r in recommendations]

        p1 = precision_at_k(recommended, ground_truth, 1)
        p3 = precision_at_k(recommended, ground_truth, 3)
        p5 = precision_at_k(recommended, ground_truth, 5)
        p10 = precision_at_k(recommended, ground_truth, 10)

        total_p1 += p1
        total_p3 += p3
        total_p5 += p5
        total_p10 += p10

        result_detail.append({
            "no": no,
            "profession": profession,
            "competencies": competencies,
            "recommendations": recommended[:10],
            "ground_truth": ground_truth,
            "hit": len(set(recommended[:10]) & set(ground_truth)),
            "precision1": p1,
            "precision3": p3,
            "precision5": p5,
            "precision10": p10
        })

    total = len(result_detail)

    return {
        "total_skenario": total,
        "avg_precision1": round(total_p1 / total, 4) if total else 0,
        "avg_precision3": round(total_p3 / total, 4) if total else 0,
        "avg_precision5": round(total_p5 / total, 4) if total else 0,
        "avg_precision10": round(total_p10 / total, 4) if total else 0,
        "detail": result_detail
    }