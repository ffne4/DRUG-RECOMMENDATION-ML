import joblib
import pandas as pd
import numpy as np

print("Loading model and data files...")

model        = joblib.load("model/disease_model.pkl")
all_symptoms = joblib.load("model/symptoms_list.pkl")
severity_map = joblib.load("model/severity_map.pkl")

description_df = pd.read_csv("data/symptom_Description.csv")
precaution_df  = pd.read_csv("data/symptom_precaution.csv")
severity_df    = pd.read_csv("data/Symptom-severity.csv")

description_df.columns = description_df.columns.str.strip()
precaution_df.columns  = precaution_df.columns.str.strip()
severity_df.columns    = severity_df.columns.str.strip()

description_df["Disease"] = description_df["Disease"].str.strip()
precaution_df["Disease"]  = precaution_df["Disease"].str.strip()
severity_df["Symptom"]    = severity_df["Symptom"].str.strip().str.lower().str.replace(" ", "_")

print("All files loaded successfully.")


def get_disease_description(disease: str) -> str:
    row = description_df[description_df["Disease"] == disease]
    if row.empty:
        return "No description available."
    return row.iloc[0]["Description"].strip()


def get_precautions(disease: str) -> list:
    row = precaution_df[precaution_df["Disease"] == disease]
    if row.empty:
        return ["No precautions available."]
    precautions = []
    for col in ["Precaution_1", "Precaution_2", "Precaution_3", "Precaution_4"]:
        val = row.iloc[0].get(col, None)
        if pd.notna(val) and str(val).strip() != "":
            precautions.append(str(val).strip())
    return precautions


def get_severity_score(user_symptoms: list) -> dict:
    total = 0
    found = 0
    for symptom in user_symptoms:
        clean  = symptom.strip().lower().replace(" ", "_")
        weight = severity_map.get(clean, 0)
        if weight > 0:
            total += weight
            found += 1

    if total == 0:
        level = "Unknown"
    elif total <= 10:
        level = "Mild"
    elif total <= 20:
        level = "Moderate"
    else:
        level = "Severe — please seek medical attention"

    return {
        "score":            total,
        "symptoms_matched": found,
        "level":            level
    }


def predict(user_symptoms: list) -> dict:
    cleaned_user = [s.strip().lower().replace(" ", "_") for s in user_symptoms]

    valid_symptoms   = [s for s in cleaned_user if s in all_symptoms]
    invalid_symptoms = [s for s in cleaned_user if s not in all_symptoms]

    if len(valid_symptoms) == 0:
        return {
            "error":   True,
            "message": "None of the symptoms you entered are recognised. Please choose from the known symptom list.",
            "invalid": invalid_symptoms,
            "valid":   []
        }

    # Build weighted input vector — same encoding as training
    input_vector = [
        severity_map.get(s, 1) if s in valid_symptoms else 0
        for s in all_symptoms
    ]
    input_array = np.array(input_vector).reshape(1, -1)

    # Get probabilities for all diseases
    probabilities = model.predict_proba(input_array)[0]
    classes       = model.classes_

    # Sort diseases by probability highest first
    disease_probs = sorted(
        zip(classes, probabilities),
        key=lambda x: x[1],
        reverse=True
    )

    # Top prediction
    predicted_disease = disease_probs[0][0]
    confidence        = round(disease_probs[0][1] * 100, 2)

    # Top 3 differential diagnoses
    top3 = [
        {
            "disease":    d,
            "confidence": f"{round(p * 100, 2)}%"
        }
        for d, p in disease_probs[:3]
    ]

    return {
        "error":      False,
        "disease":    predicted_disease,
        "confidence": confidence,
        "top3":       top3,
        "valid":      valid_symptoms,
        "invalid":    invalid_symptoms
    }