"""
run.py  ->  One command to start any ShopKart service (works on Windows, Mac, Linux)

    python run.py product                       # Product service  on :8001
    python run.py product --port 8011 --name product-2   # a SECOND copy (for load balancing)
    python run.py order                         # Order service    on :8002
    python run.py inventory                     # Inventory (Flask) on :8003
    python run.py gateway                       # Mini gateway     on :8000
    python run.py worker                        # Background order worker

Each service needs its OWN terminal window (they run forever until Ctrl+C).
"""
import argparse
import os

SERVICES = {
    "product": ("product_service.main:app", 8001),
    "order": ("order_service.main:app", 8002),
    "gateway": ("gateway.mini_gateway:app", 8000),
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Start a ShopKart microservice")
    parser.add_argument("service", choices=["product", "order", "inventory", "gateway", "worker"])
    parser.add_argument("--port", type=int, help="override the default port")
    parser.add_argument("--name", help="instance name, e.g. product-2")
    args = parser.parse_args()

    if args.name:
        os.environ["INSTANCE_NAME"] = args.name

    if args.service == "worker":
        from workers.order_worker import run_forever
        run_forever()
    elif args.service == "inventory":
        from inventory_service.app import app
        app.run(port=args.port or 8003)
    else:
        import uvicorn
        target, default_port = SERVICES[args.service]
        uvicorn.run(target, host="127.0.0.1", port=args.port or default_port)


if __name__ == "__main__":
    main()
