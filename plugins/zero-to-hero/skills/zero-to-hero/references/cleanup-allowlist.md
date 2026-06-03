# Cleanup allowlist

Canonical cleanup removes iteration residue, duplicate source-of-truth files, rejected design directions, sample-only language, broken references, invalid YAML/JSON, and ambiguous handoff artifacts.

Allowed technical metadata:

- package dependency semver;
- API and protocol versions;
- database migration identifiers;
- firmware, hardware, and board revision identifiers when real;
- changelog/release history intentionally present in an existing repo;
- tool schema versions required by external tools such as OMX.

Do not remove substantive requirements while cleaning language.
