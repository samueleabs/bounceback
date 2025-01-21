import os
import json
import firebase_admin
from firebase_admin import credentials

# Load Firebase service account key from environment variable
if 'FIREBASE_SERVICE_ACCOUNT_KEY_PATH' in os.environ:
    cred = credentials.Certificate(os.environ['FIREBASE_SERVICE_ACCOUNT_KEY_PATH'])
elif 'FIREBASE_SERVICE_ACCOUNT_KEY' in os.environ:
    service_account_info = json.loads(os.environ['FIREBASE_SERVICE_ACCOUNT_KEY'])
    cred = credentials.Certificate(service_account_info)
else:
    raise ValueError("Firebase service account key not found in environment variables")

# Initialize the Firebase app
firebase_admin.initialize_app(cred)