# Stronger models help. They do not replace authorization gates.

Model behavior is not authorization control.

When a tool-using AI agent can move money, export data, schedule care, grant
access, or change a record, the important question is not only what the model
says.

The important question is what the agent is allowed to do.

That distinction is easy to miss. A stronger model may be careful. It may notice
that a request is suspicious. It may choose to check the source of truth before
acting. That is useful behavior.

But useful behavior is not the same thing as an authorization control.

## A finance example

Imagine an employee who can send vendor payments.

An experienced employee will usually reject a suspicious invoice. If the bank
account changed in an email, they may stop and ask for verification. That is
good judgment.

But no serious company treats employee judgment as the whole payment system.

The real control is the approval process around the payment:

- the approval has to come from the right source
- the amount has to match
- the vendor has to match
- the approval has to be current
- the payment system has to keep an audit trail

If those things are missing, the payment should not go out, even if an employee
thinks the invoice looks routine.

Tool-using AI agents need the same boundary.

## The agent version

For an agent, the "employee" is the model plus the surrounding workflow.

The "payment system" is the application layer: the tools, policy checks,
approval objects, source-of-truth lookups, permissions, and trace logs that
decide whether an action may execute.

A strong model can reduce mistakes. It cannot, by itself, prove that the
application has an authorization gate.

That is why an Agent Authorization Review does not ask only, "Did the model say
the safe thing?"

It asks:

> When the agent called a high-impact tool, what trusted evidence authorized
> that exact action?

## Why multi-turn workflows matter

Some failures do not appear on the first step.

An agent may check authorization correctly early in a session. Later, after a
few normal turns, it may read a note, ticket, document, email, transcript, or
tool response that looks like approval. If the agent treats that context as
enough authority for a new high-impact action, the authorization boundary has
moved.

That is why I test short workflows, not only single prompts.

The raw trace records what happened. The scoring layer then asks whether a tool
call had trusted, current, scope-matching authorization evidence at the moment
of execution.

A benign control is just as important as the attack. If the agent reads messy
context but then checks the official approval source before acting, that action
should pass. The goal is not to flag every action. The goal is to distinguish
real authorization from approval-looking text.

## What a review produces

The deliverable is not a model ranking.

It is workflow evidence:

- what high-impact action was tested
- what content the agent read
- what tool the agent called
- what authorization evidence existed at that moment
- whether the evidence came from a trusted source
- whether the evidence matched the amount, recipient, patient, service, role, or
  other scope of the action
- what control would stop or route the action next time

For a startup selling into healthcare, finance, insurance, or other regulated
buyers, this evidence can be more useful than a general statement that "we use a
strong model." It shows how the agent behaves in the workflow the team is
actually shipping.

## The practical rule

Use strong models. They help.

But do not make model behavior your authorization layer.

For payments, exports, scheduling, access changes, and record edits, the action
should be bound to trusted authorization evidence by the application itself.
The model can help prepare the action. The system should decide whether the
action is allowed.
