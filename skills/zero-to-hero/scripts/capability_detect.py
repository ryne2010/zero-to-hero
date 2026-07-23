#!/usr/bin/env python3
"""Detect exact repository capabilities with positive and negative evidence."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Iterator

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.10
    tomllib = None  # type: ignore[assignment]

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))

from zero_to_hero_contract import ContractError, load_json_yaml  # noqa: E402

MAX_TEXT_BYTES = 1_000_000


def _safe_text(path: Path) -> str:
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _is_skipped(path: Path, root: Path, skip_dirs: set[str]) -> bool:
    try:
        rel = path.relative_to(root)
    except ValueError:
        return True
    return any(part in skip_dirs for part in rel.parts)


def _glob(root: Path, pattern: str, skip_dirs: set[str]) -> list[Path]:
    return sorted(
        {
            path
            for path in root.glob(pattern)
            if path.exists() and not _is_skipped(path, root, skip_dirs)
        }
    )


def _package_dependencies(path: Path) -> set[str]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return set()
    names: set[str] = set()
    for field in (
        "dependencies",
        "devDependencies",
        "peerDependencies",
        "optionalDependencies",
    ):
        value = data.get(field, {})
        if isinstance(value, dict):
            names.update(str(name).lower() for name in value)
    return names


def _normalize_distribution(name: str) -> str:
    """Return the normalized distribution name used by Python package indexes."""
    return re.sub(r"[-_.]+", "-", name.strip().lower())


def _requirement_name(record: str) -> str | None:
    """Extract one distribution name from a PEP 508/requirements-style record."""
    value = record.strip()
    if not value or value.startswith("#"):
        return None

    editable_match = re.match(r"^(?:-e|--editable)\s+(.+)$", value)
    if editable_match:
        egg_match = re.search(r"(?:[#&]egg=)([A-Za-z0-9][A-Za-z0-9._-]*)", value)
        return _normalize_distribution(egg_match.group(1)) if egg_match else None
    if value.startswith("-"):
        return None

    match = re.match(
        r"^([A-Za-z0-9][A-Za-z0-9._-]*)"
        r"(?:\s*\[[A-Za-z0-9_., -]+\])?"
        r"\s*(?=@|[<>=!~;]|$)",
        value,
    )
    return _normalize_distribution(match.group(1)) if match else None


def _requirements_records(text: str) -> Iterator[str]:
    """Yield logical, non-comment requirement records."""
    logical = ""
    for raw_line in text.splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        logical = f"{logical}{stripped}"
        if logical.endswith("\\"):
            logical = logical[:-1].rstrip() + " "
            continue
        yield logical
        logical = ""
    if logical:
        yield logical


def _requirements_dependencies(path: Path) -> set[str]:
    names: set[str] = set()
    for record in _requirements_records(_safe_text(path)):
        name = _requirement_name(record)
        if name:
            names.add(name)
    return names


def _string_requirements(value: Any) -> Iterator[str]:
    if isinstance(value, list):
        for item in value:
            if isinstance(item, str):
                yield item


def _dependency_table_names(value: Any) -> Iterator[str]:
    if isinstance(value, dict):
        for name in value:
            if isinstance(name, str) and name.lower() != "python":
                yield name


def _dependencies_from_pyproject(data: dict[str, Any]) -> set[str]:
    records: list[str] = []
    names: set[str] = set()

    project = data.get("project")
    if isinstance(project, dict):
        records.extend(_string_requirements(project.get("dependencies")))
        optional = project.get("optional-dependencies")
        if isinstance(optional, dict):
            for group in optional.values():
                records.extend(_string_requirements(group))

    dependency_groups = data.get("dependency-groups")
    if isinstance(dependency_groups, dict):
        for group in dependency_groups.values():
            records.extend(_string_requirements(group))

    tool = data.get("tool")
    if isinstance(tool, dict):
        poetry = tool.get("poetry")
        if isinstance(poetry, dict):
            names.update(
                _normalize_distribution(name)
                for name in _dependency_table_names(poetry.get("dependencies"))
            )
            names.update(
                _normalize_distribution(name)
                for name in _dependency_table_names(poetry.get("dev-dependencies"))
            )
            groups = poetry.get("group")
            if isinstance(groups, dict):
                for group in groups.values():
                    if isinstance(group, dict):
                        names.update(
                            _normalize_distribution(name)
                            for name in _dependency_table_names(group.get("dependencies"))
                        )

        pdm = tool.get("pdm")
        if isinstance(pdm, dict):
            dev_dependencies = pdm.get("dev-dependencies")
            if isinstance(dev_dependencies, dict):
                for group in dev_dependencies.values():
                    records.extend(_string_requirements(group))

        hatch = tool.get("hatch")
        if isinstance(hatch, dict):
            envs = hatch.get("envs")
            if isinstance(envs, dict):
                for environment in envs.values():
                    if isinstance(environment, dict):
                        records.extend(_string_requirements(environment.get("dependencies")))

    for record in records:
        name = _requirement_name(record)
        if name:
            names.add(name)
    return names


def _strip_toml_comment(line: str) -> str:
    quote: str | None = None
    escaped = False
    for index, char in enumerate(line):
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if char == "#" and quote is None:
            return line[:index]
    return line


def _toml_value_complete(value: str) -> bool:
    square = 0
    curly = 0
    quote: str | None = None
    escaped = False
    for char in value:
        if escaped:
            escaped = False
            continue
        if quote == '"' and char == "\\":
            escaped = True
            continue
        if char in {'"', "'"}:
            if quote == char:
                quote = None
            elif quote is None:
                quote = char
            continue
        if quote is None:
            square += (char == "[") - (char == "]")
            curly += (char == "{") - (char == "}")
    return quote is None and square <= 0 and curly <= 0


def _fallback_toml_assignments(
    text: str,
) -> Iterator[tuple[tuple[str, ...], str, str]]:
    """Read dependency assignments on Python 3.10 when tomllib is unavailable."""
    section: tuple[str, ...] = ()
    pending_key: str | None = None
    pending_value = ""
    for raw_line in text.splitlines():
        line = _strip_toml_comment(raw_line).strip()
        if not line:
            continue
        if pending_key is not None:
            pending_value = f"{pending_value}\n{line}"
            if _toml_value_complete(pending_value):
                yield section, pending_key, pending_value
                pending_key = None
                pending_value = ""
            continue
        table_match = re.fullmatch(r"\[([^\[\]]+)\]", line)
        if table_match:
            section = tuple(part.strip().strip("\"'") for part in table_match.group(1).split("."))
            continue
        assignment = re.match(r"^([^=]+?)\s*=\s*(.*)$", line)
        if not assignment:
            continue
        key = assignment.group(1).strip().strip("\"'")
        value = assignment.group(2).strip()
        if _toml_value_complete(value):
            yield section, key, value
        else:
            pending_key = key
            pending_value = value


def _fallback_toml_strings(value: str) -> Iterator[str]:
    for match in re.finditer(r'"(?:\\.|[^"\\])*"|\'[^\']*\'', value):
        token = match.group(0)
        if token.startswith('"'):
            try:
                parsed = json.loads(token)
            except json.JSONDecodeError:
                continue
            if isinstance(parsed, str):
                yield parsed
        else:
            yield token[1:-1]


def _fallback_pyproject_dependencies(text: str) -> set[str]:
    """Extract only dependency fields; never inspect descriptions or tool prose."""
    records: list[str] = []
    names: set[str] = set()
    for section, key, value in _fallback_toml_assignments(text):
        is_requirement_list = (
            (section == ("project",) and key == "dependencies")
            or section == ("project", "optional-dependencies")
            or section == ("dependency-groups",)
            or section == ("tool", "pdm", "dev-dependencies")
            or (
                len(section) >= 4
                and section[:3] == ("tool", "hatch", "envs")
                and key == "dependencies"
            )
        )
        if is_requirement_list:
            records.extend(_fallback_toml_strings(value))
            continue
        is_poetry_dependency = section in {
            ("tool", "poetry", "dependencies"),
            ("tool", "poetry", "dev-dependencies"),
        } or (
            len(section) == 5
            and section[:3] == ("tool", "poetry", "group")
            and section[-1] == "dependencies"
        )
        if is_poetry_dependency and key.lower() != "python":
            names.add(_normalize_distribution(key))
    for record in records:
        name = _requirement_name(record)
        if name:
            names.add(name)
    return names


def _pyproject_dependencies(path: Path) -> set[str]:
    try:
        content = path.read_bytes()
    except OSError:
        return set()
    if len(content) > MAX_TEXT_BYTES:
        return set()
    if tomllib is None:
        return _fallback_pyproject_dependencies(content.decode("utf-8", errors="ignore"))
    try:
        data = tomllib.loads(content.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError):
        return set()
    return _dependencies_from_pyproject(data)


def _pipfile_dependencies(path: Path) -> set[str]:
    try:
        content = path.read_bytes()
    except OSError:
        return set()
    if len(content) > MAX_TEXT_BYTES:
        return set()
    if tomllib is not None:
        try:
            data = tomllib.loads(content.decode("utf-8"))
        except (UnicodeDecodeError, tomllib.TOMLDecodeError):
            return set()
        names: set[str] = set()
        for field in ("packages", "dev-packages"):
            names.update(
                _normalize_distribution(name) for name in _dependency_table_names(data.get(field))
            )
        return names
    names = set()
    for section, key, _value in _fallback_toml_assignments(
        content.decode("utf-8", errors="ignore")
    ):
        if section in {("packages",), ("dev-packages",)}:
            names.add(_normalize_distribution(key))
    return names


def _environment_dependencies(path: Path) -> set[str]:
    try:
        data = load_json_yaml(path)
    except ContractError:
        return set()
    dependencies = data.get("dependencies") if isinstance(data, dict) else None
    if not isinstance(dependencies, list):
        return set()
    records: list[str] = []
    for item in dependencies:
        if isinstance(item, str):
            records.append(item)
        elif isinstance(item, dict):
            records.extend(_string_requirements(item.get("pip")))
    names: set[str] = set()
    for record in records:
        name = _requirement_name(record)
        if name:
            names.add(name)
    return names


def _python_dependency_records(root: Path, skip_dirs: set[str]) -> list[tuple[str, set[str]]]:
    candidates: set[Path] = set()
    for name in ("pyproject.toml", "Pipfile", "environment.yml", "environment.yaml"):
        candidates.update(_glob(root, name, skip_dirs))
        candidates.update(_glob(root, f"**/{name}", skip_dirs))
    for pattern in (
        "requirements*.txt",
        "**/requirements*.txt",
        "requirements/**/*.txt",
    ):
        candidates.update(_glob(root, pattern, skip_dirs))

    records: list[tuple[str, set[str]]] = []
    for path in sorted(candidate for candidate in candidates if candidate.is_file()):
        if path.name == "pyproject.toml":
            dependencies = _pyproject_dependencies(path)
        elif path.name == "Pipfile":
            dependencies = _pipfile_dependencies(path)
        elif path.suffix in {".yml", ".yaml"}:
            dependencies = _environment_dependencies(path)
        else:
            dependencies = _requirements_dependencies(path)
        records.append((_relative(path, root), dependencies))
    return records


def detect(repo: str | Path, rules_path: str | Path | None = None) -> dict[str, Any]:
    root = Path(repo).resolve()
    skill = Path(__file__).resolve().parents[1]
    rules_file = (
        Path(rules_path).resolve() if rules_path else skill / "references/capability-rules.yaml"
    )
    rules = load_json_yaml(rules_file)
    skip_dirs = set(rules.get("skip_directories", []))
    capabilities: set[str] = set()
    evidence: dict[str, list[str]] = {}
    negative_evidence: dict[str, list[str]] = {}

    def add(capability: str, item: str) -> None:
        capabilities.add(capability)
        bucket = evidence.setdefault(capability, [])
        if item not in bucket:
            bucket.append(item)

    def add_negative(capability: str, item: str) -> None:
        bucket = negative_evidence.setdefault(capability, [])
        if item not in bucket:
            bucket.append(item)

    package_files = _glob(root, "package.json", skip_dirs) + _glob(
        root, "**/package.json", skip_dirs
    )
    seen_packages: set[Path] = set()
    package_rules = rules.get("package_dependencies", {})
    for path in package_files:
        if path in seen_packages or not path.is_file():
            continue
        seen_packages.add(path)
        dependencies = _package_dependencies(path)
        for capability, markers in package_rules.items():
            matches = sorted(dependencies & {str(marker).lower() for marker in markers})
            if matches:
                add(
                    capability,
                    f"{_relative(path, root)} exact dependencies: {', '.join(matches)}",
                )
        text = _safe_text(path)
        if '"workspaces"' in text or (root / "pnpm-workspace.yaml").is_file():
            add("monorepo", f"{_relative(path, root)} workspace configuration")

    python_files = _python_dependency_records(root, skip_dirs)
    for capability, markers in rules.get("python_dependencies", {}).items():
        normalized_markers = {_normalize_distribution(str(marker)) for marker in markers}
        for rel, dependencies in python_files:
            matches = sorted(dependencies & normalized_markers)
            if matches:
                add(capability, f"{rel} exact dependencies: {', '.join(matches)}")

    for capability, patterns in rules.get("file_globs", {}).items():
        matches: list[str] = []
        for pattern in patterns:
            matches.extend(
                _relative(path, root) for path in _glob(root, pattern, skip_dirs) if path.is_file()
            )
        if matches:
            preview = sorted(set(matches))[:8]
            add(capability, "file markers: " + ", ".join(preview))

    for capability, rule in rules.get("content_rules", {}).items():
        tokens = [str(token).lower() for token in rule.get("tokens_any", [])]
        negative_reason = rule.get("negative_reason")
        seen_paths: set[Path] = set()
        for pattern in rule.get("globs", []):
            for path in _glob(root, pattern, skip_dirs):
                if not path.is_file() or path in seen_paths:
                    continue
                seen_paths.add(path)
                text = _safe_text(path).lower()
                matched = [token for token in tokens if token in text]
                if matched:
                    add(
                        capability,
                        f"{_relative(path, root)} content markers: {', '.join(matched[:6])}",
                    )
                elif isinstance(negative_reason, str) and negative_reason:
                    add_negative(
                        capability,
                        f"{_relative(path, root)} {negative_reason}",
                    )

    cmake_files = _glob(root, "**/CMakeLists.txt", skip_dirs)
    firmware_tokens = [
        token.lower()
        for token in rules.get("content_rules", {}).get("firmware", {}).get("tokens_any", [])
    ]
    for path in cmake_files:
        text = _safe_text(path).lower()
        if not any(token in text for token in firmware_tokens):
            add_negative(
                "firmware",
                f"{_relative(path, root)} is generic CMake without firmware markers",
            )

    if (root / "Dockerfile").is_file() or any(
        (root / name).is_file() for name in ("compose.yml", "compose.yaml", "docker-compose.yml")
    ):
        add("containerized", "Docker or Compose configuration")
    if (root / "migrations").is_dir() or _glob(root, "**/migrations/**", skip_dirs):
        add("database", "migration directory")
    if (root / ".github/workflows").is_dir():
        add("ci", ".github/workflows")
    if (root / ".agents/skills").is_dir():
        add("repo_scoped_skills", ".agents/skills")
    if (root / ".omx").exists():
        add("omx", ".omx directory")

    product_capabilities = {
        "web_frontend",
        "mobile_app",
        "desktop_app",
        "api_backend",
        "cli_tool",
        "ai_agent_app",
        "data_ml",
        "infra",
        "firmware",
        "mechanical_cad",
        "pcb_electronics",
        "robotics",
    }
    docs_present = (root / "docs").is_dir() or (root / "README.md").is_file()
    if docs_present and not (capabilities & product_capabilities):
        add("docs_only", "documentation exists without product-family markers")
    if not (capabilities & product_capabilities) and "docs_only" not in capabilities:
        add("unknown", "no exact project-family markers found")

    for values in evidence.values():
        values.sort()
    for values in negative_evidence.values():
        values.sort()
    return {
        "schema_version": 1,
        "root": str(root),
        "rules": str(rules_file),
        "capabilities": sorted(capabilities),
        "evidence": dict(sorted(evidence.items())),
        "negative_evidence": dict(sorted(negative_evidence.items())),
    }


def main() -> int:
    repo = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    try:
        result = detect(repo)
    except ContractError as exc:
        print(json.dumps({"status": "failed", "error": str(exc)}, indent=2))
        return 1
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
