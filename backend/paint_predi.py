import pandas as pd
import joblib

from sklearn.preprocessing import OneHotEncoder, LabelEncoder, StandardScaler
from sklearn.compose import ColumnTransformer
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.multioutput import MultiOutputClassifier
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score


# 1. Load paint dataset

file_path = "sri_lanka_paint_dataset_1000.csv"
df = pd.read_csv(file_path)


# 2. Data cleaning

df.dropna(inplace=True)

df["Location"] = df["Location"].str.strip().str.title()
df["PaintBrand"] = df["PaintBrand"].str.strip().str.title()
df["PaintGrade"] = df["PaintGrade"].str.strip().str.title()


# 3. Features & Targets

X = df[["WallSize_sqft", "PricePerSqft_LKR", "Location"]]

y = df[["PaintBrand", "PaintGrade"]].copy()


# 4. Encode targets

brand_encoder = LabelEncoder()
grade_encoder = LabelEncoder()

y["PaintBrand"] = brand_encoder.fit_transform(y["PaintBrand"])
y["PaintGrade"] = grade_encoder.fit_transform(y["PaintGrade"])


# 5. Preprocessing

preprocessor = ColumnTransformer(
    transformers=[
        ("cat", OneHotEncoder(handle_unknown="ignore"), ["Location"]),
        ("num", StandardScaler(), ["WallSize_sqft", "PricePerSqft_LKR"])
    ]
)


# 6. Model (Multi-output)

model = MultiOutputClassifier(
    RandomForestClassifier(
        n_estimators=600,
        max_depth=18,
        min_samples_split=5,
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


# 7. Train / Test split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

pipeline.fit(X_train, y_train)


# 8. Evaluation

y_pred = pipeline.predict(X_test)

brand_acc = accuracy_score(y_test["PaintBrand"], y_pred[:, 0])
grade_acc = accuracy_score(y_test["PaintGrade"], y_pred[:, 1])

print(f"Paint Brand Accuracy: {brand_acc:.2f}")
print(f"Paint Grade Accuracy: {grade_acc:.2f}")


# 9. Save model & encoders

joblib.dump(pipeline, "paint_pipeline.pkl")
joblib.dump(brand_encoder, "paint_brand_encoder.pkl")
joblib.dump(grade_encoder, "paint_grade_encoder.pkl")

print("Paint model and encoders saved successfully.")


# 10. Prediction function for API

def predict_paint(wall_size, price_per_sqft, location):
    pipeline = joblib.load("paint_pipeline.pkl")
    brand_encoder = joblib.load("paint_brand_encoder.pkl")
    grade_encoder = joblib.load("paint_grade_encoder.pkl")

    input_df = pd.DataFrame([{
        "WallSize_sqft": wall_size,
        "PricePerSqft_LKR": price_per_sqft,
        "Location": location.strip().title()
    }])

    prediction = pipeline.predict(input_df)

    brand = brand_encoder.inverse_transform([prediction[0][0]])[0]
    grade = grade_encoder.inverse_transform([prediction[0][1]])[0]

    return {
        "paint_brand": brand,
        "paint_grade": grade
    }
