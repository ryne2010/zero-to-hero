PYTHON ?= python3
UV ?= uv

.PHONY: help validate deep-validate py-compile clean-runtime-artifacts sync-mirror mirror-parity skill-health doctor deep-doctor smoke metadata plugin-metadata plugin-json archive archive-smoke release-check clean

help:
	@printf '%s\n' 'zero-to-hero maintainer commands'
	@printf '%s\n' ''
	@printf '%-24s %s\n' 'make validate' 'Run the complete authoritative release gate in the locked environment.'
	@printf '%-24s %s\n' 'make deep-validate' 'Compatibility alias for the complete authoritative release gate.'
	@printf '%-24s %s\n' 'make doctor' 'Run a fast operational doctor for the source skill.'
	@printf '%-24s %s\n' 'make deep-doctor' 'Run the deterministic deep doctor for the source skill.'
	@printf '%-24s %s\n' 'make sync-mirror' 'Copy skills/zero-to-hero into the plugin mirror.'
	@printf '%-24s %s\n' 'make mirror-parity' 'Verify source skill and plugin mirror match.'
	@printf '%-24s %s\n' 'make plugin-metadata' 'Validate plugin, marketplace, Codex metadata, icons, and version consistency.'
	@printf '%-24s %s\n' 'make archive' 'Build deterministic release archive and sidecars.'
	@printf '%-24s %s\n' 'make smoke' 'Run bounded runtime smoke checks.'
	@printf '%-24s %s\n' 'make archive-smoke' 'Verify deterministic archive, checksum, and manifest sidecars.'
	@printf '%-24s %s\n' 'make release-check' 'Run validate + smoke + archive-smoke before release.'
	@printf '%-24s %s\n' 'make clean' 'Remove Python runtime cache artifacts.'

validate:
	$(UV) run --frozen python scripts/validate_plugin_repo.py .

deep-validate:
	$(UV) run --frozen python scripts/validate_plugin_repo.py . --deep


py-compile:
	$(PYTHON) -m py_compile skills/zero-to-hero/scripts/*.py scripts/*.py tests/check_skill_mirror.py tests/smoke/*.py

clean-runtime-artifacts:
	find skills plugins scripts tests -type d -name __pycache__ -prune -exec rm -rf {} +
	find skills plugins scripts tests -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete

sync-mirror:
	$(PYTHON) scripts/release_skill_workflow.py mirror-skill

mirror-parity:
	$(PYTHON) tests/check_skill_mirror.py

skill-health:
	$(PYTHON) skills/zero-to-hero/scripts/zero_to_hero_check.py skills/zero-to-hero --deep --max-seconds 240 --summary

doctor:
	$(PYTHON) skills/zero-to-hero/scripts/zero_to_hero_doctor.py skills/zero-to-hero

deep-doctor:
	$(PYTHON) skills/zero-to-hero/scripts/zero_to_hero_doctor.py skills/zero-to-hero --deep --max-seconds 240 --timeout 20

metadata:
	$(PYTHON) scripts/release_skill_workflow.py validate-metadata

smoke:
	$(PYTHON) tests/smoke/run_all_smoke.py

plugin-metadata:
	$(PYTHON) scripts/plugin_metadata_check.py

plugin-json: plugin-metadata

archive:
	$(PYTHON) scripts/build_plugin_archive.py

archive-smoke:
	$(PYTHON) tests/smoke/run_plugin_archive_smoke.py --repeat 2

release-check: validate smoke archive-smoke

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
	find . -type f \( -name '*.pyc' -o -name '*.pyo' \) -delete
