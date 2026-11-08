# Branch trial

2026-10-14. Agent `/root/trial_branch`; model `gpt-6-sol`; reasoning effort `medium`. Fresh context at primary-task start. No agent tool calls. Parent delivered reference text on request.

## Primary reference requests

1. `playbooks/draft.md`
2. `branches/core.md`, `branches/targets.md`, `branches/multi-section.md`, `branches/short.md`

## Primary output (verbatim)

```markdown
## Status

We are keeping the production rollout paused pending production validation.

## Evidence

Our team built a new cache, and I led its 30-minute staging test. Median latency fell from 90 ms to 60 ms during that test. The team estimates the change could save $22 million annually if current usage continues; that figure is an extrapolation, not realized savings. The cache has not been deployed to production, and production benefits remain unmeasured.

## Next action

Dana must run a production shadow test by October 20, 2026 at 17:00.
```

## Additional reference requests for regression probes

One request containing `playbooks/revise.md`, `playbooks/audit.md`, and `branches/story.md`.

## Regression output (verbatim)

```markdown
Case 1

The new cache reduced median latency from 90 ms to 60 ms in a 30-minute staging test. An extrapolation puts potential production savings at up to $22 million annually. We have not deployed the cache.

Case 2

Our first mesh made endpoint discovery dynamic, but Envoy configuration remained in ConfigMaps. A year later, I built a full xDS control plane that delivered configuration over gRPC. Adopting the first mesh required changes service by service; the control plane launched through a central cutover.

Case 5

Checkout errors began at 09:10, and rollback finished at 09:18; the error rate is back to baseline. The root cause remains under investigation.

Case 8

The library robot stamped a treasure map DUE YESTERDAY and sent it down the return chute. A tiny pirate climbed out, demanding his ship back.

Dot checked the catalog. The “ship” was a pop-up book, last seen aboard the Saturday bookmobile. Dot rolled after it, carrying the pirate in a pencil cup.

At the dock, the bookmobile was leaving on a ferry. Dot shouted “OVERDUE!” and launched the cup like a cannonball. The pirate landed on the roof. Dot followed on a rope meant for bicycles.

Inside, they found the pop-up book. Its paper ship had sailed off the page and was circling the reading nook’s aquarium. Dot lowered a paperclip anchor into the tank and coaxed the ship home.

The pirate saluted. Dot amended the catalog: Adventure, one copy; pirate, fines waived.

Case 9

The team estimates potential annual savings of $22 million if current usage continues; this is a projection, not realized savings.

Case 10

1. PASS — Both sentences begin with their subjects and verbs.
2. PASS — “passed” and “tomorrow” carry the sentence endings.
3. PASS — “passed” and “deploy” state the actions directly.
4. NO TARGET — No passive construction.
5. NO TARGET — No adverb modifying an action.
6. NO TARGET — No progressive or participial construction.
7. NO TARGET — No long sentence.
8. NO TARGET — No series or setup-and-turn pattern.
9. PASS — Both periods close complete thoughts.
10. PASS — Each sentence contributes a distinct fact.
11. PASS — The wording is plain.
12. NO TARGET — No recurring key word.
13. NO TARGET — This is a report, not a story.
14. FAIL — “The test” is central but unidentified. The source supplies no identifying detail; record that gap.
15. NO TARGET — No name, title, or label.
16. NO TARGET — No metaphor or comparison.
17. NO TARGET — No quotation, paraphrase, or allusion.
18. FAIL — Both sentences have the same short cadence despite the turn from result to action. Vary the cadence if the format permits.
19. NO TARGET — No multi-section structure.
20. NO TARGET — No series or list.
21. PASS — The result uses direct, unevaluated language.
22. FAIL — “The test passed” gives no observation or criterion supporting the result. The source supplies none; record the evidence gap.
23. PASS — The voice suits an internal status update.
24. NO TARGET — The drafting plan is unavailable.
25. PASS — The report gives the result before the action.
26. NO TARGET — No dialogue.
27. NO TARGET — No character portrait.
28. NO TARGET — No contrast or comparison.
29. NO TARGET — No story payoff.
30. NO TARGET — No narrative section break.
31. NO TARGET — No multi-section structure.
32. NO TARGET — No substantive sections.
33. NO TARGET — No multi-section recurrence.
34. NO TARGET — No scene.
35. NO TARGET — No scene.
36. NO TARGET — No narrative modes.
37. PASS — Both sentences contribute necessary information.
38. NO TARGET — No character portrayal.
39. PASS — The update ends on the deployment action.
40. NO TARGET — The working mission is unavailable.
41. NO TARGET — No blocked opening is shown.
42. PASS — Both factual claims are supplied facts.
43. NO TARGET — No model text.
44. NO TARGET — No reusable context or authorized note destination.
45. NO TARGET — No multi-section project.
46. NO TARGET — Supporting work is unavailable for inspection.
47. NO TARGET — Reader-check provenance is unavailable.
48. NO TARGET — Draft history is unavailable.
49. NO TARGET — No critique was supplied.
50. PASS — This audit accounts for every rule.
51. NO TARGET — No quantity requiring calculation or comparison.
52. PASS — “The test passed” is the shortest complete sentence and states the result.
53. PASS — Diction fits an internal status update.
54. NO TARGET — No character portrait.
55. NO TARGET — This is a report, not a story.

Case 11

We definitely need to check the cache before launch.

Case 13

Checkout latency fell in the staging test by 40%.

Case 17

The rollout is paused. The team is investigating errors that affected checkout.

Case 21

1. PASS — “The team” precedes the main verb.
2. FAIL — “review” carries the action but sits at the end. Use a direct verb to give the action its proper emphasis.
3. FAIL — “Completed the review” uses a carrier verb and an action noun. Change it to “reviewed.”
4. NO TARGET — No passive construction.
5. NO TARGET — No adverb.
```
