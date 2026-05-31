"""web-article renderer — block list → clean HTML.

Takes a list of typed block dicts (conforming to schema.yaml) and returns
a single HTML string ready to store in Firestore or any web CMS.

No markdown conversion. No Quill. No stripping surprises.
"""

from typing import List, Dict, Any
import re


def render(blocks: List[Dict[str, Any]]) -> str:
    """Render a list of blocks to HTML."""
    parts = []
    for block in blocks:
        btype = block.get("type")
        fn = _RENDERERS.get(btype)
        if fn:
            parts.append(fn(block))
        else:
            parts.append(f'<!-- unknown block type: {btype} -->')
    return "\n\n".join(parts)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _md_inline(text: str) -> str:
    """Convert **bold**, *italic*, and `code` inline markdown to HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    text = re.sub(r'\[([^\]]+)\]\(([^)]+)\)', r'<a href="\2">\1</a>', text)
    return text


def _youtube_id(url: str) -> str:
    """Extract YouTube video ID from any youtube.com or youtu.be URL."""
    m = re.search(r'(?:v=|youtu\.be/)([a-zA-Z0-9_-]{11})', url)
    return m.group(1) if m else url


# ── Block renderers ──────────────────────────────────────────────────────────

def _render_intro(b: dict) -> str:
    parts = []
    if b.get("series_label") and b.get("series_url"):
        parts.append(
            f'<p><em>In <a href="{b["series_url"]}">{b["series_label"]}</a>, '
            f'{_md_inline(b.get("continuation", "I covered the background. This article picks up from there."))}</em></p>'
        )
    if b.get("note"):
        parts.append(f'<p><em>{_md_inline(b["note"])}</em></p>')
    return "\n".join(parts)


def _render_body(b: dict) -> str:
    paragraphs = b.get("text", "").strip().split("\n\n")
    return "\n".join(f"<p>{_md_inline(p.strip())}</p>" for p in paragraphs if p.strip())


def _render_heading(b: dict) -> str:
    return f'<h2>{_md_inline(b.get("text", ""))}</h2>'


def _render_subheading(b: dict) -> str:
    return f'<h3>{_md_inline(b.get("text", ""))}</h3>'


def _render_quote(b: dict) -> str:
    html = f'<blockquote><p>{_md_inline(b.get("text", ""))}</p>'
    if b.get("attribution"):
        html += f'<footer>— {b["attribution"]}</footer>'
    html += '</blockquote>'
    return html


def _render_code(b: dict) -> str:
    lang = b.get("language", "")
    content = b.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
    return f'<pre><code class="language-{lang}">{content}</code></pre>'


def _render_pipeline(b: dict) -> str:
    steps = b.get("steps", [])
    flow = " ──► ".join(f"<code>{s}</code>" for s in steps)
    return f'<p style="font-family:monospace;background:#f4f4f4;padding:12px 16px;border-radius:6px;">{flow}</p>'


def _render_bullet_list(b: dict) -> str:
    items_html = []
    for item in b.get("items", []):
        if item.get("label"):
            items_html.append(f'<li><strong>{_md_inline(item["label"])}</strong> {_md_inline(item.get("text",""))}</li>')
        else:
            items_html.append(f'<li>{_md_inline(item.get("text",""))}</li>')
    return f'<ul>{"".join(items_html)}</ul>'


def _render_divider(b: dict) -> str:
    return '<hr style="border:none;border-top:1px solid rgba(0,0,0,0.1);margin:2rem 0;"/>'


def _render_youtube(b: dict) -> str:
    vid_id = _youtube_id(b.get("url", ""))
    caption = f'<p style="font-size:0.8rem;opacity:0.6;margin-top:6px;text-align:center;">{b["caption"]}</p>' if b.get("caption") else ""
    return (
        f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;margin:1.2rem 0;border-radius:8px;">'
        f'<iframe src="https://www.youtube.com/embed/{vid_id}" '
        f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen></iframe>'
        f'</div>{caption}'
    )


def _render_image(b: dict) -> str:
    width = b.get("width", "100%")
    caption = f'<p style="font-size:0.8rem;opacity:0.6;margin-top:6px;text-align:center;">{b.get("caption","")}</p>' if b.get("caption") else ""
    return (
        f'<div style="margin:1.2rem 0;text-align:center;">'
        f'<img src="{b["url"]}" alt="{b.get("alt","")}" '
        f'style="width:{width};height:auto;border-radius:8px;display:block;margin:0 auto;"/>'
        f'{caption}</div>'
    )


def _render_image_pair(b: dict) -> str:
    def cell(side):
        caption = f'<p style="font-size:0.78rem;opacity:0.6;margin-top:6px;">{side.get("caption","")}</p>' if side.get("caption") else ""
        return (
            f'<td style="width:50%;padding:0 8px;vertical-align:top;text-align:center;">'
            f'<img src="{side["url"]}" alt="{side.get("alt","")}" '
            f'style="width:100%;height:auto;border-radius:8px;display:block;"/>'
            f'{caption}</td>'
        )
    left = b.get("left", {})
    right = b.get("right", {})
    return (
        f'<table style="width:100%;border-collapse:collapse;margin:1.2rem 0;">'
        f'<tr>{cell(left)}{cell(right)}</tr>'
        f'</table>'
    )


def _render_diagram(b: dict) -> str:
    caption = f'<p style="font-size:0.8rem;opacity:0.6;margin-top:6px;text-align:center;">{b.get("caption","")}</p>' if b.get("caption") else ""
    return (
        f'<div style="margin:1.2rem 0;text-align:center;">'
        f'<img src="{b["url"]}" alt="diagram" style="max-width:100%;height:auto;border-radius:8px;"/>'
        f'{caption}</div>'
    )


def _render_repo_links(b: dict) -> str:
    items = "".join(
        f'<li><strong>{l["label"]}:</strong> <a href="{l["url"]}">{l["url"].replace("https://","")}</a></li>'
        for l in b.get("links", [])
    )
    return f'<ul style="list-style:none;padding:0;">{items}</ul>'


def _render_closing(b: dict) -> str:
    text = f'<p>{_md_inline(b.get("text", ""))}</p>'
    tags = b.get("tags", [])
    tag_html = ""
    if tags:
        tag_html = '<p style="opacity:0.5;font-size:0.85rem;">' + " ".join(f"#{t}" for t in tags) + "</p>"
    return text + tag_html


def _render_callout(b: dict) -> str:
    """Callout/alert box — info, warning, tip, note."""
    kind = b.get("kind", "info")
    styles = {
        "info":    ("ℹ️",  "#e8f0fe", "#1a73e8", "#1a73e8"),
        "warning": ("⚠️",  "#fef7e0", "#f9ab00", "#e37400"),
        "tip":     ("💡",  "#e6f4ea", "#34a853", "#137333"),
        "danger":  ("🚨",  "#fce8e6", "#ea4335", "#c5221f"),
    }
    emoji, bg, border, text_color = styles.get(kind, styles["info"])
    title = b.get("title", "")
    text = _md_inline(b.get("text", ""))
    title_html = f'<strong style="color:{text_color};display:block;margin-bottom:4px;">{emoji} {title}</strong>' if title else f'<strong style="color:{text_color};">{emoji} </strong>'
    return (
        f'<div style="background:{bg};border-left:4px solid {border};border-radius:0 8px 8px 0;'
        f'padding:16px 20px;margin:1.5rem 0;">'
        f'{title_html}'
        f'<span style="color:#3c4043;line-height:1.6;">{text}</span>'
        f'</div>'
    )


def _render_steps(b: dict) -> str:
    """Numbered sequential steps."""
    items = b.get("items", [])
    steps_html = []
    for i, item in enumerate(items, 1):
        label = f'<strong>{_md_inline(item["label"])}</strong><br/>' if item.get("label") else ""
        text = _md_inline(item.get("text", ""))
        steps_html.append(
            f'<li style="display:flex;gap:16px;margin-bottom:20px;align-items:flex-start;">'
            f'<span style="flex:0 0 28px;height:28px;background:#1a73e8;color:white;border-radius:50%;'
            f'display:flex;align-items:center;justify-content:center;font-weight:700;font-size:0.85rem;">{i}</span>'
            f'<div style="padding-top:3px;">{label}{text}</div>'
            f'</li>'
        )
    return (
        f'<ol style="list-style:none;padding:0;margin:1.5rem 0;">'
        f'{"".join(steps_html)}'
        f'</ol>'
    )


def _render_table(b: dict) -> str:
    """HTML table with optional caption."""
    headers = b.get("headers", [])
    rows = b.get("rows", [])
    caption = b.get("caption", "")

    caption_html = f'<caption style="font-size:0.85rem;opacity:0.6;margin-bottom:8px;text-align:left;">{caption}</caption>' if caption else ""
    th_cells = "".join(
        f'<th style="background:#f1f3f4;border:1px solid #dadce0;padding:10px 14px;text-align:left;font-weight:600;white-space:nowrap;">{h}</th>'
        for h in headers
    )
    rows_html = []
    for i, row in enumerate(rows):
        bg = 'background:#f8f9fa;' if i % 2 else ''
        cells = "".join(
            f'<td style="border:1px solid #dadce0;padding:9px 14px;vertical-align:top;line-height:1.5;{bg}">{_md_inline(str(c))}</td>'
            for c in row
        )
        rows_html.append(f'<tr>{cells}</tr>')

    return (
        f'<div style="overflow-x:auto;margin:1.5rem 0;">'
        f'<table style="border-collapse:collapse;width:100%;font-size:0.9em;">'
        f'{caption_html}'
        f'<thead><tr>{th_cells}</tr></thead>'
        f'<tbody>{"".join(rows_html)}</tbody>'
        f'</table></div>'
    )


_TAB_CSS = """
<style>
.tm-tabs{margin:1.5rem 0;border-radius:10px;overflow:hidden;border:1px solid #e0e0e0;}
.tm-tabs input[type=radio]{display:none;}
.tm-tab-labels{display:flex;background:#f8f9fa;border-bottom:1px solid #e0e0e0;overflow-x:auto;}
.tm-tab-label{padding:10px 20px;cursor:pointer;font-size:0.85rem;font-weight:600;color:#5f6368;
  white-space:nowrap;border-right:1px solid #e0e0e0;transition:all 0.15s ease;user-select:none;
  border-bottom:3px solid transparent;margin-bottom:-1px;}
.tm-tab-label:hover{background:#fff;color:#1a73e8;}
.tm-tab-panels{background:#fff;}
.tm-tab-panel{display:none;padding:0;}
.tm-tab-panel pre{margin:0;border-radius:0;border:none;}
</style>
"""

def _render_tabs(b: dict, _tab_counter=[0]) -> str:
    """CSS-only tabbed panels — typically used for multi-language code examples."""
    _tab_counter[0] += 1
    group = f"tmtabs{_tab_counter[0]}"
    tabs = b.get("tabs", [])
    if not tabs:
        return ""

    accent = b.get("accent", "#1a73e8")

    # Dynamic CSS for this tab group's checked states
    checked_css = "".join(
        f'#{group}_t{i}:checked ~ .tm-tab-labels .tm-tab-label[for="{group}_t{i}"]'
        f'{{background:#fff;color:{accent};border-bottom-color:{accent};}}\n'
        f'#{group}_t{i}:checked ~ .tm-tab-panels .tm-tab-panel:nth-child({i})'
        f'{{display:block;}}\n'
        for i in range(1, len(tabs) + 1)
    )

    inputs = "".join(
        f'<input type="radio" id="{group}_t{i}" name="{group}" {"checked" if i == 1 else ""}>'
        for i, _ in enumerate(tabs, 1)
    )
    labels = "".join(
        f'<label class="tm-tab-label" for="{group}_t{i}">{tab.get("label","Tab")}</label>'
        for i, tab in enumerate(tabs, 1)
    )
    panels = "".join(
        f'<div class="tm-tab-panel">{_render_code(tab)}</div>'
        for tab in tabs
    )

    return (
        f'{_TAB_CSS}'
        f'<style>{checked_css}</style>'
        f'<div class="tm-tabs">'
        f'{inputs}'
        f'<div class="tm-tab-labels">{labels}</div>'
        f'<div class="tm-tab-panels">{panels}</div>'
        f'</div>'
    )


def _render_key_value(b: dict) -> str:
    """Key-value pairs — for env vars, config options, API fields."""
    items = b.get("items", [])
    title = b.get("title", "")
    title_html = f'<p style="font-weight:600;margin-bottom:8px;">{title}</p>' if title else ""
    def _kv_row(item):
        required_html = "<strong>Required</strong> — " if item.get("required") else ""
        default_val = item.get("default")
        default_html = f'<br/><code style="color:#34a853;">default: {default_val}</code>' if default_val is not None else ""
        return (
            f'<tr>'
            f'<td style="padding:8px 12px;font-family:monospace;font-size:0.85em;color:#1a73e8;white-space:nowrap;'
            f'border-bottom:1px solid #f0f0f0;vertical-align:top;font-weight:600;">{item.get("key","")}</td>'
            f'<td style="padding:8px 12px;color:#5f6368;font-size:0.85em;border-bottom:1px solid #f0f0f0;">'
            f'{required_html}{_md_inline(item.get("description",""))}{default_html}'
            f'</td></tr>'
        )
    rows = "".join(_kv_row(item) for item in items)
    return (
        f'{title_html}'
        f'<div style="overflow-x:auto;margin:1.2rem 0;">'
        f'<table style="border-collapse:collapse;width:100%;background:#fafafa;border-radius:8px;overflow:hidden;">'
        f'<tbody>{rows}</tbody>'
        f'</table></div>'
    )


# ── Registry ─────────────────────────────────────────────────────────────────

_RENDERERS = {
    "intro":        _render_intro,
    "body":         _render_body,
    "heading":      _render_heading,
    "subheading":   _render_subheading,
    "quote":        _render_quote,
    "code":         _render_code,
    "pipeline":     _render_pipeline,
    "bullet_list":  _render_bullet_list,
    "divider":      _render_divider,
    "youtube":      _render_youtube,
    "image":        _render_image,
    "image_pair":   _render_image_pair,
    "diagram":      _render_diagram,
    "repo_links":   _render_repo_links,
    "closing":      _render_closing,
    "callout":      _render_callout,
    "steps":        _render_steps,
    "table":        _render_table,
    "tabs":         _render_tabs,
    "key_value":    _render_key_value,
}
