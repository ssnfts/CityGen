"""Package-level safeguards for the native 3ds Max distribution."""

from __future__ import annotations

from pathlib import Path
from zipfile import ZipFile


ROOT = Path(__file__).resolve().parents[1]
PACKAGE = ROOT / "max_package"
RELEASE = ROOT / "dist" / "CityGen.mzp"


def test_native_package_has_drag_drop_install_and_macro_entrypoint():
    install = (PACKAGE / "mzp.run").read_text(encoding="utf-8")
    macro = (PACKAGE / "scripts" / "CityGen.mcr").read_text(encoding="utf-8")

    assert 'drop "install.ms"' in install
    assert "macroScript CityGen_Open" in macro
    assert "CityGen" in macro


def test_native_adapter_is_bridge_free_and_has_required_ui_controls():
    adapter = (PACKAGE / "scripts" / "citygen_max.py").read_text(encoding="utf-8")

    for label in ("Mode", "Map Picker", "Style", "Quality", "Generate"):
        assert label in adapter
    assert "maxbridge" not in adapter.lower()
    assert "socket" not in adapter.lower()


def test_map_picker_uses_the_default_browser_and_writes_a_return_file():
    picker = (PACKAGE / "scripts" / "map_picker.py").read_text(encoding="utf-8")

    assert "webbrowser.open" in picker
    assert "citygen-map-result.json" in picker


def test_supported_runtime_path_has_no_legacy_atlas_or_vray_modules():
    supported = [ROOT / "server" / "citygen.py", *PACKAGE.rglob("*")]
    text = "\n".join(path.read_text(encoding="utf-8") for path in supported if path.is_file())

    for forbidden in ("maxbridge", "atlas_max", "vraysky", "vraysun"):
        assert forbidden not in text.lower()


def test_release_archive_contains_the_native_drag_drop_tool():
    with ZipFile(RELEASE) as archive:
        names = set(archive.namelist())

    assert {"mzp.run", "install.ms", "scripts/CityGen.mcr", "scripts/citygen_max.py", "scripts/map_picker.py", "core/citygen.py"} <= names
