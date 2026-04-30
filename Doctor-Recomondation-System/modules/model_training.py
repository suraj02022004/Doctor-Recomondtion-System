from __future__ import annotations

import csv
import json
import math
import pickle
import re
from pathlib import Path

try:
    import joblib
    import pandas as pd
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.metrics import accuracy_score, classification_report
    from sklearn.pipeline import Pipeline
except ModuleNotFoundError:
    joblib = None
    pd = None
    TfidfVectorizer = None
    LogisticRegression = None
    accuracy_score = None
    classification_report = None
    Pipeline = None


ROOT_DIR = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT_DIR / "data" / "doctors.csv"
MODEL_PATH = ROOT_DIR / "models" / "specialty_model.joblib"
METADATA_PATH = ROOT_DIR / "models" / "specialty_model_metrics.json"


SPECIALTY_EXAMPLES = {
    "Cardiologist": [
        "chest pain heart palpitation high blood pressure hypertension",
        "breathlessness with chest discomfort irregular heartbeat",
    ],
    "Dermatologist": [
        "skin rash acne itching allergy eczema",
        "red patches dry skin pimples fungal infection",
    ],
    "Neurologist": [
        "migraine headache dizziness seizure nerve weakness",
        "numbness tremor memory issue severe headache",
    ],
    "Orthopedic Surgeon": [
        "joint pain knee pain back pain fracture bone injury",
        "arthritis shoulder pain sports injury swelling",
    ],
    "Pulmonologist": [
        "cough asthma breathing issue wheezing lung problem",
        "shortness of breath chronic cough chest congestion",
    ],
    "Endocrinologist": [
        "diabetes thyroid hormone weight gain sugar imbalance",
        "fatigue metabolic disorder insulin thyroid swelling",
    ],
    "General Physician": [
        "fever viral infection fatigue body pain cold",
        "general weakness cough fever routine illness",
    ],
    "Dentist": [
        "tooth pain oral care gum bleeding cavity",
        "dental pain teeth cleaning mouth infection",
    ],
    "Pediatrician": [
        "child fever vaccination infant cough growth check",
        "baby care pediatric illness school child infection",
    ],
    "Gynecologist": [
        "pregnancy care menstrual pain pcos fertility women health",
        "irregular periods pregnancy consultation pelvic pain",
    ],
    "ENT Specialist": [
        "ear pain throat infection sinus hearing issue tonsils",
        "blocked nose sore throat ear discharge voice problem",
    ],
    "Gastroenterologist": [
        "stomach pain acidity liver disease constipation gastritis",
        "abdominal pain digestion issue vomiting loose motion",
    ],
    "Psychiatrist": [
        "anxiety depression sleep disorder panic attack stress",
        "mood changes mental health insomnia fear sadness",
    ],
    "Ophthalmologist": [
        "eye pain blurred vision cataract red eye dry eyes",
        "vision loss eye infection watery eyes glasses check",
    ],
    "Urologist": [
        "urine infection kidney stone prostate bladder pain urinary issue",
        "burning urination frequent urine male urinary problem",
    ],
    "Nephrologist": [
        "kidney disease dialysis high creatinine kidney failure protein urine",
        "renal disease swelling reduced urine chronic kidney problem",
    ],
    "Oncologist": [
        "cancer care chemotherapy tumor biopsy cancer screening",
        "lump cancer treatment radiation oncology malignancy",
    ],
    "Rheumatologist": [
        "autoimmune disease joint swelling lupus rheumatoid arthritis inflammation",
        "chronic joint stiffness inflammatory arthritis immune disorder",
    ],
    "Hematologist": [
        "anemia blood disorder low platelets clotting issue thalassemia",
        "bleeding disorder blood cancer hemoglobin platelet problem",
    ],
    "Physiotherapist": [
        "rehabilitation muscle pain post surgery exercise mobility issue neck pain",
        "back therapy posture correction physiotherapy sports recovery",
    ],
}


class SimpleSpecialtyLogisticModel:
    def __init__(self, vocab: dict[str, int], classes: list[str], weights: list[list[float]], bias: list[float]):
        self.vocab = vocab
        self.classes = classes
        self.weights = weights
        self.bias = bias

    def predict(self, texts: list[str]) -> list[str]:
        return [self._predict_one(text) for text in texts]

    def _predict_one(self, text: str) -> str:
        features = _vectorize_text(text, self.vocab)
        scores = []
        for class_index, class_weights in enumerate(self.weights):
            score = self.bias[class_index]
            score += sum(class_weights[index] * value for index, value in features.items())
            scores.append(score)
        best_index = max(range(len(scores)), key=lambda index: scores[index])
        return self.classes[best_index]


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z]+", text.lower())


def _vectorize_text(text: str, vocab: dict[str, int]) -> dict[int, float]:
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts: dict[int, float] = {}
    for token in tokens:
        if token in vocab:
            counts[vocab[token]] = counts.get(vocab[token], 0.0) + 1.0
    total = float(sum(counts.values()) or 1.0)
    return {index: value / total for index, value in counts.items()}


def _read_doctor_rows() -> list[dict[str, str]]:
    with DATA_PATH.open("r", encoding="utf-8", newline="") as file:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(file)
        ]


def _build_training_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    required_cols = {"specialty", "focus"}
    columns = set(rows[0].keys()) if rows else set()
    missing = required_cols - columns
    if missing:
        raise ValueError(f"Missing required columns in doctors.csv: {sorted(missing)}")

    rows = [row for row in rows if row.get("specialty") and row.get("focus")]
    if not rows:
        raise ValueError("No training rows found in doctors.csv")

    text_columns = [
        column for column in ["focus", "about", "qualification", "specialty", "location", "hospital"]
        if column in columns
    ]
    training_rows = []
    for row in rows:
        specialty = str(row["specialty"]).strip()
        text = " ".join(str(row.get(column, "")) for column in text_columns)
        training_rows.append({"text": text, "specialty": specialty})
        for example in SPECIALTY_EXAMPLES.get(specialty, []):
            training_rows.append({"text": example, "specialty": specialty})
    return [
        row for row in training_rows
        if row["text"].strip() and row["specialty"].strip()
    ]


def _classification_report(y_true: list[str], y_pred: list[str], classes: list[str]) -> dict:
    report = {}
    for specialty in classes:
        tp = sum(1 for actual, pred in zip(y_true, y_pred) if actual == specialty and pred == specialty)
        fp = sum(1 for actual, pred in zip(y_true, y_pred) if actual != specialty and pred == specialty)
        fn = sum(1 for actual, pred in zip(y_true, y_pred) if actual == specialty and pred != specialty)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        report[specialty] = {"precision": precision, "recall": recall, "f1-score": f1}
    return report


def _train_simple_logistic_model(training_rows: list[dict[str, str]]) -> tuple[SimpleSpecialtyLogisticModel, dict]:
    classes = sorted({row["specialty"] for row in training_rows})
    if len(classes) < 2:
        raise ValueError("At least two specialties are required to train Logistic Regression.")

    vocab = sorted({token for row in training_rows for token in _tokenize(row["text"])})
    vocab_index = {token: index for index, token in enumerate(vocab)}
    class_index = {specialty: index for index, specialty in enumerate(classes)}
    weights = [[0.0 for _ in vocab] for _ in classes]
    bias = [0.0 for _ in classes]
    learning_rate = 0.8
    epochs = 320
    regularization = 0.0008

    vectors = [_vectorize_text(row["text"], vocab_index) for row in training_rows]
    labels = [class_index[row["specialty"]] for row in training_rows]

    for _ in range(epochs):
        for features, label in zip(vectors, labels):
            logits = []
            for c_idx, class_weights in enumerate(weights):
                logit = bias[c_idx] + sum(class_weights[f_idx] * value for f_idx, value in features.items())
                logits.append(logit)
            max_logit = max(logits)
            exps = [math.exp(logit - max_logit) for logit in logits]
            total = sum(exps)
            probs = [value / total for value in exps]
            for c_idx, prob in enumerate(probs):
                error = prob - (1.0 if c_idx == label else 0.0)
                bias[c_idx] -= learning_rate * error
                for f_idx, value in features.items():
                    weights[c_idx][f_idx] -= learning_rate * (error * value + regularization * weights[c_idx][f_idx])

    model = SimpleSpecialtyLogisticModel(vocab_index, classes, weights, bias)
    y_true = [row["specialty"] for row in training_rows]
    y_pred = model.predict([row["text"] for row in training_rows])
    train_acc = sum(1 for actual, pred in zip(y_true, y_pred) if actual == pred) / len(y_true)
    return model, {
        "train_accuracy": train_acc,
        "classification_report": _classification_report(y_true, y_pred, classes),
    }


def train_specialty_model() -> dict:
    doctor_rows = _read_doctor_rows()
    training_rows = _build_training_rows(doctor_rows)

    if Pipeline is not None:
        training_df = pd.DataFrame(training_rows)
        X = training_df["text"].astype(str)
        y = training_df["specialty"].astype(str)

        if training_df["specialty"].nunique() < 2:
            raise ValueError("At least two specialties are required to train Logistic Regression.")

        model = Pipeline(
            steps=[
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), lowercase=True)),
                (
                    "clf",
                    LogisticRegression(
                        max_iter=1000,
                        random_state=42,
                        class_weight="balanced",
                    ),
                ),
            ]
        )
        model.fit(X, y)
        train_pred = model.predict(X)
        train_acc = accuracy_score(y, train_pred)
        report = classification_report(y, train_pred, output_dict=True, zero_division=0)
        save_with = "joblib"
    else:
        model, simple_metrics = _train_simple_logistic_model(training_rows)
        train_acc = simple_metrics["train_accuracy"]
        report = simple_metrics["classification_report"]
        save_with = "pickle"

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    if joblib is not None:
        joblib.dump(model, MODEL_PATH)
    else:
        with MODEL_PATH.open("wb") as file:
            pickle.dump(model, file)

    classes = sorted({row["specialty"] for row in training_rows})
    metrics = {
        "algorithm": "TF-IDF + Logistic Regression" if Pipeline is not None else "Pure Python Logistic Regression",
        "source_dataset": str(DATA_PATH),
        "doctor_rows": int(len(doctor_rows)),
        "training_rows": int(len(training_rows)),
        "classes": int(len(classes)),
        "class_names": classes,
        "train_accuracy": float(train_acc),
        "classification_report": report,
        "model_path": str(MODEL_PATH),
        "saved_with": save_with,
    }
    METADATA_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


if __name__ == "__main__":
    metrics = train_specialty_model()
    print("Training complete.")
    print(f"Doctor Rows: {metrics['doctor_rows']}")
    print(f"Training Rows: {metrics['training_rows']}")
    print(f"Classes: {metrics['classes']}")
    print(f"Train Accuracy: {metrics['train_accuracy']:.4f}")
    print(f"Saved Model: {metrics['model_path']}")
