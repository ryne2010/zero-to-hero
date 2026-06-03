# Prompt sequence contract

The canonical prompt sequence is intentionally linear and phase-gated:

1. Deep interview.
2. Research and capability detection.
3. Canonical docs pack.
4. Design and visual pack.
5. Hardware/mechanical/PCB pack when applicable.
6. Frontend parity system.
7. Product usability contract.
8. Local product done harness.
9. OMX handoff.
10. Canonical cleanup.
11. Implementation-readiness review.

Planning and generation prompts must not implement product runtime code. They may create docs, specs, templates, harness scripts, repo-scoped skills, and OMX artifacts only when authorized.

`prompt_sequence_check.py` verifies that the prompt set is complete and non-overlapping.
