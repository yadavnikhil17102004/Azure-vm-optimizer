import json
import urllib.parse
from urllib import request, error

CLIENT_ID = os.environ.get("ARM_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("ARM_TENANT_ID", "")
SUBSCRIPTION_ID = os.environ.get("ARM_SUBSCRIPTION_ID", "")
RESOURCE_GROUP = "ollama-rg"

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

# List VMs in resource group
vm_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Compute/virtualMachines?api-version=2021-07-01"
req = request.Request(vm_url, headers=headers, method='GET')

try:
    with request.urlopen(req) as response:
        data = json.loads(response.read().decode())
        vms = data.get('value', [])
        
        if vms:
            for vm in vms:
                print(f"✅ VM Found: {vm['name']}")
                print(f"   Size: {vm['properties']['hardwareProfile']['vmSize']}")
                print(f"   Location: {vm['location']}")
                print(f"   Provisioning State: {vm['properties']['provisioningState']}")
        else:
            print("❌ No VMs found in resource group!")
            
except error.HTTPError as e:
    print(f"Error: {e}")
    print(e.read().decode())
