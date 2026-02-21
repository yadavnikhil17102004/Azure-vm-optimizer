import json
import os
import subprocess
import sys
import shutil
import tempfile
import urllib.parse
from urllib import request, error

# Constants
SUBSCRIPTION_ID = os.environ.get("ARM_SUBSCRIPTION_ID", "")
RESOURCE_GROUP = "ollama-rg"
LOCATION = "centralindia"
DEPLOYMENT_NAME = "ollama-deployment"
ARM_TEMPLATE_FILE = "deploy.json"
SSH_KEY_FILE = "ollama_key.pub"

def run_command(command, env=None):
    try:
        result = subprocess.run(
            command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {command}\nStderr: {e.stderr}", file=sys.stderr)
        return None

def get_token_temp_config():
    """Get access token using temp config workaround."""
    print("Setting up temp config for token retrieval...")
    temp_dir = tempfile.mkdtemp(prefix="az_deploy_tmp_")
    
    # Copy auth files
    az_dir = os.path.expanduser("~/.azure")
    for fname in ["msal_token_cache.json", "azureProfile.json", "clouds.config", "config"]:
        src = os.path.join(az_dir, fname)
        if os.path.exists(src):
            shutil.copy(src, temp_dir)
            
    env = os.environ.copy()
    env["AZURE_CONFIG_DIR"] = temp_dir
    
    # Use specific tenant to reduce token size
    tenant_id = os.environ.get("ARM_TENANT_ID", "")
    print(f"Getting access token for tenant {tenant_id}...")
    # Get token for management API
    token = run_command(f"az account get-access-token --tenant {tenant_id} --query accessToken -o tsv", env=env)
    
    # Clean up
    shutil.rmtree(temp_dir, ignore_errors=True)
    
    if not token:
        raise Exception("Failed to retrieve access token")
    return token

def deploy_template(token):
    """Deploy ARM template using REST API."""
    print(f"Deploying ARM template to RG: {RESOURCE_GROUP}...")
    
    # Read ARM template
    with open(ARM_TEMPLATE_FILE, 'r') as f:
        template = json.load(f)
        
    # Read SSH Key
    if not os.path.exists(SSH_KEY_FILE):
        raise Exception(f"SSH key file not found: {SSH_KEY_FILE}. Run deploy_vm.sh first to generate it.")
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
                }
            }
        }
    }
    
    # Create RG if not exists (using curl/mgmt api)
    # Actually, let's assume RG was created by previous script or create it now via REST
    # Create RG URL
    rg_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}?api-version=2021-04-01"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    rg_body = json.dumps({"location": LOCATION})
    req = request.Request(rg_url, data=rg_body.encode('utf-8'), headers=headers, method='PUT')
    try:
        with request.urlopen(req) as response:
            print("Resource Group created/verified.")
    except error.HTTPError as e:
        print(f"Error creating RG: {e.read().decode()}")
        # Proceed anyway, maybe it exists
        
    # Deployment URL
    deploy_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}/providers/Microsoft.Resources/deployments/{DEPLOYMENT_NAME}?api-version=2021-04-01"
    
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(deploy_url, data=data, headers=headers, method='PUT')
    
    print("Sending deployment request...")
    try:
        with request.urlopen(req) as response:
            result = json.loads(response.read().decode())
            print("Deployment started successfully!")
            # Deployment is async usually, but this returns the initial state
            # For "Complete" status we need to poll, but let's just wait a bit or return
            # The output publicIP might not be ready in the immediate response if async.
            return result
    except error.HTTPError as e:
        print(f"Deployment failed: {e.code} {e.reason}")
        print(e.read().decode())
        return None

def main():
    try:
        token = get_token_temp_config()
        result = deploy_template(token)
        print("Deployment request sent. Check Azure Portal or wait for completion.")
        
        # We can implement polling here if needed, but for now let's just rely on user checking or script re-check
        # Actually, let's try to get the IP from the deployment result if usually synchronous for small things?
        # No, typically 201 Created and then we poll.
        
        # Poll for public IP
        import time
        print("Polling for Public IP (timeout 180s)...")
        for i in range(18):
            # Check IP resource directly
            pip_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}/providers/Microsoft.Network/publicIPAddresses/ollama-worker-pip?api-version=2020-11-01"
            headers = {"Authorization": f"Bearer {token}"}
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
            
        print("\nTimed out waiting for Public IP.")
        
    except Exception as e:
        print(f"FAILED: {e}")

if __name__ == "__main__":
    main()
