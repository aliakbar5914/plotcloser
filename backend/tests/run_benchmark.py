"""Runs tests.json against a live API and prints a benchmark table.

Usage (from the backend folder):
    venv\\Scripts\\python.exe tests\\run_benchmark.py                 # local
    venv\\Scripts\\python.exe tests\\run_benchmark.py https://your-space.hf.space
Only uses the Python standard library (no extra packages).
"""
import json
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

BASE_URL = (sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000").rstrip("/")
TESTS_FILE = Path(__file__).resolve().parents[2] / "tests.json"
RESULTS_FILE = Path(__file__).resolve().parent / "benchmark_results.md"
RUN_ID = uuid.uuid4().hex[:6]  # fresh user ids every run, so old data doesn't interfere


def post_chat(user_id: str, thread_id: str, message: str) -> tuple[dict, float]:
    body = json.dumps({"user_id": user_id, "thread_id": thread_id, "message": message}).encode()
    request = urllib.request.Request(f"{BASE_URL}/chat", data=body,
                                     headers={"Content-Type": "application/json"})
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read())
    except urllib.error.HTTPError as error:
        data = json.loads(error.read() or b"{}")
    return data, time.perf_counter() - started


def check_result(data: dict, check: dict) -> list[str]:
    problems = []
    if set(data.keys()) != {"reply", "tool_calls", "tokens"}:
        problems.append(f"wrong response keys {sorted(data.keys())}")
        return problems
    reply = data["reply"].lower()
    tools = [call.get("name") for call in data["tool_calls"]]
    for tool in check.get("expect_tools", []):
        if tool not in tools:
            problems.append(f"tool {tool} not called (got {tools})")
    if check.get("expect_no_tools") and tools:
        problems.append(f"unexpected tools {tools}")
    if check.get("reply_any") and not any(word.lower() in reply for word in check["reply_any"]):
        problems.append(f"reply missing any of {check['reply_any']}")
    for word in check.get("reply_none", []):
        if word.lower() in reply:
            problems.append(f"reply contains forbidden '{word}'")
    return problems


def run_case(case: dict) -> dict:
    total_in = total_out = 0
    latencies = []
    data = {}
    for step in case["steps"]:
        user_id = f"bench_{RUN_ID}_{step['user']}"
        thread_id = f"{step['thread']}_{RUN_ID}"
        data, seconds = post_chat(user_id, thread_id, step["message"])
        latencies.append(seconds)
        tokens = data.get("tokens", {})
        total_in += tokens.get("in", 0)
        total_out += tokens.get("out", 0)
    problems = check_result(data, case["check"])
    return {
        "id": case["id"], "name": case["name"], "passed": not problems, "problems": problems,
        "latency": sum(latencies) / len(latencies), "tokens_in": total_in, "tokens_out": total_out,
        "reply": data.get("reply", "")[:120].replace("\n", " "),
    }


def main() -> None:
    suite = json.loads(TESTS_FILE.read_text(encoding="utf-8"))
    print(f"Running benchmark against {BASE_URL} (run {RUN_ID})\n")

    # Order matters: test 8 (isolation) runs after test 7 created user B's data.
    results = [run_case(case) for case in suite["tests"]]
    attack_results = [run_case(case) for case in suite["attacks"]]

    lines = ["| # | Test | Result | Avg latency (s) | Tokens in/out |", "|---|---|---|---|---|"]
    for r in results + attack_results:
        status = "PASS" if r["passed"] else "FAIL"
        lines.append(f"| {r['id']} | {r['name']} | {status} | {r['latency']:.1f} | {r['tokens_in']}/{r['tokens_out']} |")
        print(f"[{status}] {r['id']} {r['name']}  ({r['latency']:.1f}s)  -> {r['reply']}")
        for problem in r["problems"]:
            print(f"        problem: {problem}")

    passed = sum(r["passed"] for r in results)
    attacks_passed = sum(r["passed"] for r in attack_results)
    every = results + attack_results
    tokens_in = sum(r["tokens_in"] for r in every)
    tokens_out = sum(r["tokens_out"] for r in every)
    cost = (tokens_in * 0.10 + tokens_out * 0.50) / 1_000_000  # Haiku 5.5 prices
    summary = [
        "",
        f"- **Own tests passed:** {passed}/{len(results)} ({passed * 100 // len(results)}%)",
        f"- **Attack tests passed:** {attacks_passed}/{len(attack_results)} ({attacks_passed * 100 // len(attack_results)}%)",
        f"- **Average latency:** {sum(r['latency'] for r in every) / len(every):.1f} s per message",
        f"- **Total tokens:** {tokens_in} in / {tokens_out} out (about ${cost:.4f} for the whole run)",
    ]
    print("\n".join(summary))
    RESULTS_FILE.write_text("\n".join(lines + summary) + "\n", encoding="utf-8")
    print(f"\nTable saved to {RESULTS_FILE}")


if __name__ == "__main__":
    main()
