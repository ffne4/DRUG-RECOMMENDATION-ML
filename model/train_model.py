import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, VotingClassifier
from sklearn.naive_bayes import MultinomialNB
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import joblib
import os
import random

random.seed(42)
np.random.seed(42)

print("Loading datasets...")

df             = pd.read_csv("data/dataset.csv")
description_df = pd.read_csv("data/symptom_Description.csv")
precaution_df  = pd.read_csv("data/symptom_precaution.csv")
severity_df    = pd.read_csv("data/Symptom-severity.csv")
medication_df  = pd.read_csv("data/medication.csv")

# ─────────────────────────────────────────────
# CLEAN
# ─────────────────────────────────────────────

df.columns             = df.columns.str.strip()
severity_df.columns    = severity_df.columns.str.strip()

df["Disease"]          = df["Disease"].str.strip()
severity_df["Symptom"] = severity_df["Symptom"].str.strip().str.lower().str.replace(" ", "_")

symptom_cols = [col for col in df.columns if col.startswith("Symptom_")]
for col in symptom_cols:
    df[col] = df[col].str.strip().str.lower().str.replace(" ", "_")

# ─────────────────────────────────────────────
# BUILD SEVERITY WEIGHT MAP
# ─────────────────────────────────────────────

# symptom -> weight (1-7). Default to 1 if not found.
severity_map = dict(zip(severity_df["Symptom"], severity_df["weight"]))

print(f"Severity weights loaded for {len(severity_map)} symptoms")

# ─────────────────────────────────────────────
# BUILD FULL SYMPTOM LIST
# ─────────────────────────────────────────────

all_symptoms = set()
for col in symptom_cols:
    all_symptoms.update(df[col].dropna().unique())
all_symptoms = sorted(list(all_symptoms))

print(f"Total unique symptoms: {len(all_symptoms)}")

# ─────────────────────────────────────────────
# BUILD DISEASE -> FULL SYMPTOM SET MAP
# ─────────────────────────────────────────────

disease_symptom_map = {}
for _, row in df.iterrows():
    disease = row["Disease"]
    symptoms = set()
    for col in symptom_cols:
        val = row[col]
        if pd.notna(val):
            symptoms.add(val)
    if disease not in disease_symptom_map:
        disease_symptom_map[disease] = set()
    disease_symptom_map[disease].update(symptoms)

print(f"Diseases found: {len(disease_symptom_map)}")

# ─────────────────────────────────────────────
# ENCODE WITH SEVERITY WEIGHTS (not just 0/1)
# ─────────────────────────────────────────────

def encode_row(present_symptoms):
    """
    Encode a set of symptoms as a weighted vector.
    Each position = severity weight if symptom present, else 0.
    """
    return [
        severity_map.get(s, 1) if s in present_symptoms else 0
        for s in all_symptoms
    ]

# ─────────────────────────────────────────────
# DATA AUGMENTATION
# ─────────────────────────────────────────────
# For each disease, generate extra training rows using random subsets
# of its full symptom list. This teaches the model to recognize
# diseases from partial symptom inputs (like real users provide).

print("Augmenting training data with partial symptom combinations...")

augmented_X = []
augmented_y = []

for disease, full_symptoms in disease_symptom_map.items():
    symptom_list = list(full_symptoms)
    n = len(symptom_list)

    if n == 0:
        continue

    # Always add the full symptom set
    augmented_X.append(encode_row(full_symptoms))
    augmented_y.append(disease)

    # Generate partial combinations
    # More symptoms = more augmentation variations
    num_augments = max(20, n * 5)

    for _ in range(num_augments):
        # Pick a random subset — at least 2 symptoms, at most all of them
        k = random.randint(max(2, n // 3), n)
        subset = set(random.sample(symptom_list, k))
        augmented_X.append(encode_row(subset))
        augmented_y.append(disease)

X = np.array(augmented_X)
y = np.array(augmented_y)

print(f"Augmented dataset size: {X.shape[0]} rows, {X.shape[1]} features")
print(f"Diseases: {len(set(y))}")

# ─────────────────────────────────────────────
# TRAIN / TEST SPLIT
# ─────────────────────────────────────────────

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"Training rows: {len(X_train)}, Testing rows: {len(X_test)}")

# ─────────────────────────────────────────────
# TRAIN ENSEMBLE OF THREE MODELS
# ─────────────────────────────────────────────
# Each model votes. Majority wins. This gives much higher
# confidence on partial symptom inputs.

print("Training ensemble model (Random Forest + Gradient Boosting + Naive Bayes)...")

rf  = RandomForestClassifier(n_estimators=200, random_state=42, n_jobs=-1)
gb  = GradientBoostingClassifier(n_estimators=100, random_state=42)
nb  = MultinomialNB()

ensemble = VotingClassifier(
    estimators=[("rf", rf), ("gb", gb), ("nb", nb)],
    voting="soft"   # soft voting averages probabilities — more confident results
)

ensemble.fit(X_train, y_train)

# ─────────────────────────────────────────────
# EVALUATE
# ─────────────────────────────────────────────

y_pred   = ensemble.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)
print(f"Ensemble model accuracy: {accuracy * 100:.2f}%")

# ─────────────────────────────────────────────
# SAVE
# ─────────────────────────────────────────────

os.makedirs("model", exist_ok=True)

joblib.dump(ensemble,     "model/disease_model.pkl")
joblib.dump(all_symptoms, "model/symptoms_list.pkl")
joblib.dump(severity_map, "model/severity_map.pkl")

print("Saved: model/disease_model.pkl")
print("Saved: model/symptoms_list.pkl")
print("Saved: model/severity_map.pkl")
print("Training complete!")