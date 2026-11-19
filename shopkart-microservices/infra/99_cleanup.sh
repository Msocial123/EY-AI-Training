#!/usr/bin/env bash
# infra/99_cleanup.sh  ->  DELETE EVERYTHING created today (stops all billing)
# One command deletes the whole resource group and every resource inside it.
source "$(dirname "$0")/00_variables.sh"
az group delete --name "$RG" --yes --no-wait
echo "Deleting $RG in the background. Check:  az group exists --name $RG"
