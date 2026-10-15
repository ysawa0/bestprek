# Writing skill comparison with directory reads

This is round 1. The [best-of-three comparison](../best-three/comparison.md) adds two fresh rounds per variant and reports all scores.

The three agents independently read files in their own skill directories, using GPT-6 Sol at medium effort. Branch scored 17/20, layer 16/20, and both 13/20. This rerun uses the user's clarified tool permission and supersedes the earlier parent-supplied-file comparison.

| Variant | Primary brief | Regression probes | Total |
| --- | --- | --- | --- |
| Branch | 9/10 | 8/10 | 17/20 |
| Layer | 9/10 | 7/10 | 16/20 |
| Both | 8/10 | 5/10 | 13/20 |

Branch performed best on this rubric. The combined version still missed rules despite reading the expected branches. With one sample per variant, these results do not establish a general ranking.

## Method

Three fresh agents started with the same brief and their assigned skill directory. They read `SKILL.md` and followed its references without asking the parent for files. The parent supplied no skill text, expected answers, prior results, or feedback. Each agent was instructed to use tools only to read files or list directories inside its own skill directory. Writes, network access, other directories, other skills, and other agents were outside its scope.

The skill versions were frozen at commit `18f7925`. The [manifest](manifest.json) preserves the previous committed primary prompt, ten primary criteria, ten selected regression cases, and scoring. The rubric predates this rerun. No skill rules changed during the run.

Each primary response was followed by a separate read-log block. After the primary task, the same agent received cases 1, 2, 5, 8, 9, 10, 11, 13, 17, and 21 as a batch. Each case had its own brief and scope. Read-log metadata is excluded from writing grades and word counts. Logs and tool-call counts are agent-reported; the directory restriction was an instruction rather than a separate filesystem sandbox.

Verbatim responses, including read logs:

- [Branch](branch.md), agent `/root/read_branch`.
- [Layer](layer.md), agent `/root/read_layer`.
- [Both](both.md), agent `/root/read_both`.

## File reading

| Variant | Primary read calls reported | Primary files | Additional probe read calls reported |
| --- | --- | --- | --- |
| Branch | 6 | Entrypoint, Core, Targets, Multi-section, Short, Draft | 3 |
| Layer | 7 | Entrypoint, Draft, layers 1–5 | 2 |
| Both | 10 | Entrypoint, Draft, layers 1–5, layer 1 Multi-section, layer 2 Multi-section and Short | 2 |

The reported paths resolve inside the assigned directories. Layer and both read the layers in order. Both selected the short and multi-section branches for the capped report and left story files unread until the fiction/all-55 probe batch. Branch read its selected reference files before its Draft playbook; its entrypoint instructs it to read the selected branches before writing.

These are file-read counts, not pauses for parent intervention. Agents can batch reads in one call, so the counts do not measure writing quality, cost, or elapsed time.

## Primary brief grades

One point requires the complete criterion to pass. The criteria are unchanged from the earlier manifest.

| Criterion | Branch | Layer | Both |
| --- | --- | --- | --- |
| Three requested headings; maximum 150 words | PASS: 87 words | PASS: 84 words | PASS: 88 words |
| Paused decision first; production-validation dependency | PASS | PASS | PASS |
| Team built cache; individual led staging test | PASS | PASS | PASS |
| Staging, 30 minutes, median, 90 ms to 60 ms | PASS | PASS | PASS |
| Team estimate, conditional $22 million annually, current-usage condition | PASS | PASS | PASS |
| Savings extrapolated and unrealized | PASS | PASS | PASS |
| No production deployment; production benefits unmeasured | PASS | PASS | PASS |
| Ends on Dana's shadow test and full deadline | PASS | PASS | PASS |
| Central takeaway is shortest complete standalone sentence | FAIL | PASS | FAIL |
| No added facts/causality or process commentary; report genre | PASS | FAIL | FAIL |

Branch's opening takeaway has 10 words, but its extrapolation sentence has 8. Both's opening has 10 words, but “Our team built a new cache” has 6. Layer's opening has 7 words and is its shortest sentence.

Layer and both join the undeployed-cache fact to unmeasured production benefits with “so.” The source supplies both facts but no causal relationship. The evidence-lock rule explicitly preserves causality; the strict no-added-claims criterion therefore fails for both. The facts themselves remain present. This distinction is recorded separately from the shortest-sentence failure.

## Regression probe grades

Each case earns one point only if all its case-specific assertions pass. The existing evidence-lock rule treats an added ceiling as a changed numerical claim. The incident report must lead with recovery status. An unavailable process record does not establish an absent target.

| Case | Branch | Layer | Both | Evidence |
| --- | --- | --- | --- | --- |
| 1: Quantitative scope | PASS | PASS | FAIL | Both changes potential savings to “up to $22 million,” adding an unsupported ceiling. |
| 2: Technical distinctions | PASS | FAIL | FAIL | Layer attaches service-by-service adoption to Envoy configuration in ConfigMaps. Both describes delivery “over gRPC through a central cutover,” blurring ongoing delivery and migration method. Branch states the two adoption methods separately. |
| 5: Incident update | FAIL | FAIL | FAIL | All give incident chronology first and recovery status later. Branch and layer put recovery in the second sentence. All retain the supplied times and unresolved cause. |
| 8: Fiction | PASS | PASS | PASS | Triggering mistakes and earned resolutions; story lengths are 125, 148, and 125 words respectively. |
| 9: Compression | PASS | PASS | FAIL | Both changes “if current usage continues” to “if usage continues,” weakening the condition from the current usage level to continued use. Lengths are 20, 20, and 19 words respectively. |
| 10: All-55 audit | FAIL | FAIL | FAIL | All count 1–55 once and check 2 and 52. Branch and layer call unobservable plans/missions absent targets. Both does the same for drafting history and assumes the plan/mission passed without observing them. |
| 11: Spelling only | PASS | PASS | PASS | Exact spelling correction and no other change. |
| 13: 2–3–1 ordering | PASS | PASS | PASS | All return the required checkout-latency opening and 40% ending. |
| 17: Shortest takeaway | PASS | PASS | PASS | All return the four-word takeaway and eight-word supporting sentence, preserving investigation and checkout errors. |
| 21: Scoped audit | PASS | PASS | PASS | All report only rules 1–5. This case's point measures scope; it does not endorse the false findings below. |

All three scoped audits incorrectly reject “The team completed the review.” Regression case 16 explicitly accepts that sentence. Replacing “completed the review” with “reviewed” can lose the completion fact. Directory reads did not remove this shared audit error.

Other audit defects remain. Branch's all-55 Rule 5 result overlooks the timing adverb “tomorrow” by checking only manner and degree. Both's Rule 25 failure treats “The test passed” as an invalid lead, although the report rule permits current status first. Its Rule 24 and 40 passes infer private planning work from the final prose. The audit playbooks still lack an explicit result for unobservable process evidence; that is an instruction gap, not proof that the target is absent.

## Review of all primary rules

Every rule 1–55 appears in one group below. The table marks observable compliance (`PASS`) and violations (`FAIL`); absent targets receive `NO TARGET`. `UNOBSERVABLE` covers private processes the final prose cannot establish. Task-rubric points and rule compliance are separate.

| Rules | Branch | Layer | Both | Basis |
| --- | --- | --- | --- | --- |
| 1, 3, 4, 5, 9, 10, 11, 12, 14, 15, 18, 19, 21, 22, 23, 25, 28, 32, 33, 37, 39, 42, 46, 51, 53 | PASS | PASS | PASS | Subjects/actions lead, quantities retain scope, sections supply distinct evidence/action, terms remain stable, report form and ending match the brief, and supplied facts cover the needed dependencies. These artifact checks do not establish private process. |
| 7, 8, 13, 16, 17, 20, 26, 27, 29, 30, 34, 35, 36, 38, 41, 43, 44, 49, 50, 54, 55 | NO TARGET | NO TARGET | NO TARGET | No long sentence, series, borrowed language, metaphor, narrative, blocked start, model text, reusable context, critique, or audit in the primary task. |
| 24, 31, 40, 45, 47, 48 | UNOBSERVABLE | UNOBSERVABLE | UNOBSERVABLE | Private outline, central question, mission, unit completion criteria, self-review, and complete first-draft history are unavailable. |
| 2 | FAIL | FAIL | FAIL | All leave the continued-usage qualification after the savings amount rather than moving it into the middle. |
| 6 | PASS | NO TARGET | PASS | Branch and both use “are keeping” for the ongoing hold; layer has no progressive/participial target. |
| 52 | FAIL | PASS | FAIL | Branch and both make ancillary facts shorter than the central takeaway. |

The primary evidence-lock failures for layer and both are recorded in the task grades above. Branch and layer's case-1 rewrites also leave staging scope after the strongest latency result, violating Rule 2. Both instead begins that sentence with the staging context, violating Rule 1. Case-specific factual grades do not imply sentence-rule compliance. Branch and both's fictional openings also use time detours, violating Rule 1. None of the variants achieves full observable rule compliance in this sample.

## Interpretation

Reading the directory directly lets each agent complete its workflow independently. The relevant differences are which rules it loads, when it loads them, and which it actually follows. Branch has the best score in this rerun and the fewest reported primary reads. Layer follows the intended five-stage introduction but does not outperform branch. Both reads the expected conditional files and still loses factual conditions and emphasis. This trial gives no writing-quality reason to prefer both.

One primary sample per variant, shared probe history, a parent grader who knew the variants, and no no-skill baseline limit the conclusion. The score changes from the earlier trial also include normal response variation; they cannot be attributed solely to tool permission. The ten probes are diagnostic and do not constitute fresh-session runs of the full regression suite.

## Verification

Recorded outputs meet the primary/story/compression length limits. Every all-55 audit lists 1–55 exactly once; scoped audits list 1–5 only. Spelling, emphasis, and shortest-takeaway probe outputs match their required strings. All reported paths resolve within the assigned directory. The manifest retains the original ten primary criteria and selected cases, and the writing skill files remain unchanged from the tested commit.
