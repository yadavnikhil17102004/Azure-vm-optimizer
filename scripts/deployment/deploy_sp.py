import json
import os
import subprocess
import sys
import time
import shutil
import tempfile
import urllib.parse
from urllib import request, error

# ==========================================
# Service Principal Config (Fill these in!)
# ==========================================
# Client ID (App ID)
CLIENT_ID = os.environ.get("ARM_CLIENT_ID", "")
# Client Secret (Password)
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET", "")
# Tenant ID
TENANT_ID = os.environ.get("ARM_TENANT_ID", "")
# Subscription ID
SUBSCRIPTION_ID = os.environ.get("ARM_SUBSCRIPTION_ID", "")

# ==========================================
# Deployment Config
# ==========================================
RESOURCE_GROUP = "ollama-rg"
LOCATION = "centralindia"
DEPLOYMENT_NAME = "ollama-sp-deploy"
ARM_TEMPLATE_FILE = "templates/deploy.json"
SSH_KEY_FILE = "keys/ollama_key.pub"

def run_command(command, env=None):
    try:
        result = subprocess.run(
            command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\nStderr: {e.stderr}", file=sys.stderr)
        return None

def get_sp_token():
    """Get access token using Service Principal."""
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ Error: CLIENT_ID and CLIENT_SECRET must be set.")
        sys.exit(1)

    print(f"Getting token for SP {CLIENT_ID}...")
    
    url = f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/token"
    data = urllib.parse.urlencode({
        'grant_type': 'client_credentials',
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'resource': 'https://management.azure.com/'
    }).encode('utf-8')
    
    req = request.Request(url, data=data, method='POST')
    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            return result['access_token']
    except error.HTTPError as e:
        print(f"❌ Failed to login as Service Principal: {e}")
        print(e.read().decode())
        sys.exit(1)

def deploy_template(token):
    """Deploy ARM template using REST API."""
    print(f"Deploying ARM template to RG: {RESOURCE_GROUP}...")
    
    # Read ARM template
    with open(ARM_TEMPLATE_FILE, 'r') as f:
        template = json.load(f)
        
    # Read SSH Key
    if not os.path.exists(SSH_KEY_FILE):
        print("Generating new SSH key...")
        subprocess.run(f'ssh-keygen -t rsa -b 4096 -f ollama_key -N "" -q', shell=True)
        
    with open(SSH_KEY_FILE, 'r') as f:
        ssh_key = f.read().strip()
        
    # Prepare payload
    payload = {
        "properties": {
            "mode": "Incremental",
            "template": template,
            "parameters": {
                "sshPublicKey": {
                    "value": ssh_key
                },
                "vmSize": {
                    "value": "Standard_E8as_v5" 
                }
            }
        }
    }
    
    # Headers
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    # 1. Ensure Resource Group Exists
    rg_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}?api-version=2021-04-01"
    rg_body = json.dumps({"location": LOCATION})
    req = request.Request(rg_url, data=rg_body.encode('utf-8'), headers=headers, method='PUT')
    try:
        with request.urlopen(req) as response:
            print(f"✅ Resource Group '{RESOURCE_GROUP}' ready.")
    except error.HTTPError as e:
        print(f"❌ Error creating RG: {e.read().decode()}")
        sys.exit(1)
        
    # 2. Deploy
    deploy_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}/providers/Microsoft.Resources/deployments/{DEPLOYMENT_NAME}?api-version=2021-04-01"
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(deploy_url, data=data, headers=headers, method='PUT')
    
    print("🚀 Sending deployment request...")
    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("Deployment accepted!")
    except error.HTTPError as e:
        print(f"❌ Deployment failed: {e.code} {e.reason}")
        print(e.read().decode())
        sys.exit(1)

    # 3. Poll for IP
    print("⏳ Polling for Public IP (timeout 180s)...")
    for i in range(18):
        pip_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}/providers/Microsoft.Network/publicIPAddresses/ollama-worker-pip?api-version=2020-11-01"
        req = request.Request(pip_url, headers=headers, method='GET')
        try:
            with request.urlopen(req) as response:
                data = json.loads(response.read().decode())
                ip = data.get('properties', {}).get('ipAddress')
                if ip:
                    print("\n------------------------------------------------")
                    print("✅ Deployment Complete!")
                    print(f"Public IP: {ip}")
                    print(f"Connect: ssh -i ollama_key azureuser@{ip}")
                    print("------------------------------------------------")
                    return
        except Exception:
            pass
        
        print(".", end="", flush=True)
        time.sleep(10)
        
    print("\n⚠️ Timed out waiting for Public IP.")

if __name__ == "__main__":
    if len(sys.argv) == 3:
        os.environ["ARM_CLIENT_ID"] = sys.argv[1]
        os.environ["ARM_CLIENT_SECRET"] = sys.argv[2]
        # Reload globals
        CLIENT_ID = sys.argv[1]
        CLIENT_SECRET = sys.argv[2]
    else:
        CLIENT_ID = os.environ.get("ARM_CLIENT_ID", "")
        CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET", "")
        
    token = get_sp_token()
    deploy_template(token)
