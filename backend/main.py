from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from backend.predictor import predict, get_disease_description, get_precautions, get_severity_score
from backend.allergy_filter import recommend_drugs

app = FastAPI(
    title="Drug Recommendation System",
    description="Symptom-based disease diagnosis and personalised safe drug recommendation",
    version="3.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)


class PredictionRequest(BaseModel):
    symptoms:  List[str]
    allergy:   str
    age_group: str = "adult"        # child | adult | elderly
    gender:    str = "unspecified"  # male | female | unspecified


@app.get("/")
def root():
    return {"message": "Drug Recommendation System API v3.0 is running"}


@app.post("/predict")
def predict_disease(request: PredictionRequest):

    # Step 1 — validate and predict
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

    # Step 2 — description
    description = get_disease_description(disease)

    # Step 3 — precautions
    precautions = get_precautions(disease)

    # Step 4 — severity
    severity = get_severity_score(prediction["valid"])

    # Step 5 — drug regimen with allergy filter + age/gender profile
    medication = recommend_drugs(
        disease,
        request.allergy,
        request.age_group,
        request.gender
    )

    # Step 6 — confidence warning
    confidence_warning = None
    if confidence < 60:
        confidence_warning = (
            "Our confidence in this prediction is low. "
            "Your symptoms may overlap with multiple conditions. "
            "Please consult a doctor for a confirmed diagnosis."
        )

    # Step 7 — emergency flag
    emergency = severity["level"].startswith("Severe")

    return {
        "error":              False,
        "disease":            disease,
        "confidence":         f"{confidence}%",
        "confidence_warning": confidence_warning,
        "emergency":          emergency,
        "description":        description,
        "severity":           severity,
        "precautions":        precautions,
        "medication":         medication,
        "top3":               prediction.get("top3", []),
        "warnings":           [f"'{s}' was not recognised and was ignored" for s in invalid]
    }


@app.get("/symptoms")
def list_symptoms():
    from backend.predictor import all_symptoms
    return {"symptoms": all_symptoms}