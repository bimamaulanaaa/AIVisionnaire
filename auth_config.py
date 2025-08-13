import os
from dotenv import load_dotenv

load_dotenv()

# Get Firebase configuration from environment variables
FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
if not FIREBASE_API_KEY:
    raise ValueError("Please set FIREBASE_API_KEY in your .env file")

FIREBASE_AUTH_URL = "https://identitytoolkit.googleapis.com/v1"
