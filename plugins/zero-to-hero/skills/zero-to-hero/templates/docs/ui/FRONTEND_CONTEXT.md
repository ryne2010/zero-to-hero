# Frontend context router

Use for UI implementation planning.

Read first:

1. `docs/ui/DIRECTION.md`
2. `docs/ui/frontend-parity-system/README.md`
3. approved visual target index
4. relevant route capsule
5. relevant component recipe
6. relevant golden flow

Do not infer behavior from images without a contract or decision-ledger entry.

## Route, screen, state, and action contract

For every route, record its screens, user actions, data dependencies, and
loading, empty, error, offline, unauthorized, and permission-denied states.
Responsive breakpoints and negative states require explicit acceptance evidence;
screenshots alone are not a behavior contract.

| Route and screen | User action | Data dependency | Positive state | Negative states | Responsive evidence |
| --- | --- | --- | --- | --- | --- |
| Every canonical route and modal | trigger, precondition, focus result, and navigation outcome | request/cache contract and freshness rule | loading through successful completion | empty, validation error, dependency error, offline, unauthorized, and permission denied | named viewport, content stress case, and accepted behavior |

Route evidence must use deterministic fixtures and identify the requirement or
decision it proves. A screen is incomplete if any action lacks keyboard
behavior, pending/disabled behavior, failure recovery, or an observable success
condition.

## Accessibility and visual evidence

The accessibility contract records semantic structure, keyboard and
assistive-technology behavior, focus order and restoration, labels, contrast,
motion alternatives, zoom/reflow, and touch-target expectations. Automated
checks supplement but do not replace keyboard and representative
assistive-technology review.

Keep a reproducible visual evidence plan for canonical routes, responsive
widths, themes, content extremes, and negative states. Every capture records the
fixture, viewport, theme, locale, state trigger, expected invariant, capture
command, baseline owner, and diff tolerance. Review functional state assertions
separately from pixel comparison so an attractive screenshot cannot mask broken
behavior.
