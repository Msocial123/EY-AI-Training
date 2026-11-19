#!/usr/bin/env bash
# infra/03_load_balancer.sh  ->  Module 7 (instructor demo, ~10 minutes, costs money!)
# Creates: VNet, 2 small Ubuntu VMs (no public IPs), Standard public Load Balancer
#          with a health probe on /health and a rule  port 80 -> port 80.
# Then open  http://<LB_PUBLIC_IP>  and refresh - you'll see vm-web-1 / vm-web-2.
set -e
source "$(dirname "$0")/00_variables.sh"
CLOUD_INIT="$(dirname "$0")/cloud-init-web.yaml"

# 1) Network: VNet + backend subnet + NSG allowing HTTP
az network vnet create --resource-group "$RG" --name "$VNET" --address-prefix 10.0.0.0/16 \
  --subnet-name snet-backend --subnet-prefix 10.0.1.0/24
az network nsg create --resource-group "$RG" --name nsg-web
az network nsg rule create --resource-group "$RG" --nsg-name nsg-web --name allow-http \
  --priority 100 --protocol Tcp --destination-port-ranges 80 --access Allow --direction Inbound
az network vnet subnet update --resource-group "$RG" --vnet-name "$VNET" --name snet-backend \
  --network-security-group nsg-web

# 2) Load Balancer: public IP + frontend + backend pool + probe + rule
az network public-ip create --resource-group "$RG" --name pip-lb-shopkart --sku Standard
az network lb create --resource-group "$RG" --name lb-shopkart --sku Standard \
  --public-ip-address pip-lb-shopkart --frontend-ip-name fe-shopkart --backend-pool-name pool-web
az network lb probe create --resource-group "$RG" --lb-name lb-shopkart --name probe-health \
  --protocol Http --port 80 --path /health --interval 5
az network lb rule create --resource-group "$RG" --lb-name lb-shopkart --name rule-http \
  --protocol Tcp --frontend-port 80 --backend-port 80 \
  --frontend-ip-name fe-shopkart --backend-pool-name pool-web --probe-name probe-health

# 3) Two VMs in the backend pool (Standard_B1s is the cheapest; change if not available)
for i in 1 2; do
  az vm create --resource-group "$RG" --name "vm-web-$i" --image Ubuntu2204 --size Standard_B1s \
    --vnet-name "$VNET" --subnet snet-backend --public-ip-address "" --nsg "" \
    --admin-username azureuser --generate-ssh-keys --custom-data "$CLOUD_INIT"
  az network nic ip-config address-pool add --resource-group "$RG" \
    --nic-name "vm-web-${i}VMNic" --ip-config-name "ipconfigvm-web-$i" \
    --lb-name lb-shopkart --address-pool pool-web
done

LB_IP=$(az network public-ip show --resource-group "$RG" --name pip-lb-shopkart --query ipAddress -o tsv)
echo
echo "Load balancer ready:  http://$LB_IP   (wait ~2 min for VMs to boot, then refresh many times)"
echo "Test from Cloud Shell:  for i in \$(seq 1 6); do curl -s http://$LB_IP; done"
