import json
import urllib.parse
from urllib import request, error

CLIENT_ID = os.environ.get("ARM_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("ARM_TENANT_ID", "")
SUBSCRIPTION_ID = os.environ.get("ARM_SUBSCRIPTION_ID", "")
RESOURCE_GROUP = "ollama-rg"
DEPLOYMENT_NAME = "ollama-sp-deploy"

# Get token
url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
data = urllib.parse.urlencode({
    'grant_type': 'client_credentials',
    'client_id': CLIENT_ID,
    'client_secret': CLIENT_SECRET,
    'resource': 'https://management.azure.com/'
}).encode('utf-8')

req = request.Request(url, data=data, method='POST')
with request.urlopen(req) as response:
    result = json.loads(response.read().decode())
    token = result['access_token']

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# Get deployment operations
ops_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}/providers/Microsoft.Resources/deployments/{DEPLOYMENT_NAME}/operations?api-version=2021-04-01"
req = request.Request(ops_url, headers=headers, method='GET')

try:
    with request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        print("Deployment Operations:")
        for op in data.get('value', []):
            props = op['properties']
            target = props.get('targetResource', {}).get('resourceName', 'N/A')
            status = props.get('provisioningState', 'N/A')
            
            print(f"\n{target}:")
            print(f"  Status: {status}")
            
            if status == 'Failed':
                error_data = props.get('statusMessage', {}).get('error', {})
                print(f"  Error Code: {error_data.get('code', 'N/A')}")
                print(f"  Error Message: {error_data.get('message', 'N/A')}")
                
except error.HTTPError as e:
    print(f"Error: {e}")
    print(e.read().decode())
