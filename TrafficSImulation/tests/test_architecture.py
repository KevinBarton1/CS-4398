"""T-45, T-46, T-56: Dependency rules and repository scans."""

from __future__ import annotations

import ast
import re
import tokenize
from io import BytesIO
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "app"
SRC_ROOT = ROOT / "src"
PLANNING_PATH = APP_ROOT / "api" / "planning.py"

MODEL_PACKAGES = ("map", "simulation", "pricing", "weather", "heatmap")
EXPECTED_APP_PACKAGES = {
    "api",
    "config",
    "heatmap",
    "map",
    "pricing",
    "simulation",
    "weather",
}

FLAT_LEGACY_PATHS = (
    APP_ROOT / "routes.py",
    APP_ROOT / "models.py",
    APP_ROOT / "map_service.py",
    APP_ROOT / "traffic_simulator.py",
    APP_ROOT / "pricing_model.py",
    APP_ROOT / "weather_service.py",
    APP_ROOT / "heatmap.py",
)

FLAT_LEGACY_IMPORTS = tuple(
    f"app/{path.stem}" for path in FLAT_LEGACY_PATHS
)

PLANNING_ALLOWED_IMPORT_ROOTS = {
    "app.api.models",
    "app.api.mode_policy",
    "app.api.errors",
    "app.map.places",
    "app.map.routing",
    "app.map.bounds",
    "app.map.types",
    "app.simulation.segments",
    "app.simulation.scoring",
    "app.pricing.model",
    "app.weather.service",
    "app.config",
}

PLANNING_FORBIDDEN_IMPORT_ROOTS = {
    "httpx",
    "app.simulation.traffic",
    "app.map.polyline",
    *FLAT_LEGACY_IMPORTS,
}

# R4 allowlist: mode literals in backend production code.
MODE_LITERAL_ALLOWLIST = {
    APP_ROOT / "api" / "mode_policy.py",
    APP_ROOT / "api" / "models.py",
}

MODE_LITERAL_PATTERN = re.compile(r"""['"]simulated['"]|['"]realtime['"]""")

# Prompt 15 target map components. T-56 enforces once any of them exists.
GOOGLE_MAPS_ALLOWLIST = {
    SRC_ROOT / "components" / "MapConfigProvider.tsx",
    SRC_ROOT / "components" / "RouteMap.tsx",
    SRC_ROOT / "components" / "RoutePolylineLayer.tsx",
    SRC_ROOT / "components" / "MapBoundsController.tsx",
}

GOOGLE_MAPS_PATTERN = re.compile(r"google\.maps")


def _relative(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def _iter_python_files(package_dir: Path) -> list[Path]:
    return sorted(
        path
        for path in package_dir.rglob("*.py")
        if "__pycache__" not in path.parts
    )


def _module_imports(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _numeric_coefficient_literals(path: Path) -> list[str]:
    source = path.read_text(encoding="utf-8")
    # Display precision, indexing, and unit conversions are not domain coefficients.
    allowed = {0, 1, 2, 60, 1000}
    literals: list[str] = []
    for token in tokenize.tokenize(BytesIO(source.encode()).readline):
        if token.type not in {tokenize.NUMBER}:
            continue
        value = token.string
        try:
            number = ast.literal_eval(value)
        except (SyntaxError, ValueError):
            continue
        if isinstance(number, (int, float)) and number not in allowed:
            literals.append(value)
    return literals


def test_t45_model_packages_do_not_import_controller() -> None:
    violations: list[str] = []
    for package in MODEL_PACKAGES:
        for path in _iter_python_files(APP_ROOT / package):
            for imported in _module_imports(path):
                if imported.startswith("app.api") or imported == "main":
                    violations.append(f"{_relative(path)} imports {imported}")
                if imported.startswith("fastapi"):
                    violations.append(f"{_relative(path)} imports {imported}")
    assert violations == []


def test_t45_backend_package_set_matches_spec() -> None:
    packages = {
        path.name
        for path in APP_ROOT.iterdir()
        if path.is_dir() and not path.name.startswith("__")
    }
    assert packages == EXPECTED_APP_PACKAGES


@pytest.mark.parametrize(
    "legacy_path",
    FLAT_LEGACY_PATHS,
    ids=[path.name for path in FLAT_LEGACY_PATHS],
)
def test_t45_flat_legacy_paths_are_absent(legacy_path: Path) -> None:
    assert not legacy_path.exists(), f"Legacy path must not exist: {_relative(legacy_path)}"


def test_t45_planning_import_allowlist() -> None:
    imports = _module_imports(PLANNING_PATH)
    local_imports = {
        module
        for module in imports
        if module.startswith("app.") and not module.startswith("app.api.planning")
    }
    for module in local_imports:
        assert any(
            module == allowed or module.startswith(f"{allowed}.")
            for allowed in PLANNING_ALLOWED_IMPORT_ROOTS
        ), f"Undocumented import in planning.py: {module}"
    for forbidden in PLANNING_FORBIDDEN_IMPORT_ROOTS:
        assert forbidden not in imports, f"Forbidden import in planning.py: {forbidden}"


def test_t45_planning_has_no_numeric_coefficient_literals() -> None:
    literals = _numeric_coefficient_literals(PLANNING_PATH)
    assert literals == [], f"Coefficient literals found in planning.py: {literals}"


def test_t46_mode_literals_are_confined_to_allowlist() -> None:
    violations: list[str] = []
    for path in _iter_python_files(APP_ROOT):
        if path in MODE_LITERAL_ALLOWLIST:
            continue
        text = path.read_text(encoding="utf-8")
        if MODE_LITERAL_PATTERN.search(text):
            violations.append(_relative(path))
    assert violations == []


def test_t56_google_maps_usage_confined_to_map_components() -> None:
    violations: list[str] = []
    for path in sorted(SRC_ROOT.rglob("*.tsx")):
        if "node_modules" in path.parts:
            continue
        if GOOGLE_MAPS_PATTERN.search(path.read_text(encoding="utf-8")):
            if path not in GOOGLE_MAPS_ALLOWLIST:
                violations.append(_relative(path))
    assert violations == []
