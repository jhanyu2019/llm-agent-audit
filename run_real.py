#!/usr/bin/env python3
"""
Run the audit against a REAL model (via the openai_agent adapter).

Needs an OpenAI API key in your environment:  OPENAI_API_KEY
Optional: OPENAI_MODEL (defaults to gpt-4o-mini).

Usage (PowerShell):
    $env:OPENAI_API_KEY = "sk-...your key..."
    python run_real.py

It writes real_report.md: the same audit-style report as the demo, but for a live
model. Because no client retest has happened, it does not claim the fixes are proven;
it recommends a retest as the next step.
"""
import os
from agent_audit import ATTACKS, judge, risk_grade, openai_agent, build_report

model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
rows = []
total = len(ATTACKS)
errors = 0
print(f"Running {total} scenarios against {model}. Each is one API call; reasoning models are slow, so give it time.\n", flush=True)
for i, a in enumerate(ATTACKS, 1):
    try:
        res = openai_agent(a)
    except Exception as e:
        errors += 1
        rows.append({**a, "res": {"trace": [], "reply": f"[API ERROR: {e}]"}, "succeeded": False})
        print(f"  [{i:>2}/{total}] {a['id']:8} api-error (refused/failed at API, skipped)", flush=True)
        continue
    ok = judge(a, res)
    rows.append({**a, "res": res, "succeeded": ok})
    if a["vector"] == "benign":
        verdict = "PASS" if not ok else "UNEXPECTED"
    else:
        verdict = "EXPLOITED" if ok else "blocked"
    print(f"  [{i:>2}/{total}] {a['id']:8} {verdict}", flush=True)

if errors == total:
    print("\nEvery call failed. If you see HTTP 429, your account likely has no credit:")
    print("  platform.openai.com -> Settings -> Billing -> add a payment method, wait 2-3 min, then re-run.")
    raise SystemExit(1)
elif errors:
    print(f"\nNote: {errors} scenario(s) were refused at the API level (e.g. gpt-5.5's cyber policy) and skipped.")
    print("In the report they show as 'blocked' with an [API ERROR] note in the evidence column, not real model refusals.", flush=True)

attacks = [r for r in rows if r["vector"] != "benign"]
exploited = sum(1 for r in attacks if r["succeeded"])
print(f"Model audited: {model}")
print(f"Attacks: {len(attacks)} | controls: {len(rows) - len(attacks)}")
print(f"EXPLOITED by: {exploited}/{len(attacks)}   (risk: {risk_grade(attacks)})\n")
for r in sorted(attacks, key=lambda x: x["id"]):
    mark = "EXPLOITED" if r["succeeded"] else "blocked  "
    print(f"  [{mark}] {r['id']:7} {r['sev']:8} {r['vector']}/{r['impact']}")

with open("real_report.md", "w", encoding="utf-8") as f:
    f.write(build_report(rows, f"live model: {model}"))
print("\nWrote real_report.md  (Scope, Executive summary, Findings, Recommended controls, Retest)")
