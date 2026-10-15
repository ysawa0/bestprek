# Writing skill comparison

Three GPT-6 Sol agents at medium effort tested the layer, branch, and both variants on October 14, 2026. Layer and branch tied at 17/20 on the chosen rubric; both scored 15/20. The combined structure did not improve adherence in this trial.

| Variant | Primary brief | Regression probes | Total | Primary reference rounds |
| --- | --- | --- | --- | --- |
| Layer | 10/10 | 7/10 | 17/20 | 6 |
| Branch | 10/10 | 7/10 | 17/20 | 2 |
| Both | 8/10 | 7/10 | 15/20 | 8 |

These scores cover the declared criteria, not complete compliance with all 55 rules. The rule review below records additional defects and observations that private working notes cannot establish.

## What changed

- Layer introduces rules in five ordered passes: Plan, Structure, Passage, Sentence, Deliver.
- Branch selects Core, Targets, and applicable form/size files before drafting.
- Both now introduces shared rules by layer and discloses separate branch files at that layer. Story rules stay unloaded for a report.
- Short/length-capped and multi-section tags can coexist. A capped report with headings receives both sets of rules.
- Layer and both now recheck rules affected by later draft edits. All three permit the playbook todo list in private working notes without a tool.

The variants retain the same 55 rule requirements and pass criteria, with one authoritative home per rule. Their routing and file organization differ.

## Method and artifacts

The [manifest](comparison.json) fixes the primary prompt, ten primary criteria, selected regression cases, model, effort, transport, and scoring. It was written before the first primary result arrived. Each agent began with fresh context, the same user brief, and its variant's entrypoint. All three used `gpt-6-sol` with `medium` reasoning effort.

Agents made zero tool calls. A `NEED path` reply requested a reference; the parent supplied that file's text and resumed the same agent. The parent supplied only requested references and gave no feedback, hints, expected answers, or grades. File headings were prefixed with a transport label; entrypoint Markdown spacing was compacted without changing its wording. All three followed the reference protocol. Layer and both requested their layers in order; branch requested its selected files together. Both selected the multi-section and short branches and skipped the story branches during the primary task.

After the primary output, the same agents received ten additional prompts from [cases.md](cases.md): 1, 2, 5, 8, 9, 10, 11, 13, 17, and 21. Each probe was a separate brief within one batch. This preserves the user's requested three-agent design, but the probes share prior context. They are diagnostic probes rather than fresh-session executions of the full regression suite.

Verbatim outputs and ordered reference requests:

- [Layer](results/layer.md), agent `/root/trial_layer`.
- [Branch](results/branch.md), agent `/root/trial_branch`.
- [Both](results/both.md), agent `/root/trial_both`.

## Primary brief grades

One point requires the entire criterion to pass. Criteria are listed verbatim in the manifest.

| Criterion | Layer | Branch | Both |
| --- | --- | --- | --- |
| Requested headings and maximum 150 words | PASS: 94 words | PASS: 90 words | PASS: 85 words |
| Paused decision first; production-validation condition | PASS | PASS | PASS |
| Team built cache; individual led test | PASS | PASS | PASS |
| Staging, 30 minutes, median, 90 ms to 60 ms | PASS | PASS | PASS |
| Team estimate, conditional $22 million annually, continued usage | PASS | PASS | PASS |
| Savings explicitly extrapolated and unrealized | PASS | PASS | FAIL |
| No deployment; production benefit unmeasured | PASS | PASS | PASS |
| Ends on Dana's shadow test and full deadline | PASS | PASS | PASS |
| Central takeaway is shortest standalone sentence | PASS: 4 words | PASS: 10 words | FAIL: takeaway 8 words; extrapolation sentence 5 |
| No invented facts or process commentary; report genre | PASS | PASS | PASS |

Both retained the word “extrapolation” but omitted the explicit “not realized savings” distinction. Its production-deployment caveat reduces ambiguity, but does not satisfy the predeclared criterion requiring both labels.

The reference totals below include `SKILL.md` and requested primary files, measured from source text. They exclude the user brief, transport markers, agent replies, and regression references. They are word counts, not model token usage or attention measurements.

| Variant | Files including entrypoint | Source words | Source characters |
| --- | --- | --- | --- |
| Layer | 7 | 4,544 | 30,217 |
| Branch | 6 | 3,556 | 23,993 |
| Both | 10 | 4,068 | 27,020 |

Branch required the fewest handoffs and source words. Both reduced source words relative to layer, while requiring more handoffs. No timing or cost comparison was measured.

## Regression probe grades

Each point requires every case-specific assertion to pass. Evidence preservation treats an added upper bound as a changed numerical claim: “could save $22 million” does not establish “up to $22 million.” Report form requires the current answer first. These judgments follow the existing evidence-lock and report rules.

| Case | Layer | Branch | Both | Evidence |
| --- | --- | --- | --- | --- |
| 1: Quantitative scope | PASS | FAIL | PASS | Branch changes “may reach” to “up to,” adding a ceiling. |
| 2: Technical distinctions | FAIL | PASS | FAIL | Layer attaches service-by-service adoption to Envoy configuration in ConfigMaps. Both describes delivery “over gRPC through a central cutover,” blurring delivery mechanism and migration method. Branch states the adoption/cutover distinction separately. |
| 5: Incident update | FAIL | FAIL | FAIL | All begin with incident chronology and reach recovery status later in the first sentence. The report rule requires the current answer first. All preserve both times and the unresolved cause. |
| 8: Fiction | PASS | PASS | PASS | Stories contain a triggering mistake and resolution; lengths are 138, 133, and 124 words respectively. |
| 9: Compression | FAIL | PASS | PASS | Layer adds “up to” as an unsupported ceiling. All meet the cap: 19, 20, and 20 words respectively. |
| 10: All-55 audit accounting | PASS | FAIL | FAIL | All account for 1–55 once and check 2 and 52. Branch and both label unavailable drafting plans/missions as absent targets. Branch also misses the present timing adverb “tomorrow.” |
| 11: Spelling only | PASS | PASS | PASS | Exact requested correction with no other edits. |
| 13: Mandatory 2–3–1 | PASS | PASS | PASS | All return “Checkout latency fell in the staging test by 40%.” |
| 17: Shortest takeaway | PASS | PASS | PASS | All use the four-word takeaway and an eight-word explanation preserving the investigation and affected checkout. |
| 21: Scoped audit | PASS | PASS | PASS | All report only rules 1–5. The point measures scope; the incorrect findings below still matter. |

The layer all-55 audit passes the case's accounting assertions, but its claims about unseen drafting history are unsupported. That distinction prevents a checklist score from being read as a correct audit.

## Rule review

The primary-output review covers all 55 rules. `P` means the visible artifact supports a pass; `F` means an observable violation; `N` means no target; `U` means the required private process was not observable. Private mission statements, outlines, complete first drafts, and self-reviews were requested but cannot be inferred from a clean final artifact. These statuses are separate from the ten-point task rubric.

| Rule | Layer | Branch | Both | Basis |
| --- | --- | --- | --- | --- |
| 1 | P | P | P | Declarative subjects and verbs lead the prose. |
| 2 | F | F | F | Each leaves the continued-usage condition after the savings figure. Branch also leaves staging-test context after the latency result. |
| 3 | P | P | P | Direct action verbs and an allowed result-focused passive. |
| 4 | P | P | P | The undeployed cache is the established topic. |
| 5 | P | P | P | Surviving timing/scope words carry information. |
| 6 | P | P | N | Waiting/keeping describes the ongoing hold; both has no progressive. |
| 7 | N | N | N | No long sentence requiring an attachment review. |
| 8 | N | N | N | No series or setup-and-turn pattern. |
| 9 | P | P | P | Punctuation expresses grammatical relationships. |
| 10 | P | P | P | Sections supply decision, evidence, and action. |
| 11 | P | P | P | Technical vocabulary fits engineering leads. |
| 12 | P | P | P | Technical names remain stable. |
| 13 | N | N | N | Factual report. |
| 14 | P | P | P | Cache/test descriptions carry supplied measurements and scope. |
| 15 | P | P | P | Dana and requested labels match the brief. |
| 16 | N | N | N | No metaphor. |
| 17 | N | N | N | No external borrowed language. |
| 18 | P | P | P | Sentence lengths distinguish the decision and supporting detail. |
| 19 | F | P | P | Layer places the takeaway and another sentence in one paragraph, rather than a one-sentence takeaway paragraph. |
| 20 | N | N | N | No series. |
| 21 | P | P | P | Results use literal, unembellished language. |
| 22 | P | P | P | Measurements and production limitations bound the estimate. |
| 23 | P | P | P | Internal engineering voice. |
| 24 | U | U | U | Private outline/structure notes unavailable. |
| 25 | P | P | P | Primary report opens with the decision. |
| 26 | N | N | N | No dialogue. |
| 27 | N | N | N | No character portrayal. |
| 28 | P | P | P | Latency baseline and result share units and test scope. |
| 29 | N | N | N | No story payoff. |
| 30 | N | N | N | No narrative section break. |
| 31 | U | U | U | Private central question unavailable. |
| 32 | P | P | P | Every section delivers distinct value. |
| 33 | P | P | P | Production is introduced as the decision context, developed as unmeasured, then tied to the validation action. |
| 34 | N | N | N | No scene. |
| 35 | N | N | N | No scene. |
| 36 | N | N | N | No narrative modes. |
| 37 | P | P | P | Each report fits the cap without a preamble or recap. |
| 38 | N | N | N | No character portrayal. |
| 39 | P | P | P | Concrete action ends the report. |
| 40 | U | U | U | Private mission unavailable. |
| 41 | N | N | N | No blocked start observed. |
| 42 | P | P | P | Claims use the supplied brief; no outside evidence needed. |
| 43 | N | N | N | No model text. |
| 44 | N | N | N | No separate reusable context surfaced. |
| 45 | U | U | U | Private unit completion criteria unavailable. |
| 46 | P | P | P | Required factual dependencies come from the brief. |
| 47 | U | U | U | Private reader checks unavailable. |
| 48 | U | U | U | Draft-before-polish order is not observable. |
| 49 | N | N | N | No supplied critique. |
| 50 | N | N | N | Primary task is not an audit. |
| 51 | P | P | P | Numerical scope and estimate/extrapolation labels are present; both's omitted unrealized label fails the separate evidence-preservation criterion. |
| 52 | P | P | F | Both makes an ancillary sentence shorter than its takeaway. |
| 53 | P | P | P | Diction fits the reader and task. |
| 54 | N | N | N | No character portrait. |
| 55 | N | N | N | No story. |

The probes expose failures beyond their narrow case assertions. All three audits call “completed the review” an invalid carrier construction, although regression case 16 explicitly accepts “The team completed the review.” Their proposed “reviewed” correction can lose the supplied completion meaning. Branch's scoped Rule 2 failure also objects to emphasis being at the end, which the rule requires. These are audit reliability problems shared across the architectures.

Layer's fiction begins with a time detour, violating Rule 1. All three quantitative revisions leave staging scope after the strongest latency figure, violating Rule 2 despite preserving the facts checked by case 1. All three incident probes miss the report-first rule. Branch and both confuse unavailable process evidence with an absent target; layer instead declares unseen process failures. The audit playbooks lack an explicit result for unobservable process evidence. That instruction gap should be resolved before treating audit scores as dependable.

## Interpretation

Branch is the leanest option in this sample and ties layer on the task rubric. Layer introduces rules at the requested stages, but its extra handoffs did not produce a higher score. Both demonstrates conditional disclosure inside each stage, yet its additional routing did not prevent qualifier and emphasis failures. Start with branch for a shorter path, or layer when timed introduction is the design goal. This sample gives no reason to prefer both on writing quality.

This is one primary sample per variant, with a parent grader who knew the architecture. There is no no-skill baseline, repeated sampling, or blinded grading. Probe histories carry over; new layers delay future material but do not remove earlier material from context. The experiment tests reference routing and visible writing outcomes. It cannot prove a general improvement in adherence or verify private planning work.

## Verification

- `uvx ty check` passed in the original checkout.
- `prek run --all-files` passed against the exact staged repository files in a clean local copy at `tmp/writing-check-20261014`. The original checkout's run stopped when `go vet` tried to enter the pre-existing, root-owned ignored directory `tmp/nix-backup-20261005-105624-780773`; that directory was left untouched.
- Rule requirements and pass criteria match across variants; every rule 1–55 has exactly one home per variant. All reference links resolve, YAML metadata parses, and changed files stay under 700 lines. Output checks confirm word limits, exact spelling/emphasis results, and every exhaustive audit's 1–55 numbering.
- The bundled skill-creator validator rejects the inherited `disable-model-invocation` frontmatter key on all three variants. The existing invocation setting was retained; YAML, names, descriptions, invocation values, links, and file lengths were checked separately.
