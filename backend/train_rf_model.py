import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib
import os

def main():
    # 1. Connect to the database
    # Assuming this script runs from inside the 'backend' directory
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'data', 'solar.db')
    
    if not os.path.exists(db_path):
        print(f"Database not found at {db_path}")
        return

    print(f"Connecting to DB at: {db_path}")
    conn = sqlite3.connect(db_path)

    # 2. Load data into a Pandas DataFrame
    # Note: Using load_pct as 'load' to match what your routes expect
    query = "SELECT voltage, current, load_pct as load, temperature, status FROM alerts"
    df = pd.read_sql_query(query, conn)
    conn.close()

    # Check if we have data
    if len(df) == 0:
        print("Error: No data found in the database. Ensure the database has entries.")
        return

    print(f"\nLoaded {len(df)} rows from the database.")
    print("\nClass distribution:")
    print(df['status'].value_counts())

    # 3. Preprocess the Data
    # Drop rows with nulls if any exist
    df.dropna(inplace=True)

    # Separate features (X) and target labels (y)
    X = df[['voltage', 'current', 'load', 'temperature']]
    y = df['status']

    # Splitting into training and testing sets (80% train, 20% test)
    # Using stratify=y to ensure all classes are represented proportionally in both sets
    # We may need to catch ValueError if some classes only have 1 instance
    try:
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
    except ValueError:
        print("\nNote: Small classes detected. Falling back to non-stratified split.")
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    # 4. Train the Random Forest
    print("\nTraining Random Forest model...")
    # n_estimators=100 means 100 decision trees
    rf_classifier = RandomForestClassifier(n_estimators=100, random_state=42, class_weight='balanced')
    rf_classifier.fit(X_train, y_train)

    # 5. Evaluate the model
    print("\nEvaluating model on test data...")
    y_pred = rf_classifier.predict(X_test)
    print(f"Accuracy: {accuracy_score(y_test, y_pred) * 100:.2f}%\n")
    print("Classification Report:")
    print(classification_report(y_test, y_pred, zero_division=0))

    # 6. Save the trained model
    model_dir = os.path.join(base_dir, 'models')
    os.makedirs(model_dir, exist_ok=True)
    model_path = os.path.join(model_dir, 'rf_solar_model.pkl')

    joblib.dump(rf_classifier, model_path)
    print(f"Model saved successfully to: {model_path}")

    # Optional: Try a sample prediction to verify everything works
    sample_data = pd.DataFrame([{
        'voltage': 0.2, 
        'current': 500.0, 
        'load': 0.0, 
        'temperature': 35.0
    }])
    prediction = rf_classifier.predict(sample_data)
    print(f"\nSample Prediction for Normal Data: {prediction[0]}")

if __name__ == "__main__":
    main()
