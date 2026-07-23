# Firmware requirements

Status: `draft-required-input`

This document defines embedded/IoT implementation intent and inert validation. It does not contain firmware runtime code and does not authorize flashing, deployment, energizing, radio transmission, or physical actuation.

## Target and toolchain matrix

| Target ID | Board/MCU/SoC | Revision | Architecture | Memory/storage | Clock/power assumptions | Toolchain and audited version | Owner |
|---|---|---|---|---|---|---|---|
| `TARGET-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

| Inert command role | Exact resolved command | Expected evidence |
|---|---|---|
| Format check | `<FIRMWARE_FORMAT_CHECK_COMMAND>` | exit status and changed-file report |
| Lint/static analysis | `<FIRMWARE_STATIC_ANALYSIS_COMMAND>` | findings report |
| Type/compile check | `<FIRMWARE_COMPILE_CHECK_COMMAND>` | target/configuration and diagnostics |
| Unit tests | `<FIRMWARE_UNIT_TEST_COMMAND>` | deterministic test report |
| Simulator/HAL tests | `<FIRMWARE_SIMULATION_TEST_COMMAND>` | fixtures, seed, traces, and result |
| Authoritative local done gate | `<FIRMWARE_DONE_COMMAND>` | aggregated evidence |

Commands must be resolved from the actual repository and run without physical side effects. Flash, upload, deploy, radio-transmit, energize, or actuator commands are intentionally absent.

## Target, pin, and protocol map

| Interface ID | Target ID/revision | Pin/channel | Direction | Electrical level | Protocol/schema version | Peer/connector | Timing/rate | Units/encoding | Safe/default state | Validation source |
|---|---|---|---|---|---|---|---|---|---|---|
| `FW-IF-001` | `TARGET-001 / REQUIRED` | `REQUIRED` | `input/output/bidirectional` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `datasheet / schematic / test fixture` |

The map is complete only when every firmware-visible pin or channel is bound to
one approved target revision, protocol contract, peer connector or device,
electrical domain, timing rule, safe state, and validation source. Reused pins,
alternate functions, boot straps, and revision-dependent mappings require
separate rows or an explicit compatibility rule.

Document:

- pin multiplexing, pull-up/down, drive strength, polarity, boot-strapping, reset, interrupt, and debounce assumptions;
- buses, addresses, termination, voltage domains, isolation, grounding, shielding, and connector identity;
- sensors/actuators, calibration, range, resolution, update rate, saturation, and invalid-data behavior;
- clocks, synchronization, timestamp semantics, watchdogs, brownout, storage, and power state transitions;
- PCB revision compatibility and mechanical connector/interface traceability.

Conflicting datasheets, schematics, pin maps, or board revisions are blocking.

## State-machine and timing contracts

| State | Entry condition | Allowed outputs | Forbidden outputs | Timeout | Fault transition | Recovery authority |
|---|---|---|---|---|---|---|
| `SAFE_RESET` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Include boot, self-test, initialization, idle, active, degraded, update-pending, fault, safe shutdown, and recovery states when applicable. Define behavior for reset, brownout, watchdog, communication loss, stale command, invalid sensor, storage failure, over-temperature, over-current, and repeated restart.

| Timing ID | Event/source | Deadline/period | Jitter/latency | Priority | Measurement method | Failure response |
|---|---|---|---|---|---|---|
| `TIME-001` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

## Message and protocol contracts

| Message/command | Producer | Consumer | Transport | Schema/version | Units | Validity/timeout | Retry/idempotency | Error behavior |
|---|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Specify byte order, framing, checksums, sequence identifiers, compatibility, authentication when applicable, malformed input behavior, rate limits, and replay/stale-message policy.

## Configuration, secrets, and data lifecycle

| Item | Source/default | Allowed range | Persistence | Update authority | Secret/sensitive | Redaction/retention | Invalid-value behavior |
|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `yes/no` | `REQUIRED` | `REQUIRED` |

No production credential, device identity, private key, or real personal data belongs in generated docs, fixtures, logs, or source templates.

## Update, rollback, and recovery policy

Document without embedding physical execution commands:

- artifact identity, versioning, signing, compatibility, and integrity expectations;
- staged validation before a physical update;
- power-loss/interruption behavior;
- rollback trigger, retained known-good image/configuration, and recovery authority;
- downgrade, migration, bootloader, storage, and factory-reset assumptions;
- audit evidence and explicit human approval required for a physical target.

An update path without a tested rollback/recovery plan is blocking.

## Simulation or bench-test plan

| Fixture/scenario | Physical dependency replaced | Inputs/seed | Expected outputs/state | Fault injection | Evidence | Status |
|---|---|---|---|---|---|---|
| `FW-SIM-001` | `REQUIRED_FAKE_OR_HAL` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `not-run` |

Each scenario must declare whether it runs in a pure simulator, against a fake
HAL, or in an isolated bench-test harness. Record the exact inert command,
target configuration, fixture identity or hash, deterministic seed, expected
state transitions and timing, captured trace, and pass/fail oracle. A bench
plan that touches physical equipment is documentation only until a separate
authorization record approves the exact setup, energy sources, isolation,
limits, supervision, and stop authority.

Required simulation or bench-test cases include:

- nominal boot/state transitions;
- boundary and invalid sensor values;
- lost, delayed, duplicated, malformed, and stale communications;
- watchdog, reset, brownout, storage, and configuration failure;
- actuator-command saturation and safe-output enforcement using fakes only;
- update interruption and rollback logic in a simulator or isolated harness;
- deterministic log/trace replay.

## Telemetry and observability

| Signal/event | Units | Rate/trigger | Timestamp/clock | Validity/stale policy | Severity | Sensitive-data policy | Evidence consumer |
|---|---|---|---|---|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Logs and traces must identify target/configuration, source revision, test scenario, seed, toolchain version, and relevant artifact hashes without exposing secrets.

## Safety, failsafe, and failure modes

| Hazard/failure | Detection | Required safe state | Response deadline | Recovery prerequisites | Human escalation | Verification |
|---|---|---|---:|---|---|---|
| `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` | `REQUIRED` |

Software behavior is not automatically a certified safety function. Escalate mains, battery, RF, thermal, motor, pressure, medical, automotive, aerospace, industrial, human-support, or other safety-critical scope to qualified reviewers.

## Bring-up and physical authorization boundary

This scaffold stops at inert compile, static, unit, simulation, and fixture evidence. It intentionally omits commands for flashing, uploading, deploying, energizing, transmitting, homing, calibrating physical motion, or actuating hardware.

Any physical downstream runbook requires:

- approved target/revision and interface review;
- safe test environment, isolation, limits, supervision, and stop authority;
- rollback/recovery preparation;
- qualified human signoff for the exact activity;
- explicit commands reviewed in that separately authorized context.

## Done when

- Target/toolchain, board revisions, interfaces, states, timing, protocols, configuration, and observability are resolved.
- Exact inert build/check/test commands are recorded and pass.
- Simulation/HAL fixtures cover nominal, boundary, fault, stale-data, and recovery behavior.
- Update/rollback policy is reviewable without embedding physical commands.
- Safety states, failure modes, human review, and physical-authorization gates are explicit.
- No runtime product code or real-world action is generated by this scaffold.
