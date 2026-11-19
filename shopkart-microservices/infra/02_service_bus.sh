#!/usr/bin/env bash
# infra/02_service_bus.sh  ->  Module 6
# Creates: Service Bus namespace (Standard tier - needed for topics),
#          queue "orders" (max 3 delivery attempts -> dead-letter),
#          topic "order-events" with 2 subscriptions.
set -e
source "$(dirname "$0")/00_variables.sh"

az servicebus namespace create --resource-group "$RG" --name "$SB_NAMESPACE" \
  --location "$LOCATION" --sku Standard

az servicebus queue create --resource-group "$RG" --namespace-name "$SB_NAMESPACE" \
  --name orders --max-delivery-count 3 --enable-dead-lettering-on-message-expiration true

az servicebus topic create --resource-group "$RG" --namespace-name "$SB_NAMESPACE" --name order-events
for SUB in email-sub analytics-sub; do
  az servicebus topic subscription create --resource-group "$RG" \
    --namespace-name "$SB_NAMESPACE" --topic-name order-events --name "$SUB"
done

# Passwordless access for you (same role you would give a Managed Identity)
ME=$(az ad signed-in-user show --query id -o tsv)
SB_ID=$(az servicebus namespace show --resource-group "$RG" --name "$SB_NAMESPACE" --query id -o tsv)
az role assignment create --assignee-object-id "$ME" --assignee-principal-type User \
  --role "Azure Service Bus Data Owner" --scope "$SB_ID"

echo
echo "Passwordless .env  ->  SERVICEBUS_NAMESPACE=$SB_NAMESPACE"
echo "Key-based .env (learning only) ->  SERVICEBUS_CONNECTION_STRING=\"$(az servicebus namespace authorization-rule keys list \
  --resource-group "$RG" --namespace-name "$SB_NAMESPACE" --name RootManageSharedAccessKey \
  --query primaryConnectionString -o tsv)\""
