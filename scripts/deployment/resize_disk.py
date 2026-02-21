import json, urllib.parse, time, os
from urllib import request, error

# ============= CONFIGURATION =============
CLIENT_ID = os.environ.get("ARM_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("ARM_TENANT_ID", "")
SUBSCRIPTION_ID = os.environ.get("ARM_SUBSCRIPTION_ID", "")
RESOURCE_GROUP = "OpenClaw-RG"
VM_NAME = "OpenClaw-Pro"
NEW_SIZE_GB = 64 

def get_token():
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    auth_data = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "scope": "https://management.azure.com/.default"}).encode()
    return json.loads(request.urlopen(request.Request(url, data=auth_data)).read())["access_token"]

def api_call(url, token, method="GET", body=None):
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    req = request.Request(url, data=json.dumps(body).encode() if body else None, headers=headers, method=method)
    try:
        with request.urlopen(req) as response:
            if response.status in [202, 204]:
                return {}
            content = response.read().decode()
            return json.loads(content) if content else {}
    except error.HTTPError as e:
        print(f"API Error: {e.code} {e.reason}")
        print(e.read().decode())
        raise

def resize():
    token = get_token()
    base_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Compute/virtualMachines/{VM_NAME}"
    api_version = "2021-07-01"
    
    # 1. Get Disk ID
    print("🔍 Fetching Disk ID...")
    vm_data = api_call(f"{base_url}?api-version={api_version}", token)
    disk_id = vm_data['properties']['storageProfile']['osDisk']['managedDisk']['id']
    
    # 2. Deallocate VM (Required for resize)
    print(f"⏳ Deallocating VM {VM_NAME} (required to resize disk)...")
    api_call(f"{base_url}/deallocate?api-version={api_version}", token, method="POST")
    
    # Poll for deallocation
    for i in range(30):
        status_data = api_call(f"{base_url}/instanceView?api-version={api_version}", token)
        status = status_data["statuses"]
        if any("Deallocated" in s["displayStatus"] for s in status):
            print("✅ VM is Deallocated.")
            break
        print(f"  ... waiting for deallocation (attempt {i+1}/30)")
        time.sleep(15)

    # 3. Resize Disk
    print(f"💾 Resizing Disk to {NEW_SIZE_GB} GB...")
    disk_url = f"https://management.azure.com{disk_id}?api-version=2021-04-01"
    api_call(disk_url, token, method="PATCH", body={"properties": {"diskSizeGB": NEW_SIZE_GB}})
    
    # 4. Start VM
    print("🚀 Starting VM...")
    api_call(f"{base_url}/start?api-version={api_version}", token, method="POST")
    print(f"✅ Disk Resize Complete! Your VM is starting up with {NEW_SIZE_GB} GB.")

if __name__ == '__main__': 
    try:
        resize()
    except Exception as e:
        print(f"❌ Error during resize: {e}")
