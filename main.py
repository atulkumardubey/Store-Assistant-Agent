import sys
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from agent import make_client, run_react_agent
from agent.trace import print_trace, save_trace

TRACES_DIR = Path("traces")

# 15 test queries across 5 scenarios
TEST_QUERIES = [
    # Scenario 1: Happy path — all three tools called
    ("S1-a", "I want 2 blue shirts in size M delivered to 560001"),
    ("S1-b", "I need 3 shirts in size S to pincode 400001"),
    ("S1-c", "Can you deliver 1 shirt size XL to 110001?"),

    # Scenario 2: Out of stock — price and delivery skipped
    ("S2-a", "I want 5 red jackets in size XL to 400001"),
    ("S2-b", "Get me 2 red jackets in size L, pincode 600001 — I need more than 2"),
    ("S2-c", "Order 3 jackets XL to 700001"),

    # Scenario 3: Bulk order triggers discount
    ("S3-a", "I want 10 white t-shirts in size L delivered to 110001"),
    ("S3-b", "Please order 7 t-shirts size M to 560001"),
    ("S3-c", "Can I get 15 t-shirts size S shipped to pincode 380001?"),

    # Scenario 4: Unserviceable / unknown pincode
    ("S4-a", "I want 1 black trouser size 32 delivered to pincode 999999"),
    ("S4-b", "Order 2 trousers size 30 to 123456"),
    ("S4-c", "Send 1 black trouser size 34 to 000000"),

    # Scenario 5: Unknown product
    ("S5-a", "I want 3 purple hats in size M delivered to 600001"),
    ("S5-b", "Order 2 sneakers size 10 to 500001"),
    ("S5-c", "I'd like 4 silk scarves size M delivered to 302001"),
]


def run_all() -> None:
    try:
        make_client()
    except RuntimeError as exc:
        print(f"\nSetup error: {exc}\n")
        sys.exit(1)

    results_summary = []

    for idx, (scenario_id, query) in enumerate(TEST_QUERIES, start=1):
        print(f"\n[{idx:02d}/15] Scenario {scenario_id}")
        trace = run_react_agent(query)
        print_trace(trace)

        trace_path = TRACES_DIR / f"trace_{idx:02d}_{scenario_id}.json"
        save_trace(trace, trace_path)

        results_summary.append({
            "id": scenario_id,
            "tools": trace.tools_called,
            "api_calls": trace.total_api_calls,
            "steps": len(trace.steps),
        })

    # Summary table
    print("\n" + "=" * 70)
    print(f"{'ID':<8} {'Tools called':<40} {'API':<5} {'Steps'}")
    print("─" * 70)
    for r in results_summary:
        tools_str = " → ".join(r["tools"]) if r["tools"] else "(none)"
        print(f"{r['id']:<8} {tools_str:<40} {r['api_calls']:<5} {r['steps']}")
    print("=" * 70)
    print(f"\nTrace files saved to: {TRACES_DIR.resolve()}\n")


if __name__ == "__main__":
    run_all()
