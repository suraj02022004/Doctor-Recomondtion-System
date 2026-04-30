import json
import random
import csv
from html import escape
from pathlib import Path
from typing import Dict, List
from urllib import error, request

import streamlit as st


st.set_page_config(
    page_title="Doctor Recommendation System",
    page_icon="DR",
    layout="wide",
    initial_sidebar_state="expanded",
)


DOCTORS: List[Dict[str, str]] = [
    {
        "name": "Dr. Aarav Mehta",
        "specialty": "Cardiologist",
        "location": "Delhi",
        "experience": "12 years",
        "rating": "4.8",
        "focus": "Chest pain, hypertension, arrhythmia",
    },
    {
        "name": "Dr. Meera Iyer",
        "specialty": "Dermatologist",
        "location": "Mumbai",
        "experience": "9 years",
        "rating": "4.7",
        "focus": "Skin allergy, acne, eczema",
    },
    {
        "name": "Dr. Karan Verma",
        "specialty": "Neurologist",
        "location": "Bengaluru",
        "experience": "14 years",
        "rating": "4.9",
        "focus": "Migraine, seizures, neuropathy",
    },
    {
        "name": "Dr. Sana Qureshi",
        "specialty": "Orthopedic Surgeon",
        "location": "Hyderabad",
        "experience": "11 years",
        "rating": "4.6",
        "focus": "Joint pain, fractures, arthritis",
    },
    {
        "name": "Dr. Rohan Kulkarni",
        "specialty": "Pulmonologist",
        "location": "Pune",
        "experience": "10 years",
        "rating": "4.8",
        "focus": "Asthma, breathing issues, chronic cough",
    },
    {
        "name": "Dr. Naina Shah",
        "specialty": "Endocrinologist",
        "location": "Ahmedabad",
        "experience": "13 years",
        "rating": "4.7",
        "focus": "Diabetes, thyroid, hormonal imbalance",
    },
]


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


def _load_doctors_from_csv() -> List[Dict[str, str]]:
    data_path = Path(__file__).resolve().parent.parent / "data" / "doctors.csv"
    if not data_path.exists():
        return DOCTORS
    with data_path.open("r", encoding="utf-8", newline="") as file:
        return [
            {key: (value or "").strip() for key, value in row.items()}
            for row in csv.DictReader(file)
            if row.get("name") and row.get("specialty")
        ]


DOCTORS = _load_doctors_from_csv()


PAGES = [
    "Patient Intake",
    "Specialist Matching",
    "Location Aware",
    "Doctor Profiles",
    "Clinical Triage",
    "Doctor Feedback",
    "AI Model Training",
]


def _inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --clinic-teal: #0f766e;
                --clinic-teal-dark: #115e59;
                --clinic-mint: #ccfbf1;
                --clinic-red: #dc2626;
                --ink: #12323a;
                --muted: #55717a;
                --line: #cfe7e5;
            }
            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(204, 251, 241, 0.65), transparent 28rem),
                    linear-gradient(135deg, #f8fffe 0%, #eef8ff 48%, #f7fbfb 100%);
                color: var(--ink);
            }
            [data-testid="stSidebar"] {
                background: linear-gradient(180deg, #ffffff 0%, #eefdfa 100%);
                border-right: 1px solid var(--line);
            }
            [data-testid="stSidebar"] h3 {
                color: var(--clinic-teal-dark);
            }
            [data-testid="stMarkdownContainer"] p,
            [data-testid="stMarkdownContainer"] li {
                color: var(--ink);
            }
            label, .stSelectbox label, .stTextInput label, .stTextArea label {
                color: var(--ink) !important;
                font-weight: 650 !important;
            }
            .stTextInput input,
            .stNumberInput input,
            .stTextArea textarea,
            .stSelectbox div[data-baseweb="select"] > div {
                background: #ffffff;
                border: 1px solid #b9d9d6;
                border-radius: 8px;
                color: var(--ink);
            }
            div.stButton > button {
                border-radius: 8px;
                border: 1px solid var(--clinic-teal);
                font-weight: 700;
            }
            div.stButton > button[kind="primary"] {
                background: linear-gradient(135deg, #0f766e, #0891b2);
                color: #ffffff;
                box-shadow: 0 10px 22px rgba(15, 118, 110, 0.18);
            }
            .hero {
                background: linear-gradient(135deg, rgba(255, 255, 255, 0.96), rgba(232, 255, 250, 0.94));
                border: 1px solid var(--line);
                border-left: 7px solid var(--clinic-teal);
                border-radius: 8px;
                padding: 24px 28px;
                margin-bottom: 14px;
                box-shadow: 0 18px 38px rgba(15, 118, 110, 0.11);
            }
            .hero h1 {
                margin-bottom: 6px;
                font-size: 2.1rem;
                color: #0f3d43;
            }
            .hero p {
                margin-bottom: 0;
                color: var(--muted);
                line-height: 1.55;
                max-width: 58rem;
            }
            .hero-strip {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 10px;
                margin-top: 18px;
            }
            .hero-stat {
                background: #ffffff;
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 12px 14px;
            }
            .hero-stat strong {
                display: block;
                color: var(--clinic-teal-dark);
                font-size: 1.25rem;
                line-height: 1.1;
            }
            .hero-stat span {
                color: var(--muted);
                font-size: 0.86rem;
            }
            .badge-row {
                margin: 14px 0 20px 0;
                display: flex;
                gap: 10px;
                flex-wrap: wrap;
            }
            .badge {
                border: 1px solid #a7e6df;
                border-radius: 999px;
                padding: 7px 13px;
                background: #ffffff;
                color: var(--clinic-teal-dark);
                font-size: 0.84rem;
                font-weight: 700;
            }
            .page-nav-label {
                color: var(--clinic-teal-dark);
                font-size: 0.9rem;
                font-weight: 800;
                margin: 6px 0 8px 0;
            }
            .active-page {
                border: 1px solid #a7e6df;
                border-radius: 8px;
                padding: 10px 14px;
                margin: 8px 0 18px 0;
                background: #ffffff;
                color: var(--clinic-teal-dark);
                font-weight: 800;
                box-shadow: 0 8px 18px rgba(15, 118, 110, 0.08);
            }
            .glass-card {
                border: 1px solid var(--line);
                border-radius: 8px;
                padding: 20px;
                background: rgba(255, 255, 255, 0.92);
                margin-bottom: 14px;
                box-shadow: 0 12px 28px rgba(23, 91, 86, 0.08);
            }
            .doctor-card {
                display: grid;
                grid-template-columns: 58px minmax(0, 1fr);
                gap: 14px;
                border: 1px solid var(--line);
                border-left: 6px solid var(--clinic-teal);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                background: #ffffff;
                box-shadow: 0 10px 24px rgba(19, 101, 98, 0.09);
            }
            .doctor-avatar {
                width: 50px;
                height: 50px;
                border-radius: 50%;
                display: grid;
                place-items: center;
                color: #ffffff;
                background: linear-gradient(135deg, #0f766e, #38bdf8);
                font-weight: 800;
                letter-spacing: 0;
            }
            .doctor-name {
                font-size: 1.1rem;
                font-weight: 700;
                color: #0f3d43;
                margin-bottom: 6px;
            }
            .doctor-specialty {
                display: inline-flex;
                width: fit-content;
                border-radius: 999px;
                padding: 4px 10px;
                margin-left: 8px;
                background: var(--clinic-mint);
                color: var(--clinic-teal-dark);
                font-size: 0.78rem;
                font-weight: 750;
            }
            .doctor-meta {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 6px 12px;
                margin: 8px 0;
            }
            .subtle {
                color: var(--muted);
                font-size: 0.91rem;
                margin-bottom: 3px;
            }
            .confidence {
                display: inline-block;
                margin-top: 6px;
                padding: 6px 10px;
                border-radius: 8px;
                background: #ecfeff;
                color: #155e75;
                font-weight: 800;
                border: 1px solid #bae6fd;
            }
            .admin-card {
                border: 1px solid #fecaca;
                border-left: 6px solid var(--clinic-red);
                border-radius: 8px;
                padding: 16px;
                margin-bottom: 12px;
                background: #fffafa;
            }
            .admin-title {
                color: #991b1b;
                font-weight: 700;
                margin-bottom: 6px;
            }
            .clinic-note {
                color: var(--muted);
                font-size: 0.92rem;
                line-height: 1.5;
            }
            @media (max-width: 760px) {
                .hero-strip,
                .doctor-meta {
                    grid-template-columns: 1fr;
                }
                .doctor-card {
                    grid-template-columns: 1fr;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _score_doctors(symptoms: str, medical_history: str, location: str) -> List[Dict[str, str]]:
    text = f"{symptoms} {medical_history}".lower().strip()
    scores: List[Dict[str, str]] = []

    for doctor in DOCTORS:
        specialty = doctor["specialty"]
        keyword_hits = sum(1 for word in SPECIALTY_KEYWORDS[specialty] if word in text)
        location_bonus = 2 if location and location.lower() in doctor["location"].lower() else 0
        random_bonus = random.choice([0, 1])  # Simulates collaborative preference signal.
        total_score = keyword_hits * 3 + location_bonus + random_bonus

        scored = dict(doctor)
        scored["score"] = str(total_score)
        scores.append(scored)

    return sorted(scores, key=lambda d: int(d["score"]), reverse=True)[:3]


def _doctor_field(doctor: Dict[str, str], key: str, fallback: str = "N/A") -> str:
    value = str(doctor.get(key, "") or "").strip()
    return escape(value if value else fallback)


def _render_doctor_card(doctor: Dict[str, str]) -> None:
    name = _doctor_field(doctor, "name")
    initials = "".join(part[0] for part in name.replace("Dr.", "").split()[:2]).upper() or "DR"
    specialty = _doctor_field(doctor, "specialty")
    location = _doctor_field(doctor, "location")
    experience = _doctor_field(doctor, "experience")
    rating = _doctor_field(doctor, "rating")
    focus = _doctor_field(doctor, "focus")
    hospital = _doctor_field(doctor, "hospital")
    qualification = _doctor_field(doctor, "qualification")
    languages = _doctor_field(doctor, "languages")
    fee = _doctor_field(doctor, "consultation_fee")
    availability = _doctor_field(doctor, "availability")
    about = _doctor_field(doctor, "about")
    score = _doctor_field(doctor, "score", "0")

    st.markdown(
        f"""
        <div class="doctor-card">
            <div class="doctor-avatar">{initials}</div>
            <div>
                <div class="doctor-name">{name}<span class="doctor-specialty">{specialty}</span></div>
                <div class="doctor-meta">
                    <div class="subtle"><b>Location:</b> {location}</div>
                    <div class="subtle"><b>Experience:</b> {experience}</div>
                    <div class="subtle"><b>Rating:</b> {rating}/5</div>
                    <div class="subtle"><b>Fee:</b> {fee}</div>
                    <div class="subtle"><b>Hospital:</b> {hospital}</div>
                    <div class="subtle"><b>Qualification:</b> {qualification}</div>
                </div>
                <div class="subtle"><b>Best for:</b> {focus}</div>
                <div class="subtle"><b>Languages:</b> {languages}</div>
                <div class="subtle"><b>Availability:</b> {availability}</div>
                <div class="subtle"><b>About:</b> {about}</div>
                <div class="confidence">Recommendation confidence: {score}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_header() -> None:
    st.markdown(
        """
        <div class="hero">
            <h1>Clinic Doctor Recommendation Desk</h1>
            <p>
                Match patients with suitable specialists using symptoms, medical history,
                location preference, and doctor profile details in one calm clinical workspace.
            </p>
            <div class="hero-strip">
                <div class="hero-stat"><strong>6+</strong><span>specialist categories</span></div>
                <div class="hero-stat"><strong>3</strong><span>ranked doctors per search</span></div>
                <div class="hero-stat"><strong>Live</strong><span>backend or local fallback</span></div>
            </div>
        </div>
        <div class="badge-row">
            <span class="badge">Use the buttons below to open each clinic page</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_page_buttons() -> None:
    st.markdown('<div class="page-nav-label">Clinic Pages</div>', unsafe_allow_html=True)
    columns = st.columns(len(PAGES))
    for column, page_name in zip(columns, PAGES):
        with column:
            if st.button(page_name, use_container_width=True, key=f"nav_{page_name}"):
                st.session_state["selected_page"] = page_name

    st.markdown(
        f'<div class="active-page">Current page: {st.session_state["selected_page"]}</div>',
        unsafe_allow_html=True,
    )


def _render_sidebar() -> None:
    st.sidebar.markdown("### Clinic Flow")
    st.sidebar.info(
        "1. Register patient details\n\n"
        "2. Capture symptoms and history\n\n"
        "3. Match the right specialty\n\n"
        "4. Rank nearby doctors\n\n"
        "5. Review and book follow-up"
    )
    st.sidebar.markdown("### Care Signals")
    st.sidebar.markdown(
        "- Symptom urgency and specialty fit\n"
        "- Doctor experience and rating\n"
        "- Patient preferred location\n"
        "- Availability and consultation mode"
    )


def _render_recommendations(symptoms: str, medical_history: str, location: str) -> None:
    recs = _score_doctors(symptoms, medical_history, location)
    st.markdown("### Top Doctor Recommendations")
    if location.strip():
        recs = [doctor for doctor in recs if location.lower().strip() in doctor.get("location", "").lower()]
    if not recs:
        st.warning("No doctors found in this city. Try another city.")
        return
    for doctor in recs:
        _render_doctor_card(doctor)


def _fetch_backend_recommendations(
    symptoms: str,
    medical_history: str,
    location: str,
    patient_details: Dict[str, object],
    top_k: int = 3,
) -> tuple[List[Dict[str, str]], str]:
    payload = {
        "patient_name": patient_details.get("patient_name", ""),
        "age": int(patient_details.get("age", 0)),
        "gender": patient_details.get("gender", ""),
        "phone": patient_details.get("phone", ""),
        "email": patient_details.get("email", ""),
        "consultation_type": patient_details.get("consultation_type", ""),
        "insurance_provider": patient_details.get("insurance_provider", ""),
        "existing_conditions": patient_details.get("existing_conditions", []),
        "symptoms": symptoms,
        "medical_history": medical_history,
        "location": location,
        "top_k": top_k,
    }
    req = request.Request(
        "http://127.0.0.1:8000/recommend",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=8) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body.get("recommendations", []), body.get("predicted_specialty", "unknown")


def _submit_backend_feedback(
    doctor_name: str,
    rating: int,
    visit_type: str,
    comments: str,
) -> Dict[str, str]:
    payload = {
        "doctor_name": doctor_name,
        "rating": rating,
        "visit_type": visit_type,
        "comments": comments,
    }
    req = request.Request(
        "http://127.0.0.1:8000/feedback",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=8) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body.get("feedback", payload)


def _fetch_backend_feedback(limit: int = 5) -> List[Dict[str, str]]:
    with request.urlopen(f"http://127.0.0.1:8000/feedback?limit={limit}", timeout=8) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body.get("records", [])


def _submit_backend_appointment(
    doctor: Dict[str, str],
    patient_details: Dict[str, object],
    preferred_date: str,
    preferred_time: str,
    reason: str,
) -> Dict[str, str]:
    payload = {
        "patient_name": patient_details.get("patient_name", ""),
        "phone": patient_details.get("phone", ""),
        "email": patient_details.get("email", ""),
        "doctor_name": doctor.get("name", ""),
        "specialty": doctor.get("specialty", ""),
        "location": doctor.get("location", ""),
        "consultation_type": patient_details.get("consultation_type", "In-person"),
        "preferred_date": preferred_date,
        "preferred_time": preferred_time,
        "reason": reason,
    }
    req = request.Request(
        "http://127.0.0.1:8000/appointments",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=8) as response:
        body = json.loads(response.read().decode("utf-8"))
    return body.get("appointment", payload)


def _train_backend_model() -> Dict[str, object]:
    req = request.Request(
        "http://127.0.0.1:8000/model/train",
        data=b"",
        method="POST",
    )
    with request.urlopen(req, timeout=30) as response:
        return json.loads(response.read().decode("utf-8"))


def _fetch_model_status() -> Dict[str, object]:
    with request.urlopen("http://127.0.0.1:8000/model/status", timeout=8) as response:
        return json.loads(response.read().decode("utf-8"))


def _render_appointment_form(doctor: Dict[str, str], patient_details: Dict[str, object]) -> None:
    doctor_name = doctor.get("name", "doctor")
    safe_key = "".join(ch for ch in doctor_name if ch.isalnum()).lower()
    with st.expander(f"Book appointment with {doctor_name}"):
        with st.form(f"appointment_{safe_key}_{doctor.get('location', '')}"):
            preferred_date = st.date_input("Preferred Date")
            preferred_time = st.time_input("Preferred Time")
            reason = st.text_area(
                "Appointment Reason",
                value=str(patient_details.get("symptoms", "")),
                height=90,
            )
            submitted = st.form_submit_button("Confirm Appointment", type="primary", use_container_width=True)

        if submitted:
            patient_name = str(patient_details.get("patient_name", "")).strip()
            if not patient_name:
                st.warning("Please enter patient name before booking appointment.")
                return
            try:
                appointment = _submit_backend_appointment(
                    doctor,
                    patient_details,
                    preferred_date.isoformat(),
                    preferred_time.strftime("%H:%M"),
                    reason.strip(),
                )
                st.success(
                    "Appointment requested for "
                    f"{appointment.get('doctor_name', doctor_name)} on "
                    f"{appointment.get('preferred_date', preferred_date.isoformat())} "
                    f"at {appointment.get('preferred_time', preferred_time.strftime('%H:%M'))}."
                )
            except (error.HTTPError, error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
                st.error("Backend not reachable. Start the backend to save appointment permanently.")


def _render_recommendations_from_backend(
    symptoms: str,
    medical_history: str,
    location: str,
    patient_details: Dict[str, object],
) -> None:
    st.markdown("### Top Doctor Recommendations")
    try:
        recs, predicted_specialty = _fetch_backend_recommendations(
            symptoms,
            medical_history,
            location,
            patient_details,
        )
        st.info(f"Predicted specialty by model: **{predicted_specialty}**")
    except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
        st.warning("Backend not reachable. Showing local fallback recommendations.")
        _render_recommendations(symptoms, medical_history, location)
        return

    if location.strip() and not recs:
        st.warning(f"No matching doctors found in {location}. Try another city.")
        return

    for doctor in recs:
        _render_doctor_card(doctor)
        _render_appointment_form(
            doctor,
            {
                **patient_details,
                "symptoms": symptoms,
                "medical_history": medical_history,
                "location": location,
            },
        )


def _admin_add_doctor_panel() -> None:
    st.markdown(
        '<div class="admin-card"><div class="admin-title">Doctor Admin Desk</div>'
        '<div class="clinic-note">Add clinic doctors, specialties, timings, and consultation details.</div></div>',
        unsafe_allow_html=True,
    )
    st.caption("Open panel to add or update doctor listings.")
    if st.button("Open Admin Panel", type="secondary", use_container_width=True):
        _admin_add_doctor_popup()


@st.dialog("Admin Panel: Add Doctor")
def _admin_add_doctor_popup() -> None:
    admin_token = st.text_input("Admin Token", type="password")
    name = st.text_input("Doctor Name")
    specialty = st.text_input("Specialty")
    location = st.text_input("Doctor Location")
    col_x, col_y = st.columns(2)
    with col_x:
        experience = st.text_input("Experience", placeholder="e.g., 8 years")
        hospital = st.text_input("Hospital/Clinic")
        languages = st.text_input("Languages", placeholder="English|Hindi")
    with col_y:
        rating = st.text_input("Rating", placeholder="e.g., 4.7")
        qualification = st.text_input("Qualification")
        consultation_fee = st.text_input("Consultation Fee", placeholder="e.g., 1000")
    availability = st.text_input("Availability", placeholder="Mon-Sat 10:00-17:00")
    focus = st.text_area("Focus Areas", placeholder="Symptoms/conditions this doctor handles")
    about = st.text_area("About Doctor")

    if st.button("Add Doctor", type="primary", use_container_width=True):
        payload = {
            "admin_token": admin_token,
            "name": name,
            "specialty": specialty,
            "location": location,
            "experience": experience,
            "rating": rating or "4.5",
            "focus": focus,
            "hospital": hospital,
            "qualification": qualification,
            "languages": languages,
            "consultation_fee": consultation_fee,
            "availability": availability,
            "about": about,
        }
        req = request.Request(
            "http://127.0.0.1:8000/admin/doctors",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with request.urlopen(req, timeout=8) as response:
                body = json.loads(response.read().decode("utf-8"))
            st.success(body.get("message", "Doctor added successfully"))
        except error.HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode("utf-8")).get("detail", "Request failed")
            except Exception:
                detail = "Request failed"
            st.error(f"Failed to add doctor: {detail}")
        except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            st.error("Backend not reachable.")


def _render_patient_intake_page() -> None:
    left, right = st.columns([1.45, 1.0], gap="large")
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Patient Intake Form")
        col_a, col_b = st.columns(2)
        with col_a:
            patient_name = st.text_input("Patient Name", placeholder="Full name")
            age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
            gender = st.selectbox("Gender", ["Male", "Female", "Other", "Prefer not to say"])
        with col_b:
            phone = st.text_input("Phone Number", placeholder="+91XXXXXXXXXX")
            email = st.text_input("Email", placeholder="name@example.com")
            appointment_mode = st.selectbox("Consultation Type", ["In-person", "Online", "Either"])

        existing_conditions = st.multiselect(
            "Existing Conditions (Optional)",
            ["Diabetes", "Hypertension", "Asthma", "Thyroid", "Heart Disease", "Arthritis"],
        )
        symptoms = st.text_area(
            "Symptoms",
            placeholder="Example: frequent cough, chest discomfort, shortness of breath",
            height=120,
        )
        medical_history = st.text_area(
            "Medical History",
            placeholder="Example: asthma for 6 years, hypertension, prior medication details",
            height=110,
        )
        location = st.text_input("Preferred Location", placeholder="City name")
        submit = st.button("Get AI Recommendations", type="primary", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)

        if submit:
            if not symptoms.strip():
                st.warning("Please enter symptoms to generate recommendations.")
            elif not patient_name.strip():
                st.warning("Please enter patient name.")
            else:
                st.success(
                    f"Patient profile captured: {patient_name} ({age}, {gender}) | "
                    f"Consultation: {appointment_mode}"
                )
                if phone or email or existing_conditions:
                    st.caption(
                        "Contact/extra details saved for triage: "
                        f"Phone: {phone or 'N/A'} | Email: {email or 'N/A'} | "
                        f"Conditions: {', '.join(existing_conditions) if existing_conditions else 'None'}"
                    )
                _render_recommendations_from_backend(
                    symptoms,
                    medical_history,
                    location,
                    {
                        "patient_name": patient_name,
                        "age": age,
                        "gender": gender,
                        "phone": phone,
                        "email": email,
                        "consultation_type": appointment_mode,
                        "existing_conditions": existing_conditions,
                    },
                )

    with right:
        _admin_add_doctor_panel()
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Care Matching Summary")
        st.markdown(
            "- **Symptom review**: Reads the patient's current concern.\n"
            "- **Specialty fit**: Maps concerns to the right type of doctor.\n"
            "- **Location preference**: Gives nearby doctors a stronger rank.\n"
            "- **Profile quality**: Shows ratings, experience, and availability.\n"
            "- **Fallback ready**: Keeps recommendations visible if the backend is offline."
        )
        st.markdown("</div>", unsafe_allow_html=True)

        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Clinic Checklist")
        st.markdown(
            "1. Confirm patient contact details\n"
            "2. Record symptoms and medical history\n"
            "3. Review the predicted specialty\n"
            "4. Compare top doctor profiles\n"
            "5. Share the preferred consultation option"
        )
        st.markdown("</div>", unsafe_allow_html=True)


def _render_specialist_matching_page() -> None:
    left, right = st.columns([1.35, 1.0], gap="large")
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Specialist Matching")
        symptoms = st.text_area(
            "Symptoms",
            placeholder="Example: chest discomfort, high BP, fast heartbeat",
            height=130,
            key="specialist_symptoms",
        )
        history = st.text_area(
            "Medical History",
            placeholder="Example: hypertension for 3 years, current medicines",
            height=110,
            key="specialist_history",
        )
        city = st.text_input("Preferred City", placeholder="Delhi", key="specialist_city")
        if st.button("Find Matching Specialist", type="primary", use_container_width=True):
            if symptoms.strip():
                _render_recommendations(symptoms, history, city)
            else:
                st.warning("Please enter symptoms to match a specialist.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Common Specialty Guide")
        for specialty, keywords in SPECIALTY_KEYWORDS.items():
            st.markdown(f"**{specialty}**: {', '.join(keywords)}")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_location_page() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Location Aware Search")
    city = st.text_input("Search doctors by city", placeholder="Delhi, Mumbai, Pune...")
    st.markdown("</div>", unsafe_allow_html=True)

    matches = [
        doctor for doctor in DOCTORS
        if not city.strip() or city.lower().strip() in doctor["location"].lower()
    ]
    st.markdown("### Available Doctors")
    if matches:
        for doctor in matches:
            _render_doctor_card({**doctor, "score": "Location match"})
    else:
        st.warning("No doctors found for this location.")


def _render_profiles_page() -> None:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.subheader("Doctor Profiles")
    specialties = ["All"] + sorted({doctor["specialty"] for doctor in DOCTORS})
    specialty = st.selectbox("Filter by specialty", specialties)
    st.markdown("</div>", unsafe_allow_html=True)

    doctors = DOCTORS if specialty == "All" else [
        doctor for doctor in DOCTORS if doctor["specialty"] == specialty
    ]
    for doctor in doctors:
        _render_doctor_card({**doctor, "score": "Profile"})


def _render_triage_page() -> None:
    left, right = st.columns([1.1, 1.0], gap="large")
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Clinical Triage")
        urgency = st.select_slider(
            "Symptom urgency",
            options=["Routine", "Soon", "Urgent"],
            value="Soon",
        )
        duration = st.selectbox(
            "How long has the patient had symptoms?",
            ["Less than 24 hours", "1-3 days", "More than 3 days", "More than 2 weeks"],
        )
        warning_signs = st.multiselect(
            "Warning signs",
            ["Severe pain", "Breathing difficulty", "Chest discomfort", "Fainting", "High fever"],
        )
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Suggested Next Step")
        if urgency == "Urgent" or warning_signs:
            st.error("Prioritize urgent medical review and choose the nearest suitable specialist.")
        elif duration in ["More than 3 days", "More than 2 weeks"]:
            st.warning("Recommend a specialist consultation soon.")
        else:
            st.success("Routine doctor matching is suitable based on current inputs.")
        st.markdown(
            "1. Confirm patient details\n"
            "2. Review symptoms carefully\n"
            "3. Choose specialty and location\n"
            "4. Compare doctor profiles\n"
            "5. Share appointment preference"
        )
        st.markdown("</div>", unsafe_allow_html=True)


def _render_feedback_page() -> None:
    if "doctor_feedback" not in st.session_state:
        st.session_state["doctor_feedback"] = []

    left, right = st.columns([1.2, 1.0], gap="large")
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Doctor Feedback")
        doctor_names = [doctor["name"] for doctor in DOCTORS]
        selected_doctor = st.selectbox("Select Doctor", doctor_names)
        rating = st.slider("Doctor Rating", min_value=1, max_value=5, value=5)
        visit_type = st.selectbox("Visit Type", ["Consultation", "Follow-up", "Online Consultation", "Emergency Review"])
        comments = st.text_area(
            "Feedback Comments",
            placeholder="Write about communication, treatment clarity, waiting time, or overall experience",
            height=130,
        )

        if st.button("Submit Feedback", type="primary", use_container_width=True):
            if not comments.strip():
                st.warning("Please add a short feedback comment.")
            else:
                try:
                    saved_feedback = _submit_backend_feedback(
                        selected_doctor,
                        rating,
                        visit_type,
                        comments.strip(),
                    )
                    st.success("Feedback saved to backend successfully.")
                    st.session_state["doctor_feedback"].append(saved_feedback)
                except (error.HTTPError, error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
                    st.session_state["doctor_feedback"].append(
                        {
                            "doctor_name": selected_doctor,
                            "rating": str(rating),
                            "visit_type": visit_type,
                            "comments": comments.strip(),
                        }
                    )
                    st.warning("Backend not reachable. Feedback saved temporarily in this app session.")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Recent Feedback")
        try:
            feedback_records = _fetch_backend_feedback(limit=5)
        except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            feedback_records = list(reversed(st.session_state["doctor_feedback"][-5:]))

        if feedback_records:
            for feedback in feedback_records:
                doctor_name = feedback.get("doctor_name") or feedback.get("doctor", "Unknown doctor")
                st.markdown(
                    f"**{doctor_name}**  \n"
                    f"Rating: **{feedback.get('rating', 'N/A')}/5** | "
                    f"Visit: {feedback.get('visit_type', 'N/A')}  \n"
                    f"{feedback.get('comments', '')}"
                )
                st.divider()
        else:
            st.info("No feedback submitted yet.")
        st.markdown("</div>", unsafe_allow_html=True)


def _render_model_training_page() -> None:
    left, right = st.columns([1.1, 1.0], gap="large")
    with left:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("AI Model Training")
        st.markdown(
            "Train the specialty prediction model using TF-IDF text features "
            "and Logistic Regression from the doctor dataset."
        )
        if st.button("Train Logistic Regression Model", type="primary", use_container_width=True):
            try:
                result = _train_backend_model()
                metrics = result.get("metrics", {})
                st.success(result.get("message", "Model trained successfully."))
                st.metric("Training Rows", metrics.get("training_rows", 0))
                st.metric("Specialty Classes", metrics.get("classes", 0))
                st.metric("Training Accuracy", f"{metrics.get('train_accuracy', 0):.2%}")
            except (error.HTTPError, error.URLError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                st.error(f"Training failed. Make sure backend is running and requirements are installed. {exc}")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.subheader("Model Status")
        try:
            status = _fetch_model_status()
            st.write(f"Model exists: **{status.get('model_exists')}**")
            st.caption(status.get("model_path", ""))
            metrics = status.get("metrics") or {}
            if metrics:
                st.write(f"Algorithm: **{metrics.get('algorithm', 'Logistic Regression')}**")
                st.write(f"Training rows: **{metrics.get('training_rows', 'N/A')}**")
                st.write(f"Accuracy: **{metrics.get('train_accuracy', 0):.2%}**")
            else:
                st.info("No training metrics found yet.")
        except (error.URLError, TimeoutError, ValueError, json.JSONDecodeError):
            st.warning("Backend not reachable. Start the backend to train or view model status.")
        st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    _inject_styles()
    if "selected_page" not in st.session_state:
        st.session_state["selected_page"] = PAGES[0]

    _render_sidebar()
    page = st.sidebar.radio(
        "Pages",
        PAGES,
        index=PAGES.index(st.session_state["selected_page"]),
    )
    st.session_state["selected_page"] = page
    _render_header()
    _render_page_buttons()
    page = st.session_state["selected_page"]

    if page == "Patient Intake":
        _render_patient_intake_page()
    elif page == "Specialist Matching":
        _render_specialist_matching_page()
    elif page == "Location Aware":
        _render_location_page()
    elif page == "Doctor Profiles":
        _render_profiles_page()
    elif page == "Clinical Triage":
        _render_triage_page()
    elif page == "Doctor Feedback":
        _render_feedback_page()
    else:
        _render_model_training_page()


if __name__ == "__main__":
    main()
