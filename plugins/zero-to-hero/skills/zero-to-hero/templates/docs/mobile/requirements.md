# Mobile application requirements

## Platform contract

- Supported platforms and minimum OS versions: record only approved deployment
  targets and their support window.
- Native or cross-platform framework: preserve the framework detected from the
  repository or explicitly approved in discovery.
- Device classes, orientations, and form factors: cover every approved layout
  family and rotation policy.
- Accessibility and localization requirements: meet platform semantics, dynamic
  text, focus, contrast, reduced motion, and locale formatting.
- Deep links, notifications, background work, and widgets: specify lifecycle,
  privacy, and denied-permission behavior before implementation.

## Screen and state inventory

| Flow | Screens | Loading/empty/error/offline states | Data dependency |
| --- | --- | --- | --- |
| Every approved user journey | named screens and transitions | deterministic loading, empty, error, and offline states | explicit local cache or service contract |

### Primary mobile workflows

Define each primary mobile workflow from app entry or deep link through
user-visible completion. Record the navigation stack, gesture or control,
required device state, permission transition, local and remote data effects,
loading/empty/error/offline branches, cancellation, process-death recovery, and
deterministic success evidence. Background work and notification-driven flows
must name the lifecycle state in which each transition is legal.

## Device and permission boundaries

Document every camera, microphone, location, contacts, Bluetooth, health,
filesystem, biometrics, or notification permission. Define the user-facing
rationale, denied/revoked behavior, data lifetime, and platform review impact.

Every interactive control must meet the approved accessibility and touch target
requirements for its platform, including dynamic text, semantic labels, focus
order, keyboard or switch access, contrast, reduced motion, and the documented
minimum target size. Prove those requirements at the smallest and largest
supported text and display configurations.

## Offline and lifecycle behavior

- Cache and synchronization: version local state and bound freshness.
- Conflict resolution: define server/client authority and user-visible recovery.
- App background/foreground and process-death recovery: persist only safe,
  restartable state.
- Network loss and retry: use bounded idempotent retries with offline feedback.
- Account/session recovery: handle expiry, revocation, device change, and
  sign-out without data leakage.

## Delivery and proof

- Unit, UI, integration, and accessibility checks: cover state reducers,
  navigation, adapters, permissions, and primary flows.
- Simulator/emulator matrix: exercise minimum and current supported OS versions.
- Device evidence plan: for each supported platform family, record the OS
  version, device class, orientation, locale, text scale, network condition,
  permission state, fixture, workflow, expected result, and retained artifact.
  Simulator evidence covers deterministic states; sensor, radio, notification,
  thermal, and performance claims require separately authorized real-device
  evidence.
- Real-device checks requiring human authorization: enumerate sensors, radios,
  notifications, and performance cases separately.
- Signing and store credentials boundary: never require release credentials for
  local validation.
- Crash, performance, and privacy evidence: record startup, responsiveness,
  memory, network, data-access, and crash-free results.

Building, signing, uploading, or publishing is a separate downstream action and
is not authorized by this scaffold.
