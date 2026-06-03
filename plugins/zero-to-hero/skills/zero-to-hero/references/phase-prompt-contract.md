# Phase prompt contract

Every phase prompt should be safe to paste into Codex/OMX and should contain enough structure that the agent does not improvise product policy.

## Required elements

Each phase prompt should define:

- purpose;
- required reads;
- allowed writes;
- forbidden writes;
- expected outputs;
- stop conditions;
- required evidence or checks;
- confirmation that product runtime code must not be implemented unless the phase explicitly permits it.

## Prompt quality bar

A phase prompt is weak if it only says "generate docs" or "build the pack" without naming source files, output paths, stop conditions, and acceptance evidence.

A phase prompt is actionable when another agent can run it in a new repo and produce the same class of artifacts without relying on hidden conversation context.
