import pandas as pd
import joblib

from sklearn.preprocessing import OneHotEncoder, LabelEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score


# 1. Load dataset

file_path = "sri_lanka_skim_coat_dataset_5000.csv"
df = pd.read_csv(file_path)


# 2. Data cleaning
df.dropna(inplace=True)

df["Location"] = df["Location"].str.strip().str.title()
df["Brand"] = df["Brand"].str.strip().str.title()


# 3. Features and target

X = df[[
    "WallSize_sqft",
    "PricePerSqft_LKR",
    "Location"
]]

y = df["Brand"].copy()


# 4. Encode target

label_encoder = LabelEncoder()
y = label_encoder.fit_transform(y)


# 5. Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["Location"]),
        ("num", StandardScaler(), ["WallSize_sqft", "PricePerSqft_LKR"])
    ]
)


# 6. Model

rf_model = RandomForestClassifier(
    n_estimators=600,
    max_depth=18,
    min_samples_split=5,
    min_samples_leaf=2,
    class_weight="balanced",
    random_state=42,
    n_jobs=-1
)


# 7. Pipeline
pipeline = Pipeline([
    ("preprocessor", preprocessor),
    ("model", rf_model)
])


# 8. Train / Test split
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

pipeline.fit(X_train, y_train)


# 9. Evaluation
y_pred = pipeline.predict(X_test)
accuracy = accuracy_score(y_test, y_pred)

print(f"Skim Coat Brand Prediction Accuracy: {accuracy:.2f}")


# 10. Save model & encoder

joblib.dump(pipeline, "skimcoat_pipeline.pkl")
joblib.dump(label_encoder, "skimcoat_brand_encoder.pkl")

print("Skim coat model and encoder saved successfully.")


# 11. Prediction function for API

def predict_skimcoat(wall_size, price_per_sqft, location):
    pipeline = joblib.load("skimcoat_pipeline.pkl")
    label_encoder = joblib.load("skimcoat_brand_encoder.pkl")

    input_df = pd.DataFrame([{
        "WallSize_sqft": wall_size,
        "PricePerSqft_LKR": price_per_sqft,
        "Location": location.strip().title()
    }])

    prediction = pipeline.predict(input_df)
    brand = label_encoder.inverse_transform(prediction)[0]

    return {
        "skimcoat_brand": brand
    }
