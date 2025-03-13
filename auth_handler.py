from typing import Tuple, Optional, Dict
import json
import requests
from ory_kratos_client.api.frontend_api import FrontendApi
from ory_kratos_client.model.login_flow import LoginFlow
from ory_kratos_client.model.registration_flow import RegistrationFlow
from ory_kratos_client.exceptions import ApiException
from auth_config import get_kratos_api, get_kratos_admin_api

class AuthHandler:
    def __init__(self):
        self.kratos_api = get_kratos_api()
        self.kratos_admin_api = get_kratos_admin_api()
        self.base_url = self.kratos_api.api_client.configuration.host

    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Handle user login through Ory Kratos
        Returns: (success, message, session_token)
        """
        try:
            # Initialize login flow
            response = requests.get(f"{self.base_url}/self-service/login/api")
            response.raise_for_status()
            flow_data = response.json()
            
            # Submit login
            login_response = requests.post(
                f"{self.base_url}/self-service/login?flow={flow_data['id']}", 
                json={
                    "method": "password",
                    "identifier": email,
                    "password": password
                }
            )
            
            if login_response.status_code == 200:
                session_data = login_response.json()
                if 'session_token' in session_data:
                    return True, "Login successful!", session_data['session_token']
            
            error_msg = login_response.json().get('error', {}).get('message', 'Invalid credentials')
            return False, f"Login failed: {error_msg}", None

        except requests.RequestException as e:
            return False, f"Login failed: Network error", None
        except Exception as e:
            return False, f"An unexpected error occurred: {str(e)}", None

    def register(self, email: str, password: str, name: str) -> Tuple[bool, str]:
        """
        Handle user registration through Ory Kratos
        Returns: (success, message)
        """
        try:
            # Initialize registration flow
            response = requests.get(f"{self.base_url}/self-service/registration/api")
            response.raise_for_status()
            flow_data = response.json()
            
            # Get the CSRF token if available
            csrf_token = None
            for node in flow_data.get('ui', {}).get('nodes', []):
                if node.get('attributes', {}).get('name') == 'csrf_token':
                    csrf_token = node.get('attributes', {}).get('value')
                    break

            # Prepare registration payload
            registration_payload = {
                "method": "password",
                "password": password,
                "traits.email": email,
                "traits.name": name
            }
            
            # Add CSRF token if found
            if csrf_token:
                registration_payload["csrf_token"] = csrf_token

            # Submit registration with debug output
            print(f"Registration URL: {self.base_url}/self-service/registration?flow={flow_data['id']}")
            print(f"Registration payload: {json.dumps(registration_payload, indent=2)}")
            
            registration_response = requests.post(
                f"{self.base_url}/self-service/registration?flow={flow_data['id']}", 
                json=registration_payload
            )
            
            # Debug output
            print(f"Registration response status: {registration_response.status_code}")
            print(f"Registration response: {registration_response.text}")
            
            if registration_response.status_code == 200:
                return True, "Registration successful! Please login."
            
            try:
                error_data = registration_response.json()
                error_msg = error_data.get('error', {}).get('message')
                if error_msg:
                    return False, f"Registration failed: {error_msg}"
                
                # Check for UI error messages
                ui_errors = []
                for node in error_data.get('ui', {}).get('nodes', []):
                    if 'messages' in node:
                        for msg in node['messages']:
                            ui_errors.append(msg.get('text', ''))
                
                if ui_errors:
                    return False, f"Registration failed: {', '.join(ui_errors)}"
                
            except Exception as e:
                print(f"Error parsing registration response: {str(e)}")
                pass
            
            return False, "Registration failed. Please try again with different credentials."

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
            headers = {"Authorization": f"Bearer {session_token}"}
            response = requests.get(f"{self.base_url}/sessions/whoami", headers=headers)
            
            if response.status_code == 200:
                session_data = response.json()
                identity = session_data.get('identity', {})
                traits = identity.get('traits', {})
                return True, {
                    "id": identity.get('id'),
                    "email": traits.get('email'),
                    "name": traits.get('name')
                }
            return False, None
        except Exception as e:
            print(f"Session validation error: {str(e)}")
            return False, None

    def logout(self, session_token: str) -> Tuple[bool, str]:
        """
        Handle user logout
        Returns: (success, message)
        """
        try:
            response = requests.post(
                f"{self.base_url}/self-service/logout/api", 
                json={"session_token": session_token}
            )
            
            if response.status_code in [200, 204]:
                return True, "Logout successful!"
            return False, "Logout failed"
        except Exception as e:
            return False, f"Logout failed: {str(e)}" 