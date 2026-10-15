---
name: writing-tools-branch
description: "Draft, revise, or audit prose against 55 writing rules."
disable-model-invocation: true
---

# Writing Tools

The 55 rules live in branch files. Before writing anything, record the piece's branch tags, then read every branch file the tags select. Core and Targets apply to every piece; a rule in Targets applies once its target appears. Every applied rule ends on its Pass line.

## Branch tags

Record the form and every matching size tag in working notes.

- Form, per Rule 25: report, story, or hybrid. A piece with any narrative passage is story or hybrid.
- Size: short or length-capped (a message, a reply, or any length limit); multi-section (headings or several distinct parts); standard if neither applies. Short and multi-section can both apply.

| Tag | Read |
| --- | --- |
| Every piece | [Core](branches/core.md), [Targets](branches/targets.md) |
| Story or hybrid | [Story](branches/story.md) |
| Multi-section | [Multi-section](branches/multi-section.md) |
| Short or length-capped | [Short](branches/short.md) |

## Ground rules

- Evidence lock. Facts, quantities, units, dates, names, attribution, quotations, uncertainty, causality, and ownership survive every edit. Measurements stay distinct from projections. An added factual claim is verified or marked as a gap. Invented detail belongs to fiction alone.
- Authorized scope. Edit only what the user authorized, and leave quotations and out-of-scope text byte-identical. A spelling-only request returns spelling fixes alone.
- Genre holds. A report stays a report; story rules apply only to pieces tagged story or hybrid.
- Requirements, not advice. A Pass line is binary. Polishing ends when every applied rule passes and the requested format and length are met; an irreconcilable conflict is disclosed, not claimed as a pass.
- Clean output. Deliver the prose plus essential gap or conflict notes. Rule numbers, tags, and check results appear only in an audit.

## Playbooks

Keep a todo list in working notes whose first items are the matched playbook's steps, copied verbatim. A todo tool is optional; the steps and their completion criteria still apply.

- [Draft](playbooks/draft.md). New prose from a brief, notes, or facts.
- [Revise](playbooks/revise.md). Edit, tighten, shorten, or restyle supplied prose.
- [Audit](playbooks/audit.md). Report rule results for supplied prose.

## Maintenance

Each rule has one home, its branch file. Measure behavior changes with the [regression cases](evals/cases.md).
