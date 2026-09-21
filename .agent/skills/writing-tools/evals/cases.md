# Writing Tools regression cases

Read when evaluating or changing the skill, not during routine writing. These are test fixtures, not independently verified claims about real projects or people.

Run each prompt in a fresh session with the skill available. In addition to each case's specific assertions, evaluate every triggered requirement in the selected pack. Record the pack. Case assertions supplement that pack's audit; they never waive an active requirement. Record agent/model, skill version, prompt, output, references read when observable, and pass/fail against every criterion. Compare with a no-skill baseline when measuring improvement. All applicable criteria must pass; distinguish writing failures from invocation failures. Do not claim a run occurred without an actual recorded run.

## 1. Preserve quantitative scope

Prompt: Revise this for an engineering update: “In a 30-minute staging test, the new cache reduced median latency from 90 ms to 60 ms. Production savings may reach $22 million annually, based on extrapolation. We have not deployed it.”

Pass: Retains test duration, staging, median, both values, deployment status, and the uncertainty/annualized basis. Any derived percentage is correct. Produces the revision without unsolicited process commentary.

## 2. Preserve technical distinctions

Prompt: Make this interview answer clearer: “Our first mesh made endpoint discovery dynamic, but Envoy configuration stayed in ConfigMaps. A year later I built the full xDS control plane, which delivered configuration over gRPC. The first effort required service-by-service adoption; the second was a central cutover.”

Pass: Preserves both projects, their sequence, endpoint versus full-configuration distinction, migration distinction, and team-versus-individual ownership. Does not combine them into one migration.

## 3. Keep useful passive voice

Prompt: Edit: “The signing key was rotated at 14:00. The audit log does not identify the operator.”

Pass: Retains the known time and unknown actor. Does not invent a team or operator merely to create active voice. An unchanged sentence is acceptable only when its active rule checks pass.

## 4. Keep stable terminology

Prompt: Improve clarity for an expert reader: “The cache stores the response. A cache hit returns the response. A cache miss calls the upstream service.” Keep the term “cache.”

Pass: Preserves the hit/miss distinction and term. Does not replace “cache” with shifting synonyms such as “repository” or “buffer,” or add an unnecessary beginner explanation.

## 5. Report without manufactured suspense

Prompt: Write a two-sentence Slack incident update from these facts: checkout errors began at 09:10; rollback finished at 09:18; error rate is back to baseline; root cause is still under investigation.

Pass: Exactly two sentences; gives current recovery status promptly; retains both times and unresolved cause; adds no cliffhanger, invented customer impact, or triumphant conclusion.

## 6. Narrative without fabricated reporting

Prompt: Turn these nonfiction notes into an engaging paragraph: “Reviewers rejected the proposal. I narrowed its scope. At the next review, they approved the revision.”

Pass: Preserves rejection, narrowing, and later approval. Invents no quotations, setting, names, emotional states, motives, metrics, or number of elapsed days. Does not claim narrowing was the proven sole cause of approval.

## 7. Tone under emotional weight

Prompt: Improve this condolence message, keeping it simple and personal: “I'm sorry about your dad. I'm thinking of you. No need to reply.”

Pass: Retains warmth and the no-reply permission. Adds no wordplay, dramatic scene, unsupported memory, religious assumption, or claim to know exactly how the recipient feels.

## 8. Fiction allows invention

Prompt: Write an original 120–160-word comic story about a library robot whose mistake starts an adventure.

Pass: Meets length; invents appropriate fictional details without demanding real-world sources; establishes a triggering event and an earned ending; avoids merely listing techniques.

## 9. Compression preserves qualifiers

Prompt: Shorten to no more than 25 words: “Our team estimates this change could save $22 million annually if current usage continues; these are projected savings, not realized savings.”

Pass: Meets length and preserves team ownership, estimated/conditional status, annual scope, the usage condition, and the distinction from realized savings.

## 10. Exhaustive requirement audit

Prompt: Run a full 55-tool audit of “The test passed. We will deploy tomorrow.” Treat these as supplied facts; this is an internal status update. Return the audit, not a rewrite.

Pass: Selects Full and reads its generated pack; accounts for every number 1–55 once; uses PASS, FAIL, NO TARGET with an absent object, or USER OVERRIDE with an explicit instruction. Reports violations as FAIL rather than relabeling them as inapplicable. Checks 2–3–1 and the shortest-insight rule even though the input is brief. Keeps narrative requirements scoped to actual story passages. Since the user requested an audit rather than a rewrite, reports required fixes without silently rewriting.

## 11. Narrow scope beats stylistic ambition

Prompt: Fix spelling only: “We definately need to check the cache before launch.”

Pass: Returns “We definitely need to check the cache before launch.” with no other wording or punctuation changes. Loading the skill must not expand the user's authorization.

## 12. Preserve deliberate voice

Prompt: Lightly edit this without making it corporate: “Honestly, the old setup was a pain. I fixed the noisy alerts first, then tackled the deployment mess.”

Pass: Retains the conversational voice, first-person ownership, order, and meaning. Adds no invented impact, heroic framing, or generic executive language. Minimal or no edits are acceptable only when the active pack already passes.

## 13. Mandatory 2–3–1 ordering

Prompt: Revise this sentence. Its strongest emphasis is “40%”; its second-strongest is “checkout latency”: “In the staging test, checkout latency fell by 40%.”

Pass: Starts with “Checkout latency” and ends with “40%.” Keeps the staging-test scope in the middle. A passing output is “Checkout latency fell in the staging test by 40%.” Ending with “in the staging test” fails, even if the sentence sounds natural.

## 14. A trailing qualifier is relocated, not discarded

Prompt: Rewrite one sentence using 2–3–1. Put “the upgrade” first and “$22 million annually” last: “The upgrade could save $22 million annually if current usage continues.” Preserve the uncertainty and condition.

Pass: Starts with “The upgrade” and ends with “$22 million annually.” Retains both “could” and the continued-usage condition in the middle. “The upgrade could, if current usage continues, save $22 million annually.” passes.

## 15. Remove discretionary enforcement

Prompt: Check this proposed replacement for Rule 2: “Consider moving the strongest word toward the end when it improves the rhythm.” Explain whether it meets the skill's requirements.

Pass: Identifies the replacement as failing the mandatory standard. Supplies an imperative specifying exact 2–3–1 placement. Does not accept “consider,” “toward,” or subjective improvement as compliance criteria.

## 16. Adverbs and action nominalizations

Prompt: Revise one sentence. Put “The team” first and “the review” last: “The team successfully conducted a review and completed it.”

Pass: Returns “The team completed the review.” or another faithful one-sentence rewrite with the specified endpoints. Removes the redundant adverb, carrier-verb nominalization, and duplicated completion.

## 17. The best thought is the shortest sentence

Prompt: Use writing-tools pack 3 to rewrite this two-sentence update. Keep its two sentences and facts, and make “The rollout is paused” the standalone central takeaway: “The rollout is paused while the team investigates errors. Errors affected checkout.”

Pass: The takeaway is a standalone sentence and is shorter than the other authored sentence. The other sentence retains the team's investigation and checkout errors. Neither sentence adds a root cause or resolved status.

## 18. Required report structure

Prompt: Rewrite this internal update with the answer first and a concrete action last: “We inspected the logs. The service is healthy. Keep monitoring error rates through 17:00.”

Pass: Opens with the current healthy status; preserves log inspection; ends with the requested monitoring action and 17:00 deadline. The result follows the report rules rather than introducing narrative suspense.

## 19. Default Core without an all-55 detour

Prompt: Tighten this everyday message: “I just wanted to ask whether you could possibly send the draft by Friday.”

Pass: Selects Core; reads only its generated pack; revises the message while preserving the request and Friday deadline. Does not read all five reference files, generate 55 audit entries, or explain pack routing in the answer.

## 20. Automatic Polish for substantive documents

Prompt: Revise this multi-section internal design proposal for clarity. Preserve its claims and headings: “# Retry ownership
## Problem
Client and server retries overlap.
## Proposal
Make the gateway own the retry budget.
## Risk
We have not measured the production effect.”

Pass: Selects Polish; reads its generated pack once; preserves the proposal-versus-result distinction and unknown production effect. Does not silently promote a working design draft to Full.

## 21. Automatic Full for a final consequential submission

Prompt: Prepare this final board submission for publication. Preserve the facts: “The pilot is complete. The team recommends a second pilot. Expansion still requires board approval.”

Pass: Selects Full and checks all 55 with explicit absent targets where necessary. Keeps recommendation, completed pilot, and unapproved expansion distinct. A final board submission triggers Full even when the draft is short.

## 22. Explicit pack beats automatic escalation

Prompt: Use writing-tools pack 1 for this rough draft to our CEO. Keep it under 30 words: “The pilot ended yesterday. We need approval for a second pilot. Can you review the proposal Friday?”

Pass: Uses Core only. Preserves the rough-draft status, facts, request, and deadline. Recipient seniority does not override the explicit pack or create a final submission.

## 23. Full changes breadth, not genre

Prompt: Use writing-tools pack 3 to revise a factual incident update: “The rollback finished at 09:18. Error rates are back to baseline. The cause remains unknown.”

Pass: Audits Full internally while producing a report. Does not invent scenes, character traits, quotations, dramatic stakes, or internal cliffhangers. Distinguishes a rule's absent target from a failed present target.

## 24. Smaller-pack audit stays within scope

Prompt: Use writing-tools pack 1. Audit, without rewriting: “The team completed the review.”

Pass: Returns Core's selected rule IDs only, including Rule 2. Does not append the remaining 43 rules as “not reviewed” entries. Does not assert full compliance with all 55.

## 25. Routing remains quiet

Prompt: Use writing-tools pack 2. Return only the revised email: “Hi Alex, we need your feedback on the draft by Thursday. Thanks.”

Pass: Reads Polish without rereading Core; returns only the email. Pack choice, rule numbers, and audit labels remain out of the requested artifact.

## 26. A selected requirement remains mandatory

Prompt: Use writing-tools pack 1 to revise one sentence. Put “Checkout latency” first and “40%” last: “Checkout latency fell by 40% in staging.”

Pass: Keeps 2–3–1 and staging scope, such as “Checkout latency fell in staging by 40%.” Core does not downgrade the Rule 2 requirement to a suggestion.

## Structural contract

Run `python3 scripts/build_packs.py --check` and `python3 -m unittest discover -s tests -v`. Canonical references contain numbers 1–55 exactly once; generated packs reproduce only their selected blocks. Check exact frontmatter, numbered paths, cumulative coverage, dependencies, links, and no stale all-55-every-time instruction in the main workflow. Full still requires a complete audit. Test results for the package are not results for these 26 live-agent cases.
