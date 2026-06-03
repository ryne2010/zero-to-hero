# Canonical cleanup policy

Cleanup must be lossless: preserve hard truths, final design decisions, user stories, constraints, and implementation requirements while removing iteration residue.

## Remove or normalize

```txt
sample-only language
approval-gated leftovers after approval
rejected design directions in canonical paths
placeholder/stub/TODO language
old design-lane naming
duplicate source-of-truth maps
duplicate ADR numbers
duplicate feature indexes
broken internal references
invalid YAML
ambiguous UI source-of-truth locations
```

## Allow

```txt
package dependency versions
API versions
migration IDs
hardware revision metadata when real
firmware semantic versions
protocol versions
changelog/release docs when intentionally present
OMX schema version fields required by tools
```

## Required cleanup report

```txt
.codex/reports/zero-to-hero/cleanup-report.md
```

The report must state what changed, what was preserved, and any user decisions still needed.
