# QuickBite — Day 8 code (Azure Cosmos DB) — Mac + VS Code

Full instructions: Day8_Trainer_Playbook_Mac_Edition.pdf (Part A).
Run everything from THIS folder in the VS Code terminal (Ctrl + `):

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env          # then fill it in (Azure keys, or COSMOS_EMULATOR=true)
    python check_setup.py         # must show all [OK]

    python live/01_connect.py          # 8.1 / 8.2
    python live/02_ru_meter.py         # 8.3
    python live/03_modelling.py        # 8.4
    python live/04_partition_keys.py   # 8.5
    python live/06_order_flow_demo.py  # 8.6 (uses 05_order_repository.py)
    python live/07_lost_update.py      # 8.6 ETag demo
    python mini_project/test_reviews.py   # mini project, target 6/6
    python reset_db.py                 # fresh start

Trainer: python mini_project/test_reviews.py reviews_solution
Windows freshers: py -m venv .venv  /  .venv\Scripts\Activate.ps1  /  copy .env.example .env
