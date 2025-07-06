"""
CyberVault AI Fraud Detection - Real model loading and inference
"""
import joblib
import numpy as np
import os

MODEL_PATH = os.path.join(os.path.dirname(__file__), 'fraud_model.joblib')
if os.path.exists(MODEL_PATH):
    clf = joblib.load(MODEL_PATH)
else:
    clf = None

def predict_fraud(transaction):
    # transaction: {amount, type}
    if not clf:
        return False
    try:
        amount = int(transaction.get('amount', 0))
        tx_type = 0 if transaction.get('type', 'loan') == 'loan' else 1
        hour = 12  # Placeholder: could be extracted from timestamp
        X = np.array([[amount, tx_type, hour]])
        return bool(clf.predict(X)[0])
    except Exception:
        return False
