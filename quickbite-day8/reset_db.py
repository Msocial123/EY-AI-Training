"""Delete your QuickBite database to start fresh (e.g. before a new batch).
   python reset_db.py          -> asks for confirmation
   python reset_db.py --yes    -> no question"""
import sys
from azure.cosmos import exceptions
from qb.config import get_client, DB_NAME

if "--yes" not in sys.argv:
    if input(f"Delete database '{DB_NAME}' and ALL its containers? Type yes: ").strip().lower() != "yes":
        sys.exit("Cancelled.")
try:
    get_client().delete_database(DB_NAME)
    print(f"Deleted '{DB_NAME}'. Run the labs again to recreate it.")
except exceptions.CosmosResourceNotFoundError:
    print(f"'{DB_NAME}' does not exist - nothing to delete.")
