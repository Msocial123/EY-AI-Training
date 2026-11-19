#!/usr/bin/env bash
# infra/00_variables.sh  ->  shared names for every infra script
# Use:  source infra/00_variables.sh
# Tip: run these scripts in Azure Cloud Shell (Bash) - az CLI is pre-installed.

export RG="rg-shopkart-day12"
export LOCATION="centralindia"
# Storage & Service Bus names must be GLOBALLY unique -> we add a random suffix.
# It is saved in infra/.suffix so EVERY script reuses the SAME names.
SUFFIX_FILE="$(dirname "${BASH_SOURCE[0]}")/.suffix"
if [ -z "$SUFFIX" ]; then
  [ -f "$SUFFIX_FILE" ] || echo "sk$RANDOM" > "$SUFFIX_FILE"
  SUFFIX=$(cat "$SUFFIX_FILE")
fi
export SUFFIX
export STORAGE="stshopkart${SUFFIX}"       # 3-24 chars, lowercase letters + numbers only
export SB_NAMESPACE="sb-shopkart-${SUFFIX}"
export VNET="vnet-shopkart"

echo "RG=$RG  LOCATION=$LOCATION  STORAGE=$STORAGE  SB_NAMESPACE=$SB_NAMESPACE"
