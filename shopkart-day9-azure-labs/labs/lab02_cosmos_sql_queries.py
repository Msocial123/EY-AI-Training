"""
LAB 2 - Querying ShopKart data with the Cosmos DB SQL (NoSQL) API
=================================================================
Curriculum topic : "Querying with SQL API"

Every query below answers a REAL question someone at ShopKart asks.
Read the 'business question' first, then the SQL, then the output.

Rules to remember
  * FROM c        -> 'c' is just an alias for "each document in the container"
  * Always use @parameters for user input (never string formatting = SQL injection)
  * Give the partition key when you know it -> single-partition query = cheap + fast
  * Cross-partition query = fans out to every partition = more RU

Run:  python labs/lab02_cosmos_sql_queries.py
"""
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from azure.cosmos import exceptions  # noqa: E402
from azure.core import MatchConditions  # noqa: E402

from common.clients import cosmos_database, last_request_charge  # noqa: E402
from common.pretty import banner, step, info, ok, warn, table  # noqa: E402

QUERY_NO = 0


def run(container, business_question, sql, params=None, partition_key=None, columns=None, show=True):
    """Runs one query and prints it nicely. Returns the list of results."""
    global QUERY_NO
    QUERY_NO += 1
    step(f"Q{QUERY_NO}. {business_question}")
    for line in sql.strip().splitlines():
        info(f"SQL> {line.strip()}")
    if params:
        info(f"params: {params}")

    kwargs = {"query": sql, "parameters": params or []}
    if partition_key is not None:
        kwargs["partition_key"] = partition_key          # single-partition query
        scope = f"single partition ('{partition_key}')"
    else:
        kwargs["enable_cross_partition_query"] = True     # fan-out query
        scope = "cross-partition"

    results = list(container.query_items(**kwargs))
    info(f"-> {len(results)} result(s) | {scope} | cost: {last_request_charge(container)}")
    if show:
        if results and isinstance(results[0], dict):
            table(results, columns)
        else:
            info(f"value: {results}")
    return results


def product_queries(products):
    banner("PART A - Product catalogue queries (container: products, pk=/category)")

    run(products, "Homepage: show every product name and price",
        "SELECT c.name, c.category, c.price FROM c")

    run(products, "Electronics page: list electronics (we KNOW the partition -> cheap)",
        "SELECT c.name, c.brand, c.price FROM c WHERE c.category = @cat",
        [{"name": "@cat", "value": "Electronics"}], partition_key="Electronics")

    run(products, "Price filter slider: products between Rs.1,000 and Rs.10,000, cheapest first",
        """SELECT c.name, c.price FROM c
           WHERE c.price BETWEEN @min AND @max
           ORDER BY c.price ASC""",
        [{"name": "@min", "value": 1000}, {"name": "@max", "value": 10000}])

    run(products, "'Top rated' carousel: best 5 products by rating",
        "SELECT TOP 5 c.name, c.rating FROM c ORDER BY c.rating DESC")

    run(products, "Search box: customer typed 'shoe' (case-insensitive)",
        "SELECT c.name, c.price FROM c WHERE CONTAINS(LOWER(c.name), @term)",
        [{"name": "@term", "value": "shoe"}])

    run(products, "Bestseller badge: products tagged 'bestseller' (search inside an ARRAY)",
        "SELECT c.name, c.tags FROM c WHERE ARRAY_CONTAINS(c.tags, 'bestseller')")

    run(products, "Brand filter: Samsung OR Apple (IN operator)",
        "SELECT c.name, c.brand FROM c WHERE c.brand IN ('Samsung', 'Apple')")

    run(products, "Local delivery: products whose seller is in Hyderabad (NESTED property)",
        "SELECT c.name, c.seller.city AS sellerCity FROM c WHERE c.seller.city = 'Hyderabad'")

    run(products, "Festive sale page: only products that HAVE a discount field (semi-structured!)",
        """SELECT c.name, c.price, c.discount.percent AS off
           FROM c WHERE IS_DEFINED(c.discount)""")

    run(products, "Warehouse alert: which colour VARIANTS have stock below 10? (JOIN = unwind array)",
        """SELECT p.name, v.color, v.stock
           FROM p JOIN v IN p.variants
           WHERE v.stock < 10""")

    run(products, "Out-of-stock report (computed field with a ternary)",
        """SELECT c.name, c.stock,
                  (c.stock = 0 ? 'OUT OF STOCK' : (c.stock < 10 ? 'LOW' : 'OK')) AS level
           FROM c WHERE c.stock < 10""")

    run(products, "Dashboard KPI: how many products do we sell? (SELECT VALUE returns a plain number)",
        "SELECT VALUE COUNT(1) FROM c")

    run(products, "Category filter chips: list of DISTINCT categories",
        "SELECT DISTINCT VALUE c.category FROM c")

    run(products, "Category manager: average price inside ONE category (aggregate in a partition)",
        "SELECT VALUE AVG(c.price) FROM c WHERE c.category = 'Electronics'",
        partition_key="Electronics")

    # GROUP BY note: the Python SDK supports GROUP BY only INSIDE one partition.
    step("Category report: product count + avg price per category")
    warn("Python SDK cannot run GROUP BY across partitions -> loop over the partitions instead.")
    report = []
    for cat in run(products, "(helper) list categories", "SELECT DISTINCT VALUE c.category FROM c", show=False):
        rows = run(products, f"(helper) group inside partition '{cat}'",
                   "SELECT c.category, COUNT(1) AS products, AVG(c.price) AS avgPrice "
                   "FROM c GROUP BY c.category", partition_key=cat, show=False)
        report.extend(rows)
    table([{**r, "avgPrice": round(r["avgPrice"], 2)} for r in report])

    step("Pagination: 'Load more' button on the product listing (5 per page)")
    pager = products.query_items(
        query="SELECT c.id, c.name FROM c ORDER BY c.id",
        enable_cross_partition_query=True,
        max_item_count=5,
    ).by_page()
    first_page = list(next(pager))
    token = pager.continuation_token
    info(f"page 1: {[p['id'] for p in first_page]}")
    info(f"continuation token (send this to the frontend): {str(token)[:60]}...")
    warn("Store the token, NOT the page number. Next request resumes exactly where we stopped.")

    run(products, "Simple numbered pages: OFFSET/LIMIT (page 2, size 5)",
        "SELECT c.id, c.name FROM c ORDER BY c.id OFFSET 5 LIMIT 5")


def order_queries(orders):
    banner("PART B - Order queries (container: orders, pk=/customerId)")

    run(orders, "'My Orders' page for Ananya (CUST-001) - newest first, single partition",
        """SELECT c.id, c.orderDate, c.status, c.total FROM c
           WHERE c.customerId = @cid ORDER BY c.orderDate DESC""",
        [{"name": "@cid", "value": "CUST-001"}], partition_key="CUST-001")

    run(orders, "Customer support: all orders with status 'Returned' or 'Cancelled'",
        "SELECT c.id, c.customerName, c.status FROM c WHERE c.status IN ('Returned', 'Cancelled')")

    run(orders, "Fraud team: COD orders above Rs.20,000",
        "SELECT c.id, c.customerName, c.total FROM c WHERE c.paymentMode = 'COD' AND c.total > 20000")

    run(orders, "Which orders contain the iPhone? (EXISTS + sub-query over an array)",
        """SELECT c.id, c.customerName FROM c
           WHERE EXISTS (SELECT VALUE i FROM i IN c.items WHERE i.sku = 'ELEC-1002')""")

    rows = run(orders, "Finance: revenue per city (fetch small projection, aggregate in Python)",
               "SELECT c.city, c.total FROM c WHERE c.status != 'Cancelled'", show=False)
    revenue = defaultdict(int)
    for r in rows:
        revenue[r["city"]] += r["total"]
    table([{"city": k, "revenue_INR": f"{v:,}"} for k, v in sorted(revenue.items(), key=lambda x: -x[1])])

    run(orders, "Ananya's order count by status (GROUP BY inside one partition works)",
        "SELECT c.status, COUNT(1) AS n FROM c GROUP BY c.status",
        partition_key="CUST-001")


def write_operations(products):
    banner("PART C - Writes that real e-commerce code does every second")

    step("Customer bought 2 boAt headphones -> PATCH only the stock field (no full rewrite)")
    before = products.read_item("ELEC-1003", partition_key="Electronics")
    info(f"stock before: {before['stock']}")
    after = products.patch_item(
        item="ELEC-1003", partition_key="Electronics",
        patch_operations=[{"op": "incr", "path": "/stock", "value": -2},
                          {"op": "set", "path": "/lastSoldAt", "value": "2026-11-17T10:00:00Z"}],
    )
    ok(f"stock after : {after['stock']}  | cost: {last_request_charge(products)}")

    step("Two admins edit the same product price at the same time -> optimistic concurrency with _etag")
    item = products.read_item("BOOK-4001", partition_key="Books")
    etag = item["_etag"]
    item["price"] = 449
    products.replace_item(item=item["id"], body=item, etag=etag, match_condition=MatchConditions.IfNotModified)
    ok("Admin A saved price=449 (etag matched)")
    item["price"] = 399
    try:
        products.replace_item(item=item["id"], body=item, etag=etag, match_condition=MatchConditions.IfNotModified)
        warn("Admin B also saved (emulator may not enforce etag checks).")
    except exceptions.CosmosAccessConditionFailedError:
        ok("Admin B got 412 Precondition Failed -> must reload before saving. No lost update!")

    # restore original values so the lab can be re-run
    products.patch_item("ELEC-1003", "Electronics", [{"op": "incr", "path": "/stock", "value": 2}])
    restore = products.read_item("BOOK-4001", partition_key="Books")
    restore["price"] = 499
    products.upsert_item(restore)
    info("(original stock/price restored so you can run the lab again)")


def main():
    db = cosmos_database()
    products = db.get_container_client("products")
    orders = db.get_container_client("orders")
    try:
        products.read()
    except exceptions.CosmosResourceNotFoundError:
        print("Container not found - run labs/lab01_cosmos_setup.py first.")
        sys.exit(1)

    product_queries(products)
    order_queries(orders)
    write_operations(products)
    banner("LAB 2 complete - try exercises/EXERCISES.md, section 'Lab 2'")


if __name__ == "__main__":
    main()
