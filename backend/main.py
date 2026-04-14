from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List

from backend.predictor import predict, get_disease_description, get_precautions, get_severity_score
from backend.allergy_filter import recommend_drug

# ─────────────────────────────────────────────
# CREATE THE FASTAPI APP
# ─────────────────────────────────────────────

app = FastAPI(
    title="Drug Recommendation System",
    description="Enter symptoms and allergies — get disease prediction, description, precautions, severity, and a safe drug recommendation",
    version="1.0.0"
)

# Allow the frontend (HTML file) to talk to this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

# ─────────────────────────────────────────────
# DEFINE WHAT THE FRONTEND SENDS US
# ─────────────────────────────────────────────

class PredictionRequest(BaseModel):
    symptoms: List[str]   # e.g. ["itching", "skin_rash", "fever"]
    allergy:  str         # e.g. "penicillin" or "none"

# ─────────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Drug Recommendation API is running"}


@app.post("/predict")
def predict_disease(request: PredictionRequest):
    """
    Main endpoint. Receives symptoms + allergy,
    returns disease, description, severity, precautions, and safe drug.
    """

    # Step 1: Predict — this now validates symptoms first
    prediction = predict(request.symptoms)

    # If no valid symptoms were found, return a clear error
    if prediction.get("error"):
        return {
            "error":   True,
            "message": prediction["message"],
            "invalid": prediction["invalid"]
        }

    disease    = prediction["disease"]
    confidence = prediction["confidence"]
    invalid    = prediction.get("invalid", [])

    # Step 2: Get the disease description
    description = get_disease_description(disease)

    # Step 3: Get precautions
    precautions = get_precautions(disease)

    # Step 4: Calculate severity score from valid symptoms only
    severity = get_severity_score(prediction["valid"])

    # Step 5: Recommend a safe drug based on allergy
    drug_info = recommend_drug(disease, request.allergy)

    # Step 6: Return everything as JSON
    return {
        "error":       False,
        "disease":     disease,
        "confidence":  f"{confidence}%",
        "description": description,
        "severity":    severity,
        "precautions": precautions,
        "medication":  drug_info,
        "warnings":    [f"'{s}' was not recognised and was ignored" for s in invalid]
    }


@app.get("/symptoms")
def list_symptoms():
    """Returns the full list of known symptoms — useful for the frontend dropdown."""
    from backend.predictor import all_symptoms
    return {"symptoms": all_symptoms}