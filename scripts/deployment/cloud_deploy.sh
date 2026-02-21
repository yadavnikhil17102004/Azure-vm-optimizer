#!/bin/bash
# ==========================================
# Azure Cloud Shell Deployment Script
# ==========================================
# Run this script in the Azure Cloud Shell to bypass local authentication issues.
# 1. Go to https://portal.azure.com
# 2. Click the specific icon for Cloud Shell (terminal icon in top bar)
# 3. Select "Bash"
# 4. Paste this script

# --- Configuration ---
RG="ollama-rg"
LOC="centralindia"
VM_NAME="worker-vm-4vcpu"
# Standard_D4as_v5: 4 vCPU, 16 GB RAM (~$0.11/hr Standard, ~$0.02/hr Spot)
SIZE="Standard_D4as_v5" 
IMAGE="Ubuntu2204"

echo "------------------------------------------------"
echo "Deploying High-Performance VM: $VM_NAME"
echo "Size: $SIZE (4 vCPU / 16 GB RAM)"
echo "Region: $LOC"
echo "------------------------------------------------"

# 1. Create Resource Group
echo "Creating Resource Group '$RG'..."
az group create --name "$RG" --location "$LOC" --output table

# 2. Create VM
echo "Creating VM (this takes 1-2 minutes)..."
az vm create \
  --resource-group "$RG" \
  --name "$VM_NAME" \
  --image "$IMAGE" \
  --size "$SIZE" \
  --location "$LOC" \
  --admin-username azureuser \
  --generate-ssh-keys \
  --public-ip-sku Standard \
  --output json > deploy_output.json

# 3. Output Result
IP=$(jq -r '.publicIpAddress' deploy_output.json)

echo "------------------------------------------------"
if [ -n "$IP" ] && [ "$IP" != "null" ]; then
    echo "✅ SUCCESS! VM Deployed."
    echo "Public IP: $IP"
    echo ""
    echo "SSH Command:"
    echo "ssh azureuser@$IP"
else
    echo "❌ Deployment completed but IP not found in output."
    cat deploy_output.json
fi
echo "------------------------------------------------"
