# Audit

Check prose against the rules. Report fixes. Rewrite only when asked.

1. Set the audit's scope. Use the rules the user named. An exhaustive or all-55 request covers every rule. Otherwise cover the always rules plus every triggered rule.
2. Read the reference block for every rule in scope.
3. Give each rule in scope exactly one result:
   - `PASS`.
   - `FAIL`, with the passage and the required fix. A violation is a FAIL, never relabeled as inapplicable.
   - `NO TARGET`, naming the absent object, such as "no dialogue".
   - `USER OVERRIDE`, quoting the conflicting instruction.
4. Report results by rule number. List only the rules in scope, and claim no compliance beyond them.
