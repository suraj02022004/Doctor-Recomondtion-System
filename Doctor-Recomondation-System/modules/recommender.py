from __future__ import annotations

import csv
import random
from pathlib import Path
from typing import Dict, List


DEFAULT_DATA_PATH = Path(__file__).resolve().parent.parent / "data" / "doctors.csv"

SPECIALTY_KEYWORDS: Dict[str, List[str]] = {
    "Cardiologist": ["chest", "heart", "bp", "pressure", "palpitation"],
    "Dermatologist": ["skin", "rash", "acne", "itch", "allergy"],
    "Neurologist": ["headache", "migraine", "dizzy", "seizure", "nerve"],
    "Orthopedic Surgeon": ["joint", "bone", "knee", "back", "fracture"],
    "Pulmonologist": ["cough", "breath", "asthma", "lung", "wheezing"],
    "Endocrinologist": ["sugar", "diabetes", "thyroid", "hormone", "weight"],
    "General Physician": ["fever", "viral", "fatigue", "cold", "body pain"],
    "Dentist": ["tooth", "gum", "cavity", "oral", "dental"],
    "Pediatrician": ["child", "infant", "vaccination", "growth", "baby"],
    "Gynecologist": ["pregnancy", "menstrual", "pcos", "fertility", "women"],
    "ENT Specialist": ["ear", "throat", "sinus", "hearing", "tonsil"],
    "Gastroenterologist": ["stomach", "acidity", "liver", "constipation", "gastric"],
    "Psychiatrist": ["anxiety", "depression", "sleep", "panic", "stress"],
    "Ophthalmologist": ["eye", "vision", "cataract", "red eye", "dry eyes"],
    "Urologist": ["urine", "prostate", "bladder", "urinary", "stone"],
    "Nephrologist": ["kidney", "dialysis", "creatinine", "protein urine", "renal"],
    "Oncologist": ["cancer", "chemotherapy", "tumor", "biopsy", "screening"],
    "Rheumatologist": ["autoimmune", "swelling", "lupus", "rheumatoid", "inflammation"],
    "Hematologist": ["anemia", "blood", "platelets", "clotting", "thalassemia"],
    "Physiotherapist": ["rehabilitation", "muscle", "exercise", "mobility", "neck"],
}


def load_doctors(data_path: Path | None = None) -> List[Dict[str, str]]:
    path = data_path or DEFAULT_DATA_PATH
    if not path.exists():
        return []

    doctors: List[Dict[str, str]] = []
    with path.open(mode="r", encoding="utf-8", newline="") as file:
        reader = csv.DictReader(file)
        for row in reader:
            doctors.append(
                {
                    "name": row.get("name", "").strip(),
                    "specialty": row.get("specialty", "").strip(),
                    "location": row.get("location", "").strip(),
                    "experience": row.get("experience", "").strip(),
                    "rating": row.get("rating", "").strip(),
                    "focus": row.get("focus", "").strip(),
                    "hospital": row.get("hospital", "").strip(),
                    "qualification": row.get("qualification", "").strip(),
                    "languages": row.get("languages", "").strip(),
                    "consultation_fee": row.get("consultation_fee", "").strip(),
                    "availability": row.get("availability", "").strip(),
                    "about": row.get("about", "").strip(),
                }
            )
    return [doctor for doctor in doctors if doctor["name"] and doctor["specialty"]]


def score_doctors(
    doctors: List[Dict[str, str]],
    symptoms: str,
    medical_history: str,
    location: str,
    top_k: int = 3,
) -> List[Dict[str, str]]:
    text = f"{symptoms} {medical_history}".lower().strip()
    location_text = location.lower().strip()

    scored: List[Dict[str, str]] = []
    for doctor in doctors:
        specialty = doctor["specialty"]
        keywords = SPECIALTY_KEYWORDS.get(specialty, [])
        keyword_hits = sum(1 for word in keywords if word in text)
        location_bonus = 2 if location_text and location_text in doctor["location"].lower() else 0
        collaborative_signal = random.choice([0, 1])

        confidence = keyword_hits * 3 + location_bonus + collaborative_signal
        enriched = dict(doctor)
        enriched["score"] = str(confidence)
        scored.append(enriched)

    scored.sort(key=lambda item: int(item["score"]), reverse=True)
    return scored[:top_k]
