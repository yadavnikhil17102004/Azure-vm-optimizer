#!/bin/bash

BUDGET=0.14
RESULTS=()

echo "Finding best VM under $BUDGET/hr..."
echo ""

regions=$(az account list-locations --query "[].name" -o tsv)

for region in $regions; do
  echo "Checking $region..."

  skus=$(az vm list-skus \
    --location $region \
    --resource-type virtualMachines \
    --query "[?(contains(name,'D2') || contains(name,'D4') || contains(name,'D8')) && (restrictions==null || length(restrictions)==\`0\`)].name" \
    -o tsv)

  for sku in $skus; do
    response=$(curl -s "https://prices.azure.com/api/retail/prices?\$filter=armRegionName eq '$region' and contains(skuName,'$sku')")

    price=$(echo "$response" | jq -r '.Items[0].unitPrice // empty' 2>/dev/null)

    if [[ -n "$price" ]]; then
      ok=$(echo "$price <= $BUDGET" | bc -l)
      if [[ $ok -eq 1 ]]; then
        vcpu=$(az vm list-skus --location $region --size $sku --query "[0].capabilities[?name=='vCPUs'].value" -o tsv)
        ram=$(az vm list-skus --location $region --size $sku --query "[0].capabilities[?name=='MemoryGB'].value" -o tsv)

        RESULTS+=("$price|$vcpu|$ram|$region|$sku")
      fi
    fi
  done
done

echo ""
echo "===== BEST OPTIONS ====="

printf "%s\n" "${RESULTS[@]}" | sort -t'|' -k1,1n -k2,2nr | while IFS="|" read price vcpu ram region sku; do
  echo "$region | $sku | $vcpu vCPU | $ram GB | $price/hr"
done