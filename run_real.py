#!/usr/bin/env python3
"""
Run the audit against a REAL model (via the openai_agent adapter).

Needs an OpenAI API key in your environment:  OPENAI_API_KEY
Optional: OPENAI_MODEL (defaults to gpt-5-mini).

Usage (PowerShell):
    $env:OPENAI_API_KEY = "sk-...your key..."
    python run_real.py

It writes real_report.md: the same audit-style report as the demo, but for a live
model. Because no client retest has happened, it does not claim the fixes are proven;
it recommends a retest as the next step.
"""
import os
from agent_audit import (ATTACKS, ADVANCED, judge, risk_grade, build_report,
                         openai_agent, anthropic_agent, gemini_agent)

PROVIDER = os.environ.get("PROVIDER", "openai").lower()
AGENTS = {"openai": openai_agent, "anthropic": anthropic_agent, "gemini": gemini_agent}
MODEL_ENV = {"openai": "OPENAI_MODEL", "anthropic": "ANTHROPIC_MODEL", "gemini": "GEMINI_MODEL"}
KEY_ENV = {"openai": "OPENAI_API_KEY", "anthropic": "ANTHROPIC_API_KEY", "gemini": "GEMINI_API_KEY"}
if PROVIDER not in AGENTS:
    raise SystemExit(f"PROVIDER must be one of {sorted(AGENTS)}; got {PROVIDER!r}")
agent = AGENTS[PROVIDER]
model = os.environ.get(MODEL_ENV[PROVIDER], "")
if not os.environ.get(KEY_ENV[PROVIDER]):
    raise SystemExit(f"Set {KEY_ENV[PROVIDER]} before running with PROVIDER={PROVIDER}.")
if not model:
    raise SystemExit(f"Set {MODEL_ENV[PROVIDER]} to a current model id before running with PROVIDER={PROVIDER} (list your models first).")
SCENARIOS = ATTACKS + ADVANCED
rows = []
total = len(SCENARIOS)
errors = 0
print(f"Provider: {PROVIDER} | model: {model or '(set the model env var)'} | {total} scenarios\n", flush=True)
import time
DELAY = float(os.environ.get("REQUEST_DELAY", "0"))  # seconds between calls; set e.g. 6 for free tiers
for i, a in enumerate(SCENARIOS, 1):
    res = err = None
    for attempt in range(3):
        try:
            res, err = agent(a), None
            break
        except Exception as e:
            err = e
            m = str(e).lower()
            if attempt < 2 and ("429" in m or "rate" in m or "quota" in m or "exhausted" in m):
                time.sleep(10 * (attempt + 1))
                continue
            break
    if err is not None:
        errors += 1
        rows.append({**a, "res": {"trace": [], "reply": f"[API ERROR: {err}]"}, "succeeded": False})
        print(f"  [{i:>2}/{total}] {a['id']:8} api-error (refused/failed at API, skipped)", flush=True)
        if DELAY:
            time.sleep(DELAY)
        continue
    ok = judge(a, res)
    rows.append({**a, "res": res, "succeeded": ok})
    if a["vector"] == "benign":
        verdict = "PASS" if not ok else "UNEXPECTED"
    else:
        verdict = "EXPLOITED" if ok else "blocked"
    print(f"  [{i:>2}/{total}] {a['id']:8} {verdict}", flush=True)
    if DELAY:
        time.sleep(DELAY)

if errors == total:
    print(f"\nEvery call to {PROVIDER} failed. Check that {KEY_ENV[PROVIDER]} is valid, {MODEL_ENV[PROVIDER]} is a current model id, and the account has credit (HTTP 429 usually means no credit).")
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
    f.write(build_report(rows, f"live model: {PROVIDER}/{model}"))
print("\nWrote real_report.md  (Scope, Executive summary, Findings, Recommended controls, Retest)")
