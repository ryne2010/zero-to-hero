# Robotics simulation, bring-up, telemetry, and failure-mode plan

Status: `draft-required-input`

This is a validation plan, not a deployment or actuation procedure. It may define deterministic simulation and evidence commands, but physical bring-up commands belong in a separately authorized downstream runbook after human engineering review.

## Simulation contract

| Field | Required value |
|---|---|
| Simulator and audited version | `REQUIRED` |
| Robot-description input/hash | `REQUIRED` |
| World/environment input/hash | `REQUIRED` |
| Fixed time step / real-time policy | `REQUIRED` |
| Random seed policy | `REQUIRED` |
| Physics/contact assumptions | `REQUIRED` |
| Sensor/actuator model assumptions | `REQUIRED` |
| External service fakes | `REQUIRED` |
| Exact inert validation command | `<SIMULATION_VALIDATION_COMMAND>` |
| Evidence output path | `REQUIRED` |

Simulation must run without physical devices, live credentials, production services, external side effects, or actuator-capable bridges.

## Deterministic scenario matrix

| Scenario ID | Initial state/seed | Inputs | Expected state and outputs | Safety invariant | Evidence | Status |
|---|---|---|---|---|---|---|
| `SIM-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `not-run` |

Include:

- nominal task completion;
- boundary workspace/joint-limit behavior;
- sensor dropout, noise, bias, stale data, and disagreement;
- communications loss, delay, reordering, duplication, and restart;
- actuator saturation, stuck/offline behavior, thermal/power derating assumptions;
- localization/planning/perception uncertainty;
- collision, near-collision, unreachable goal, and blocked-path behavior;
- emergency/stop request, safe-state transition, recovery refusal, and operator handoff.

## Telemetry and trace contract

| Signal/event | Producer | Units/frame | Rate/trigger | Timestamp/clock | Validity/stale rule | Privacy/sensitivity | Retention | Evidence consumer |
|---|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Required trace correlation:

- scenario ID, seed, source revision, artifact hashes, configuration, and simulator version;
- commanded versus observed state;
- mode transitions and decision reasons;
- limit, fault, warning, stop, and recovery events;
- frame/timestamp validity;
- dropped, delayed, stale, invalid, or suppressed data;
- exact validation command, exit status, and evidence paths.

## Failure-mode and recovery matrix

| Failure ID | Injection/detection method | Expected detection latency | Required safe response | Recovery prerequisites | Forbidden automatic recovery | Evidence |
|---|---|---:|---|---|---|---|
| `FAIL-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

A recovery path must not silently clear a safety-relevant fault, bypass an interlock, reset an emergency condition, or resume motion without the documented authority.

## Staged bring-up gates

| Gate | Scope | Preconditions | Evidence required | Human reviewer/authority | Physical effects allowed |
|---|---|---|---|---|---|
| `B0` | document/schema review | canonical docs complete | profile, geometry, interface, risk reviews | `REQUIRED` | none |
| `B1` | deterministic simulation | consumer checks pass | scenarios, traces, faults, recovery evidence | `REQUIRED` | none |
| `B2` | hardware-offline interface review | approved equipment and isolated plan | wiring/interface/limits checklist | `REQUIRED` | none |
| `B3+` | physical downstream activity | separate authorized runbook | qualified signoff and site-specific safety controls | `REQUIRED` | only as explicitly authorized |

This scaffold intentionally omits flash, deployment, energizing, homing, calibration-motion, motor, or actuation commands. Those commands must not be inferred from placeholders or simulation steps.

## Simulation-to-reality assumptions

| Assumption | Simulation representation | Physical uncertainty | Validation needed | Owner | Blocking |
|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `true` |

Address contact/friction, compliance/backlash, latency/jitter, sensor noise/bias, actuator limits, thermal/power behavior, cable forces, payload variation, environmental changes, and human interaction.

## Evidence and review

The final evidence report must state:

- scenarios and failure injections actually run;
- exact commands, versions, hashes, seeds, exit statuses, and evidence locations;
- applicable checks not run and why;
- observed versus expected behavior;
- assumptions and simulation limitations;
- unresolved risks and the owner of each;
- human review verdicts and conditions.

Skipped, unavailable, or failed checks are never reported as passed.

## Done when

- Simulation is deterministic, isolated from physical effects, and consumer-valid.
- Nominal, boundary, negative, fault, stop, and recovery cases have traceable evidence.
- Telemetry includes units, frames, time, validity, and correlation.
- Simulation-to-reality gaps and residual risks have owners.
- Staged gates clearly separate inert evidence from physical authorization.
- No physical bring-up command or implied authorization is present.
