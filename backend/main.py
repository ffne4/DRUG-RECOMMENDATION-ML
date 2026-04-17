from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from typing import List, Optional
import pandas as pd
import joblib

from backend.predictor import predict, get_disease_description, get_precautions, get_severity_score
from backend.allergy_filter import recommend_drugs
from backend.pdf_report import generate_pdf
from backend.symptom_extractor import extract_symptoms_from_narrative

app = FastAPI(
    title="Drug Recommendation System",
    version="5.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ─────────────────────────────────────────────
# LOAD DISEASE-SYMPTOM MAP AT STARTUP
# We need to know which symptoms belong to each disease
# so we can ask the patient about the ones they missed.
# ─────────────────────────────────────────────

df = pd.read_csv("data/dataset.csv")
df.columns = df.columns.str.strip()
df["Disease"] = df["Disease"].str.strip()
symptom_cols = [c for c in df.columns if c.startswith("Symptom_")]
for col in symptom_cols:
    df[col] = df[col].str.strip().str.lower().str.replace(" ", "_")

# Build: disease -> set of all its symptoms
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
                    "hospital immediately."
                )
            }
    return {"is_emergency": False, "reason": None}

# ─────────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────────

class PredictionRequest(BaseModel):
    symptoms:  List[str]
    allergy:   str
    age_group: str = "adult"
    gender:    str = "unspecified"

class NarrativeRequest(BaseModel):
    narrative: str

class InterviewQuestionsRequest(BaseModel):
    confirmed_symptoms: List[str]   # what patient has confirmed so far
    top_n: int = 3                  # how many candidate diseases to consider

class PDFRequest(BaseModel):
    symptoms:           List[str]
    allergy:            str
    age_group:          str = "adult"
    gender:             str = "unspecified"
    disease:            str
    confidence:         str
    confidence_warning: Optional[str] = None
    emergency:          bool = False
    emergency_reason:   Optional[str] = None
    description:        str
    severity:           dict
    precautions:        List[str]
    medication:         dict
    top3:               List[dict] = []
    clinical_summary:   Optional[str] = None

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "MediPredict API v5.0"}


@app.post("/extract-symptoms")
def extract_symptoms(request: NarrativeRequest):
    from backend.predictor import all_symptoms
    return extract_symptoms_from_narrative(request.narrative, all_symptoms)


@app.post("/interview-questions")
def get_interview_questions(request: InterviewQuestionsRequest):
    """
    Given the symptoms confirmed so far, predict the top candidate diseases,
    then find symptoms those diseases have that the patient has NOT mentioned.
    Return those missing symptoms as interview questions — most discriminating first.

    This is the smart interview: we only ask about symptoms that are actually
    relevant to the most likely diseases, not random questions.
    """
    confirmed = set(request.confirmed_symptoms)

    if not confirmed:
        return {"questions": [], "candidates": []}

    # Step 1: Run prediction to get top candidate diseases
    from backend.predictor import model, all_symptoms, severity_map
    import numpy as np

    input_vector = [
        severity_map.get(s, 1) if s in confirmed else 0
        for s in all_symptoms
    ]
    input_array   = np.array(input_vector).reshape(1, -1)
    probabilities = model.predict_proba(input_array)[0]
    classes       = model.classes_

    # Get top N candidate diseases with probability > 5%
    disease_probs = sorted(
        zip(classes, probabilities),
        key=lambda x: x[1],
        reverse=True
    )
    candidates = [
        {"disease": d, "confidence": round(p * 100, 1)}
        for d, p in disease_probs[:request.top_n]
        if p > 0.05
    ]

    # Step 2: Collect all symptoms from candidate diseases
    # that the patient has NOT yet confirmed
    missing_per_disease = {}
    for item in candidates:
        disease = item["disease"]
        all_disease_symptoms = DISEASE_SYMPTOM_MAP.get(disease, set())
        missing = all_disease_symptoms - confirmed
        missing_per_disease[disease] = missing

    # Step 3: Score each missing symptom by how many candidate diseases have it
    # Symptoms shared by more candidates are more discriminating — ask those first
    symptom_score = {}
    for disease, missing in missing_per_disease.items():
        disease_confidence = next(
            (c["confidence"] for c in candidates if c["disease"] == disease), 0
        )
        for symptom in missing:
            if symptom not in symptom_score:
                symptom_score[symptom] = 0
            # Weight by disease confidence so top disease symptoms come first
            symptom_score[symptom] += disease_confidence

    # Sort missing symptoms by score — highest first
    ranked_symptoms = sorted(symptom_score.keys(), key=lambda s: symptom_score[s], reverse=True)

    # Return top 10 most relevant missing symptoms as questions
    questions = ranked_symptoms[:10]

    return {
        "questions":  questions,
        "candidates": candidates
    }


@app.post("/predict")
def predict_disease(request: PredictionRequest):

    prediction = predict(request.symptoms)

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
        disease, request.allergy, request.age_group, request.gender
    )

    confidence_warning = None
    if confidence < 60:
        confidence_warning = (
            "Our confidence in this prediction is low. "
            "Your symptoms may overlap with multiple conditions. "
            "Please consult a doctor for a confirmed diagnosis."
        )

    severity_emergency = severity["level"].startswith("Severe")
    symptom_check      = check_emergency(prediction["valid"])
    combo_emergency    = symptom_check["is_emergency"]
    emergency          = severity_emergency or combo_emergency
    emergency_reason   = symptom_check["reason"] if combo_emergency else (
        "Your symptom severity score indicates a serious condition. "
        "Please seek medical attention promptly." if severity_emergency else None
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
        "warnings":           [f"'{s}' was not recognised and was ignored" for s in invalid]
    }


@app.post("/download-report")
def download_report(request: PDFRequest):
    report_data = {
        "profile": {
            "age_group": request.age_group,
            "gender":    request.gender,
            "allergy":   request.allergy,
        },
        "symptoms":           request.symptoms,
        "disease":            request.disease,
        "confidence":         request.confidence,
        "confidence_warning": request.confidence_warning,
        "emergency":          request.emergency,
        "emergency_reason":   request.emergency_reason,
        "description":        request.description,
        "severity":           request.severity,
        "precautions":        request.precautions,
        "medication":         request.medication,
        "top3":               request.top3,
        "clinical_summary":   request.clinical_summary,
    }
    pdf_bytes = generate_pdf(report_data)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=medipredict_report.pdf"}
    )


@app.get("/symptoms")
def list_symptoms():
    from backend.predictor import all_symptoms
    return {"symptoms": all_symptoms}