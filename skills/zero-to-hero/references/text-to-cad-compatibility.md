# text-to-CAD compatibility contract

## Audited baseline

- source: [`earthtojake/text-to-cad`](https://github.com/earthtojake/text-to-cad);
- tested compatibility range: `==0.3.9`;
- tag: [`0.3.9`](https://github.com/earthtojake/text-to-cad/tree/0.3.9);
- tag commit: [`fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423`](https://github.com/earthtojake/text-to-cad/commit/fdbb4b4fb62d95ae298cfe9a46fdc7092bdaf423);
- release source commit: `ac2659a1e7256b030a87dd4d45a37dcdccce6b45`;
- published: `2026-07-10T19:58:16Z`;
- audited: `2026-07-23`;
- release evidence: [text-to-CAD 0.3.9](https://github.com/earthtojake/text-to-cad/releases/tag/0.3.9);
- runtime baseline: Python `>=3.12`.

Only the exact audited content is accepted automatically. Do not infer compatibility from a later tag, a catalog label, or the presence of a similarly named skill.

The audited skills CLI hashes are:

| Skill | `computedHash` |
| --- | --- |
| `cad` | `b610dd9fa7db52306080304f10f7a08c9625e42a189de9e34040f4a956951196` |
| `cad-viewer` | `a7e9c02d2bfa838c20f6926c8b6d3983163fae5d756c6a6b277139f638223283` |
| `step-parts` | `6e915d1d1e1b2da6d5fae2dd412371b6d500145816da2ae203eed1b5ad6eacfc` |
| `urdf` | `a48999f1d3868b03412d7ae6e0ba9fae44e8d293bb04a2d929959ed2f4fb5441` |
| `srdf` | `5597782c3ab7afc7f3e1fc8474d5853e64bf0abcef229b62db8b46417efa13d2` |
| `sdf` | `dd508dc1478fce583cd17eecca255532950ade368468aa36dee3fb5b8ffbfdef` |

`scripts/text_to_cad_probe.py` also records a locale-independent tree hash for each skill. That second digest verifies actual installed contents even when no lock entry is available.

## Discovery and provenance

The read-only probe considers, in order:

1. project skills under `.agents/skills/` and `.codex/skills/`;
2. local skills under `skills/`;
3. global skills under `~/.agents/skills/` and `~/.codex/skills/`;
4. an already-installed `skills` CLI, or `npx --no-install skills`, for project and global JSON inventories.

Project scope takes precedence over local and global scope. An incompatible project skill is reported rather than silently bypassed in favor of a global copy.

For each selected skill the probe verifies:

- the directory and `SKILL.md`;
- the audited content digest;
- `skills-lock.json` source, tag ref, upstream `skillPath`, and `computedHash` when recorded;
- the selected Python version;
- required imports through that selected interpreter;
- the audited launcher and its help tokens.

The probe never invokes `npx skills add`, package installation, network search, CAD generation, model download, viewer service startup, simulation, flashing, deployment, or physical actuation.

## Status contract

Every component reports exactly one status:

- `operational`: audited provenance, runtime, imports, and launcher interface passed;
- `unavailable`: the skill, interpreter, package executable, or dependency is absent;
- `incompatible`: installed content, ref, hash, runtime version, or launcher interface conflicts with the audited contract;
- `skipped`: a check could not run because its prerequisite was not operational or optional provenance metadata was absent.

The default command is an inventory probe, so an explicit `unavailable` or `incompatible` result exits zero and must be read from the report. Use `--require-feature` to create a gate. Any required feature that is not `operational` makes the gate `incompatible` and exits nonzero.

Examples:

```bash
python scripts/text_to_cad_probe.py /path/to/repo --json

python scripts/text_to_cad_probe.py /path/to/repo \
  --require-feature cad \
  --require-feature step-parts \
  --json

python scripts/text_to_cad_probe.py /path/to/repo \
  --skip-skills-cli \
  --skill-root project=/path/to/repo/.agents/skills \
  --json
```

Use `--python-command` when the target CAD environment has a dedicated Python 3.12+ interpreter. The probe itself remains compatible with the repository’s older maintenance Python because it checks the external interpreter in a child process.

## Canonical STEP-first interface

The adapter routes work to the installed upstream skills. It does not duplicate their implementation.

| Operation | Audited command shape |
| --- | --- |
| Generate STEP | `python <cad>/scripts/step SOURCE.py=OUTPUT.step` |
| Baseline inspection | `python <cad>/scripts/inspect refs OUTPUT.step --facts --planes --positioning` |
| Measure | `python <cad>/scripts/inspect measure OUTPUT.step --from REF --to REF [--axis x\|y\|z]` |
| Align | `python <cad>/scripts/inspect align OUTPUT.step --moving REF --target REF [--mode flush\|center] [--offset FLOAT]` |
| Frame | `python <cad>/scripts/inspect frame OUTPUT.step [SELECTOR]` |
| Diff | `python <cad>/scripts/inspect diff OLD.step NEW.step` |
| Snapshot | `python <cad>/scripts/snapshot --input OUTPUT.step --output SNAPSHOT.png --appearance workbench` |
| Part search/download | `python <step-parts>/scripts/download_step_part.py QUERY --download --out-dir DIR` |
| URDF | `python <urdf>/scripts/urdf SOURCE.py=OUTPUT.urdf` |
| SRDF | `python <srdf>/scripts/srdf SOURCE.py=OUTPUT.srdf` |
| SDF | `python <sdf>/scripts/sdf SOURCE.py=OUTPUT.sdf --gz-check auto` |

The editable CAD source defines `gen_step()`. URDF, SRDF, and SDF sources define `gen_urdf()`, `gen_srdf()`, and `gen_sdf()` respectively.

The required workflow is:

1. write the geometry brief with units, frames, datums, dimensions, fit, tolerance, interfaces, and verification criteria;
2. use `$step-parts` before modeling a named purchasable component;
3. edit build123d source and generate an explicit STEP target;
4. inspect facts, planes, and positioning;
5. run the required measure, align, frame, or diff checks;
6. create a snapshot for every new or visibly changed primary STEP;
7. make the smallest source correction and repeat the evidence loop;
8. hand off to `$cad-viewer` only when its launcher is operational;
9. report source, STEP, derived artifacts, inspection results, snapshot, provenance, license status, and every skipped check.

STEP is the primary interchange artifact. STL, 3MF, GLB, and similar meshes are derived outputs and do not replace the STEP evidence loop.

## Audited cad-viewer defect

The v0.3.9 `cad-viewer` skill documents:

```bash
npm --prefix <cad-viewer>/scripts/viewer run agent:start -- \
  --host 127.0.0.1 --dir ABSOLUTE_ROOT
```

The bundled v0.3.9 `package.json` does not define `agent:start`. Its available scripts include `serve`, `start`, `moveit2:setup`, `moveit2:check`, and `moveit2:serve`.

The probe therefore reports:

```text
status: incompatible
reason_code: audited_v0_3_9_agent_start_missing
```

Do not claim a viewer handoff for this audited tag. Use deterministic `inspect` results and the mandatory `snapshot` as the fallback. The lower-level `npm start` server is not equivalent to the skill’s documented agent lifecycle and is not treated as the canonical interface.

## Robotics routing

- `$urdf` owns physical robot structure, links, joints, inertial data, visual geometry, collision geometry, and limits.
- `$srdf` owns MoveIt semantics and requires a valid linked URDF.
- `$sdf` owns simulation and world semantics. `--gz-check auto|required|never` controls the optional Gazebo consumer check; `--strict` promotes bundled warnings.
- Consumer checks that cannot run are reported as skipped, never passed.

Generated descriptions do not authorize real hardware effects. Simulation and hardware-abstraction paths remain the default. Flashing, deployment, actuator commands, calibration motion, machine upload, printing, and fabrication require a separately reviewed human decision.

## Parts provenance and licensing

The text-to-CAD repository is MIT licensed. The [step.parts repository](https://github.com/earthtojake/step.parts) is MIT for its original project material, but third-party model files retain their source licenses. Consult its [LICENSE](https://github.com/earthtojake/step.parts/blob/main/LICENSE) and [THIRD_PARTY_NOTICES](https://github.com/earthtojake/step.parts/blob/main/THIRD_PARTY_NOTICES.md).

The step.parts API may provide source, product, page, asset URL, and SHA-256 data, but it does not provide a reliable per-part license field. Record the query or part ID, every source URL, expected and actual checksum, source notice, attribution, and an explicit SPDX identifier or `unknown/unverified`. Do not infer redistribution or fabrication permission from checksum success.

## Hermetic verification

Run:

```bash
python scripts/test_text_to_cad_probe.py
```

The temporary test environments cover:

- absent project/local/global skills;
- project and global discovery;
- exact source, ref, portable hash, and lock hash matches;
- incompatible ref and lock hash;
- Python 3.11 rejection;
- Python 3.12 import and launcher help probes;
- the v0.3.9 missing-`agent:start` defect;
- deterministic inspect-and-snapshot fallback;
- required-feature fail-closed behavior;
- a synthetic operational viewer launcher path.

The test performs no network requests, artifact generation, or physical actions and removes its temporary directories.
