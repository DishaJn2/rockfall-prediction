import pandas as pd
import numpy as np
import joblib
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.ensemble import RandomForestClassifier

# ---------- Load Dataset ----------
df = pd.read_csv("data/slope_stability.csv")

# Check categorical columns
if "Reinforcement Type" in df.columns:
    le = LabelEncoder()
    df["Reinforcement Type"] = le.fit_transform(df["Reinforcement Type"])
    joblib.dump(le, "models/label_encoder.pkl")  # save encoder for app.py

# ---------- Features & Target ----------
X = df.drop(columns=["Factor of Safety (FS)"])   # input features
y = (df["Factor of Safety (FS)"] < 1.0).astype(int)  # 1 = Risky, 0 = Safe

# ---------- Scale ----------
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# ---------- Train/Test Split ----------
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y, test_size=0.2, random_state=42)

# ---------- Train Model ----------
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# ---------- Save Model ----------
joblib.dump(model, "models/rockfall_model.pkl")
joblib.dump(scaler, "models/scaler.pkl")

print("✅ Model trained and saved successfully!")




