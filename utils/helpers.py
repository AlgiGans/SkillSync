def extract_skills(text):
    # versi sederhana (bisa kamu upgrade pakai NLP nanti)
    keywords = text.split()
    return list(set(keywords))