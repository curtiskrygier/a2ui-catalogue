"""Renderer tests — one test per atom, plus surface compatibility assertions."""

import pytest


# ── Helpers ───────────────────────────────────────────────────────────────────

def r(renderer, *blocks):
    return renderer(list(blocks))

def rd(renderer, *blocks):
    return renderer(list(blocks), theme="dark")


# ── Text atoms ────────────────────────────────────────────────────────────────

def test_body(renderer):
    html = r(renderer, {"type": "body", "text": "Hello **world**."})
    assert "<p>" in html
    assert "<strong>world</strong>" in html


def test_heading(renderer):
    html = r(renderer, {"type": "heading", "text": "My Section"})
    assert "<h2>" in html
    assert "My Section" in html


def test_subheading(renderer):
    html = r(renderer, {"type": "subheading", "text": "Sub"})
    assert "<h3>" in html


def test_quote(renderer):
    html = r(renderer, {"type": "quote", "text": "The substrate is what compounds.", "attribution": "Curtis"})
    assert "<blockquote>" in html
    assert "Curtis" in html


def test_code(renderer):
    html = r(renderer, {"type": "code", "language": "python", "content": "x = 1"})
    assert "<pre>" in html
    assert 'class="language-python"' in html
    assert "x = 1" in html


def test_pipeline(renderer):
    html = r(renderer, {"type": "pipeline", "steps": ["build", "deploy", "run"]})
    assert "build" in html
    assert "──►" in html


def test_bullet_list(renderer):
    html = r(renderer, {"type": "bullet_list", "items": [
        {"label": "Key", "text": "value"},
        {"text": "plain item"},
    ]})
    assert "<ul>" in html
    assert "<strong>Key</strong>" in html


def test_divider(renderer):
    html = r(renderer, {"type": "divider"})
    assert "<hr" in html


def test_intro(renderer):
    html = r(renderer, {"type": "intro", "series_label": "the first article",
                         "series_url": "https://example.com", "continuation": "picks up here."})
    assert "<em>" in html
    assert "the first article" in html


def test_closing(renderer):
    html = r(renderer, {"type": "closing", "text": "Final thought.", "tags": ["AI", "A2UI"]})
    assert "Final thought." in html
    assert "#AI" in html


# ── Media atoms ───────────────────────────────────────────────────────────────

def test_youtube(renderer):
    html = r(renderer, {"type": "youtube", "url": "https://youtu.be/DnGvNgftRGQ", "caption": "Demo"})
    assert "DnGvNgftRGQ" in html
    assert "iframe" in html
    assert "Demo" in html


def test_image(renderer):
    html = r(renderer, {"type": "image", "url": "https://example.com/img.png", "alt": "test"})
    assert "<img" in html
    assert "example.com/img.png" in html


def test_image_pair(renderer):
    html = r(renderer, {"type": "image_pair",
                         "left": {"url": "https://example.com/a.png", "alt": "a", "caption": "Left"},
                         "right": {"url": "https://example.com/b.png", "alt": "b", "caption": "Right"}})
    assert "a.png" in html
    assert "b.png" in html
    assert "Left" in html
    assert "Right" in html


def test_repo_links(renderer):
    html = r(renderer, {"type": "repo_links", "links": [
        {"label": "Catalogue", "url": "https://github.com/curtiskrygier/a2ui-catalogue"}
    ]})
    assert "Catalogue" in html
    assert "github.com/curtiskrygier/a2ui-catalogue" in html


# ── Enhanced atoms ────────────────────────────────────────────────────────────

def test_callout_kinds(renderer):
    for kind in ["info", "warning", "tip", "danger"]:
        html = r(renderer, {"type": "callout", "kind": kind, "title": kind.title(), "text": "test"})
        assert kind.title() in html


def test_steps(renderer):
    html = r(renderer, {"type": "steps", "items": [
        {"label": "First", "text": "do this"},
        {"label": "Second", "text": "then this"},
    ]})
    assert "First" in html
    assert "Second" in html
    # Blue circle indicators
    assert "border-radius:50%" in html


def test_table(renderer):
    html = r(renderer, {"type": "table",
                         "headers": ["A", "B", "C"],
                         "rows": [["1", "2", "3"], ["4", "5", "6"]]})
    assert "<table" in html
    assert "<th" in html
    assert "A" in html and "B" in html


def test_tabs(renderer):
    html = r(renderer, {"type": "tabs", "tabs": [
        {"label": "Python", "language": "python", "content": "x = 1"},
        {"label": "bash",   "language": "bash",   "content": "echo hi"},
    ]})
    assert 'type="radio"' in html
    assert "tm-tab-label" in html
    assert "Python" in html
    assert "bash" in html
    assert "x = 1" in html


def test_key_value(renderer):
    html = r(renderer, {"type": "key_value", "items": [
        {"key": "GEMINI_PROJECT", "description": "GCP project", "required": True},
        {"key": "REGION", "description": "Region", "default": "us-central1"},
    ]})
    assert "GEMINI_PROJECT" in html
    assert "Required" in html
    assert "us-central1" in html


def test_before_after(renderer):
    html = r(renderer, {"type": "before_after", "language": "python",
                         "before": "old code", "after": "new code"})
    assert "old code" in html
    assert "new code" in html
    assert "#c5221f" in html  # red for before
    assert "#137333" in html  # green for after


def test_api_reference(renderer):
    html = r(renderer, {"type": "api_reference",
                         "name": "my_function", "kind": "function",
                         "description": "Does something useful.",
                         "parameters": [
                             {"name": "x", "type": "str", "required": True, "description": "input"}
                         ],
                         "returns": "str"})
    assert "my_function" in html
    assert "Does something useful" in html
    assert "✓" in html  # required checkmark indicator


def test_timeline(renderer):
    html = r(renderer, {"type": "timeline", "events": [
        {"date": "Jan 2026", "label": "Start", "text": "began"},
        {"date": "Feb 2026", "label": "End",   "text": "done"},
    ]})
    assert "Jan 2026" in html
    assert "Start" in html
    assert "border-radius:50%" in html  # dot indicators


def test_annotated_code(renderer):
    html = r(renderer, {"type": "annotated_code", "language": "python",
                         "code": "x = 1\ny = 2\nz = 3",
                         "annotations": [
                             {"line": 1, "text": "assigns x"},
                             {"line": 3, "text": "assigns z"},
                         ]})
    assert "assigns x" in html
    assert "assigns z" in html
    assert "f9ab00" in html  # yellow callout badge


def test_gallery(renderer):
    html = r(renderer, {"type": "gallery", "cols": 2, "images": [
        {"url": "https://example.com/a.png", "alt": "a", "caption": "A"},
        {"url": "https://example.com/b.png", "alt": "b", "caption": "B"},
    ]})
    assert "a.png" in html
    assert "b.png" in html
    assert "grid-template-columns" in html


def test_video_pair(renderer):
    html = r(renderer, {"type": "video_pair",
                         "left":  {"url": "https://youtu.be/AAA1111111A", "label": "Left"},
                         "right": {"url": "https://youtu.be/BBB2222222B", "label": "Right"}})
    assert "AAA1111111A" in html
    assert "BBB2222222B" in html
    assert "Left" in html


def test_carousel(renderer):
    html = r(renderer, {"type": "carousel", "slides": [
        {"url": "https://example.com/a.png", "label": "Slide 1"},
        {"url": "https://example.com/b.png", "label": "Slide 2"},
    ]})
    assert 'type="radio"' in html
    assert "Slide 1" in html
    assert "cubic-bezier" in html  # smooth transition


# ── Dark theme ────────────────────────────────────────────────────────────────

def test_dark_theme_injects_overrides(renderer):
    html = rd(renderer, {"type": "body", "text": "test"})
    assert "meet-stage dark theme" in html
    assert "#00f2ff" in html


def test_light_theme_no_overrides(renderer):
    html = r(renderer, {"type": "body", "text": "test"})
    assert "meet-stage dark theme" not in html


# ── Surface compatibility via schema ──────────────────────────────────────────

def test_tabs_incompatible_googlechat(atoms):
    surfaces = atoms["tabs"]["surfaces"]
    incompatible = [e["surface"] for e in surfaces.get("incompatible_on", [])]
    assert "googlechat" in incompatible


def test_youtube_incompatible_email(atoms):
    surfaces = atoms["youtube"]["surfaces"]
    incompatible = [e["surface"] for e in surfaces.get("incompatible_on", [])]
    assert "email" in incompatible


def test_carousel_works_on_meet_stage(atoms):
    works_on = atoms["carousel"]["surfaces"]["works_on"]
    assert "meet-stage" in works_on


def test_body_works_everywhere(atoms):
    works_on = atoms["body"]["surfaces"]["works_on"]
    assert set(works_on) == {"web", "meet-stage", "googlechat", "email", "pdf"}
