#!/usr/bin/env python3
"""
Beginner-friendly local verifier for the AP L4 customer-like harness.

This does not call a model and does not use the network. It reruns all L4
scenarios, rewrites the JSON/Markdown outputs, and prints a compact health
check that is easier to read than the full trace.

Run from the repository root:
    .\\.venv-s5\\Scripts\\python.exe pilot\\ap_l4_verify_local.py
"""

from __future__ import annotations

from collections import defaultdict
import json
import sys

import ap_l4_customer_harness as l4


MODES = ["naive", "careful", "enforced"]


def main() -> int:
    runs = [l4.run_scenario(scenario_id, mode) for scenario_id in sorted(l4.SCENARIOS) for mode in MODES]
    errors = l4.validate_expectations(runs)

    l4.OUT_RUNS.write_text(json.dumps(runs, indent=2, sort_keys=True), encoding="utf-8")
    l4.write_summary(runs, errors)

    matrix: dict[str, dict[str, str]] = defaultdict(dict)
    for doc in runs:
        matrix[doc["scenario_id"]][doc["mode"]] = doc["scoring"]["overall"]

    print("AP L4 local verifier")
    print("=" * 22)
    for scenario_id in sorted(matrix):
        outcomes = " | ".join(f"{mode}: {matrix[scenario_id][mode]}" for mode in MODES)
        print(f"{scenario_id}: {outcomes}")

    print()
    print(f"Wrote: {l4.OUT_RUNS}")
    print(f"Wrote: {l4.OUT_SUMMARY}")
    print()

    if errors:
        print("FAIL: AP L4 local harness did not match expected outcomes.")
        for error in errors:
            print(f"- {error}")
        return 1

    print("PASS: AP L4 local harness matched all expected outcomes.")
    print("Next: read pilot/ap_l4_customer_harness_summary.md, then attach a real agent adapter.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
