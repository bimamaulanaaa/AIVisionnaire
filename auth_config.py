import os
from dotenv import load_dotenv
import ory_kratos_client
from ory_kratos_client.api import frontend_api
from ory_kratos_client.api import identity_api

load_dotenv()

# Get Ory configuration from environment variables
ORY_PROJECT_URL = os.getenv("ORY_SDK_URL")  # Use ORY_SDK_URL from your .env
ORY_API_KEY = os.getenv("ORY_API_KEY")

if not ORY_PROJECT_URL or not ORY_API_KEY:
    raise ValueError("Please set ORY_PROJECT_URL and ORY_API_KEY in your .env file")

def get_kratos_api():
    configuration = ory_kratos_client.Configuration(
        host=ORY_PROJECT_URL
    )
    configuration.api_key['ory_kratos_session'] = ORY_API_KEY
    return frontend_api.FrontendApi(ory_kratos_client.ApiClient(configuration))

def get_kratos_admin_api():
    configuration = ory_kratos_client.Configuration(
        host=ORY_PROJECT_URL
    )
    configuration.api_key['oryAccessToken'] = ORY_API_KEY
    return identity_api.IdentityApi(ory_kratos_client.ApiClient(configuration)) 