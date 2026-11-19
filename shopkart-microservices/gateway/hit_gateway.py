"""
gateway/hit_gateway.py  ->  Send many requests through the gateway and count
which server answered. Shows round robin with your own eyes.

Run:   python -m gateway.hit_gateway            (default 10 requests)
       python -m gateway.hit_gateway 20
"""
import sys
from collections import Counter

import httpx

GATEWAY = "http://127.0.0.1:8000"


def main(total: int = 10) -> None:
    counter = Counter()
    for i in range(1, total + 1):
        resp = httpx.get(f"{GATEWAY}/api/products/1", timeout=5)
        server = resp.headers.get("X-Served-By", "?")
        instance = resp.headers.get("X-Instance", "?")
        counter[f"{server} ({instance})"] += 1
        print(f"Request {i:>2}: status={resp.status_code}  served by {server}  instance={instance}")

    print("\nSummary:")
    for server, count in counter.items():
        print(f"  {server:<40} {'#' * count} {count}")


if __name__ == "__main__":
    main(int(sys.argv[1]) if len(sys.argv) > 1 else 10)
