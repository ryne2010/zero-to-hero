# Target repo preflight

Before generating or applying artifacts, inspect the target repo for:

- existing source-of-truth docs;
- package/build/test commands;
- technology capabilities;
- neutral implementation/planning evidence and any optional CLI-owned adapter
  state;
- existing `.agents/skills`;
- generated or archived artifacts;
- scaffold residue;
- secrets or PII risk;
- conflicting instructions.

Use `target_repo_audit.py --preflight`. Writing reports is optional and must not
be mistaken for a passing post-generation readiness audit.
