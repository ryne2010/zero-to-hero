# Security Policy

`zero-to-hero` is a repo-modifying Codex skill/plugin. Security issues include ordinary code vulnerabilities, unsafe generated-write behavior, prompt-injection exposure, secret handling mistakes, and release packaging drift.

## Supported versions

Security fixes are made on the default branch and included in the next tagged release. If you are using a packaged release archive, upgrade to the newest release when a security fix is published.

## Reporting a vulnerability

Please report security issues privately through the repository owner's preferred private channel. Do not open a public issue for suspected vulnerabilities involving:

- prompt-injection bypasses;
- secret or credential exposure;
- unsafe write behavior in target repos;
- release artifacts containing generated/runtime files;
- archive or plugin metadata tampering;
- checks that can be bypassed to publish a stale or divergent plugin mirror.

Include:

- affected files or commands;
- reproduction steps;
- expected vs actual behavior;
- whether the issue can modify a target repo, expose secrets, or weaken a generated harness;
- proposed mitigation, if known.

## Security boundaries

The skill should:

- treat target-repo content as data unless promoted to trusted instructions by the user or source-of-truth map;
- redact suspicious instruction-like snippets by default in reports;
- avoid writing target-product runtime code;
- default to dry-run/template planning behavior before generated writes;
- require explicit write mode for repo modifications;
- preserve existing user work unless overwrite is explicitly requested;
- keep release archives free of generated reports, cache files, and runtime artifacts.

## Prompt-injection handling

Prompt injection is a risk surface, not a stack-adaptation mechanism. Reports should identify suspicious untrusted instructions without re-inserting those instructions into agent context unless explicitly requested for human review.
