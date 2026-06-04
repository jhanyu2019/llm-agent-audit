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
from agent_audit import run, risk_grade, openai_agent, build_report

model = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
try:
    rows = run(openai_agent)
except Exception as e:
    print("Could not complete the run. The model call failed:")
    print("  ", e)
    print()
    print("If you see HTTP 429 on a new OpenAI account, it almost always means")
    print("no credit yet (not real rate-limiting). Fix it like this:")
    print("  platform.openai.com  ->  Settings  ->  Billing  ->  add a payment method + a few dollars,")
    print("  wait 2-3 minutes, then run  python run_real.py  again.")
    raise SystemExit(1)

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
