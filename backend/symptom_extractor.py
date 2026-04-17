"""
Local symptom extractor — no external API needed.
Scans the patient narrative for keywords and phrases
that map to known symptoms in our dataset.
"""

# ─────────────────────────────────────────────
# KEYWORD MAP
# Plain English words/phrases a Ugandan patient
# might use → matched symptom name in our dataset
# ─────────────────────────────────────────────

KEYWORD_MAP = {
    # Fever / temperature
    "fever":                  "high_fever",
    "very hot":               "high_fever",
    "feeling hot":            "high_fever",
    "body is hot":            "high_fever",
    "temperature":            "high_fever",
    "mild fever":             "mild_fever",
    "slight fever":           "mild_fever",
    "burning up":             "high_fever",
    "chills":                 "chills",
    "shivering":              "chills",
    "shaking with cold":      "chills",
    "feeling cold":           "chills",

    # Pain
    "headache":               "headache",
    "head is paining":        "headache",
    "head pain":              "headache",
    "head ache":              "headache",
    "my head":                "headache",
    "body pain":              "muscle_pain",
    "body is paining":        "muscle_pain",
    "body ache":              "muscle_pain",
    "muscle pain":            "muscle_pain",
    "joint pain":             "joint_pain",
    "joints are paining":     "joint_pain",
    "back pain":              "back_pain",
    "back is paining":        "back_pain",
    "stomach pain":           "abdominal_pain",
    "stomach is paining":     "abdominal_pain",
    "abdominal pain":         "abdominal_pain",
    "belly pain":             "abdominal_pain",
    "chest pain":             "chest_pain",
    "chest is paining":       "chest_pain",
    "chest tightness":        "chest_pain",

    # Digestive
    "vomiting":               "vomiting",
    "throwing up":            "vomiting",
    "i vomit":                "vomiting",
    "keeps vomiting":         "vomiting",
    "nausea":                 "nausea",
    "feeling like vomiting":  "nausea",
    "want to vomit":          "nausea",
    "diarrhoea":              "diarrhoea",
    "diarrhea":               "diarrhoea",
    "running stomach":        "diarrhoea",
    "loose stool":            "diarrhoea",
    "no appetite":            "loss_of_appetite",
    "not eating":             "loss_of_appetite",
    "lost appetite":          "loss_of_appetite",
    "cannot eat":             "loss_of_appetite",
    "don't feel like eating": "loss_of_appetite",
    "constipation":           "constipation",
    "not passing stool":      "constipation",
    "indigestion":            "indigestion",
    "heartburn":              "acidity",
    "stomach burns":          "acidity",
    "bloating":               "stomach_bleeding",

    # Skin
    "itching":                "itching",
    "body itches":            "itching",
    "skin itches":            "itching",
    "scratching":             "itching",
    "rash":                   "skin_rash",
    "skin rash":              "skin_rash",
    "skin has bumps":         "skin_rash",
    "pimples":                "acne",
    "spots on skin":          "skin_rash",
    "yellow eyes":            "yellowing_of_eyes",
    "eyes are yellow":        "yellowing_of_eyes",
    "yellowish eyes":         "yellowing_of_eyes",
    "yellow skin":            "yellowish_skin",
    "skin is yellow":         "yellowish_skin",
    "skin has turned yellow": "yellowish_skin",
    "dark urine":             "dark_urine",
    "urine is dark":          "dark_urine",
    "brown urine":            "dark_urine",
    "swelling":               "swelling_joints",
    "swollen":                "swollen_legs",
    "feet are swollen":       "swollen_legs",
    "pale skin":              "pallor",

    # Breathing / chest
    "shortness of breath":    "breathlessness",
    "short of breath":        "breathlessness",
    "breathing problem":      "breathlessness",
    "difficult to breathe":   "breathlessness",
    "hard to breathe":        "breathlessness",
    "breathing is hard":      "breathlessness",
    "cough":                  "cough",
    "coughing":               "cough",
    "dry cough":              "cough",
    "wet cough":              "mucoid_sputum",
    "phlegm":                 "mucoid_sputum",
    "sputum":                 "mucoid_sputum",
    "wheezing":               "breathlessness",
    "runny nose":             "runny_nose",
    "nose is running":        "runny_nose",
    "blocked nose":           "congestion",
    "stuffy nose":            "congestion",
    "sore throat":            "throat_irritation",
    "throat is paining":      "throat_irritation",
    "throat pain":            "throat_irritation",

    # Weakness / energy
    "fatigue":                "fatigue",
    "tired":                  "fatigue",
    "weakness":               "weakness_in_limbs",
    "body is weak":           "fatigue",
    "weak":                   "fatigue",
    "no energy":              "fatigue",
    "feeling weak":           "fatigue",
    "exhausted":              "fatigue",
    "cannot do anything":     "fatigue",
    "dizziness":              "dizziness",
    "feeling dizzy":          "dizziness",
    "head is spinning":       "dizziness",
    "blackout":               "loss_of_balance",
    "fainting":               "loss_of_balance",
    "fell down":              "loss_of_balance",

    # Eyes / vision
    "blurred vision":         "blurred_and_distorted_vision",
    "cannot see well":        "blurred_and_distorted_vision",
    "vision is blurred":      "blurred_and_distorted_vision",
    "eyes are red":           "redness_of_eyes",
    "red eyes":               "redness_of_eyes",

    # Urinary
    "painful urination":      "burning_micturition",
    "burns when urinating":   "burning_micturition",
    "pain when passing urine":"burning_micturition",
    "frequent urination":     "polyuria",
    "urinating too much":     "polyuria",
    "passing urine often":    "polyuria",

    # Mental / neurological
    "anxiety":                "anxiety",
    "worried":                "anxiety",
    "stress":                 "anxiety",
    "cannot sleep":           "irregular_sugar_level",
    "insomnia":               "irregular_sugar_level",
    "confusion":              "lack_of_concentration",
    "forgetful":              "lack_of_concentration",
    "memory loss":            "lack_of_concentration",
    "depression":             "depression",
    "feeling sad":            "depression",
    "mood swings":            "mood_swings",

    # Weight
    "weight loss":            "weight_loss",
    "losing weight":          "weight_loss",
    "weight gain":            "weight_gain",
    "gaining weight":         "weight_gain",

    # Other common
    "sweating":               "sweating",
    "sweats a lot":           "sweating",
    "night sweats":           "sweating",
    "fast heartbeat":         "fast_heart_rate",
    "heart is racing":        "fast_heart_rate",
    "palpitations":           "fast_heart_rate",
    "high blood pressure":    "hypertension",
    "sugar":                  "excessive_hunger",
    "too hungry":             "excessive_hunger",
    "always hungry":          "excessive_hunger",
    "thirsty":                "excessive_hunger",
    "always thirsty":         "excessive_hunger",
    "stiff neck":             "stiff_neck",
    "neck is stiff":          "stiff_neck",
    "painful neck":           "stiff_neck",
    "hair loss":              "hair_loss",
    "losing hair":            "hair_loss",
    "numbness":               "numbness",
    "tingling":               "tingling",
    "burning feet":           "burning_micturition",
    "wounds not healing":     "ulcers_on_tongue",
    "mouth sores":            "ulcers_on_tongue",
    "bad breath":             "altered_sensorium",
    "smell from mouth":       "altered_sensorium",
}


def extract_symptoms_from_narrative(narrative: str, known_symptoms: list) -> dict:
    """
    Scan the patient's narrative for keywords and phrases
    that map to known symptoms. Returns matched symptoms
    and a simple clinical summary.
    No external API required.
    """

    if not narrative or len(narrative.strip()) < 10:
        return {
            "extracted": [],
            "summary":   "",
            "error":     "Please describe your symptoms in more detail."
        }

    text = narrative.lower().strip()

    matched   = set()
    key_found = []

    # Scan for every keyword in our map
    for keyword, symptom in KEYWORD_MAP.items():
        if keyword in text and symptom in known_symptoms:
            matched.add(symptom)
            key_found.append(keyword)

    # Also do a direct scan for known symptom names themselves
    # (in case user types exact symptom like "fatigue" or "nausea")
    for symptom in known_symptoms:
        readable = symptom.replace("_", " ")
        if readable in text:
            matched.add(symptom)

    extracted = sorted(list(matched))

    # Build a simple clinical summary from what was found
    if extracted:
        readable_list = [s.replace("_", " ") for s in extracted]
        if len(readable_list) == 1:
            symptom_str = readable_list[0]
        elif len(readable_list) == 2:
            symptom_str = f"{readable_list[0]} and {readable_list[1]}"
        else:
            symptom_str = ", ".join(readable_list[:-1]) + f", and {readable_list[-1]}"

        summary = (
            f"Based on the patient's description, the following symptoms were identified: "
            f"{symptom_str}."
        )
    else:
        summary = ""

    if not extracted:
        return {
            "extracted": [],
            "summary":   "",
            "error": (
                "We could not find any recognisable symptoms in your description. "
                "Try adding more detail — for example mention fever, vomiting, headache, "
                "or use the symptom search box above."
            )
        }

    return {
        "extracted": extracted,
        "summary":   summary,
        "error":     None
    }