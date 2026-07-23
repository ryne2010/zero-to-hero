# CLI requirements

## Command contract

Maintain a command, option, and exit code matrix as the canonical public
interface for both human callers and automation.

| Command | Purpose | Option or argument | Input/output streams | Exit code |
| --- | --- | --- | --- | --- |
| Each approved command | one bounded operation | type, default, precedence, required/optional status, and incompatible options | stdin contract; stable stdout; diagnostics on stderr | `0` for success and one documented nonzero class per failure category |

Specify flags, environment variables, configuration precedence, stdin/stdout/
stderr behavior, working-directory assumptions, and non-interactive behavior.
Machine-readable output must have an explicit schema and stable exit semantics.

## Safety and idempotency

- Dry-run behavior: display the resolved action without mutation.
- Confirmation and `--force` boundaries: replacement or destructive behavior
  requires an exact target and explicit flag.
- Interrupted-run recovery: leave recoverable state and explain the next safe
  command.
- Repeatability and partial-state handling: repeated safe invocations converge
  or fail with a precise conflict.
- Files, services, or external systems the command may affect: enumerate these
  per command before implementation.

Destructive or external-production actions require a separate explicit user
authorization. Never infer consent from a broad command.

## User experience

- Help and examples: every command and risky flag has a copyable inert example.
- Progress and quiet modes: progress uses stderr; quiet mode preserves errors
  and machine output.
- Color/TTY behavior: color is conditional and can be disabled.
- Actionable error messages: name the failed input, boundary, and safe recovery.
- Cross-platform path and shell expectations: avoid shell-only assumptions and
  test native path handling.

## Validation

- Parser/unit checks: cover valid, invalid, ambiguous, and repeated inputs.
- Golden output cases: version help text, one representative human-readable
  stdout result, machine-readable output, quiet behavior, and progress on
  stderr. Each case records its invocation, fixture, stdout, stderr, and exit
  code so intentional interface changes receive explicit review.
- Error path tests: cover malformed input, conflicting options, missing
  configuration, denied permission, unavailable dependency, interrupted
  execution, and partial state. Each test proves the documented nonzero exit
  code, actionable stderr, unchanged machine-output schema, and safe recovery.
- Temporary-directory integration checks: prove file behavior without user
  state.
- Windows, macOS, and Linux coverage: exercise quoting, paths, signals, and
  terminal differences.
- Packaging/install smoke check: install into a clean environment and invoke
  help plus one inert workflow.
