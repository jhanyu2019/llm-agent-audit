#!/usr/bin/env python3
"""
Run the audit against a REAL model (via the openai_agent adapter).

Needs an OpenAI API key in your environment:  OPENAI_API_KEY
Optional: OPENAI_MODEL (defaults to gpt-4o-mini).

Usage (PowerShell):
    $env:OPENAI_API_KEY = "sk-...your key..."
    python run_real.py
"""
import os, datetime
from agent_audit import run, risk_grade, fmt_trace, SEV_ORDER, openai_agent, ATTACKS

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
attacks = [r for r in rows if r["cat"] != "control"]
exploited = sum(1 for r in attacks if r["succeeded"])

print(f"Model audited: {model}")
print(f"Attacks: {len(attacks)} | controls: {len(rows) - len(attacks)}")
print(f"EXPLOITED by: {exploited}/{len(attacks)}   (risk: {risk_grade(attacks)})\n")
for r in sorted(attacks, key=lambda x: (SEV_ORDER[x["sev"]], x["id"])):
    mark = "EXPLOITED" if r["succeeded"] else "blocked  "
    print(f"  [{mark}] {r['id']:6} {r['sev']:8} {r['cat']}")

lines = [
    "# AI Agent Reliability Audit - live model run",
    f"_Generated {datetime.date.today().isoformat()} | model: {model}_",
    "",
    f"**{exploited} of {len(attacks)} attacks exploited this model. Risk: {risk_grade(attacks)}.**",
    "",
    "| ID | Category | OWASP | Severity | Result | What the model did |",
    "|---|---|---|---|---|---|",
]
for r in sorted(attacks, key=lambda x: (SEV_ORDER[x["sev"]], x["id"])):
    v = "**EXPLOITED**" if r["succeeded"] else "blocked"
    lines.append(f"| {r['id']} | {r['cat']} | {r['owasp']} | {r['sev']} | {v} | `{fmt_trace(r['res'])}` |")
with open("real_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(lines) + "\n")
print("\nWrote real_report.md")
