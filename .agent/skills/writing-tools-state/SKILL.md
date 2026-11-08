---
name: writing-tools
description: "Draft, revise, or audit prose against 55 writing rules."
disable-model-invocation: true
---

# Writing Tools

Run every request as a state machine. Start in ROUTE, do one state at a time, and leave a state only when its exit check passes. Read a layer file when its state starts, never ahead. Within a layer, the Always section applies to every piece, and a rule with a Target line applies once its target appears. Every applied rule ends on its Pass line.

## Ground rules

- Evidence lock. Facts, quantities, units, dates, names, attribution, quotations, uncertainty, causality, and ownership survive every edit. Measurements stay distinct from projections. An added factual claim is verified or marked as a gap. Invented detail belongs to fiction alone.
- Authorized scope. Edit only what the user authorized, and leave quotations and out-of-scope text byte-identical. A spelling-only request returns spelling fixes alone.
- Genre holds. A report stays a report under every layer; a story rule applies only where a narrative passage already exists.
- Requirements, not advice. A Pass line is binary. Polishing ends when every applied rule passes and the requested format and length are met; an irreconcilable conflict is disclosed, not claimed as a pass.
- Clean output. Deliver the prose plus essential gap or conflict notes. Rule numbers and check results appear only in an audit.

## State record

Keep this record in working notes and update it as each state ends:

- `mode`: draft, revise, narrow, or audit.
- `form`: report, story, or hybrid.
- `size`: short (a message, a reply, or any length limit), standard, or multi-section (headings or several distinct parts).
- `scope`: the authorized edits and byte-identical text, or the audit's rules.
- `applied`: each applied rule number with its layer.
- `open`: applied rules whose Pass line currently fails.

## Transitions

| State | Read | Work | Exit check | Next |
| --- | --- | --- | --- | --- |
| ROUTE | | Set `mode`. New prose from a brief, notes, or facts is draft. Supplied prose to edit, tighten, shorten, or restyle is revise; a fix limited to one kind, such as spelling only, is narrow. A request for rule results is audit. | `mode` is set. | draft: PLAN. revise: LOCK. narrow: NARROW. audit: SCOPE. |
| NARROW | | Make only the authorized fix. | The output differs from the input only by that fix. | DONE |
| LOCK | | Set `scope`: what the user authorized, and what stays byte-identical. | `scope` is set. | PLAN |
| PLAN | [Layer 1](layers/1-plan.md) | Set `form` and `size`. Apply Layer 1; for revise, map the mission and structure of the existing text. | `form` and `size` are set, and every applied Layer 1 rule passes. | draft: WRITE. revise: STRUCTURE. |
| WRITE | | Write the whole draft from beginning to end before any editing. | A complete draft exists. | STRUCTURE |
| STRUCTURE | [Layer 2](layers/2-structure.md) | Apply Layer 2. | Every applied Layer 2 rule passes. | PASSAGE |
| PASSAGE | [Layer 3](layers/3-passage.md) | Apply Layer 3. | Every applied Layer 3 rule passes. | SENTENCE |
| SENTENCE | [Layer 4](layers/4-sentence.md) | Apply Layer 4. Qualifiers move into the middle of the sentence; they stay in the text. | Every applied Layer 4 rule passes. | VERIFY |
| VERIFY | | Recheck every rule in `applied` against the current text, and the requested format and length. Put each failure in `open`. | `open` is empty. | `open` empty: DELIVER. Otherwise: the state owning the lowest-layer open rule, then back to VERIFY. |
| DELIVER | [Layer 5](layers/5-deliver.md) | Apply Layer 5. | Every applied Layer 5 rule passes. | DONE |
| SCOPE | | Set `scope`: the rules the user named; every rule for an all-55 request; otherwise every layer's applicable rules. | `scope` is set. | CHECK |
| CHECK | The layer files holding rules in `scope` | Give each rule in scope exactly one result: `PASS`; `FAIL`, with the passage and the required fix, since a present target that misses its Pass line is a FAIL; `NO TARGET`, naming the absent target, such as "no dialogue"; or `USER OVERRIDE`, quoting the conflicting instruction. Rewrite only on request. | Every rule in `scope` has one result. | REPORT |
| REPORT | | Report results by rule number. | The report claims nothing beyond `scope`. | DONE |

A rule that fails VERIFY twice after its owning state has run again is an irreconcilable conflict: disclose it and go to DELIVER.

## Branches

- `form` report: story Targets stay absent. A hybrid applies them to its narrative part only.
- `size` short: multi-section Targets stay absent.

## Layers

| Layer | Rules |
| --- | --- |
| [1. Plan](layers/1-plan.md) | 24, 25, 31, 40, 41, 42, 43, 44, 45, 48, 49, 55 |
| [2. Structure](layers/2-structure.md) | 10, 19, 29, 30, 32, 33, 35, 36, 37, 39 |
| [3. Passage](layers/3-passage.md) | 14, 18, 20, 21, 22, 26, 27, 28, 34, 38, 51, 54 |
| [4. Sentence](layers/4-sentence.md) | 1, 2, 3, 4, 5, 6, 7, 8, 9, 11, 12, 13, 15, 16, 17, 23, 52, 53 |
| [5. Deliver](layers/5-deliver.md) | 46, 47, 50 |
