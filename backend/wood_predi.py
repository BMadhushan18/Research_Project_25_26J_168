import pandas as pd
import joblib

from sklearn.preprocessing import OneHotEncoder, LabelEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score

# 1. Load dataset

file_path = "wood_price_dataset_3000.csv"
df = pd.read_csv(file_path)

# 2. Data cleaning

df.dropna(inplace=True)

text_cols = ["Location", "Building Type", "Wood Species", "Wood Grade"]
for col in text_cols:
    df[col] = df[col].str.strip().str.title()


# 3. Features & targets

X = df[
    ["Price per cubic foot (LKR)", "Size (cu.ft)", "Location", "Building Type"]
]

y = df[["Wood Species", "Wood Grade"]].copy()


# 4. Encode targets

le_species = LabelEncoder()
le_grade = LabelEncoder()

y["Wood Species"] = le_species.fit_transform(y["Wood Species"])
y["Wood Grade"] = le_grade.fit_transform(y["Wood Grade"])


# 5. Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["Location", "Building Type"]),
        ("num", StandardScaler(), ["Price per cubic foot (LKR)", "Size (cu.ft)"])
    ]
)

# 6. Model (CORRECT MultiOutput)
model = MultiOutputClassifier(
    RandomForestClassifier(
        n_estimators=500,
        max_depth=15,
        min_samples_split=4,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
        n_jobs=-1
    )
)

pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", model)
])


# 7. Train/Test Split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline.fit(X_train, y_train)


# 8. Evaluation
y_pred = pipeline.predict(X_test)

species_acc = accuracy_score(y_test["Wood Species"], y_pred[:, 0])
grade_acc = accuracy_score(y_test["Wood Grade"], y_pred[:, 1])

print(f"Wood Species Accuracy: {species_acc:.2f}")
print(f"Wood Grade Accuracy: {grade_acc:.2f}")


# 9. Save model & encoders

joblib.dump(pipeline, "wood_pipeline.pkl")
joblib.dump(le_species, "le_species.pkl")
joblib.dump(le_grade, "le_grade.pkl")

print("Model and encoders saved successfully.")


# 10. Prediction function for API

def predict_wood(price, size, location, building_type):
    pipeline = joblib.load("wood_pipeline.pkl")
    le_species = joblib.load("le_species.pkl")
    le_grade = joblib.load("le_grade.pkl")

    input_df = pd.DataFrame([{
        "Price per cubic foot (LKR)": price,
        "Size (cu.ft)": size,
        "Location": location.strip().title(),
        "Building Type": building_type.strip().title()
    }])

    prediction = pipeline.predict(input_df)

    species = le_species.inverse_transform([prediction[0][0]])[0]
    grade = le_grade.inverse_transform([prediction[0][1]])[0]

    return {
        "wood_species": species,
        "wood_grade": grade
    }
