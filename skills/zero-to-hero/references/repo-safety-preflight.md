# Repo safety preflight

`zero-to-hero` can generate docs, harnesses, repo-scoped skills, and OMX artifacts. Before writing into an existing repository, run a safety preflight so generated files are reviewable and reversible.

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

The safety check is advisory by default. It should not block audits, interviews, dry-runs, or report generation.

Template writes should remain dry-run by default. For direct writes, agents should warn when:

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

When the safety check reports `safe_to_write_templates: false`, the agent should prefer:

1. report-only mode;
2. dry-run template manifests;
3. asking the user to create a branch, commit, stash, or back up current work;
4. only then writing generated artifacts.

Do not delete or rewrite existing product implementation to create a clean state. This preflight protects user work; it is not a cleanup command.
