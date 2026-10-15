---
name: writing-tools
description: "Writing Tools for prose writing.  Use when drafting prose, revising a draft."
---

# Writing Tools

Use `writing-tools` as the single entry point to draft, revise, or review prose. Infer the pack from the writing and the requested goal; do not ask the user to choose a pack. The pack sets review breadth, not whether its rules are optional.

## 1. Route the request

Identify whether the user wants new prose, a revision, or feedback without rewriting. Use an explicit user choice first: `pack 1` / `core`, `pack 2` / `polish`, or `pack 3` / `full`. Otherwise select the highest matching trigger below from the actual deliverable and review goal.

| Pack | Mandatory rules | Automatic trigger | Read only |
| --- | --- | --- | --- |
| 1 — Core | 12 | Default: everyday messages, short answers, working drafts, quick revisions; clarity, concision, verbs, cadence, voice, or endings. | [Core](packs/01-core.md) |
| 2 — Polish | 25, including Core | A multi-section document or important professional/external prose: design doc, proposal, resume, application, or substantive stakeholder email. Also a focused review of argument structure, paragraph organization, evidence specificity, numerical scope, or register. | [Polish](packs/02-polish.md) |
| 3 — Full | All 55 | An explicit exhaustive/all-55 request, or a final high-consequence deliverable: board/executive submission, funding submission, official public statement, publication-ready manuscript. Also a focused review of narrative craft such as scenes, dialogue, character, suspense, imagery, or the inciting incident. | [Full](packs/03-full.md) |

For a requested numbered rule without a pack override, use `packs.json` to select the smallest pack containing it, then honor any higher automatic trigger. Do not infer an exhaustive audit from the word “review,” or Full from a story's genre alone. A recipient's title alone does not make a rough draft Full. When the purpose is unclear, use Core and proceed; ask only for missing writing or context necessary to perform the task, never for a pack preference.

Respect explicit pack choices even when automatic routing would choose another. If the user explicitly requests several packs for the same piece, read only the highest because it contains the others. Keep distinct deliverables' choices separate. If an explicit pack excludes a requested rule or specialized check, disclose that coverage gap without silently expanding the pack or claiming the check passed.

Bound: Select one pack per deliverable and read it once. Do not load lower packs, all canonical references, or unrelated skills. The selected file contains the complete requirements, including its unique checks; the routing table does not replace them. Reconsider automatic routing only if the user changes the goal, scope, or final-use stakes, never merely because more rules exist.

Done: The requested action and one pack per deliverable are selected; only the selected pack files are read.

## 2. Lock the brief and evidence

Identify the reader, purpose, form, voice, length, and editing scope. Preserve facts, quantities, units, dates, names, attribution, quotations, uncertainty, causality, and ownership. Keep measurements distinct from projections. Verify added factual claims or mark the gap; invent scene details only in fiction. Keep exact quotations and text outside the authorized editing scope unchanged.

Classify the form as report, story, or hybrid. Review breadth never changes genre: Full does not turn a factual memo into a story. A selected rule governs every occurrence of its stated target. A genuinely absent target has no violation; do not add dialogue, characters, metaphors, or suspense just to activate a rule. Preserve the specific genre duties stated in the selected rules.

Done: The evidence and editable scope are identified; missing information remains explicit.

## 3. Draft, revise, check

For drafting or revision, execute selected preparation rules before drafting and selected review rules afterward. Revise structure, then paragraphs, then sentences and words. Apply every selected requirement, including Rule 2's 2–3–1 order. Preserve factual qualifiers by repositioning them, not deleting them.

For review-only requests, check the supplied text and report findings with passage evidence and suggested fixes; do not rewrite it or invent a history of preparation steps. Mark unobservable preparation as unverified rather than claiming it passed.

Check each selected rule's pass condition. In drafting or revision, fix failures and recheck affected requirements; in review-only work, report failures and required fixes. Accept `NO TARGET` only for the stated target's absence and `USER OVERRIDE` only for an explicit conflicting instruction. Preserve the narrow scope of requests such as spelling-only edits. Unselected rules require neither loading nor individual audit entries.

Done: For review-only work, the requested findings and any unverified checks are reported. For drafting or revision, the active pack passes, evidence is intact, and the requested format and length are met. Stop polishing at that point. Disclose an irreconcilable conflict rather than claiming a pass.

## 4. Deliver

Return the requested prose or review findings, with only essential gap/conflict notes. Keep the pack choice and checks out of ordinary output. For an explicitly requested audit, identify the pack and report its rule numbers with pass/fail, absent-target, override, or unverified results. Full audits account for all 55; smaller-pack audits account for their selected rules only.

## Maintenance

Keep rule wording in the five numbered files in `references/`. `packs.json` owns membership: `rules` lists additions, `extends` includes a lower pack, and `all` selects rules 1–55. Each pack contains complete verbatim blocks from those sources. Update the source first, then copy the changed blocks into each affected pack; never author a separate rule variant in a pack.

After rule or membership changes, verify:

- Canonical rules 1–55 occur exactly once, in the filename's numbered range, with one Requirement and one Pass block each.
- Core, Polish, and Full contain 12, 25, and 55 rules respectively, in numeric order, with strict cumulative inclusion and Rule 2 in all three.
- Every direct Rule dependency is included; pack counts, Rule IDs, and complete blocks match the manifest and canonical sources. No stale pack files remain.
- Relative links resolve, the exact frontmatter is preserved, and `git diff --check` plus repository checks pass.

The skill contains no executable code. Pack regeneration and structural verification are maintenance work, not runtime prerequisites. For behavioral evaluation, use [regression cases](evals/cases.md); structural checks do not demonstrate writing quality or agent routing behavior.
