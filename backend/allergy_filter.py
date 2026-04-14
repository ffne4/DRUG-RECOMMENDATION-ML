import pandas as pd

# Load the medication data once when this file is imported
medication_df = pd.read_csv("data/medication.csv")
medication_df.columns = medication_df.columns.str.strip()
medication_df["disease"]      = medication_df["disease"].str.strip()
medication_df["drug_name"]    = medication_df["drug_name"].str.strip()
medication_df["allergy_flag"] = medication_df["allergy_flag"].str.strip().str.lower()


def recommend_drug(disease: str, user_allergy: str) -> dict:
    """
    Given a predicted disease and the user's allergy,
    return the safest drug recommendation.

    user_allergy can be:
      - "none"         → no allergy, return first available drug
      - "penicillin"   → skip any drug with allergy_flag = penicillin
      - "sulfa"        → skip any drug with allergy_flag = sulfa
      - "nsaid"        → skip any drug with allergy_flag = nsaid
    """

    # Normalize the allergy input — lowercase and strip spaces
    allergy = user_allergy.strip().lower()

    # Get all drugs available for this disease
    available = medication_df[medication_df["disease"] == disease]

    # If we have no drugs at all for this disease, say so
    if available.empty:
        return {
            "drug": "No medication data available for this disease",
            "note": "Please consult a doctor"
        }

    # If user has no allergy, return the first drug immediately
    if allergy == "none" or allergy == "":
        drug = available.iloc[0]["drug_name"]
        return {
            "drug": drug,
            "note": "No allergy reported — first available drug selected"
        }

    # Filter out drugs that conflict with the user's allergy
    safe_drugs = available[available["allergy_flag"] != allergy]

    if safe_drugs.empty:
        # Every drug for this disease conflicts — warn the user
        return {
            "drug": "No safe drug found given your allergy",
            "note": f"All available drugs for {disease} conflict with {allergy} allergy. Please see a doctor."
        }

    # Return the first safe drug
    drug = safe_drugs.iloc[0]["drug_name"]
    return {
        "drug": drug,
        "note": f"Selected because it does not conflict with {allergy} allergy"
    }