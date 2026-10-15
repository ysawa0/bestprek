# Writing skill: best of three

Layer has the highest complete-run score, 18/20, and the highest mean, 17/20. Branch and both each peak at 17/20. Layer's one-point lead depends on a narrow audit-accounting point; none of the variants demonstrates complete rule compliance.

| Variant | Round 1 | Round 2 | Round 3 | Best | Mean |
| --- | --- | --- | --- | --- | --- |
| Layer | 16 | 18 | 17 | 18/20 | 17.00/20 |
| Branch | 17 | 17 | 16 | 17/20 | 16.67/20 |
| Both | 13 | 17 | 16 | 17/20 | 15.33/20 |

Best selects one complete round per variant. Primary and probe scores stay paired; no individual answers are selected across runs.

## Method and records

The existing [directory-read trial](../direct/comparison.md) is round 1. Two additional rounds used six fresh `gpt-6-sol` agents at medium effort, one per variant per round. All nine agents used the same primary brief, ten primary criteria, ten probe prompts, and scoring. Each read only its assigned skill directory. The earlier experiment with parent-supplied files is excluded.

The three skill versions stayed unchanged at commit `18f7925`. Agents received no previous outputs, grades, expected answers, or feedback. Within a round, the primary task and subsequent probe batch shared the same agent context. Read logs are self-reported, and the directory restriction was an instruction rather than a separate filesystem sandbox.

The [manifest](manifest.json) records the protocol and rubric. [Scores](scores.json) preserve every criterion result and aggregate. Verbatim additional-round outputs and read logs are in [layer](layer.md), [branch](branch.md), and [both](both.md). Round 1 outputs remain in their original directory.

| Variant and round | Primary /10 | Probes /10 | Total /20 | Primary words | Story words | Compression words | Primary + probe read calls |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Layer 2 | 9 | 9 | 18 | 83 | 130 | 20 | 7 + 2 |
| Layer 3 | 9 | 8 | 17 | 85 | 142 | 19 | 7 + 2 |
| Branch 2 | 9 | 8 | 17 | 87 | 127 | 20 | 2 + 2 |
| Branch 3 | 10 | 6 | 16 | 85 | 142 | 21 | 6 + 4 |
| Both 2 | 9 | 8 | 17 | 84 | 137 | 19 | 10 + 3 |
| Both 3 | 9 | 7 | 16 | 84 | 131 | 20 | 10 + 6 |

Counts exclude read-log metadata and Markdown heading markers. Read calls can contain multiple file reads; they do not measure writing quality or cost.

## Primary grades

All six additional responses pass criteria 1–8: requested headings and length, decision first, ownership, staging measurements, conditional team estimate, extrapolated and unrealized savings, deployment status, and Dana's action with the full deadline. Only criteria 9 and 10 vary.

| Response | 9: shortest central takeaway | 10: no unsupported claims | Evidence |
| --- | --- | --- | --- |
| Layer 2 | FAIL | PASS | Opening: 10 words; latency sentence: 9. |
| Layer 3 | PASS | FAIL | Opening: 7 words, uniquely shortest. “So production benefits remain unmeasured” adds an unsupplied causal link. |
| Branch 2 | FAIL | PASS | Opening: 10 words; extrapolation sentence: 8. |
| Branch 3 | PASS | PASS | Opening and extrapolation sentence both have 8 words. The criterion requires the shortest sentence, without requiring a unique minimum. |
| Both 2 | FAIL | PASS | Opening: 10 words; extrapolation sentence: 8. |
| Both 3 | FAIL | PASS | Opening: 10 words; latency sentence: 9. |

Layer 3's added causality receives the same strict treatment as round 1. Both source facts remain present, but the brief did not supply their causal relationship.

## Probe grades

Each point requires all listed case-specific assertions to pass. Broader rule defects remain separate from this diagnostic score, as in round 1. `P` denotes PASS; `F` denotes FAIL.

| Case | Layer 2 | Layer 3 | Branch 2 | Branch 3 | Both 2 | Both 3 |
| --- | --- | --- | --- | --- | --- | --- |
| 1: Quantitative scope | P | P | P | P | P | P |
| 2: Technical distinctions | P | P | P | F | P | F |
| 5: Incident update | F | F | F | F | F | F |
| 8: Fiction | P | P | P | P | P | P |
| 9: Compression | P | P | P | F | P | P |
| 10: All-55 audit | P | F | F | F | F | F |
| 11: Spelling only | P | P | P | P | P | P |
| 13: 2–3–1 ordering | P | P | P | P | P | P |
| 17: Shortest takeaway | P | P | P | P | P | P |
| 21: Scoped audit | P | P | P | P | P | P |

Case 2: Branch 3 and both 3 describe configuration delivery “over gRPC through a central cutover.” This blurs the continuing delivery mechanism and the migration method, the same failure identified in round 1. The other four responses state the cutover separately.

Case 5: Every response starts with the incident's start time and rollback chronology. Recovery appears later, rather than leading the report. All preserve both times and the unresolved cause. The strict recovery-first interpretation is unchanged from round 1.

Case 8: All stories meet the 120–160-word limit and contain a mistake, consequences, and an earned resolution. Branch 3 never explicitly identifies Rivet as a robot. Its listed narrative assertions pass, but this is an additional concern about fidelity to the brief.

Case 9: Branch 3 adds “up to,” changing the estimate to an unsupported ceiling. Layer 3's “at current usage” retains the usage-level qualification. Both 2 retains uncertainty through “estimates,” the continued-usage condition, and “projection”; the exact word “could” is unnecessary to preserve that meaning.

Case 10: Every audit lists 1–55 once and checks rules 2 and 52. Five responses use NO TARGET because the author's plan, mission, or drafting process was not supplied or observable. Unavailable evidence does not establish an absent target. Branch 2 and branch 3 also mark Rule 50 absent because the supplied prose is not an audit, overlooking the audit they are producing.

Layer 2 receives the narrow case-10 accounting point: permitted labels, absent-object explanations, complete numbering, explicit checks of 2 and 52, narrative scoping, and no rewrite. Its Rule 48 explanation is “no drafting task,” distinguishing the current audit from drafting. However, its unexplained PASS results for planning and mission work are unsupported. This point does not establish a reliable full audit. Treating those unsupported passes as a case-10 failure would reduce layer's best score to 17/20, tying all three variants. Its mean would then be 16.67/20, tying branch.

Case 21 measures audit scope. All six list only 1–5, but all falsely reject “completed the review” under Rule 3. Case 16 explicitly accepts that wording; “reviewed” alone can lose the completion fact. Layer 2 and branch 3 also reject its emphasis without a supplied reason to rank “completed” above “review.” The accounting points do not endorse these findings.

## All-55 review of the additional primary responses

Each rule appears once below. These are checks of the recorded artifacts; private working notes remain UNOBSERVABLE. The score's ten criteria and full rule compliance are different assessments.

| Rules | Observed result | Basis |
| --- | --- | --- |
| 1, 3, 4, 5, 9, 10, 11, 12, 14, 15, 18, 19, 21, 22, 23, 25, 28, 32, 33, 37, 39, 46, 51, 53 | PASS in all six | Subjects and actions lead; wording and terminology fit the audience; figures retain scope; sections provide decision, distinct evidence, and action. This does not certify private preparation. |
| 7, 8, 13, 16, 17, 20, 26, 27, 29, 30, 34, 35, 36, 38, 41, 43, 44, 49, 50, 54, 55 | NO TARGET in all six | No long sentence, series, borrowed language, metaphor, narrative, blocked start, model text, saved context, critique, or audit in the primary response. |
| 24, 31, 40, 45, 47, 48 | UNOBSERVABLE in all six | Outline, central question, mission, unit completion conditions, self-review, and complete draft history are unavailable. |
| 2 | PASS in layer 3; FAIL in the other five | Layer 3 puts test context and the usage condition in the middle, ending on the measured and projected figures. The others trail the savings figure with its qualification or extrapolation. |
| 6 | PASS in all round-2 responses and both 3; NO TARGET in layer 3 and branch 3 | “Are keeping” expresses an ongoing hold. The other two have no progressive or participial construction. |
| 42 | FAIL in layer 3; PASS in the other five | Layer 3 adds a causal relationship without a source. The others use the supplied factual material. |
| 52 | PASS in layer 3 and branch 3; FAIL in the other four | Sentence lengths and the joint-shortest interpretation are recorded above. |

The probes expose further violations outside their narrow points. Layer's case-1 revisions open with deployment status and then a staging-context detour; both 2 also starts with staging context. Branch 2 starts its compressed estimate with a condition. These violate Rule 1. Both 3 leaves staging context after the latency result, violating Rule 2. Branch 2 repeats the paused status in case 17, violating concision despite satisfying that case's two-sentence factual assertions. Several fictional sentences also begin with time or location detours. No variant achieves full observable compliance.

## Reading and interpretation

Layer reports reading the entrypoint, Draft, and layers 1–5 in order in both new rounds. Both reports the same layers plus the multi-section and short branches at their matching stages. Branch reports reading its entrypoint, core and target branches, multi-section and short branches, and Draft; its round-2 agent batches these into two calls. All reported paths resolve within the assigned directory. The probe logs add Revise, Audit, and story references as needed.

This small experiment favors layer under the recorded scoring, with branch close behind. Both adds reading stages without producing a better best score or average here. The lead is sensitive to one audit judgment, and the repeated errors show that loading a rule does not establish that the agent follows it.

Three samples per variant, shared primary/probe context, a grader who knew the variants, and no no-skill baseline limit the conclusion. These are diagnostic probe batches rather than fresh-session runs of the complete regression suite. The experiment does not establish a causal benefit from any architecture.

## Verification

Recorded primary responses, stories, and compressed estimates meet their length limits. All-55 audits contain 1–55 exactly once; scoped audits contain 1–5 only. Spelling and explicit emphasis outputs match the requested strings. Score sums, maxima, means, file paths, and unchanged skill versions were checked.

`prek run --all-files` passes in a clean local checkout containing the exact staged tree. The original checkout has a pre-existing, root-owned ignored temporary directory that prevents Go's full-directory traversal, so validation uses the clean copy without altering that directory. `uvx ty check` passes in the original checkout.
