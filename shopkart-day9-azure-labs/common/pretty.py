"""Small printing helpers so lab output is easy to read on a projector."""
import json

LINE = "=" * 72


def banner(title: str) -> None:
    print(f"\n{LINE}\n  {title}\n{LINE}")


def step(text: str) -> None:
    print(f"\n>>> {text}")


def info(text: str) -> None:
    print(f"    {text}")


def ok(text: str) -> None:
    print(f"    [OK]   {text}")


def warn(text: str) -> None:
    print(f"    [NOTE] {text}")


def fail(text: str) -> None:
    print(f"    [FAIL] {text}")


def show_json(obj, limit: int = 1200) -> None:
    text = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    if len(text) > limit:
        text = text[:limit] + "\n    ... (truncated)"
    for line in text.splitlines():
        print(f"    {line}")


def table(rows: list[dict], columns: list[str] | None = None, max_width: int = 34) -> None:
    """Print a list of dicts as a simple text table."""
    if not rows:
        info("(no rows)")
        return
    columns = columns or list(rows[0].keys())

    def cell(v):
        s = "" if v is None else str(v)
        return s if len(s) <= max_width else s[: max_width - 3] + "..."

    widths = {c: max(len(c), *(len(cell(r.get(c))) for r in rows)) for c in columns}
    header = " | ".join(c.ljust(widths[c]) for c in columns)
    print("    " + header)
    print("    " + "-+-".join("-" * widths[c] for c in columns))
    for r in rows:
        print("    " + " | ".join(cell(r.get(c)).ljust(widths[c]) for c in columns))
