API_PREFIX = "/api/v1"
# Canonical decision thresholds. Keep in sync with phishing_detector.py
# (RISK_MEDIUM_THRESHOLD / RISK_HIGH_THRESHOLD). Currently unused by code
# paths but retained as the single documented source for clients.
RISK_THRESHOLDS = {"medium": 45, "high": 75}
