import pandas as pd
from sklearn.tree import DecisionTreeClassifier
import joblib

# Sample training data (you can improve this later)
data = {
    "temp":    [30, 35, 40, 45, 50, 55, 60],
    "voltage": [3.7, 3.6, 3.5, 3.4, 3.3, 3.2, 3.1],
    "current": [5, 7, 9, 11, 13, 15, 17],
    "label":   ["Normal", "Normal", "Warning", "Warning", "Overheating", "Overheating", "Overheating"]
}

df = pd.DataFrame(data)

X = df[["temp", "voltage", "current"]]
y = df["label"]

model = DecisionTreeClassifier()
model.fit(X, y)

# Save model
joblib.dump(model, "fault_model.pkl")

print("Model trained and saved!")