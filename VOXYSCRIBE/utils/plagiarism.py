from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

def compute_similarity(text1, text2):
    texts = [text1 or "", text2 or ""]
    vectorizer = TfidfVectorizer().fit_transform(texts)
    if vectorizer.shape[0] < 2:
        return 0.0
    sim = cosine_similarity(vectorizer[0:1], vectorizer[1:2])[0][0]
    return float(sim)

def check_against_batch(target_text, list_of_texts):
    if not list_of_texts:
        return {"max_score": 0.0, "index": -1}
    scores = [compute_similarity(target_text, t) for t in list_of_texts]
    max_idx = int(np.argmax(scores))
    return {"max_score": float(scores[max_idx]), "index": max_idx}

def grade_plagiarism(score):
    return "copied" if score > 0.5 else "unique"

# Example:
# compute_similarity("hello world","hello") -> 0.x
