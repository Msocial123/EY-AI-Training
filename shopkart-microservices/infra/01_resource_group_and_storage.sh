#!/usr/bin/env bash
# infra/01_resource_group_and_storage.sh  ->  Module 5
# Creates: Resource Group, Storage Account (blob container + queue),
#          and gives YOU data access through Azure RBAC (no keys needed).
set -e
source "$(dirname "$0")/00_variables.sh"

# 1) Resource Group = a folder for everything in this project
az group create --name "$RG" --location "$LOCATION" \
  --tags project=shopkart env=training owner=day12

# 2) Storage Account (Standard, locally-redundant, no anonymous public access)
az storage account create --name "$STORAGE" --resource-group "$RG" --location "$LOCATION" \
  --sku Standard_LRS --kind StorageV2 --allow-blob-public-access false --min-tls-version TLS1_2

# 3) Give the signed-in user data-plane roles (this is what Managed Identity will also get)
ME=$(az ad signed-in-user show --query id -o tsv)
SA_ID=$(az storage account show --name "$STORAGE" --resource-group "$RG" --query id -o tsv)
az role assignment create --assignee-object-id "$ME" --assignee-principal-type User \
  --role "Storage Blob Data Contributor" --scope "$SA_ID"
az role assignment create --assignee-object-id "$ME" --assignee-principal-type User \
  --role "Storage Queue Data Contributor" --scope "$SA_ID"
echo "Role assignments can take 1-5 minutes to start working."

# 4) Container + queue (uses your login, not keys)
az storage container create --name product-images --account-name "$STORAGE" --auth-mode login
az storage queue create --name orders-queue --account-name "$STORAGE" --auth-mode login

echo
echo "Put this in your .env  ->  AZURE_STORAGE_ACCOUNT_NAME=$STORAGE"
