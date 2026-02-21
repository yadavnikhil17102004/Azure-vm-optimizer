import json
import os
import sys
import time
import urllib.parse
from urllib import request, error

# ==========================================
# Service Principal Config
# ==========================================
CLIENT_ID = os.environ.get("ARM_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("ARM_TENANT_ID", "")
SUBSCRIPTION_ID = os.environ.get("ARM_SUBSCRIPTION_ID", "")
RESOURCE_GROUP = "ollama-rg"
VM_NAME = "ollama-worker"

def get_sp_token():
    print(f"Getting token for SP {CLIENT_ID}...")
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token"
    data = {
        "grant_type": "client_credentials",
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "scope": "https://management.azure.com/.default"
    }
    encoded_data = urllib.parse.urlencode(data).encode("utf-8")
    req = request.Request(url, data=encoded_data)
    with request.urlopen(req) as response:
        return json.load(response)["access_token"]

def dpreq(url, token, method="GET", body=None):
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    encoded_body = None
    if body:
        encoded_body = json.dumps(body).encode("utf-8")
    
    req = request.Request(url, data=encoded_body, headers=headers, method=method)
    try:
        with request.urlopen(req) as response:
            if response.status == 204: return {}
            return json.load(response)
    except error.HTTPError as e:
        print(f"HTTP Error: {e.code} - {e.reason}")
        print(e.read().decode())
        return None

def delete_resources(token):
    print(f"🗑️ Deleting VM: {VM_NAME}...")
    base_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/providers/Microsoft.Compute/virtualMachines/{VM_NAME}?api-version=2023-09-01"
    
    # Delete VM
    dpreq(base_url, token, method="DELETE")
    
    # We should wait for VM deletion before deleting NIC/Disks to avoid locks
    print("⏳ Waiting for VM deletion to initiate...")
    time.sleep(10)
    
    print("🗑️ Deleting associated Disks and NICs in {RESOURCE_GROUP}...")
    # List all resources in the group and delete them if they match the name pattern
    resources_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourceGroups/{RESOURCE_GROUP}/resources?api-version=2021-04-01"
    res_list = dpreq(resources_url, token)
    
    if res_list and "value" in res_list:
        for res in res_list["value"]:
            if VM_NAME in res["name"] or "ollama" in res["name"]:
                print(f"Deleting resource: {res['name']} ({res['type']})")
                del_url = f"https://management.azure.com{res['id']}?api-version=2021-04-01"
                # Use individual API versions if needed, but 2021-04-01 is generic enough for many
                dpreq(del_url, token, method="DELETE")

if __name__ == "__main__":
    token = get_sp_token()
    delete_resources(token)
    print("✅ Deletion requests sent!")
