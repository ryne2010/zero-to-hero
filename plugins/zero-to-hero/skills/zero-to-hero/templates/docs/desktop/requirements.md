# Desktop application requirements

## Platform contract

- Supported operating systems and versions: record the approved OS matrix and
  support window.
- Native or cross-platform framework: preserve the detected or explicitly
  approved application framework.
- Window, menu, tray, shortcut, and multi-display behavior: follow platform
  conventions and define restoration semantics.
- Accessibility, localization, and high-DPI behavior: validate semantic
  controls, keyboard access, scaling, contrast, and locale formatting.

## Launch and primary workflow

The local launch command is the exact target-specific command recorded in root
`AGENTS.md`; it must start from a clean checkout without release credentials or
system-wide installation. Define the primary workflow as a numbered sequence
from launch through user-visible completion, including input, window/state
transition, persistence boundary, success evidence, cancellation, and recovery.
The workflow is not accepted until it can be repeated in a disposable user-data
directory on every supported platform family.

## System integration

| Integration | Permission | Failure behavior | Test boundary |
| --- | --- | --- | --- |
| filesystem | least required | actionable, recoverable error | temporary sandbox |
| Each additional native integration | least required, requested just in time | safe degraded behavior | mocked contract plus authorized OS integration check |

Document protocols, file associations, clipboard, notifications, auto-start,
updates, native services, and sandbox/entitlement requirements where relevant.

## State and lifecycle

- Local data and migration: version schemas and prove upgrade plus rollback.
- Multi-window/process concurrency: define ownership, locking, and conflict
  behavior.
- Crash and interrupted-write recovery: use atomic writes and restore a
  consistent last-known state.
- Offline and update compatibility: preserve user work across unavailable
  services and supported version transitions.
- Import/export and backup: validate formats, paths, permissions, and partial
  failure recovery.

## Packaging and proof

- Packaging and update path: identify the exact build, installer, upgrade,
  rollback, and compatibility evidence for each supported platform.
- Unit, UI, integration, and accessibility checks: cover state, windows, native
  adapters, permissions, and keyboard flows.
- OS matrix and clean-install/upgrade tests: exercise each supported family in a
  disposable environment.
- Signing/notarization boundary: local proof does not require release identity.
- Installer/uninstaller data-retention behavior: make retained user data
  explicit and reversible.
- Performance and crash evidence: record startup, responsiveness, memory, and
  crash recovery.

### Signing, sandbox, and security policy

Unsigned local proof remains separate from release signing and notarization.
For each platform, record the package identity, sandbox or entitlement set,
trusted update origin, signature verification behavior, credential custodian,
and release approval owner. Default-deny filesystem, process, IPC, URL-handler,
and network access outside the documented integration boundary. Tampered,
expired, downgraded, or untrusted packages and updates must fail closed while
preserving recoverable user data.

Signing, notarization, publishing, or system-wide installation requires a
separate explicit downstream authorization.
