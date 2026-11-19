"""
gateway/mini_gateway.py   ->   A tiny LOAD BALANCER + API GATEWAY in ~100 lines

Run:   uvicorn gateway.mini_gateway:app --port 8000

This is NOT for production. It exists so you can SEE on your laptop what
Azure Load Balancer and Azure Application Gateway do in the cloud:

  * Round robin      -> requests are shared one-by-one across copies (Load Balancer)
  * Health probe     -> a dead copy is skipped automatically (Load Balancer)
  * Path routing     -> /api/products/* goes to one pool,
                        /api/orders/* to another   (Application Gateway, layer 7)
"""
import os
import threading

import httpx
from fastapi import FastAPI, HTTPException, Request, Response

# --- [7.1] Backend pools (like "Backend pools" in the Azure Portal) ---
PRODUCT_POOL = os.getenv("PRODUCT_POOL", "http://127.0.0.1:8001,http://127.0.0.1:8011").split(",")
ORDER_POOL = os.getenv("ORDER_POOL", "http://127.0.0.1:8002").split(",")
INVENTORY_POOL = os.getenv("INVENTORY_POOL", "http://127.0.0.1:8003").split(",")


class BackendPool:
    """A list of servers + a round-robin pointer."""

    def __init__(self, name: str, servers: list[str]):
        self.name = name
        self.servers = servers
        self._next = 0
        self._lock = threading.Lock()

    def order_to_try(self) -> list[str]:
        """Round robin: start from the next server, then the others as backup."""
        with self._lock:
            start = self._next
            self._next = (self._next + 1) % len(self.servers)
        return self.servers[start:] + self.servers[:start]


# --- [7.2] Routing rules (like "URL path-based rules" in Application Gateway) ---
ROUTES = {
    "products": BackendPool("product-pool", PRODUCT_POOL),
    "orders": BackendPool("order-pool", ORDER_POOL),
    "inventory": BackendPool("inventory-pool", INVENTORY_POOL),
}


def pick_pool(service: str) -> BackendPool:
    pool = ROUTES.get(service)
    if pool is None:
        raise HTTPException(status_code=404, detail=f"No route for /api/{service}")
    return pool


app = FastAPI(title="ShopKart Mini Gateway")


# --- [7.3] Health probe: check every backend ---
@app.get("/gateway/health")
def gateway_health():
    report = {}
    for service, pool in ROUTES.items():
        for server in pool.servers:
            try:
                ok = httpx.get(f"{server}/health", timeout=1).status_code == 200
            except httpx.RequestError:
                ok = False
            report[f"{service} -> {server}"] = "healthy" if ok else "DOWN"
    return report


# --- [7.4] The proxy: forward the request, fail over if a server is down ---
@app.api_route("/api/{service}/{path:path}", methods=["GET", "POST", "PUT", "PATCH", "DELETE"])
@app.api_route("/api/{service}", methods=["GET", "POST"])
async def proxy(service: str, request: Request, path: str = ""):
    pool = pick_pool(service)
    target_path = f"/{service}/{path}" if path else f"/{service}"
    body = await request.body()

    async with httpx.AsyncClient(timeout=5) as client:
        for server in pool.order_to_try():
            try:
                upstream = await client.request(
                    request.method,
                    server + target_path,
                    params=request.query_params,
                    content=body,
                    headers={"content-type": request.headers.get("content-type", "application/json")},
                )
            except httpx.RequestError:
                print(f"[gateway] {server} is DOWN, trying next server...")
                continue  # failover to the next server in the pool

            return Response(
                content=upstream.content,
                status_code=upstream.status_code,
                media_type=upstream.headers.get("content-type"),
                headers={
                    "X-Served-By": server,
                    "X-Backend-Pool": pool.name,
                    "X-Instance": upstream.headers.get("X-Instance", "-"),
                },
            )

    raise HTTPException(status_code=502, detail=f"All servers in {pool.name} are down")
