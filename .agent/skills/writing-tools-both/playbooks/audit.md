# Audit

Report rule results for supplied prose. Rewrite only on request.

1. Record the branch tags (Layer 1).
2. Set the scope: the rules the user named; every rule for an all-55 request; otherwise every layer's applicable rules.
3. Read only the layer files and linked branch files holding rules in scope. An all-55 audit reads every branch, including absent branches, so each rule receives a result.
4. Give each rule in scope exactly one result:
   - `PASS`.
   - `FAIL`, with the passage and the required fix. A present target that misses its Pass line is a FAIL.
   - `NO TARGET`, naming the absent target or branch, such as "no dialogue" or "report, not story".
   - `USER OVERRIDE`, quoting the conflicting instruction.
5. Report results by rule number. Done when every rule in scope has one result and the report claims nothing beyond that scope.
