#!/usr/bin/env python3
import json
import subprocess
import concurrent.futures
import time
import sys
import os
import urllib.parse

# Configuration
OUTPUT_FILE = "vms.json"
MAX_WORKERS = 20  # REST API handles concurrency well
AZURE_DIR = os.path.expanduser("~/.azure")

def ensure_az_works():
    """Check if az works, if not try to fix permission issues by using a temp config."""
    try:
        subprocess.run("az account show", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        print("Initial az check failed. Attempting permission workaround...")
        # Create temp dir
        import tempfile
        import shutil
        
        temp_dir = tempfile.mkdtemp(prefix="az_config_tmp_")
        print(f"Created temp config dir: {temp_dir}")
        
        # Copy critical files
        files_to_copy = ["msal_token_cache.json", "azureProfile.json", "clouds.config", "config"]
        for fname in files_to_copy:
             src = os.path.join(AZURE_DIR, fname)
             if os.path.exists(src):
                 shutil.copy(src, temp_dir)
        
        # Set env var for this process and children
        os.environ["AZURE_CONFIG_DIR"] = temp_dir
        
        # Retry
        try:
             subprocess.run("az account show", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
             print("Workaround successful! Proceeding...")
             
             # Register cleanup
             import atexit
             def cleanup():
                 shutil.rmtree(temp_dir, ignore_errors=True)
             atexit.register(cleanup)
             
             return True
        except subprocess.CalledProcessError as e:
             print("Workaround failed. Please fix your Azure CLI installation.")
             return False

def run_command(command, use_shell=True):
    """Run a shell command and return the output as a string.
    If command is a list, use_shell should be False (or it's ignored on posix).
    """
    try:
        if isinstance(command, list):
            use_shell = False
            
        result = subprocess.run(
            command, shell=use_shell, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        # Some regions might fail or have no access, just warn and continue
        # print(f"Warning: Command failed: {command}\nError: {e.stderr.strip()}", file=sys.stderr)
        return None

def get_token_and_sub():
    """Get access token and subscription ID."""
    print("Getting access token...")
    token = run_command("az account get-access-token --query accessToken -o tsv")
    sub_id = run_command("az account show --query id -o tsv")
    if not token or not sub_id:
        print("Failed to get token or subscription ID.")
        sys.exit(1)
    return token, sub_id

def get_regions():
    """Get list of all Azure regions."""
    # We can use az here since it's just one call (or fetch from management API)
    print("Fetching list of regions...")
    cmd = "az account list-locations --query '[].name' -o tsv"
    output = run_command(cmd)
    if not output:
        return []
    return output.split()

def get_vm_skus_rest(region, token, sub_id):
    """Get VM SKUs using REST API."""
    # Encode the filter properly
    filter_val = f"location eq '{region}'"
    filter_enc = urllib.parse.quote(filter_val)
    url = f"https://management.azure.com/subscriptions/{sub_id}/providers/Microsoft.Compute/skus?api-version=2021-07-01&$filter={filter_enc}"
    
    # Use list args to avoid shell quoting hell
    cmd = [
        "curl", "-s", "-X", "GET", url,
        "-H", f"Authorization: Bearer {token}",
        "-H", "Content-Type: application/json",
        "--connect-timeout", "10",
        "--max-time", "30"
    ]
    output = run_command(cmd, use_shell=False)
    if not output:
        # print(f"DEBUG: No output for {region}")
        return {}
    
    try:
        data = json.loads(output)
        items = data.get('value', [])
        # if not items:
        #     print(f"DEBUG: Empty items for {region}. Output snippet: {output[:200]}")
    except json.JSONDecodeError:
        # print(f"DEBUG: JSON decode error for {region}. Output snippet: {output[:200]}")
        return {}

    sku_map = {}
    for item in items:
        name = item.get('name')
        # resourceType should be virtualMachines to ensure it's computable
        if item.get('resourceType') != 'virtualMachines':
            continue
            
        restrictions = item.get('restrictions', [])
        if restrictions and len(restrictions) > 0:
            if any(r.get('type') == 'Location' for r in restrictions):
                continue

        caps = {cap['name']: cap['value'] for cap in item.get('capabilities', [])}
        
        vcpu = caps.get('vCPUs')
        ram = caps.get('MemoryGB')
        
        if vcpu and ram:
            sku_map[name] = {
                'vcpu': float(vcpu),
                'ram': float(ram)
            }
            
    return sku_map

def get_regional_prices_rest(region):
    """Fetch retail prices for Virtual Machines in a region using REST API (public)."""
    base_url = "https://prices.azure.com/api/retail/prices"
    filter_str = f"serviceName eq 'Virtual Machines' and armRegionName eq '{region}' and priceType eq 'Consumption'"
    filter_enc = urllib.parse.quote(filter_str)
    
    items = []
    url = f"{base_url}?$filter={filter_enc}"
    
    while url:
        cmd = ["curl", "-s", url, "--connect-timeout", "10", "--max-time", "30"]
        output = run_command(cmd, use_shell=False)
        if not output:
            break
            
        try:
            data = json.loads(output)
            items.extend(data.get('Items', []))
            url = data.get('NextPageLink')
        except json.JSONDecodeError:
            break
            
    return items

def process_region(region, token, sub_id):
    """Process a single region: fetch SKUs, fetch prices, merge."""
    # print(f"Processing {region}...") # overly verbose with many threads
    try:
        # 1. Get Hardware Specs via REST
        sku_specs = get_vm_skus_rest(region, token, sub_id)
        if not sku_specs:
            return []
            
        # 2. Get Prices via REST
        price_items = get_regional_prices_rest(region)
        
        merged_data = []
        for p in price_items:
            sku_name = p.get('armSkuName')
            unit_price = p.get('unitPrice')
            
            if unit_price is None:
                continue
                
            spec = sku_specs.get(sku_name)
            if spec:
                merged_data.append({
                    'region': region,
                    'sku': sku_name,
                    'vcpu': spec['vcpu'],
                    'ram': spec['ram'],
                    'price': float(unit_price)
                })
        
        return merged_data
        
    except Exception as e:
        print(f"Error processing region {region}: {e}")
        return []

def main():
    print(f"Starting Azure VM Database Builder (REST API Optimized)")
    
    if not ensure_az_works():
        sys.exit(1)
        
    token, sub_id = get_token_and_sub()
    
    start_time = time.time()
    regions = get_regions()
    # regions = regions[:5] # uncomment for quick test
    
    print(f"Found {len(regions)} regions. Starting parallel processing with {MAX_WORKERS} workers...")
    
    all_vms = []
    processed_count = 0
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        future_to_region = {executor.submit(process_region, r, token, sub_id): r for r in regions}
        
        for i, future in enumerate(concurrent.futures.as_completed(future_to_region)):
            region = future_to_region[future]
            try:
                data = future.result()
                all_vms.extend(data)
                processed_count += 1
                if processed_count % 5 == 0 or processed_count == len(regions):
                    print(f"[{processed_count}/{len(regions)}] Processed {region} ({len(data)} VMs found)...")
            except Exception as exc:
                print(f"{region} generated an exception: {exc}")

    print(f"Saving {len(all_vms)} records to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_vms, f, indent=2)
        
    elapsed = time.time() - start_time
    print(f"Done! Database built in {elapsed:.2f} seconds.")

if __name__ == "__main__":
    main()
