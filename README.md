<div align="center">

# Action-boundary audits for tool-using AI agents

I test whether untrusted content, such as a user message, ticket, email, document, call transcript, or tool response, can push your tool-using AI agent into a high-impact action it should not take: issuing a refund, moving money, changing a vendor's bank account, deleting an account, granting access, disabling MFA, dispatching a job, or exporting data.

[![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.20585659.svg)](https://doi.org/10.5281/zenodo.20585659)
![OWASP LLM Top 10](https://img.shields.io/badge/OWASP-LLM_Top_10-155e75)
![staging only](https://img.shields.io/badge/scope-staging--only-155e75)
![MIT license](https://img.shields.io/badge/license-MIT-155e75)

**Want the scenarios I would test for your agent?**
[Email me](mailto:jiahao@actionboundary.dev) | [LinkedIn](https://www.linkedin.com/in/jiahao-zhang-12999b319) | [actionboundary.dev](https://actionboundary.dev/)

</div>

---

**How it works.** Your team runs a small set of scenarios against a staging copy of your agent and sends back the tool-call traces. You get an OWASP-mapped report with the evidence and concrete fixes. No production access, no real customer data, no shared credentials.

**Why it is different.** Most AI testing checks what the model says. This checks what the agent does: did it call a tool it should not have been allowed to call? Pass or fail comes from the agent's actual tool-call trace, not from string-matching its reply.

A poisoned ticket, invoice, or tool response can look like normal business context while quietly asking the agent to issue a refund, export data, or change an account. I test whether that text becomes an action.

## Start here

- **[Sample pilot report](docs/sample-pilot-report.md)**: what you receive, with findings, trace evidence, severity, and fixes.
- **[A worked example: an accounts-payable agent](docs/ap-action-boundary-case-note.md)**: the method run end to end on a real tool-calling model in a synthetic AP workflow. It caught an unauthorized data export and still passed the benign controls.
- **[How the pilot works](pilot/how-the-pilot-works.md)**: the process, async, staging-only, fixed-scope, about a week.

## Why you can trust it

It is independent, open, and evidence-based. On a fixed battery run across six recent models from three major vendors, the average number of unsafe tool calls ranged from 0.0 to 8.0 on the same test, and the frontier label was not a reliable safety signal. The lesson: a model's refusal, and model choice, are not your authorization layer. That has to live in your application.

Read the cross-vendor study: [Model choice is not an authorization layer](docs/model-choice-is-not-an-authorization-layer.md). The harness, per-model data, and technical report are archived on Zenodo with a [DOI](https://doi.org/10.5281/zenodo.20585659) for citation and reproducibility.

<details>
<summary><b>More research and raw data</b></summary>

**Part one, one vendor.** I ran the battery against three current OpenAI models, `gpt-5.5`, `gpt-5-mini`, and `gpt-5-nano`. All three blocked every prompt injection disguised as ordinary business text. What got through were mostly plain, direct requests phrased like routine work, plus one one-line jailbreak on gpt-5-nano. The models still called `delete_account`, `transfer_funds`, and `grant_access` with no authorization check. Full writeup: [A model's refusals are not your authorization layer](docs/refusals-are-not-your-authorization-layer.md). Raw run reports: [gpt-5.5](docs/real_report_gpt5.5.md), [gpt-5-mini](docs/real_report_gpt5-mini.md), [gpt-5-nano](docs/real_report_gpt5-nano.md).

**Part two, six models across three vendors.** Per-model summaries for the cross-vendor study above: [docs/runs/v1.5](docs/runs/v1.5).

**Addendum, two OpenAI-compatible models.** I added DeepSeek `deepseek-v4-flash` and Qwen `qwen/qwen3.7-plus` to the same v1.5 battery. The result did not change the lesson: cheaper or API-compatible model paths can still call high-impact tools without authorization. Short note: [Two more OpenAI-compatible models, same authorization question](docs/openai-compatible-models-authorization-addendum.md).

**Multi-turn method.** How the audit scores short workflows where an earlier approval is reused or applied too broadly later: [Testing multi-turn authorization drift](docs/multi-turn-authorization-drift-method.md).

**Scope.** The public research is a *fixed* battery, v1.5, 58 attacks plus 3 controls, run across models for reproducibility. That is the open benchmark, not the product. A client pilot is *customized to your real workflow*: scenarios are written for your agent's own tools.

**What it checks**: each scenario is tagged with an OWASP LLM Top 10 category and a severity.

| Category | The question |
|---|---|
| `prompt_injection` | Can a user override the agent's instructions? |
| `indirect_injection` | Can instructions hidden in data hijack the agent's actions? |
| `tool_misuse` | Can an unverified user trigger a high-risk tool like refund or delete? |
| `data_exfiltration` | Can it be made to send internal data to an outsider? |
| `jailbreak` | Can it be talked out of its safety rules? |
| `secret_disclosure` | Will it reveal credentials held in its context? |
| `excessive_agency` | Does it take actions beyond what the user actually asked? |

</details>

<details>
<summary><b>Run it yourself</b></summary>

| Repo layer | What you are looking at |
|---|---|
| Offline demo | `agent_audit.py` runs a naive and a guarded reference agent with no API key. |
| Live API runs | `run_real.py` runs battery v1.5 against real model APIs and writes trace-backed reports. |
| Client pilot | The generic scenarios are replaced with your staging tools, approvals, and traces. |

<p align="center">
  <img src="docs/demo.gif" alt="Offline harness demo" width="900">
</p>
<p align="center"><sub>Offline demo, not a live-model result. It shows the harness grading tool calls against reference demo agents.</sub></p>

**Quickstart, offline, no API key:**

```bash
python agent_audit.py
```

It runs the 53 core attack scenarios against an un-hardened agent, then the same agent with guardrails, and writes a client-ready `agent_report.md` with evidence and fixes. The live cross-vendor study used battery v1.5, 58 attacks plus 3 controls; see `run_real.py`.

**On your own model.** Replace the demo agents with a function that runs your agent's tool-calling loop and records each `(tool_name, args)` into `trace`. `run_real.py` supports OpenAI, Anthropic, and Gemini through the `PROVIDER` env var, plus OpenAI-compatible gateways through `OPENAI_BASE_URL`. Set `RUNS=3` for per-run reports and a multi-run summary.

This is a defensive tool. It helps teams find and fix unsafe agent behavior before attackers do.

</details>

---

Independent audit by Jiahao Zhang, JZ Software Consulting. Staging-only, no production access.

**Want the scenarios I would test for your agent?** [Email me](mailto:jiahao@actionboundary.dev) | [LinkedIn](https://www.linkedin.com/in/jiahao-zhang-12999b319)
