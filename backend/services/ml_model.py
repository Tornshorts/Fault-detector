import joblib

model = joblib.load("services/fault_model.pkl")

def predict_fault(temp, voltage, current):
    prediction = model.predict([[temp, voltage, current]])
    return prediction[0]