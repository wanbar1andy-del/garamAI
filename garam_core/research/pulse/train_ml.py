# garam_core/research/pulse/train_ml.py
import numpy as np
import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import classification_report
try:
    import joblib
except ImportError:
    # Fallback or error if joblib not present, but standard in sklearn context often
    pass

def train_ml_model(features: pd.DataFrame, labels: pd.Series):
    """
    Trains a Gradient Boosting Classifier.
    Splits: 70% Train, 15% Val, 15% Test.
    """
    model = GradientBoostingClassifier()
    
    n = len(features)
    train_end = int(n * 0.7)
    val_end   = int(n * 0.85)
    
    X_train, y_train = features.iloc[:train_end], labels.iloc[:train_end]
    X_val, y_val     = features.iloc[train_end:val_end], labels.iloc[train_end:val_end]
    
    print(f"Training on {len(X_train)} samples, Validating on {len(X_val)} samples...")
    model.fit(X_train, y_train)
    
    preds = model.predict(X_val)
    print("Optimization Validation Classification Report:")
    print(classification_report(y_val, preds))
    
    return model
