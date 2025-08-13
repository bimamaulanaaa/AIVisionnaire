from typing import Tuple, Optional, Dict
import os
import requests
from dotenv import load_dotenv

load_dotenv()

class AuthHandler:
    def __init__(self):
        """Initialize authentication handler with Firebase configuration"""
        self.api_key = os.getenv("FIREBASE_API_KEY")
        if not self.api_key:
            raise ValueError("FIREBASE_API_KEY environment variable is not set")

        self.base_url = "https://identitytoolkit.googleapis.com/v1"

    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Handle user login through Firebase Authentication
        Returns: (success, message, id_token)
        """
        try:
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True
            }
            response = requests.post(
                f"{self.base_url}/accounts:signInWithPassword?key={self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                data = response.json()
                return True, "Login successful!", data.get("idToken")
            error_msg = response.json().get("error", {}).get("message", "Invalid credentials")
            return False, f"Login failed: {error_msg}", None
        except requests.RequestException as e:
            return False, f"Login failed: Network error - {str(e)}", None
        except Exception as e:
            return False, f"An unexpected error occurred: {str(e)}", None

    def register(self, email: str, password: str, name: str) -> Tuple[bool, str]:
        """
        Handle user registration through Firebase Authentication
        Returns: (success, message)
        """
        try:
            payload = {
                "email": email,
                "password": password,
                "returnSecureToken": True,
                "displayName": name
            }
            response = requests.post(
                f"{self.base_url}/accounts:signUp?key={self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                return True, "Registration successful! Please login."
            error_msg = response.json().get("error", {}).get("message", "Registration failed")
            return False, f"Registration failed: {error_msg}"
        except requests.RequestException as e:
            return False, f"Registration failed: Network error - {str(e)}"
        except Exception as e:
            return False, f"An unexpected error occurred: {str(e)}"

    def validate_session(self, session_token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a session token and return user information
        Returns: (is_valid, user_data)
        """
        try:
            if not session_token:
                return False, None

            payload = {"idToken": session_token}
            response = requests.post(
                f"{self.base_url}/accounts:lookup?key={self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                users = response.json().get("users", [])
                if users:
                    user = users[0]
                    user_data = {
                        "id": user.get("localId"),
                        "email": user.get("email"),
                        "name": user.get("displayName", "User")
                    }
                    return True, user_data
            return False, None
        except Exception as e:
            print(f"Session validation error: {str(e)}")
            return False, None

    def logout(self, session_token: str) -> Tuple[bool, str]:
        """
        Handle user logout. Firebase tokens are client-managed,
        so this simply invalidates the token on the server.
        Returns: (success, message)
        """
        try:
            if not session_token:
                return False, "Logout failed: No session token provided"

            payload = {"idToken": session_token}
            response = requests.post(
                f"{self.base_url}/accounts:signOut?key={self.api_key}",
                json=payload
            )

            if response.status_code == 200:
                return True, "Logout successful!"
            return False, "Logout failed"
        except Exception as e:
            return False, f"Logout failed: {str(e)}"
