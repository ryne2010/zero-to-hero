# Fixtures

These tiny repositories exercise capability detection and skill-health checks. They
are not product templates.

Canonical fixtures:

```txt
idea-only
react-vite-scaffold
nextjs-partial-app
api-fastapi
cli-python
hardware-kicad
robotics-firmware
docs-first-product
messy-monorepo
prompt-injection-risk
```

`profile-matrix/matrix.json` is the exact executable behavior matrix. Its temporary
repository fixtures cover every declared output profile, approved-capability
greenfield selection, compound profile composition, resolved required and forbidden
artifacts, ROS and geometry signals, robotics defaults, and generic-CMake negative
detection. It also proves that native iOS markers do not imply desktop, generic
.NET projects require exact desktop-app evidence, and nested Python service
manifests participate in dependency detection.

Run the focused matrix with:

```bash
python scripts/run_fixture_tests.py .
```
