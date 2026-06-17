# How the pilot works

A fixed-scope, lightweight check of whether your tool-using agent can be talked into an action it should not take. Staging only. I do not need access to your systems.

## The steps

1. We agree on 5 to 10 scenarios mapped to your riskiest workflows. I write them for your tools, not a generic checklist. Scenarios can cover a single high-impact action or a short workflow where an earlier approval might be reused or applied too broadly later in the workflow.
2. You run them against a staging copy of your agent and send back the tool-call traces. There is a small adapter to make this easy, and we can do a quick one-scenario setup check first so the results are valid.
3. I score the traces by hand and send you an OWASP-mapped report with the tool-call evidence and concrete fixes.
4. One included retest of the same scenario set after you apply fixes.

## What you provide

- A staging or sandbox copy of the agent, with its tools mocked or sandboxed.
- A way to capture the agent's tool calls (most teams already log these).
- A short written authorization for the test.

That is it. No production access, no real customer data, no shared credentials.

## What you get

An independent, evidence-backed report you can act on, and that you can show to a customer's security review or your own team.

## What it is not

Not production testing. Not a broad penetration test. Not a compliance certification. It is a focused look at one thing, whether content your agent reads can push it into an unsafe action.

## Safety

Staging or sandbox only, never production. Written authorization before any test. A harmless canary value for any leak test, never real secrets.
