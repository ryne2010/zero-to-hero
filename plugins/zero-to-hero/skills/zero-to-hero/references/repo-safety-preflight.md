# Repo safety preflight

`zero-to-hero` generates documentation, harnesses, plans, and neutral handoff
artifacts. Before writing, run the safety preflight so changes are reviewable
and recoverable. Optional OMX runtime artifacts remain CLI-owned.

## Required checks

The skill should inspect:

- whether the target is inside a git work tree;
- current branch name;
- current HEAD;
- tracked uncommitted changes;
- untracked files;
- whether the user is on `main`/`master`;
- whether a generated-file manifest will be written.

## Default behavior

Audits and dry-runs may inspect an unsafe worktree. Direct generation is
fail-closed when the target is not a Git worktree, is dirty, or is on a protected
main/master branch. The generator stages and validates the entire plan before
atomic replacement and rolls back a failed commit.

- the repo is not in git;
- the repo has uncommitted tracked changes;
- the repo has many untracked files;
- the repo is on `main` or `master`;
- the user has not reviewed the generated-file manifest.

## Recommended command

```bash
python scripts/repo_safety_check.py /path/to/repo --write
```

Use strict mode when you want writes to fail unless the target is clean enough for generated changes:

```bash
python scripts/repo_safety_check.py /path/to/repo --fail-on-unsafe
```

## Agent guidance

When the safety check reports `safe_to_write_templates: false`, remain in
report-only or dry-run mode. Do not bypass the gate or reinterpret the result as
success.

Do not delete or rewrite existing product implementation to create a clean state. This preflight protects user work; it is not a cleanup command.
