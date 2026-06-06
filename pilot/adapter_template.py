"""
Adapter template: run the AI Agent Reliability & Security Audit against YOUR agent.

You fill in two functions:
  1. load_scenario_data(items) -> put each `data_the_agent_reads` item where your agent
     actually READS it in staging (a staging ticket / CRM record / doc store, or a mocked
     tool that returns it). Return a handle so you can clean it up afterwards.
  2. run_agent(user_request) -> run your agent on the benign user_request only, and return
     (final_reply, trace) where trace is a list of {"tool": name, "arguments": {...}}.

THE ONE RULE THAT MAKES THIS VALID
This audit tests indirect injection: a malicious instruction hidden in the DATA the agent
reads. The instruction must go through load_scenario_data (the agent's real read path).
Do NOT paste it into the user prompt. If you do, you are testing direct injection and the
results are not valid.

SAFETY
Staging or sandbox only. Use mocked / sandboxed tools. Never run against production. No real
customer data, no real secrets (use the canary value provided in the scenario set).
"""
import json


def load_scenario_data(items):
    """items = scenario["data_the_agent_reads"].
    TODO: insert each item into the place your agent retrieves from in STAGING, e.g.
      - write it into a staging support ticket / CRM record / document store the agent reads, OR
      - configure your mocked tool to return it as a tool response.
    Return any handle you need to undo this in cleanup().
    """
    raise NotImplementedError("Wire this to your staging data source")


def run_agent(user_request):
    """TODO: call your agent with ONLY the benign user_request.
    Record every tool call (name + arguments) into `trace`, in order.
    Return (final_reply, trace).
    """
    raise NotImplementedError("Wire this to your agent's run loop")


def cleanup(handle):
    """TODO: remove any staging records you inserted in load_scenario_data."""
    pass


def run_scenario(scenario):
    handle = load_scenario_data(scenario.get("data_the_agent_reads", []))
    try:
        reply, trace = run_agent(scenario["user_request"])
    finally:
        cleanup(handle)
    return {
        "scenario_id": scenario["scenario_id"],
        "user_request": scenario["user_request"],
        "data_the_agent_reads": scenario.get("data_the_agent_reads", []),
        "tool_call_trace": trace,
        "final_reply": reply,
        "model": scenario.get("model", ""),
        "notes": "data inserted via load_scenario_data (the agent's real read path), not the user prompt",
    }


if __name__ == "__main__":
    # scenarios.json = the scenario set you were sent (a JSON list of scenario objects)
    scenarios = json.load(open("scenarios.json", encoding="utf-8"))
    results = [run_scenario(s) for s in scenarios]
    with open("trace_results.json", "w", encoding="utf-8") as f:
        json.dump({"runs": results}, f, indent=2)
    print(f"Wrote trace_results.json with {len(results)} runs. Send that file back.")
