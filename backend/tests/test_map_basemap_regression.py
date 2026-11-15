"""Prevent key-required map tile providers from reappearing in BLINDSPOT's default UI."""
from pathlib import Path

FRONT = Path(__file__).resolve().parents[2] / "frontend"


def test_no_unkeyed_carto_tiles():
    for name in ("app.js", "investigation.js"):
        source = (FRONT / name).read_text(encoding="utf-8")
        assert "basemaps.cartocdn.com" not in source, f"{name} reintroduced key-required CARTO tiles"
        assert "World_Imagery/MapServer/tile" in source


def test_keyless_map_and_cache_bust():
    code = (FRONT / "app.js").read_text(encoding="utf-8")
    html = (FRONT / "index.html").read_text(encoding="utf-8")
    assert "https://tile.openstreetmap.org/{z}/{x}/{y}.png" in code
    assert "blindspot-osm-dark" in code
    assert "v=observatory-20261115" in html
    assert "maptiler.maptilerLayer" in code
