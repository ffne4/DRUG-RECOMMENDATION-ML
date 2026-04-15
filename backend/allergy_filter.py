import pandas as pd

# Load medication data once on startup
medication_df = pd.read_csv("data/medication.csv")
medication_df.columns = medication_df.columns.str.strip()
medication_df["disease"] = medication_df["disease"].str.strip()

for col in medication_df.columns:
    if medication_df[col].dtype == object:
        medication_df[col] = medication_df[col].str.strip()

# ─────────────────────────────────────────────
# AGE & GENDER RULES
# These are applied as advisory notes on top of the regimen.
# They do not remove drugs — they add important warnings.
# ─────────────────────────────────────────────

# Drugs that are NOT safe for children
DRUGS_UNSAFE_FOR_CHILDREN = [
    "ciprofloxacin", "doxycycline", "methotrexate",
    "aspirin", "ibuprofen", "sumatriptan",
    "methimazole", "glipizide", "efavirenz"
]

# Drugs that require extra caution in elderly patients
DRUGS_CAUTION_ELDERLY = [
    "ibuprofen", "aspirin", "metformin", "glipizide",
    "ciprofloxacin", "nitrofurantoin", "diazepam",
    "prednisolone", "amlodipine"
]

# Drugs flagged during pregnancy
DRUGS_UNSAFE_PREGNANCY = [
    "methotrexate", "doxycycline", "ciprofloxacin",
    "ibuprofen", "aspirin", "efavirenz", "ribavirin",
    "methimazole", "glipizide", "sumatriptan"
]

# Conditions more serious in certain age/gender groups
CONDITION_AGE_NOTES = {
    "child": {
        "Hypertension":   "Hypertension in children requires specialist evaluation. Dosages differ significantly from adults.",
        "Diabetes":       "Paediatric diabetes management requires specialist supervision.",
        "Heart attack":   "Cardiac events in children are rare — seek emergency care immediately.",
        "Tuberculosis":   "TB drug doses in children are weight-based. Consult a paediatrician.",
        "Arthritis":      "Juvenile arthritis requires specialist rheumatology care.",
    },
    "elderly": {
        "Hypertension":   "Elderly patients may need lower starting doses to avoid dizziness and falls.",
        "Diabetes":       "Tight glucose control in the elderly increases fall risk. Discuss targets with your doctor.",
        "Hypoglycemia":   "Elderly patients are at higher risk — ensure regular meal schedules.",
        "Osteoarthritis": "Avoid prolonged NSAID use in elderly patients — increases kidney and GI risk.",
        "Pneumonia":      "Elderly patients with pneumonia should be monitored closely for rapid deterioration.",
    }
}

CONDITION_GENDER_NOTES = {
    "female": {
        "Urinary tract infection": "UTIs are significantly more common in females. Ensure full course completion to prevent recurrence.",
        "Hyperthyroidism":         "Thyroid conditions are more prevalent in females. Regular thyroid function tests are advised.",
        "Hypothyroidism":          "Levothyroxine doses may need adjustment during pregnancy. Inform your doctor if pregnant.",
        "Arthritis":               "Rheumatoid arthritis is more common in females. Monitor for joint damage progression.",
        "Osteoarthritis":          "Post-menopausal females have higher osteoarthritis risk. Calcium and Vitamin D are important.",
        "Migraine":                "Hormonal changes can trigger migraines in females. Track your cycle alongside symptoms.",
    },
    "male": {
        "Heart attack":   "Males have higher cardiovascular risk. Lifestyle changes are critical alongside medication.",
        "Hypertension":   "Males tend to develop hypertension earlier. Regular monitoring is strongly advised.",
        "Tuberculosis":   "TB incidence is higher in males. Ensure full treatment course to prevent drug resistance.",
    }
}


def get_age_gender_notes(disease: str, age_group: str, gender: str, regimen: list) -> list:
    """
    Returns a list of advisory notes based on the patient's age group and gender.
    These are informational — they do not remove any drugs from the regimen.
    """
    notes = []
    age   = age_group.strip().lower()
    sex   = gender.strip().lower()

    # Check for unsafe drugs in children
    if age == "child":
        for drug_entry in regimen:
            drug_lower = drug_entry["drug"].lower()
            for unsafe in DRUGS_UNSAFE_FOR_CHILDREN:
                if unsafe in drug_lower:
                    notes.append(
                        f"Warning: {drug_entry['drug']} is generally not recommended for children. "
                        f"Consult a paediatrician for an appropriate alternative."
                    )

    # Check for caution drugs in elderly
    if age == "elderly":
        for drug_entry in regimen:
            drug_lower = drug_entry["drug"].lower()
            for caution in DRUGS_CAUTION_ELDERLY:
                if caution in drug_lower:
                    notes.append(
                        f"Caution: {drug_entry['drug']} should be used carefully in elderly patients. "
                        f"Start with the lowest effective dose and monitor closely."
                    )

    # Check for pregnancy warnings in females
    if sex == "female":
        for drug_entry in regimen:
            drug_lower = drug_entry["drug"].lower()
            for unsafe in DRUGS_UNSAFE_PREGNANCY:
                if unsafe in drug_lower:
                    notes.append(
                        f"Pregnancy Warning: {drug_entry['drug']} may not be safe during pregnancy. "
                        f"Inform your doctor if you are pregnant or planning to conceive."
                    )

    # Add condition-specific age note
    if age in CONDITION_AGE_NOTES:
        if disease in CONDITION_AGE_NOTES[age]:
            notes.append(CONDITION_AGE_NOTES[age][disease])

    # Add condition-specific gender note
    if sex in CONDITION_GENDER_NOTES:
        if disease in CONDITION_GENDER_NOTES[sex]:
            notes.append(CONDITION_GENDER_NOTES[sex][disease])

    return notes


def recommend_drugs(disease: str, user_allergy: str, age_group: str = "adult", gender: str = "unspecified") -> dict:
    """
    Given a predicted disease, allergy, age group, and gender,
    return a full drug regimen with dosages, durations,
    and personalized age/gender advisory notes.
    """

    allergy = user_allergy.strip().lower()

    row = medication_df[medication_df["disease"] == disease]

    if row.empty:
        return {
            "regimen":      [],
            "note":         "No medication data found for this disease. Please consult a doctor.",
            "profile_notes": []
        }

    row = row.iloc[0]
    regimen           = []
    allergy_conflicts = []

    for i in ["1", "2", "3"]:
        drug_name = row.get(f"drug_{i}", None)
        dosage    = row.get(f"drug_{i}_dosage", None)
        duration  = row.get(f"drug_{i}_duration", None)
        flag      = row.get(f"allergy_flag_{i}", "none")

        if pd.isna(drug_name) or str(drug_name).strip() == "":
            continue

        drug_name = str(drug_name).strip()
        dosage    = str(dosage).strip() if pd.notna(dosage) else "As directed"
        duration  = str(duration).strip() if pd.notna(duration) else "As directed"
        flag      = str(flag).strip().lower() if pd.notna(flag) else "none"

        if allergy != "none" and flag == allergy:
            allergy_conflicts.append(drug_name)
            continue

        regimen.append({
            "drug":     drug_name,
            "dosage":   dosage,
            "duration": duration,
            "role":     get_drug_role(i)
        })

    # Build main note
    if len(regimen) == 0:
        note = (
            f"All standard medications for {disease} conflict with your {allergy} allergy. "
            f"Please see a doctor immediately for an alternative treatment plan."
        )
    elif allergy_conflicts:
        skipped = ", ".join(allergy_conflicts)
        note = f"Safe regimen for your {allergy} allergy. Skipped: {skipped} (conflicts with your allergy)."
    elif allergy == "none":
        note = "Full standard treatment regimen. No allergy restrictions applied."
    else:
        note = f"All medications in this regimen are safe for {allergy} allergy."

    # Get age and gender advisory notes
    profile_notes = get_age_gender_notes(disease, age_group, gender, regimen)

    return {
        "regimen":       regimen,
        "note":          note,
        "profile_notes": profile_notes
    }


def get_drug_role(index: str) -> str:
    roles = {
        "1": "Primary treatment",
        "2": "Supporting treatment",
        "3": "Supplementary / symptomatic relief"
    }
    return roles.get(index, "Additional medication")