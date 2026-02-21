import json, urllib.parse, time, subprocess, os
from urllib import request, error

# ============= CONFIGURATION =============
CLIENT_ID = os.environ.get("ARM_CLIENT_ID", "")
CLIENT_SECRET = os.environ.get("ARM_CLIENT_SECRET", "")
TENANT_ID = os.environ.get("ARM_TENANT_ID", "")
SUBSCRIPTION_ID = os.environ.get("ARM_SUBSCRIPTION_ID", "")
RESOURCE_GROUP = "OpenClaw-RG" # New clean group
LOCATION = "centralindia"
VM_SIZE = "Standard_E8as_v5" # 64GB RAM

# Use your public key from keys/ollama_key.pub if available, otherwise env var
SSH_KEY_PATH = "keys/ollama_key.pub"
if os.path.exists(SSH_KEY_PATH):
    with open(SSH_KEY_PATH, "r") as f:
        SSH_PUBLIC_KEY = f.read().strip()
else:
    SSH_PUBLIC_KEY = os.environ.get("ARM_SSH_PUBLIC_KEY", "")

# Embedded ARM Template (Corrected for 64GB + Auto-shutdown)
TEMPLATE = {
    "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
    "contentVersion": "1.0.0.0",
    "parameters": {"sshPublicKey": {"type": "secureString"}, "vmSize": {"type": "string", "defaultValue": VM_SIZE}},
    "variables": {"vmName": "OpenClaw-Pro", "nicName": "OpenClaw-nic", "vnetName": "OpenClaw-vnet", "pipName": "OpenClaw-pip", "nsgName": "OpenClaw-nsg"},
    "resources": [
        {"type": "Microsoft.Network/networkSecurityGroups", "apiVersion": "2020-11-01", "name": "[variables('nsgName')]", "location": LOCATION, "properties": {"securityRules": [{"name": "SSH", "properties": {"priority": 1000, "protocol": "Tcp", "access": "Allow", "direction": "Inbound", "sourceAddressPrefix": "*", "sourcePortRange": "*", "destinationAddressPrefix": "*", "destinationPortRange": "22"}}]}},
        {"type": "Microsoft.Network/publicIPAddresses", "apiVersion": "2020-11-01", "name": "[variables('pipName')]", "location": LOCATION, "sku": {"name": "Standard"}, "properties": {"publicIPAllocationMethod": "Static"}},
        {"type": "Microsoft.Network/virtualNetworks", "apiVersion": "2020-11-01", "name": "[variables('vnetName')]", "location": LOCATION, "properties": {"addressSpace": {"addressPrefixes": ["10.0.0.0/16"]}, "subnets": [{"name": "default", "properties": {"addressPrefix": "10.0.0.0/24", "networkSecurityGroup": {"id": "[resourceId('Microsoft.Network/networkSecurityGroups', variables('nsgName'))]"}}}]}},
        {"type": "Microsoft.Network/networkInterfaces", "apiVersion": "2020-11-01", "name": "[variables('nicName')]", "location": LOCATION, "dependsOn": ["[resourceId('Microsoft.Network/publicIPAddresses', variables('pipName'))]", "[resourceId('Microsoft.Network/virtualNetworks', variables('vnetName'))]"], "properties": {"ipConfigurations": [{"name": "ipconfig1", "properties": {"publicIPAddress": {"id": "[resourceId('Microsoft.Network/publicIPAddresses', variables('pipName'))]"}, "subnet": {"id": "[concat(resourceId('Microsoft.Network/virtualNetworks', variables('vnetName')), '/subnets/default')]"}}}]}},
        {"type": "Microsoft.Compute/virtualMachines", "apiVersion": "2021-07-01", "name": "[variables('vmName')]", "location": LOCATION, "dependsOn": ["[resourceId('Microsoft.Network/networkInterfaces', variables('nicName'))]"], "properties": {"hardwareProfile": {"vmSize": "[parameters('vmSize')]"}, "osProfile": {"computerName": "[variables('vmName')]", "adminUsername": "azureuser", "linuxConfiguration": {"disablePasswordAuthentication": True, "ssh": {"publicKeys": [{"path": "/home/azureuser/.ssh/authorized_keys", "keyData": "[parameters('sshPublicKey')]"}]}}}, "storageProfile": {"imageReference": {"publisher": "Canonical", "offer": "0001-com-ubuntu-server-jammy", "sku": "22_04-lts-gen2", "version": "latest"}, "osDisk": {"createOption": "FromImage", "managedDisk": {"storageAccountType": "Premium_LRS"}}}, "networkProfile": {"networkInterfaces": [{"id": "[resourceId('Microsoft.Network/networkInterfaces', variables('nicName'))]"}]}}},
        {"type": "Microsoft.DevTestLab/schedules", "apiVersion": "2018-09-15", "name": "[concat('shutdown-computevm-', variables('vmName'))]", "location": LOCATION, "dependsOn": ["[resourceId('Microsoft.Compute/virtualMachines', variables('vmName'))]"], "properties": {"status": "Enabled", "taskType": "ComputeVmShutdownTask", "dailyRecurrence": {"time": "2200"}, "timeZoneId": "India Standard Time", "targetResourceId": "[resourceId('Microsoft.Compute/virtualMachines', variables('vmName'))]", "notificationSettings": {"status": "Disabled"}}}
    ]
}

def run():
    # 1. Get Token
    print("🔑 Authenticating as Service Principal...")
    auth_data = urllib.parse.urlencode({"grant_type": "client_credentials", "client_id": CLIENT_ID, "client_secret": CLIENT_SECRET, "scope": "https://management.azure.com/.default"}).encode()
    token = json.loads(request.urlopen(request.Request(f"https://login.microsoftonline.com/{TENANT_ID}/oauth2/v2.0/token", data=auth_data)).read())["access_token"]
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

    # 2. Create Resource Group
    print(f"📁 Creating Resource Group {RESOURCE_GROUP}...")
    rg_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}?api-version=2021-04-01"
    request.urlopen(request.Request(rg_url, data=json.dumps({"location": LOCATION}).encode(), headers=headers, method="PUT"))

    # 3. Deploy Template
    print("🚀 Deploying 64GB VM + Auto-Shutdown (Central India)...")
    payload = {"properties": {"mode": "Incremental", "template": TEMPLATE, "parameters": {"sshPublicKey": {"value": SSH_PUBLIC_KEY}}}}
    deploy_url = f"https://management.azure.com/subscriptions/{SUBSCRIPTION_ID}/resourcegroups/{RESOURCE_GROUP}/providers/Microsoft.Resources/deployments/PowerUpgrade?api-version=2021-04-01"
    request.urlopen(request.Request(deploy_url, data=json.dumps(payload).encode(), headers=headers, method="PUT"))
    print("✅ Deployment Started! Wait 2-3 minutes, then check the portal for your new IP.")

if __name__ == "__main__": run()
