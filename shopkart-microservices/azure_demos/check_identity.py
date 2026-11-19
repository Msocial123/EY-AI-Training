"""
azure_demos/check_identity.py   ->   Module 5: "Who am I?" for Azure SDKs

DefaultAzureCredential tries several login methods in order and uses the
first one that works:
    Environment variables -> Workload Identity -> MANAGED IDENTITY
    -> Azure CLI (az login) -> Azure PowerShell -> Azure Developer CLI ...

On your laptop it will find your `az login`.
On an Azure VM / App Service with Managed Identity it will find the identity.

Run:  python -m azure_demos.check_identity
"""
import base64
import json

from common.azure_clients import get_credential


def decode_token(token: str) -> dict:
    """A token is a JWT: header.payload.signature  -> decode the payload part."""
    payload = token.split(".")[1]
    payload += "=" * (-len(payload) % 4)  # fix padding
    return json.loads(base64.urlsafe_b64decode(payload))


if __name__ == "__main__":
    credential = get_credential()
    token = credential.get_token("https://storage.azure.com/.default")
    claims = decode_token(token.token)
    print("Got an Azure AD token for Storage")
    print("  identity (oid):", claims.get("oid"))
    print("  name/app      :", claims.get("name") or claims.get("app_displayname") or claims.get("appid"))
    print("  tenant        :", claims.get("tid"))
    print("  expires (unix):", token.expires_on)
