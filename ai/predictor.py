import re

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


CATEGORIES = {
    "Roads": [
        "pothole",
        "road",
        "street",
        "traffic",
        "footpath",
        "sidewalk"
    ],
    "Water": [
        "water",
        "leakage",
        "pipeline",
        "pipe",
        "flood"
    ],
    "Sanitation": [
        "garbage",
        "waste",
        "trash",
        "dump",
        "dirty"
    ],
    "Streetlight": [
        "streetlight",
        "street light",
        "lamp",
        "light"
    ],
    "Public Safety": [
        "manhole",
        "accident",
        "danger",
        "unsafe",
        "fire",
        "school",
        "hazard"
    ],
    "Electricity": [
        "electricity",
        "power",
        "electric",
        "wire"
    ]
}


URGENCY_KEYWORDS = {
    "Critical": [
        "danger",
        "dangerous",
        "emergency",
        "open manhole",
        "fire",
        "accident",
        "life threatening"
    ],

    "High": [
        "urgent",
        "serious",
        "major",
        "immediate",
        "risk",
        "large pothole",
        "huge pothole",
        "children",
        "school"
    ],

    "Medium": [
        "problem",
        "broken",
        "leak",
        "leakage",
        "damaged",
        "five days",
        "several days",
        "many days",
        "not collected"
    ]
}


def clean_text(text):
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text
def calculate_similarity(text1, text2):
    text1 = clean_text(text1)
    text2 = clean_text(text2)

    vectorizer = TfidfVectorizer()

    vectors = vectorizer.fit_transform([text1, text2])

    similarity = cosine_similarity(vectors[0:1], vectors[1:2])[0][0]

    return round(float(similarity), 2)

def calculate_credibility(description, location=None, has_evidence=False):
    score = 50
    description = clean_text(description)
    word_count = len(description.split())

    # More detailed descriptions are easier to verify
    if word_count >= 15:
        score += 15
    elif word_count >= 8:
        score += 10
    elif word_count < 4:
        score -= 15

    # Location helps administrators verify the complaint
    if location:
        score += 15

    # Evidence such as an uploaded image increases verification confidence
    if has_evidence:
        score += 10

    score = max(0, min(score, 100))

    if score >= 75:
        verification = "High"
    elif score >= 50:
        verification = "Medium"
    else:
        verification = "Needs Review"

    return score, verification
def predict_category(text):
    text = clean_text(text)

    scores = {}

    for category, keywords in CATEGORIES.items():
        score = 0

        for keyword in keywords:
            if keyword in text:
                score += 1

        scores[category] = score

    best_category = max(scores, key=scores.get)

    if scores[best_category] == 0:
        return "Other"

    return best_category


def predict_urgency(text):
    text = clean_text(text)

    for urgency, keywords in URGENCY_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text:
                return urgency

    return "Low"


def calculate_priority(urgency, category):
    urgency_score = {
        "Critical": 90,
        "High": 70,
        "Medium": 50,
        "Low": 25
    }

    category_bonus = {
        "Public Safety": 8,
        "Water": 5,
        "Electricity": 5,
        "Roads": 4,
        "Sanitation": 3,
        "Streetlight": 2,
        "Other": 0
    }

    score = urgency_score.get(urgency, 25)
    score += category_bonus.get(category, 0)

    return min(score, 100)


def analyze_complaint(
    description,
    location=None,
    has_evidence=False,
    previous_complaints=None
):
    # 1. Predict category
    category = predict_category(description)

    # 2. Predict urgency
    urgency = predict_urgency(description)

    # 3. Calculate priority
    priority = calculate_priority(urgency, category)

    # 4. Calculate credibility
    credibility, verification = calculate_credibility(
    description,
    location,
    has_evidence
)

    # 5. Check for duplicates
    duplicate = False
    duplicate_similarity = 0.0
    duplicate_message = "No similar complaint found"

    if previous_complaints:
        for old_complaint in previous_complaints:
            similarity = calculate_similarity(
                description,
                old_complaint
            )

            if similarity >= 0.5:
                duplicate = True
                duplicate_similarity = similarity
                duplicate_message = "Similar complaint detected"
                break

    # Final AI result
    return {
    "category": category,
    "urgency": urgency,
    "priority": priority,
    "credibility": credibility,
    "verification": verification,
    "duplicate": duplicate,
    "duplicate_similarity": duplicate_similarity,
    "duplicate_message": duplicate_message
}
    return {
        "category": category,
        "urgency": urgency,
        "priority": priority,
        "credibility": credibility,
        "verification": verification,
        "duplicate": duplicate,
        "duplicate_similarity": duplicate_similarity,
        "duplicate_message": duplicate_message
    }