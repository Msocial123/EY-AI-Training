#!/usr/bin/env bash
# infra/05_managed_identity.sh  ->  Module 5 (optional, needs 01 + 03 done)
# Gives vm-web-1 a SYSTEM-ASSIGNED MANAGED IDENTITY and lets it read blobs.
# Then the VM can call Blob Storage with NO password, NO key, NO connection string.
set -e
source "$(dirname "$0")/00_variables.sh"

az vm identity assign --resource-group "$RG" --name vm-web-1
PRINCIPAL=$(az vm show --resource-group "$RG" --name vm-web-1 --query identity.principalId -o tsv)
SA_ID=$(az storage account show --name "$STORAGE" --resource-group "$RG" --query id -o tsv)

az role assignment create --assignee-object-id "$PRINCIPAL" --assignee-principal-type ServicePrincipal \
  --role "Storage Blob Data Reader" --scope "$SA_ID"

echo "vm-web-1 identity: $PRINCIPAL  ->  Storage Blob Data Reader on $STORAGE"
echo
echo "Proof (runs INSIDE the VM, asks the local identity endpoint for a token):"
az vm run-command invoke --resource-group "$RG" --name vm-web-1 --command-id RunShellScript \
  --scripts "curl -s -H Metadata:true 'http://169.254.169.254/metadata/identity/oauth2/token?api-version=2018-02-01&resource=https://storage.azure.com/' | cut -c1-120" \
  --query "value[0].message" -o tsv
