# Coverage and Traceability Harness

Map every requirement to implementation and evidence.

```yaml
requirement_id: example_user_story
route: /example
components:
  - ExampleCard
actions:
  - example.primary_action
services:
  - exampleService.performAction
events:
  - example.action_completed
tests:
  - e2e.example_flow
evidence:
  - playwright_trace
  - screenshot
  - before_after_state_snapshot
```

This prevents broad claims of completion without route, action, data, and test coverage.
