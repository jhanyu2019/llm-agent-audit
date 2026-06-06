# Audit your own agent (pilot kit)

Run the AI Agent Reliability & Security Audit against your own tool-using agent, fully async, staging only. You get back an OWASP-mapped report with tool-call evidence and concrete fixes. I never need access to your systems, your production, or any real secrets.

## The one rule that makes the test valid

This audit is about **indirect** prompt injection: can a malicious instruction hidden in the **data your agent reads** (a ticket, an invoice, a tool response) make it take an unsafe tool action? So the adversarial text must go into `data_the_agent_reads`, **not** into the user's message. If you paste it into the user prompt, you are testing direct injection and the results are not valid.

## Files

- `trace_schema.json` — the format for what you send back (a `runs` array).
- `sample_trace_indirect_injection.json` — a worked example. Note where the malicious instruction lives (in the data, not the request) and that the trace shows the agent reading that data before it acts.
- `adapter_template.py` — fill in two functions (`load_scenario_data`, `run_agent`) to run the scenarios you were sent against your staging agent and emit traces in the schema.

## Steps

1. Fill in `adapter_template.py` for your agent. Staging or sandbox only, with mocked or sandboxed tools.
2. Run it on the scenario set you were sent. It writes `trace_results.json`.
3. Send `trace_results.json` back. That is all the access needed. No production, no real customer data, no shared credentials.

Tip: before the full run, do one scenario first and send it back so the wiring can be checked. The common mistake is putting the test instruction in the user prompt instead of in the data the agent reads.

Main project and writeup: https://github.com/hugoii/llm-agent-audit
