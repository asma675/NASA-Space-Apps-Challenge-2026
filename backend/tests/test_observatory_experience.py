"""Route and visual feature checks for the Parallax-first Observatory experience."""
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

FRONT=Path(__file__).resolve().parents[2]/"frontend"

def test_three_distinct_pages():
    with TestClient(app) as client:
        start=client.get('/')
        story=client.get('/observatory')
        explore=client.get('/explore')
        assert all(r.status_code==200 for r in (start,story,explore))
        assert 'Enter the observatory' in start.text
        assert 'cabin-door' in start.text
        assert 'id="story-next"' in story.text
        assert 'id="story-title"' in story.text
        assert 'id="reveal-left-map"' in explore.text
        assert 'id="reveal-right-map"' in explore.text
        assert 'id="reveal-map-style"' in explore.text
        assert 'id="map-style"' in explore.text
        assert 'Illustrated Atlas' in explore.text
        assert 'href="/observatory"' in explore.text

def test_sourced_map_and_no_hidden_carto():
    app=(FRONT/'app.js').read_text()
    reveal=(FRONT/'investigation.js').read_text()
    story=(FRONT/'observatory.js').read_text()
    assert 'https://tile.openstreetmap.org/{z}/{x}/{y}.png' in app
    assert 'https://tile.openstreetmap.org/{z}/{x}/{y}.png' in reveal
    assert 'basemaps.cartocdn.com' not in app+reveal
    assert 'updateComparisonBasemap' in reveal
    assert 'no simulated NASA metrics' in story

def test_story_assets_and_source_coverage_are_clear():
    landing=(FRONT/'landing.html').read_text()
    story=(FRONT/'observatory.html').read_text()
    assert 'MAYA' in story.upper()
    assert 'Illustration' in landing
    assert 'MAY–OCT 2023' in landing
    assert 'not a verified wildfire' in landing.lower()
