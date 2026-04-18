from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
from collections import defaultdict
import time
import httpx
import pandas as pd

from backend.predictor import predict, get_disease_description, get_precautions, get_severity_score
from backend.allergy_filter import recommend_drugs
from backend.pdf_report import generate_pdf
from backend.symptom_extractor import extract_symptoms_from_narrative

app = FastAPI(
    title="MediPredict — Drug Recommendation System",
    description="Symptom-based disease diagnosis and personalised safe drug recommendation",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ─────────────────────────────────────────────
# RATE LIMITING — max 30 requests per minute per IP
# ─────────────────────────────────────────────
request_counts = defaultdict(list)
RATE_LIMIT     = 30
RATE_WINDOW    = 60  # seconds

def check_rate_limit(ip: str):
    now = time.time()
    # Remove requests older than the window
    request_counts[ip] = [t for t in request_counts[ip] if now - t < RATE_WINDOW]
    if len(request_counts[ip]) >= RATE_LIMIT:
        raise HTTPException(
            status_code=429,
            detail="Too many requests. Please wait a moment before trying again."
        )
    request_counts[ip].append(now)

# ─────────────────────────────────────────────
# LOAD DISEASE-SYMPTOM MAP AT STARTUP
# ─────────────────────────────────────────────
df = pd.read_csv("data/dataset.csv")
df.columns = df.columns.str.strip()
df["Disease"] = df["Disease"].str.strip()
symptom_cols = [c for c in df.columns if c.startswith("Symptom_")]
for col in symptom_cols:
    df[col] = df[col].str.strip().str.lower().str.replace(" ", "_")

DISEASE_SYMPTOM_MAP = {}
for _, row in df.iterrows():
    disease = row["Disease"]
    if disease not in DISEASE_SYMPTOM_MAP:
        DISEASE_SYMPTOM_MAP[disease] = set()
    for col in symptom_cols:
        val = row[col]
        if pd.notna(val) and str(val).strip():
            DISEASE_SYMPTOM_MAP[disease].add(val)

# ─────────────────────────────────────────────
# EMERGENCY COMBINATIONS
# ─────────────────────────────────────────────
EMERGENCY_SYMPTOM_SETS = [
    {"chest_pain", "sweating", "breathlessness"},
    {"chest_pain", "fatigue", "vomiting"},
    {"chest_pain", "dizziness", "nausea"},
    {"headache", "loss_of_balance", "blurred_and_distorted_vision"},
    {"breathlessness", "high_fever", "bluish_discolouration"},
    {"breathlessness", "chest_pain", "fast_heart_rate"},
    {"excessive_hunger", "fatigue", "sweating", "anxiety"},
    {"stiff_neck", "high_fever", "headache", "vomiting"},
]

def check_emergency(symptoms: list) -> dict:
    s = set(symptoms)
    for combo in EMERGENCY_SYMPTOM_SETS:
        if combo.issubset(s):
            return {
                "is_emergency": True,
                "reason": (
                    "Your symptoms include a combination that may indicate "
                    "a life-threatening emergency. Please go to the nearest "
                    "hospital or health centre immediately."
                )
            }
    return {"is_emergency": False, "reason": None}

# ─────────────────────────────────────────────
# OPENFDA DRUG INTERACTION CHECK
# ─────────────────────────────────────────────
async def check_drug_interactions(drug_names: list) -> Optional[str]:
    """
    Queries the OpenFDA API to check for known interactions
    between the drugs in the recommended regimen.
    Returns a warning string if interactions are found, else None.
    """
    if len(drug_names) < 2:
        return None

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            warnings = []
            for i in range(len(drug_names)):
                for j in range(i + 1, len(drug_names)):
                    drug_a = drug_names[i].split()[0]  # use first word only
                    drug_b = drug_names[j].split()[0]

                    query = (
                        f"https://api.fda.gov/drug/label.json?"
                        f"search=drug_interactions:{drug_a}+AND+drug_interactions:{drug_b}"
                        f"&limit=1"
                    )
                    res = await client.get(query)
                    if res.status_code == 200:
                        data = res.json()
                        if data.get("results"):
                            warnings.append(
                                f"Possible interaction between {drug_a} and {drug_b} — "
                                f"ask your pharmacist or doctor before taking both together."
                            )
            return " | ".join(warnings) if warnings else None
    except Exception:
        # If OpenFDA is unreachable, return None silently — do not block the prediction
        return None

# ─────────────────────────────────────────────
# VITAL SIGNS INTERPRETATION
# ─────────────────────────────────────────────
def interpret_vitals(temperature: Optional[float],
                     blood_pressure_systolic: Optional[int],
                     pulse_rate: Optional[int]) -> dict:
    """
    Interprets vital signs and returns additional symptom flags
    and a clinical note to add to the prediction context.
    """
    flags  = []
    notes  = []
    urgent = False

    if temperature is not None:
        if temperature >= 39.5:
            flags.append("high_fever")
            notes.append(f"Temperature {temperature}°C — high fever confirmed.")
            urgent = True
        elif temperature >= 37.5:
            flags.append("mild_fever")
            notes.append(f"Temperature {temperature}°C — mild fever present.")
        elif temperature < 36.0:
            notes.append(f"Temperature {temperature}°C — below normal (hypothermia possible).")
            urgent = True

    if blood_pressure_systolic is not None:
        if blood_pressure_systolic >= 180:
            flags.append("high_blood_pressure")
            notes.append(f"Blood pressure {blood_pressure_systolic} mmHg — hypertensive crisis. Seek emergency care.")
            urgent = True
        elif blood_pressure_systolic >= 140:
            flags.append("high_blood_pressure")
            notes.append(f"Blood pressure {blood_pressure_systolic} mmHg — high blood pressure detected.")
        elif blood_pressure_systolic < 90:
            notes.append(f"Blood pressure {blood_pressure_systolic} mmHg — dangerously low. Seek emergency care.")
            urgent = True

    if pulse_rate is not None:
        if pulse_rate > 100:
            flags.append("fast_heart_rate")
            notes.append(f"Pulse rate {pulse_rate} bpm — fast heart rate detected.")
        elif pulse_rate < 50:
            notes.append(f"Pulse rate {pulse_rate} bpm — very slow heart rate. Seek medical attention.")
            urgent = True

    return {
        "symptom_flags": flags,
        "vitals_notes":  notes,
        "vitals_urgent": urgent
    }

# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────
class PredictionRequest(BaseModel):
    symptoms:              List[str]
    allergy:               str
    age_group:             str           = "adult"
    gender:                str           = "unspecified"
    has_kidney_disease:    bool          = False
    is_pregnant:           bool          = False
    temperature:           Optional[float] = None
    blood_pressure:        Optional[int]   = None
    pulse_rate:            Optional[int]   = None

class NarrativeRequest(BaseModel):
    narrative: str

class InterviewQuestionsRequest(BaseModel):
    confirmed_symptoms: List[str]
    top_n: int = 3

class PDFRequest(BaseModel):
    symptoms:              List[str]
    allergy:               str
    age_group:             str           = "adult"
    gender:                str           = "unspecified"
    has_kidney_disease:    bool          = False
    is_pregnant:           bool          = False
    disease:               str
    confidence:            str
    confidence_warning:    Optional[str] = None
    emergency:             bool          = False
    emergency_reason:      Optional[str] = None
    description:           str
    severity:              dict
    precautions:           List[str]
    medication:            dict
    top3:                  List[dict]    = []
    clinical_summary:      Optional[str] = None
    vitals_notes:          List[str]     = []

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────
@app.get("/")
def root():
    return {"message": "MediPredict API v5.0 is running"}


@app.post("/extract-symptoms")
async def extract_symptoms(request: Request, body: NarrativeRequest):
    check_rate_limit(request.client.host)
    from backend.predictor import all_symptoms
    return extract_symptoms_from_narrative(body.narrative, all_symptoms)


@app.post("/interview-questions")
async def get_interview_questions(request: Request, body: InterviewQuestionsRequest):
    check_rate_limit(request.client.host)
    confirmed = set(body.confirmed_symptoms)
    if not confirmed:
        return {"questions": [], "candidates": []}

    from backend.predictor import model, all_symptoms, severity_map
    import numpy as np

    input_vector  = [severity_map.get(s, 1) if s in confirmed else 0 for s in all_symptoms]
    input_array   = np.array(input_vector).reshape(1, -1)
    probabilities = model.predict_proba(input_array)[0]
    classes       = model.classes_

    disease_probs = sorted(zip(classes, probabilities), key=lambda x: x[1], reverse=True)
    candidates    = [
        {"disease": d, "confidence": round(p * 100, 1)}
        for d, p in disease_probs[:body.top_n]
        if p > 0.05
    ]

    missing_per_disease = {}
    for item in candidates:
        disease = item["disease"]
        all_disease_symptoms = DISEASE_SYMPTOM_MAP.get(disease, set())
        missing_per_disease[disease] = all_disease_symptoms - confirmed

    symptom_score = {}
    for disease, missing in missing_per_disease.items():
        disease_confidence = next(
            (c["confidence"] for c in candidates if c["disease"] == disease), 0
        )
        for symptom in missing:
            if symptom not in symptom_score:
                symptom_score[symptom] = 0
            symptom_score[symptom] += disease_confidence

    ranked_symptoms = sorted(symptom_score.keys(), key=lambda s: symptom_score[s], reverse=True)

    return {
        "questions":  ranked_symptoms[:10],
        "candidates": candidates
    }


@app.post("/predict")
async def predict_disease(request: Request, body: PredictionRequest):
    check_rate_limit(request.client.host)

    # Interpret vital signs and add symptom flags
    vitals = interpret_vitals(body.temperature, body.blood_pressure, body.pulse_rate)
    enhanced_symptoms = list(set(body.symptoms + vitals["symptom_flags"]))

    prediction = predict(enhanced_symptoms)

    if prediction.get("error"):
        return {
            "error":   True,
            "message": prediction["message"],
            "invalid": prediction["invalid"]
        }

    disease    = prediction["disease"]
    confidence = prediction["confidence"]
    invalid    = prediction.get("invalid", [])

    description = get_disease_description(disease)
    precautions = get_precautions(disease)
    severity    = get_severity_score(prediction["valid"])
    medication  = recommend_drugs(
        disease,
        body.allergy,
        body.age_group,
        body.gender,
        body.has_kidney_disease,
        body.is_pregnant
    )

    # OpenFDA interaction check
    drug_names = [d["drug"] for d in medication.get("regimen", [])]
    fda_warning = await check_drug_interactions(drug_names)

    # Merge FDA warning with our local interaction warning
    local_warning = medication.get("interaction_warning")
    combined_interaction = None
    if local_warning and fda_warning:
        combined_interaction = f"{local_warning} | {fda_warning}"
    elif local_warning:
        combined_interaction = local_warning
    elif fda_warning:
        combined_interaction = fda_warning

    medication["interaction_warning"] = combined_interaction

    confidence_warning = None
    if confidence < 60:
        confidence_warning = (
            "Our confidence in this prediction is low. "
            "Your symptoms may overlap with multiple conditions. "
            "Please consult a doctor for a confirmed diagnosis."
        )

    severity_emergency = severity["level"].startswith("Severe")
    symptom_check      = check_emergency(prediction["valid"])
    vitals_emergency   = vitals["vitals_urgent"]
    emergency          = severity_emergency or symptom_check["is_emergency"] or vitals_emergency
    emergency_reason   = (
        symptom_check["reason"] if symptom_check["is_emergency"]
        else "Your vital signs or severity score indicate an urgent condition. Please seek medical attention."
        if (severity_emergency or vitals_emergency)
        else None
    )

    return {
        "error":              False,
        "disease":            disease,
        "confidence":         f"{confidence}%",
        "confidence_warning": confidence_warning,
        "emergency":          emergency,
        "emergency_reason":   emergency_reason,
        "description":        description,
        "severity":           severity,
        "precautions":        precautions,
        "medication":         medication,
        "top3":               prediction.get("top3", []),
        "vitals_notes":       vitals["vitals_notes"],
        "warnings":           [f"'{s}' was not recognised and was ignored" for s in invalid]
    }


@app.post("/download-report")
async def download_report(request: Request, body: PDFRequest):
    check_rate_limit(request.client.host)
    report_data = {
        "profile": {
            "age_group":         body.age_group,
            "gender":            body.gender,
            "allergy":           body.allergy,
            "has_kidney_disease": body.has_kidney_disease,
            "is_pregnant":       body.is_pregnant,
        },
        "symptoms":           body.symptoms,
        "disease":            body.disease,
        "confidence":         body.confidence,
        "confidence_warning": body.confidence_warning,
        "emergency":          body.emergency,
        "emergency_reason":   body.emergency_reason,
        "description":        body.description,
        "severity":           body.severity,
        "precautions":        body.precautions,
        "medication":         body.medication,
        "top3":               body.top3,
        "clinical_summary":   body.clinical_summary,
        "vitals_notes":       body.vitals_notes,
    }
    pdf_bytes = generate_pdf(report_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=medipredict_report.pdf"}
    )


@app.get("/symptoms")
async def list_symptoms():
    from backend.predictor import all_symptoms
    return {"symptoms": all_symptoms}