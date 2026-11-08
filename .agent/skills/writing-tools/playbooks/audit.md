# Audit

Report rule results for supplied prose. Rewrite only on request.

1. Set the scope: the rules the user named; every rule for an all-55 request; otherwise every layer's applicable rules.
2. Read only the layer files holding rules in scope.
3. Give each rule in scope exactly one result:
   - `PASS`.
   - `FAIL`, with the passage and the required fix. A present target that misses its Pass line is a FAIL.
   - `NO TARGET`, naming the absent target, such as "no dialogue".
   - `USER OVERRIDE`, quoting the conflicting instruction.
4. Report results by rule number. Done when every rule in scope has one result and the report claims nothing beyond that scope.
