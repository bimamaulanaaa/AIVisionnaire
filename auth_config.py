import os
from dotenv import load_dotenv
from ory_kratos_client import Configuration
from ory_kratos_client.api import frontend_api, identity_api
from ory_kratos_client.api_client import ApiClient

load_dotenv()

# Ory Cloud configuration
ORY_PROJECT_URL = os.getenv('ORY_PROJECT_URL')
ORY_API_KEY = os.getenv('ORY_API_KEY')

if not ORY_PROJECT_URL or not ORY_API_KEY:
    raise ValueError("Please set ORY_PROJECT_URL and ORY_API_KEY in your .env file")

def get_kratos_api():
    """Initialize and return Kratos API client"""
    config = Configuration(
        host=ORY_PROJECT_URL,
        access_token=ORY_API_KEY
    )
    with ApiClient(config) as api_client:
        return frontend_api.FrontendApi(api_client)

def get_kratos_admin_api():
    """Initialize and return Kratos Admin API client"""
    config = Configuration(
        host=ORY_PROJECT_URL,
        access_token=ORY_API_KEY
    )
    with ApiClient(config) as api_client:
        return identity_api.IdentityApi(api_client) 