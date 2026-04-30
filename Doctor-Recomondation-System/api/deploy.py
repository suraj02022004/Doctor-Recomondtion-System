from __future__ import annotations

import csv
import json
import os
import pickle
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import List

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from modules.recommender import load_doctors, score_doctors

try:
    import joblib
except ModuleNotFoundError:
    joblib = None


class RecommendationRequest(BaseModel):
    patient_name: str = Field(default="", description="Patient full name")
    age: int = Field(default=0, ge=0, le=120)
    gender: str = Field(default="")
    phone: str = Field(default="")
    email: str = Field(default="")
    consultation_type: str = Field(default="")
    insurance_provider: str = Field(default="")
    existing_conditions: List[str] = Field(default_factory=list)
    symptoms: str = Field(min_length=3, description="Patient symptoms in free text")
    medical_history: str = Field(default="", description="Patient medical history")
    location: str = Field(default="", description="Preferred city/location")
    top_k: int = Field(default=3, ge=1, le=10)


class DoctorRecommendation(BaseModel):
    name: str
    specialty: str
    location: str
    experience: str
    rating: str
    focus: str
    hospital: str = ""
    qualification: str = ""
    languages: str = ""
    consultation_fee: str = ""
    availability: str = ""
    about: str = ""
    score: str


class RecommendationResponse(BaseModel):
    recommendations: List[DoctorRecommendation]
    total_candidates: int
    predicted_specialty: str


class PatientsResponse(BaseModel):
    records: List[dict]
    total: int


class DoctorCreateRequest(BaseModel):
    admin_token: str = Field(min_length=1)
    name: str = Field(min_length=2)
    specialty: str = Field(min_length=2)
    location: str = Field(min_length=2)
    experience: str = Field(default="")
    rating: str = Field(default="4.5")
    focus: str = Field(min_length=3)
    hospital: str = Field(default="")
    qualification: str = Field(default="")
    languages: str = Field(default="")
    consultation_fee: str = Field(default="")
    availability: str = Field(default="")
    about: str = Field(default="")


class DoctorCreateResponse(BaseModel):
    message: str
    doctor: dict


class DoctorFeedbackRequest(BaseModel):
    doctor_name: str = Field(min_length=2)
    rating: int = Field(ge=1, le=5)
    visit_type: str = Field(default="")
    comments: str = Field(min_length=3)


class DoctorFeedbackResponse(BaseModel):
    message: str
    feedback: dict


class FeedbackListResponse(BaseModel):
    records: List[dict]
    total: int


class AppointmentCreateRequest(BaseModel):
    patient_name: str = Field(min_length=1)
    phone: str = Field(default="")
    email: str = Field(default="")
    doctor_name: str = Field(min_length=2)
    specialty: str = Field(default="")
    location: str = Field(default="")
    consultation_type: str = Field(default="In-person")
    preferred_date: str = Field(default="")
    preferred_time: str = Field(default="")
    reason: str = Field(default="")


class AppointmentCreateResponse(BaseModel):
    message: str
    appointment: dict


class AppointmentListResponse(BaseModel):
    records: List[dict]
    total: int


class ModelTrainResponse(BaseModel):
    message: str
    metrics: dict


class ModelStatusResponse(BaseModel):
    model_exists: bool
    model_path: str
    metrics: dict | None = None


app = FastAPI(
    title="Doctor Recommendation Backend",
    description="Backend API for ML-inspired doctor recommendation system",
    version="1.0.0",
)

MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "specialty_model.joblib"
MODEL_METADATA_PATH = Path(__file__).resolve().parent.parent / "models" / "specialty_model_metrics.json"
PATIENTS_PATH = Path(__file__).resolve().parent.parent / "data" / "patients.csv"
DOCTORS_PATH = Path(__file__).resolve().parent.parent / "data" / "doctors.csv"
DATABASE_PATH = Path(__file__).resolve().parent.parent / "data" / "doctor_recommendation.db"
def _load_specialty_model():
    if not MODEL_PATH.exists():
        return None
    if joblib is not None:
        try:
            return joblib.load(MODEL_PATH)
        except Exception:
            pass
    try:
        with MODEL_PATH.open("rb") as file:
            return pickle.load(file)
    except Exception:
        return None


SPECIALTY_MODEL = _load_specialty_model()
# Set ADMIN_TOKEN in environment for production; fallback keeps local dev working.
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin123")


def _connect_db() -> sqlite3.Connection:
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def _init_database() -> None:
    with _connect_db() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS patients (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL DEFAULT '',
                age INTEGER NOT NULL DEFAULT 0,
                gender TEXT NOT NULL DEFAULT '',
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                consultation_type TEXT NOT NULL DEFAULT '',
                insurance_provider TEXT NOT NULL DEFAULT '',
                existing_conditions TEXT NOT NULL DEFAULT '',
                symptoms TEXT NOT NULL,
                medical_history TEXT NOT NULL DEFAULT '',
                preferred_location TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS doctor_feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                doctor_name TEXT NOT NULL,
                rating INTEGER NOT NULL,
                visit_type TEXT NOT NULL DEFAULT '',
                comments TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                patient_name TEXT NOT NULL,
                phone TEXT NOT NULL DEFAULT '',
                email TEXT NOT NULL DEFAULT '',
                doctor_name TEXT NOT NULL,
                specialty TEXT NOT NULL DEFAULT '',
                location TEXT NOT NULL DEFAULT '',
                consultation_type TEXT NOT NULL DEFAULT '',
                preferred_date TEXT NOT NULL DEFAULT '',
                preferred_time TEXT NOT NULL DEFAULT '',
                reason TEXT NOT NULL DEFAULT '',
                status TEXT NOT NULL DEFAULT 'Requested',
                created_at TEXT NOT NULL
            )
            """
        )


_init_database()


@app.get("/")
def home() -> dict:
    return {
        "message": "Doctor Recommendation Backend is running",
        "available_routes": {
            "health": "/health",
            "api_docs": "/docs",
            "train_logistic_regression": "POST /model/train",
            "model_status": "GET /model/status",
            "recommendations": "POST /recommend",
            "doctor_feedback": "POST /feedback and GET /feedback",
            "appointments": "POST /appointments and GET /appointments",
            "database_file": str(DATABASE_PATH),
            "patients": "GET /patients",
            "admin_add_doctor": "POST /admin/doctors",
        },
    }


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/model/train", response_model=ModelTrainResponse)
def train_model() -> ModelTrainResponse:
    global SPECIALTY_MODEL
    try:
        from modules.model_training import train_specialty_model
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=500,
            detail="Training packages are missing. Run: python -m pip install -r requirements.txt",
        ) from exc

    try:
        metrics = train_specialty_model()
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Model training failed: {exc}") from exc

    SPECIALTY_MODEL = _load_specialty_model()

    return ModelTrainResponse(message="Logistic Regression model trained successfully", metrics=metrics)


@app.get("/model/status", response_model=ModelStatusResponse)
def model_status() -> ModelStatusResponse:
    return ModelStatusResponse(
        model_exists=MODEL_PATH.exists(),
        model_path=str(MODEL_PATH),
        metrics=_read_model_metrics(),
    )


def _predict_specialty(symptoms: str, medical_history: str, location: str = "") -> str:
    if SPECIALTY_MODEL is None:
        return ""
    text = f"{symptoms} {medical_history} {location}".strip()
    prediction = SPECIALTY_MODEL.predict([text])[0]
    return str(prediction)


def _read_model_metrics() -> dict | None:
    if not MODEL_METADATA_PATH.exists():
        return None
    try:
        return json.loads(MODEL_METADATA_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return None


def _append_patient_record(payload: RecommendationRequest) -> None:
    with _connect_db() as connection:
        connection.execute(
            """
            INSERT INTO patients (
                patient_name,
                age,
                gender,
                phone,
                email,
                consultation_type,
                insurance_provider,
                existing_conditions,
                symptoms,
                medical_history,
                preferred_location,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.patient_name,
                payload.age,
                payload.gender,
                payload.phone,
                payload.email,
                payload.consultation_type,
                payload.insurance_provider,
                "|".join(payload.existing_conditions),
                payload.symptoms,
                payload.medical_history,
                payload.location,
                datetime.now(timezone.utc).isoformat(),
            ),
        )


def _read_patient_records() -> List[dict]:
    with _connect_db() as connection:
        rows = connection.execute(
            """
            SELECT
                patient_name,
                age,
                gender,
                phone,
                email,
                consultation_type,
                insurance_provider,
                existing_conditions,
                symptoms,
                medical_history,
                preferred_location,
                created_at
            FROM patients
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _append_feedback_record(payload: DoctorFeedbackRequest) -> dict:
    feedback_row = {
        "doctor_name": payload.doctor_name,
        "rating": payload.rating,
        "visit_type": payload.visit_type,
        "comments": payload.comments,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _connect_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO doctor_feedback (doctor_name, rating, visit_type, comments, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                feedback_row["doctor_name"],
                feedback_row["rating"],
                feedback_row["visit_type"],
                feedback_row["comments"],
                feedback_row["created_at"],
            ),
        )
        feedback_row["id"] = cursor.lastrowid
    return feedback_row


def _read_feedback_records() -> List[dict]:
    with _connect_db() as connection:
        rows = connection.execute(
            """
            SELECT id, doctor_name, rating, visit_type, comments, created_at
            FROM doctor_feedback
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _append_appointment_record(payload: AppointmentCreateRequest) -> dict:
    appointment_row = {
        "patient_name": payload.patient_name,
        "phone": payload.phone,
        "email": payload.email,
        "doctor_name": payload.doctor_name,
        "specialty": payload.specialty,
        "location": payload.location,
        "consultation_type": payload.consultation_type,
        "preferred_date": payload.preferred_date,
        "preferred_time": payload.preferred_time,
        "reason": payload.reason,
        "status": "Requested",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    with _connect_db() as connection:
        cursor = connection.execute(
            """
            INSERT INTO appointments (
                patient_name,
                phone,
                email,
                doctor_name,
                specialty,
                location,
                consultation_type,
                preferred_date,
                preferred_time,
                reason,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                appointment_row["patient_name"],
                appointment_row["phone"],
                appointment_row["email"],
                appointment_row["doctor_name"],
                appointment_row["specialty"],
                appointment_row["location"],
                appointment_row["consultation_type"],
                appointment_row["preferred_date"],
                appointment_row["preferred_time"],
                appointment_row["reason"],
                appointment_row["status"],
                appointment_row["created_at"],
            ),
        )
        appointment_row["id"] = cursor.lastrowid
    return appointment_row


def _read_appointment_records() -> List[dict]:
    with _connect_db() as connection:
        rows = connection.execute(
            """
            SELECT
                id,
                patient_name,
                phone,
                email,
                doctor_name,
                specialty,
                location,
                consultation_type,
                preferred_date,
                preferred_time,
                reason,
                status,
                created_at
            FROM appointments
            """
        ).fetchall()
    return [dict(row) for row in rows]


def _append_doctor_record(payload: DoctorCreateRequest) -> dict:
    DOCTORS_PATH.parent.mkdir(parents=True, exist_ok=True)
    file_exists = DOCTORS_PATH.exists()
    doctor_row = {
        "name": payload.name,
        "specialty": payload.specialty,
        "location": payload.location,
        "experience": payload.experience,
        "rating": payload.rating,
        "focus": payload.focus,
        "hospital": payload.hospital,
        "qualification": payload.qualification,
        "languages": payload.languages,
        "consultation_fee": payload.consultation_fee,
        "availability": payload.availability,
        "about": payload.about,
    }
    fieldnames = list(doctor_row.keys())
    with DOCTORS_PATH.open("a", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        if not file_exists:
            writer.writeheader()
        writer.writerow(doctor_row)
    return doctor_row


@app.post("/recommend", response_model=RecommendationResponse)
def recommend(payload: RecommendationRequest) -> RecommendationResponse:
    doctors = load_doctors()
    if not doctors:
        raise HTTPException(status_code=500, detail="Doctor dataset is missing or empty.")
    _append_patient_record(payload)

    predicted_specialty = _predict_specialty(payload.symptoms, payload.medical_history, payload.location)
    city = payload.location.strip().lower()
    city_doctors = [
        doctor for doctor in doctors
        if not city or city in doctor.get("location", "").lower()
    ]
    if city and not city_doctors:
        return RecommendationResponse(
            recommendations=[],
            total_candidates=0,
            predicted_specialty=predicted_specialty or "unknown",
        )

    search_pool = city_doctors or doctors
    candidate_doctors = (
        [doctor for doctor in search_pool if doctor["specialty"] == predicted_specialty]
        if predicted_specialty
        else search_pool
    )
    if not candidate_doctors:
        candidate_doctors = search_pool

    ranked = score_doctors(
        doctors=candidate_doctors,
        symptoms=payload.symptoms,
        medical_history=payload.medical_history,
        location=payload.location,
        top_k=payload.top_k,
    )

    return RecommendationResponse(
        recommendations=ranked,
        total_candidates=len(candidate_doctors),
        predicted_specialty=predicted_specialty or "unknown",
    )


@app.post("/admin/doctors", response_model=DoctorCreateResponse)
def add_doctor(payload: DoctorCreateRequest) -> DoctorCreateResponse:
    if payload.admin_token != ADMIN_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid admin token")
    doctor = _append_doctor_record(payload)
    return DoctorCreateResponse(message="Doctor added successfully", doctor=doctor)


@app.post("/feedback", response_model=DoctorFeedbackResponse)
def add_feedback(payload: DoctorFeedbackRequest) -> DoctorFeedbackResponse:
    doctor_names = {doctor["name"] for doctor in load_doctors()}
    if doctor_names and payload.doctor_name not in doctor_names:
        raise HTTPException(status_code=404, detail="Doctor not found")
    feedback = _append_feedback_record(payload)
    return DoctorFeedbackResponse(message="Feedback submitted successfully", feedback=feedback)


@app.get("/feedback", response_model=FeedbackListResponse)
def get_feedback(
    doctor_name: str = Query(default="", description="Filter by doctor name"),
    limit: int = Query(default=20, ge=1, le=500),
) -> FeedbackListResponse:
    records = _read_feedback_records()
    if doctor_name:
        needle = doctor_name.strip().lower()
        records = [record for record in records if needle in record.get("doctor_name", "").lower()]
    records = sorted(records, key=lambda record: record.get("created_at", ""), reverse=True)
    return FeedbackListResponse(records=records[:limit], total=len(records))


@app.post("/appointments", response_model=AppointmentCreateResponse)
def create_appointment(payload: AppointmentCreateRequest) -> AppointmentCreateResponse:
    doctor_names = {doctor["name"] for doctor in load_doctors()}
    if doctor_names and payload.doctor_name not in doctor_names:
        raise HTTPException(status_code=404, detail="Doctor not found")
    appointment = _append_appointment_record(payload)
    return AppointmentCreateResponse(message="Appointment requested successfully", appointment=appointment)


@app.get("/appointments", response_model=AppointmentListResponse)
def get_appointments(
    patient_name: str = Query(default="", description="Filter by patient name"),
    doctor_name: str = Query(default="", description="Filter by doctor name"),
    limit: int = Query(default=50, ge=1, le=500),
) -> AppointmentListResponse:
    records = _read_appointment_records()
    if patient_name:
        needle = patient_name.strip().lower()
        records = [record for record in records if needle in record.get("patient_name", "").lower()]
    if doctor_name:
        needle = doctor_name.strip().lower()
        records = [record for record in records if needle in record.get("doctor_name", "").lower()]
    records = sorted(records, key=lambda record: record.get("created_at", ""), reverse=True)
    return AppointmentListResponse(records=records[:limit], total=len(records))


@app.get("/patients", response_model=PatientsResponse)
def get_patients(
    name: str = Query(default="", description="Filter by patient name (contains, case-insensitive)"),
    limit: int = Query(default=100, ge=1, le=1000, description="Maximum records to return"),
    from_date: str = Query(
        default="",
        description="ISO date-time filter, returns records created_at >= from_date",
    ),
    sort_by: str = Query(
        default="created_at",
        description="Sort field: created_at, patient_name, age",
    ),
    order: str = Query(default="desc", description="Sort order: asc or desc"),
) -> PatientsResponse:
    records = _read_patient_records()
    filtered = records

    if name:
        needle = name.strip().lower()
        filtered = [r for r in filtered if needle in (r.get("patient_name", "").lower())]

    if from_date:
        try:
            threshold = datetime.fromisoformat(from_date.replace("Z", "+00:00"))
        except ValueError as exc:
            raise HTTPException(status_code=400, detail="Invalid from_date format. Use ISO date-time.") from exc

        def is_after_threshold(record: dict) -> bool:
            created_at = record.get("created_at", "")
            if not created_at:
                return False
            try:
                created_time = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                return False
            return created_time >= threshold

        filtered = [r for r in filtered if is_after_threshold(r)]

    allowed_sort_fields = {"created_at", "patient_name", "age"}
    if sort_by not in allowed_sort_fields:
        raise HTTPException(
            status_code=400,
            detail="Invalid sort_by. Allowed values: created_at, patient_name, age",
        )

    if order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid order. Allowed values: asc, desc")

    reverse = order == "desc"

    def sort_key(record: dict):
        if sort_by == "created_at":
            created_at = record.get("created_at", "")
            try:
                return datetime.fromisoformat(created_at.replace("Z", "+00:00"))
            except ValueError:
                return datetime.min.replace(tzinfo=timezone.utc)
        if sort_by == "age":
            try:
                return int(record.get("age", 0))
            except ValueError:
                return 0
        return record.get("patient_name", "").lower()

    filtered = sorted(filtered, key=sort_key, reverse=reverse)

    return PatientsResponse(records=filtered[:limit], total=len(filtered))
