# Hardware, mechanical, PCB, and robotics reality checks

Generated hardware docs are engineering intent, not fabrication approval.

Required warnings for applicable repos:

- Human engineering review is required before fabrication or deployment.
- Electrical, RF, battery, motor, medical, aerospace, automotive, industrial, or safety-critical designs require domain-specific review.
- Text-to-CAD prompts must be backed by dimensions, tolerances, materials, and assembly constraints.
- PCB workflows should include ERC/DRC, power tree review, connector review, BOM review, fabrication outputs, assembly notes, and bring-up tests.
- Firmware/robotics workflows should include safe-state behavior, simulation, telemetry, test jig/fixture strategy, and emergency stop assumptions where relevant.

## Review before fabrication or deployment

Mechanical, CAD, PCB, firmware, robotics, electrical, battery, RF, medical, automotive, aerospace, industrial, or safety-relevant outputs require human engineering review before fabrication, energizing hardware, field deployment, or safety-critical operation. Capture assumptions, tolerances, derating, thermal/power limits, test plans, and compliance questions explicitly.
