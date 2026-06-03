# Risk tiering

Use risk tiers to decide how much evidence and review a generated repo needs.

| Tier | Examples | Required posture |
|---|---|---|
| Low | brochure site, static docs, toy CLI | lightweight docs and basic checks |
| Medium | SaaS app, internal tool, data app | full source-of-truth docs, tests, local done gate |
| High | auth, payments, PII, AI agents, regulated domains | evidence harness, role walkthroughs, negative paths, final review |
| Critical | medical, legal, financial, safety, hardware, RF, batteries, robotics | human expert review, formal safety gates, manufacturing/deployment hold |

The skill may prepare specs and harnesses for high/critical systems, but it must not claim expert approval or production safety.
