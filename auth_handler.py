from typing import Tuple, Optional, Dict
import json
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class AuthHandler:
    def __init__(self):
        """Initialize authentication handler with Ory Kratos configuration"""
        self.base_url = os.getenv("ORY_SDK_URL", "").rstrip("/")
        if not self.base_url:
            raise ValueError("ORY_SDK_URL environment variable is not set")
            
        self.api_key = os.getenv("ORY_API_KEY", "")
        if not self.api_key:
            raise ValueError("ORY_API_KEY environment variable is not set")
            
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        # Print initialization info for debugging
        print(f"Initialized AuthHandler with base URL: {self.base_url}")

    def login(self, email: str, password: str) -> Tuple[bool, str, Optional[str]]:
        """
        Handle user login through Ory Kratos
        Returns: (success, message, session_token)
        """
        try:
            # Initialize login flow
            print(f"Initializing login flow for {email}")
            response = requests.get(f"{self.base_url}/self-service/login/api", headers=self.headers)
            response.raise_for_status()
            flow_data = response.json()
            flow_id = flow_data.get('id')
            
            if not flow_id:
                print("Error: No flow ID received from login flow initialization")
                return False, "Login failed: Could not initialize login flow", None
                
            print(f"Login flow initialized with ID: {flow_id}")
            
            # Submit login
            login_payload = {
                "method": "password",
                "identifier": email,
                "password": password
            }
            
            print(f"Submitting login request to: {self.base_url}/self-service/login?flow={flow_id}")
            login_response = requests.post(
                f"{self.base_url}/self-service/login?flow={flow_id}", 
                json=login_payload,
                headers=self.headers
            )
            
            print(f"Login response status: {login_response.status_code}")
            
            if login_response.status_code == 200:
                session_data = login_response.json()
                session_token = session_data.get('session_token')
                
                if session_token:
                    print("Login successful, session token received")
                    return True, "Login successful!", session_token
                    
                # Check if there's a session cookie even if no token
                cookies = login_response.cookies
                if 'ory_kratos_session' in cookies:
                    print("Login successful, session cookie received")
                    return True, "Login successful!", cookies['ory_kratos_session']
            
            # Try to extract error message
            try:
                error_data = login_response.json()
                error_msg = error_data.get('error', {}).get('message', 'Invalid credentials')
                print(f"Login error: {error_msg}")
                return False, f"Login failed: {error_msg}", None
            except Exception:
                print(f"Login failed with status code: {login_response.status_code}")
                return False, f"Login failed with status {login_response.status_code}", None

        except requests.RequestException as e:
            print(f"Network error during login: {str(e)}")
            return False, f"Login failed: Network error - {str(e)}", None
        except Exception as e:
            print(f"Unexpected error during login: {str(e)}")
            return False, f"An unexpected error occurred: {str(e)}", None

    def register(self, email: str, password: str, name: str) -> Tuple[bool, str]:
        """
        Handle user registration through Ory Kratos
        Returns: (success, message)
        """
        try:
            # Initialize registration flow
            print(f"Initializing registration flow for {email}")
            response = requests.get(f"{self.base_url}/self-service/registration/api", headers=self.headers)
            response.raise_for_status()
            flow_data = response.json()
            flow_id = flow_data.get('id')
            
            if not flow_id:
                print("Error: No flow ID received from registration flow initialization")
                return False, "Registration failed: Could not initialize registration flow"
                
            print(f"Registration flow initialized with ID: {flow_id}")
            
            # Dump the full flow data to analyze
            with open('registration_flow.json', 'w') as f:
                json.dump(flow_data, f, indent=2)
                print("Saved registration flow data to registration_flow.json for debugging")
            
            # Try a simpler approach with just email and password
            registration_payload = {
                "method": "password",
                "password": password,
                "traits": {
                    "email": email
                }
            }
            
            # Add CSRF token if found
            csrf_token = None
            for node in flow_data.get('ui', {}).get('nodes', []):
                if node.get('attributes', {}).get('name') == 'csrf_token':
                    csrf_token = node.get('attributes', {}).get('value')
                    break
                    
            if csrf_token:
                registration_payload["csrf_token"] = csrf_token
                print(f"CSRF token found and added to registration payload")

            # Submit registration with debug output
            print(f"Submitting registration request to: {self.base_url}/self-service/registration?flow={flow_id}")
            print(f"Registration payload: {json.dumps(registration_payload, indent=2)}")
            
            registration_response = requests.post(
                f"{self.base_url}/self-service/registration?flow={flow_id}", 
                json=registration_payload,
                headers=self.headers
            )
            
            # Debug output
            print(f"Registration response status: {registration_response.status_code}")
            print(f"Registration response body: {registration_response.text}")
            
            # Save the registration response for detailed analysis
            try:
                with open('registration_response.json', 'w') as f:
                    json.dump(registration_response.json(), f, indent=2)
                    print("Saved registration response to registration_response.json for debugging")
            except:
                print("Could not save response as JSON, it may not be valid JSON format")
            
            if registration_response.status_code == 200:
                print("Registration successful")
                return True, "Registration successful! Please login."
            
            # Try to extract error message
            try:
                error_data = registration_response.json()
                
                # Check if there's a specific error message
                error_msg = error_data.get('error', {}).get('message')
                if error_msg:
                    print(f"Registration error: {error_msg}")
                    return False, f"Registration failed: {error_msg}"
                
                # Check for UI error messages
                ui_errors = []
                for node in error_data.get('ui', {}).get('nodes', []):
                    if 'messages' in node:
                        for msg in node['messages']:
                            ui_errors.append(msg.get('text', ''))
                
                if ui_errors:
                    error_str = ', '.join(ui_errors)
                    print(f"Registration UI errors: {error_str}")
                    return False, f"Registration failed: {error_str}"
                
                # Check for any errors in the response text
                if "error" in registration_response.text.lower():
                    print("Found error in response text")
                    return False, "Registration failed: Error in response. See logs for details."
                
            except Exception as e:
                print(f"Error parsing registration response: {str(e)}")
            
            print(f"Registration failed with unknown error or invalid schema configuration")
            if 'name' in registration_response.text:
                return False, "Registration failed: The 'name' field is not allowed in this Ory configuration. Try registering without a name."
            return False, "Registration failed. Try using only email and password."

        except requests.RequestException as e:
            print(f"Network error during registration: {str(e)}")
            return False, f"Registration failed: Network error - {str(e)}"
        except Exception as e:
            print(f"Unexpected error during registration: {str(e)}")
            return False, f"An unexpected error occurred: {str(e)}"

    def validate_session(self, session_token: str) -> Tuple[bool, Optional[Dict]]:
        """
        Validate a session token and return user information
        Returns: (is_valid, user_data)
        """
        try:
            if not session_token:
                print("Warning: Empty session token provided to validate_session")
                return False, None
                
            print(f"Validating session token: {session_token[:10]}...")
                
            # Try cookie-based auth first
            headers = {
                **self.headers,
                "Cookie": f"ory_kratos_session={session_token}"
            }
            
            print(f"Making whoami request to: {self.base_url}/sessions/whoami")
            response = requests.get(
                f"{self.base_url}/sessions/whoami", 
                headers=headers
            )
            
            print(f"Session validation response status: {response.status_code}")
            
            # If cookie auth fails, try token-based auth
            if response.status_code != 200:
                headers = {
                    **self.headers,
                    "Authorization": f"Bearer {session_token}"
                }
                
                print("Trying token-based auth instead")
                response = requests.get(
                    f"{self.base_url}/sessions/whoami", 
                    headers=headers
                )
                
                print(f"Token-based validation response status: {response.status_code}")
            
            if response.status_code == 200:
                session_data = response.json()
                identity = session_data.get('identity', {})
                traits = identity.get('traits', {})
                
                user_data = {
                    "id": identity.get('id'),
                    "email": traits.get('email'),
                    "name": traits.get('name', 'User')  # Default to 'User' if name is not present
                }
                
                print(f"Session valid for user: {user_data['email']}")
                return True, user_data
                
            print(f"Session validation failed: {response.text[:100]}...")
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
            if not session_token:
                print("Warning: Empty session token provided to logout")
                return False, "Logout failed: No session token provided"
                
            print(f"Logging out session token: {session_token[:10]}...")
            
            # Try both methods of authentication
            # 1. First with the session token directly
            headers = {
                **self.headers
            }
            
            payload = {
                "session_token": session_token
            }
            
            print(f"Making logout request to: {self.base_url}/self-service/logout/api")
            response = requests.post(
                f"{self.base_url}/self-service/logout/api", 
                json=payload,
                headers=headers
            )
            
            print(f"Logout response status: {response.status_code}")
            
            # 2. If that fails, try with a cookie
            if response.status_code not in [200, 204]:
                headers = {
                    **self.headers,
                    "Cookie": f"ory_kratos_session={session_token}"
                }
                
                print("Trying cookie-based auth for logout")
                response = requests.post(
                    f"{self.base_url}/self-service/logout/browser", 
                    headers=headers,
                    allow_redirects=False
                )
                
                print(f"Cookie-based logout response status: {response.status_code}")
            
            # Check if any of the attempts succeeded
            if response.status_code in [200, 204, 302]:
                print("Logout successful")
                return True, "Logout successful!"
                
            print(f"Logout failed: {response.text[:100]}...")
            return False, f"Logout failed with status {response.status_code}"
            
        except Exception as e:
            print(f"Logout error: {str(e)}")
            return False, f"Logout failed: {str(e)}" 