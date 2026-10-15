---
name: raw-materials
description: Rewrite a prompt into the deeper version a top professional would run.
disable-model-invocation: true
---

# Raw Materials

Turn the user's prompt into a deeper version of the same task, not a bigger one. Depth means more rigor on the same question: rawer inputs, sharper methods, an outside check. Scope stays fixed. A deeper prompt answers the same question as the original, with the user's goal and constraints unchanged.

## Steps

1. Name the field. Pick the profession that owns this task, at its most exacting: "forensic accountant", not "finance person". Done when one specific role is named.
2. Answer the four questions about what that professional would do, each in a few concrete lines:
   1. Unasked work. What would they do here that the prompt leaves out? Name the actions, such as reproducing the failure first, checking base rates, or reading the contract's definitions section.
   2. Raw material. What primary source would they start from instead of the digested version the user has? Logs over dashboards, the dataset over the summary, the spec and source over the blog post, the filing over the press release. Name the artifact and where it lives.
   3. Methods and tools. Name the specific techniques and instruments, such as `git bisect`, a flame graph, a difference-in-differences design, a red-team checklist, or a style guide by title.
   4. Oracle. What outside both of you would show the result is right? A test that goes red then green, a measurement against a baseline, a primary record, a reproduction by a third party, a real-world outcome on a date. Name it, and state the observation that counts as passing.

   Done when each answer names things the user could look up or run. Replace any line that would fit any task ("be thorough", "use best practices") with a named action, artifact, tool, or oracle.
3. Rewrite the prompt. Write a new prompt that asks for exactly what the four answers named: start from the raw material, apply the named methods, do the unasked work, and finish by checking against the oracle. Keep the original goal, deliverable, and constraints. Done when every named item from step 2 appears in the rewrite and nothing in it widens the scope.

## Output

Give the field, the four answers under their headings, then the rewritten prompt in a fenced block the user can paste.
