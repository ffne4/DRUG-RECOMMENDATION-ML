import pandas as pd

medication_df = pd.read_csv("data/medication.csv")
medication_df.columns = medication_df.columns.str.strip()
medication_df["disease"] = medication_df["disease"].str.strip()

for col in medication_df.columns:
    if medication_df[col].dtype == object:
        medication_df[col] = medication_df[col].str.strip()

DRUGS_UNSAFE_FOR_CHILDREN = [
    "ciprofloxacin", "doxycycline", "methotrexate", "aspirin",
    "ibuprofen", "sumatriptan", "carbimazole", "efavirenz",
    "cotrimoxazole", "hydroxychloroquine", "carvedilol",
    "prochlorperazine", "prednisolone"
]

DRUGS_CAUTION_ELDERLY = [
    "ibuprofen", "aspirin", "metformin", "glibenclamide",
    "ciprofloxacin", "nitrofurantoin", "prednisolone",
    "amlodipine", "methotrexate", "carbimazole"
]


def get_age_gender_notes(disease, age_group, gender, regimen):
    notes = []
    age = age_group.strip().lower()
    sex = gender.strip().lower()

    if age == "child":
        for drug_entry in regimen:
            drug_lower = drug_entry["drug"].lower()
            for unsafe in DRUGS_UNSAFE_FOR_CHILDREN:
                if unsafe in drug_lower:
                    notes.append(
                        f"Warning: {drug_entry['drug']} is generally not recommended "
                        f"for children. Consult a paediatrician for an appropriate alternative."
                    )
                    break

    if age == "elderly":
        for drug_entry in regimen:
            drug_lower = drug_entry["drug"].lower()
            for caution in DRUGS_CAUTION_ELDERLY:
                if caution in drug_lower:
                    notes.append(
                        f"Caution: {drug_entry['drug']} should be used carefully in "
                        f"elderly patients. Start with the lowest effective dose and monitor closely."
                    )
                    break

    return notes


def recommend_drugs(disease: str, user_allergy: str,
                    age_group: str = "adult", gender: str = "unspecified",
                    has_kidney_disease: bool = False,
                    is_pregnant: bool = False) -> dict:
    """
    Build a safe drug regimen for a disease, filtering by:
    - Allergy (penicillin, sulfa, nsaid, none)
    - Kidney disease (skip drugs with kidney_safe = no)
    - Pregnancy (skip drugs with pregnancy_safe = no)
    - Age group and gender advisories
    Returns up to 5 drugs with dosage, duration, role, and all warnings.
    """

    allergy = user_allergy.strip().lower()
    row = medication_df[medication_df["disease"] == disease]

    if row.empty:
        return {
            "regimen":          [],
            "note":             "No medication data found for this disease. Please consult a doctor.",
            "profile_notes":    [],
            "interaction_warning": None,
            "regimen_notes":    None
        }

    row = row.iloc[0]
    regimen           = []
    allergy_conflicts = []
    kidney_conflicts  = []
    pregnancy_conflicts = []

    roles = [
        "Primary treatment",
        "Supporting treatment",
        "Supplementary / symptomatic relief",
        "Additional treatment",
        "Protective supplement"
    ]

    for i, role in enumerate(roles, 1):
        drug_name     = row.get(f"drug_{i}", None)
        dosage        = row.get(f"drug_{i}_dosage", None)
        duration      = row.get(f"drug_{i}_duration", None)
        allergy_flag  = row.get(f"drug_{i}_allergy", "none")
        preg_safe     = row.get(f"drug_{i}_pregnancy_safe", "yes")
        kidney_safe   = row.get(f"drug_{i}_kidney_safe", "yes")

        if pd.isna(drug_name) or str(drug_name).strip() == "":
            continue

        drug_name    = str(drug_name).strip()
        dosage       = str(dosage).strip()   if pd.notna(dosage)      else "As directed"
        duration     = str(duration).strip() if pd.notna(duration)    else "As directed"
        allergy_flag = str(allergy_flag).strip().lower() if pd.notna(allergy_flag) else "none"
        preg_safe    = str(preg_safe).strip().lower()    if pd.notna(preg_safe)    else "yes"
        kidney_safe  = str(kidney_safe).strip().lower()  if pd.notna(kidney_safe)  else "yes"

        # Allergy check
        if allergy != "none" and allergy_flag == allergy:
            allergy_conflicts.append(drug_name)
            continue

        # Kidney disease check
        if has_kidney_disease and kidney_safe == "no":
            kidney_conflicts.append(drug_name)
            continue

        # Pregnancy check
        if is_pregnant and preg_safe == "no":
            pregnancy_conflicts.append(drug_name)
            continue

        regimen.append({
            "drug":     drug_name,
            "dosage":   dosage,
            "duration": duration,
            "role":     role
        })

    # Build main note
    note_parts = []
    if allergy_conflicts:
        note_parts.append(
            f"Removed due to {allergy} allergy: {', '.join(allergy_conflicts)}."
        )
    if kidney_conflicts:
        note_parts.append(
            f"Removed due to kidney disease: {', '.join(kidney_conflicts)}."
        )
    if pregnancy_conflicts:
        note_parts.append(
            f"Removed due to pregnancy: {', '.join(pregnancy_conflicts)}."
        )

    if not regimen:
        note = (
            f"All standard medications for {disease} were removed due to your "
            f"health conditions. Please see a doctor immediately for alternatives."
        )
    elif note_parts:
        note = " ".join(note_parts) + " The remaining drugs are safe for your profile."
    else:
        note = "Full standard treatment regimen. All drugs are safe for your profile."

    # Get interaction warning
    interaction_raw = row.get("interaction_warning", None)
    interaction_warning = (
        str(interaction_raw).strip()
        if pd.notna(interaction_raw) and str(interaction_raw).strip() not in ["", "None"]
        else None
    )

    # Get regimen notes
    notes_raw = row.get("regimen_notes", None)
    regimen_notes = (
        str(notes_raw).strip()
        if pd.notna(notes_raw) and str(notes_raw).strip() not in ["", "None"]
        else None
    )

    # Age/gender profile notes
    profile_notes = get_age_gender_notes(disease, age_group, gender, regimen)

    return {
        "regimen":             regimen,
        "note":                note,
        "profile_notes":       profile_notes,
        "interaction_warning": interaction_warning,
        "regimen_notes":       regimen_notes
    }