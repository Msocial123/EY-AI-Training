#!/usr/bin/env bash
# infra/04_app_gateway.sh  ->  Module 7 (instructor demo, TAKES 15-25 MINUTES, costs money!)
# Start this script BEFORE lunch so it is ready for Module 7.
# Needs: 03_load_balancer.sh already run (VNet + vm-web-1 + vm-web-2 exist).
# Creates: Application Gateway (Standard_v2) with PATH-BASED routing:
#          /orders/*  -> pool-orders (vm-web-2 only)
#          everything else -> default pool (both VMs)
set -e
source "$(dirname "$0")/00_variables.sh"

# App Gateway needs its OWN empty subnet
az network vnet subnet create --resource-group "$RG" --vnet-name "$VNET" \
  --name snet-appgw --address-prefixes 10.0.2.0/24
az network public-ip create --resource-group "$RG" --name pip-appgw-shopkart --sku Standard

VM1_IP=$(az vm list-ip-addresses -g "$RG" -n vm-web-1 --query "[0].virtualMachine.network.privateIpAddresses[0]" -o tsv)
VM2_IP=$(az vm list-ip-addresses -g "$RG" -n vm-web-2 --query "[0].virtualMachine.network.privateIpAddresses[0]" -o tsv)
echo "Backends: $VM1_IP  $VM2_IP"

# 1) The gateway with a default pool (both VMs) - this is the slow step
az network application-gateway create --resource-group "$RG" --name appgw-shopkart \
  --location "$LOCATION" --sku Standard_v2 --capacity 1 \
  --vnet-name "$VNET" --subnet snet-appgw --public-ip-address pip-appgw-shopkart \
  --frontend-port 80 --http-settings-port 80 --http-settings-protocol Http \
  --priority 100 --servers "$VM1_IP" "$VM2_IP"

# 2) A second pool just for orders
az network application-gateway address-pool create --resource-group "$RG" \
  --gateway-name appgw-shopkart --name pool-orders --servers "$VM2_IP"

# 3) URL path map: /orders/* -> pool-orders, everything else -> default pool
az network application-gateway url-path-map create --resource-group "$RG" \
  --gateway-name appgw-shopkart --name pathmap-shopkart \
  --paths "/orders/*" --address-pool pool-orders \
  --http-settings appGatewayBackendHttpSettings \
  --default-address-pool appGatewayBackendPool \
  --default-http-settings appGatewayBackendHttpSettings

# 4) Switch the default rule from Basic to PathBasedRouting
az network application-gateway rule update --resource-group "$RG" \
  --gateway-name appgw-shopkart --name rule1 \
  --rule-type PathBasedRouting --url-path-map pathmap-shopkart

AGW_IP=$(az network public-ip show -g "$RG" -n pip-appgw-shopkart --query ipAddress -o tsv)
echo
echo "Try:  curl http://$AGW_IP/products/   (either VM)"
echo "      curl http://$AGW_IP/orders/     (always vm-web-2)"
