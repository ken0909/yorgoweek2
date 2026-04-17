"""
train.py

This script handles model training for the ML pipeline.
"""
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import joblib
import os

def train_model(cleaned_data_path: str, model_output_path: str):
    """Train a simple model and save it."""
    df = pd.read_csv(cleaned_data_path)
    # Example: Assume last column is the target
    X = df.iloc[:, :-1]
    y = df.iloc[:, -1]
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    score = model.score(X_test, y_test)
    print(f"Validation accuracy: {score:.4f}")
    joblib.dump(model, model_output_path)
    print(f"Model saved to {model_output_path}")

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Train a model.")
    parser.add_argument('--input', required=True, help='Path to cleaned data CSV')
    parser.add_argument('--output', required=True, help='Path to save trained model (joblib)')
    args = parser.parse_args()
    train_model(args.input, args.output)
