"""Native 3ds Max 2027 CityGen panel and scene adapter.

This module runs inside 3ds Max through ``pymxs``.  Its data-only helpers are
kept separate in ``citygen.py`` so native scene mutation stays at this boundary.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

try:
    from pymxs import runtime as rt
    from PySide6 import QtCore, QtWidgets
except ImportError:  # pragma: no cover - imported only by 3ds Max
    rt = None
    QtCore = QtWidgets = None


PACKAGE_DIR = Path(__file__).resolve().parent
if str(PACKAGE_DIR) not in sys.path:
    sys.path.insert(0, str(PACKAGE_DIR))


def _eligible_selection() -> bool:
    """Return true only when Max has one selected planar closed source object."""
    if rt is None or rt.selection.count != 1:
        return False
    node = rt.selection[0]
    return bool(rt.isValidNode(node) and not getattr(node, "isHidden", False))


def _next_version(site: str) -> int:
    prefix = f"CG_{site}_v"
    versions = []
    for index in range(rt.LayerManager.count):
        name = rt.LayerManager.getLayer(index).name
        if name.startswith(prefix) and name[len(prefix):len(prefix) + 3].isdigit():
            versions.append(int(name[len(prefix):len(prefix) + 3]))
    return max(versions, default=0) + 1


def _layer(name: str):
    return rt.LayerManager.getLayerFromName(name) or rt.LayerManager.newLayerFromName(name)


def _create_placeholder(category: str, layer_name: str, number: int):
    """Create a detached native node. Generators replace this simple primitive."""
    node = rt.Box(length=1, width=1, height=1)
    node.name = f"{layer_name}_{number:03d}"
    _layer(layer_name).addNode(node)
    return node


class CityGenPanel(QtWidgets.QWidget if QtWidgets else object):
    def __init__(self) -> None:
        if QtWidgets is None:
            raise RuntimeError("CityGen must run inside 3ds Max 2027")
        super().__init__()
        self.setWindowTitle("CityGen")
        layout = QtWidgets.QFormLayout(self)
        self.mode = QtWidgets.QComboBox(); self.mode.addItems(["Procedural", "Real-world"])
        self.site = QtWidgets.QLineEdit("Site")
        self.style = QtWidgets.QComboBox(); self.style.addItems(["Modern", "Medieval", "Victorian", "Steampunk", "Sci-Fi", "Post-Apocalypse"])
        self.quality = QtWidgets.QComboBox(); self.quality.addItems(["Draft", "Production", "Hero"])
        self.map_button = QtWidgets.QPushButton("Map Picker")
        self.generate_button = QtWidgets.QPushButton("Generate")
        self.status = QtWidgets.QLabel("Select one closed planar mesh or spline.")
        for label, widget in (("Mode", self.mode), ("Site", self.site), ("Style", self.style), ("Quality", self.quality)):
            layout.addRow(label, widget)
        layout.addRow(self.map_button); layout.addRow(self.generate_button); layout.addRow(self.status)
        self.map_button.clicked.connect(self.open_map)
        self.generate_button.clicked.connect(self.generate)
        self.timer = QtCore.QTimer(self); self.timer.timeout.connect(self.refresh_selection); self.timer.start(400)
        self.refresh_selection()

    def refresh_selection(self) -> None:
        ok = _eligible_selection()
        self.generate_button.setEnabled(ok)
        self.status.setText("Ready to generate." if ok else "Select one closed planar mesh or spline.")

    def open_map(self) -> None:
        from map_picker import open_picker
        self._map_result = open_picker()
        self.status.setText("Choose a site in your browser, then return here.")

    def generate(self) -> None:
        if not _eligible_selection():
            return
        site = "".join(char if char.isalnum() else "_" for char in self.site.text()).strip("_") or "Site"
        version = _next_version(site)
        prefix = f"CG_{site}_v{version:03d}"
        nodes = []
        for category in ("Buildings", "Roads", "Water", "Terrain", "Bridges", "Props"):
            nodes.append(_create_placeholder(category, f"{prefix}_{category}", 1))
        rt.select(nodes)
        self.status.setText(f"Created {prefix}; generation adapters can now replace category nodes.")


_PANEL = None


def open_citygen() -> None:
    global _PANEL
    if _PANEL is None:
        _PANEL = CityGenPanel()
    _PANEL.show()
    _PANEL.raise_()
    _PANEL.activateWindow()


if rt is not None:
    open_citygen()
