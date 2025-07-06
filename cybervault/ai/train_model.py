"""
Train a Random Forest model for fraud detection on synthetic data and export with joblib
"""
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import numpy as np
import joblib

# Generate synthetic data: [amount, type (0=loan, 1=payment), time_of_day], label (0=not fraud, 1=fraud)
X = np.random.randint(1, 10000, (1000, 1))
types = np.random.randint(0, 2, (1000, 1))
times = np.random.randint(0, 24, (1000, 1))
X = np.hstack([X, types, times])
y = ((X[:,0] > 8000) & (X[:,1] == 0) & (X[:,2] < 6)).astype(int)  # High loan at night = fraud

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2)
clf = RandomForestClassifier(n_estimators=10, max_depth=4)
clf.fit(X_train, y_train)
print('Accuracy:', accuracy_score(y_test, clf.predict(X_test)))
joblib.dump(clf, 'fraud_model.joblib')
