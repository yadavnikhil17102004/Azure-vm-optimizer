#!/bin/bash

# Azure VM Deployment Script with Permission Fix

# Azure VM Deployment Script with Permission Fix

# Azure VM Deployment Script with Permission Fix

# 1. Setup Temporary Config (Bypass Permission Issues)
echo "Setting up temporary Azure CLI config..."
TEMP_DIR="/tmp/az_deploy_config_$(date +%s)"
mkdir -p "$TEMP_DIR"

# Copy auth tokens
# Copy auth tokens
cp "$HOME/.azure/azureProfile.json" "$TEMP_DIR/" 2>/dev/null
cp "$HOME/.azure/msal_token_cache.json" "$TEMP_DIR/" 2>/dev/null
cp "$HOME/.azure/clouds.config" "$TEMP_DIR/" 2>/dev/null
cp "$HOME/.azure/config" "$TEMP_DIR/" 2>/dev/null

export AZURE_CONFIG_DIR="$TEMP_DIR"

# Use subscription ID from environment variable
SUB_ID="${ARM_SUBSCRIPTION_ID:-}"
echo "Setting subscription to $SUB_ID..."
az account set --subscription "$SUB_ID"

# Verify az works
echo "Verifying Azure CLI connectivity..."
az account show --output json > account_check.json 2> account_check_error.log
if [ -s account_check.json ]; then
    echo "✅ Azure CLI is working."
else
    echo "❌ Azure CLI is NOT working."
    cat account_check_error.log
    exit 1
fi

# 2. Configuration
RG="ollama-rg"
LOC="centralindia"
VM_NAME="ollama-worker"
SIZE="Standard_D2as_v5" # 2 vCPU, 8 GB RAM
IMAGE="Ubuntu2204"

echo "------------------------------------------------"
echo "Deploying to Resource Group: $RG"
echo "Region: $LOC"
echo "VM Size: $SIZE"
echo "------------------------------------------------"

# 3. Create Resource Group
echo "Creating Resource Group..."
az group create --name "$RG" --location "$LOC" --output table

# 3b. Generate SSH Keys Locally (Avoids ~/.ssh permission issues)
KEY_NAME="ollama_key"
if [ ! -f "$KEY_NAME" ]; then
    echo "Generating local SSH key pair ($KEY_NAME)..."
    ssh-keygen -t rsa -b 4096 -f "$KEY_NAME" -N "" -q
    chmod 600 "$KEY_NAME"
fi

# 4. Create VM
echo "Creating VM (this may take 2-3 minutes)..."
az vm create \
  --resource-group "$RG" \
  --name "$VM_NAME" \
  --image "$IMAGE" \
  --size "$SIZE" \
  --location "$LOC" \
  --admin-username azureuser \
  --ssh-key-values "$KEY_NAME.pub" \
  --public-ip-sku Standard \
  --output json --debug > deployment_debug.log 2>&1

# 5. Result
# Parse IP from debug log? No, debug log is messy.
# Just check if it succeeded by grep.
IP=$(grep -o '"publicIpAddress": "[^"]*"' deployment_debug.log | cut -d'"' -f4)

echo "------------------------------------------------"
if [ -n "$IP" ]; then
    echo "✅ Deployment Successful!"
    echo "Public IP: $IP"
    echo ""
    echo "Connect via SSH:"
    echo "ssh -i $KEY_NAME azureuser@$IP"
else
    echo "❌ Deployment might have failed."
    echo "--- TAIL OF DEBUG LOG ---"
    tail -n 20 deployment_debug.log
    echo "-------------------------"
fi
echo "------------------------------------------------"

# Cleanup
rm -rf "$TEMP_DIR"
