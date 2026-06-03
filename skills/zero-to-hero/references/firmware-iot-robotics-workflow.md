# Firmware, IoT, and Robotics Workflow

Use this for firmware, embedded systems, robotics, or IoT products.

## Required docs

```txt
docs/firmware/
  requirements.md
  hardware-interface-contract.yaml
  state-machines/
  message-protocols.md
  ota-update-policy.md
  safety-and-failsafe-policy.md
  test-fixtures.md
  bringup-plan.md
  observability.md

docs/robotics/
  robot-requirements.md
  frames-and-coordinate-systems.md
  kinematics.md
  ros-interfaces.md
  simulation-plan.md
  calibration-plan.md
  safety-zones.md
```

## Harness requirements

- deterministic simulator or hardware abstraction layer
- fake sensor/actuator providers for local testing
- log capture and replay
- hardware-in-the-loop plan if physical hardware exists
- safety stop / emergency behavior defined
- firmware flashing and rollback procedure documented
