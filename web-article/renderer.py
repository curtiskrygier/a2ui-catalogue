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


def _render_github_repo_card(b: dict) -> str:
    """GitHub repo card — fetches live star/fork/language data from GitHub API and renders as a styled card."""
    import urllib.request as _ur
    import json as _json
    from datetime import datetime as _dt

    repo = b.get("repo", "")
    label = b.get("label", "")
    description_override = b.get("description", "")

    name = repo.split("/")[-1] if "/" in repo else repo
    description = description_override or ""
    stars = forks = 0
    language = ""
    updated = ""
    url = f"https://github.com/{repo}" if repo else b.get("url", "#")

    if repo:
        try:
            req = _ur.Request(
                f"https://api.github.com/repos/{repo}",
                headers={"User-Agent": "a2ui-renderer", "Accept": "application/vnd.github+json"},
            )
            with _ur.urlopen(req, timeout=8) as resp:
                data = _json.loads(resp.read())
                name        = data.get("name", name)
                description = description_override or data.get("description", "")
                stars       = data.get("stargazers_count", 0)
                forks       = data.get("forks_count", 0)
                language    = data.get("language", "")
                url         = data.get("html_url", url)
                pushed      = data.get("pushed_at", "")
                if pushed:
                    dt = _dt.fromisoformat(pushed.replace("Z", "+00:00"))
                    updated = dt.strftime("Updated %b %Y")
        except Exception:
            pass

    display_label = label or name
    lang_html = (
        f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:0.78rem;color:#9aa0a6;">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#f9ab00;display:inline-block;"></span>'
        f'{language}</span>'
    ) if language else ""
    updated_html = f'<span style="font-size:0.78rem;color:#9aa0a6;">{updated}</span>' if updated else ""
    desc_html    = f'<p style="margin:6px 0 10px;font-size:0.85rem;color:#555;line-height:1.5;">{description}</p>' if description else ""

    return (
        f'<a href="{url}" target="_blank" rel="noopener" style="display:block;text-decoration:none;margin:1.2rem 0;">'
        f'<div style="border:1px solid #d0d7de;border-radius:10px;padding:16px 20px;'
        f'background:#fff;transition:box-shadow 0.15s;font-family:system-ui,sans-serif;" '
        f'onmouseover="this.style.boxShadow=\'0 4px 12px rgba(0,0,0,0.1)\'" '
        f'onmouseout="this.style.boxShadow=\'none\'">'
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:2px;">'
        f'<svg width="16" height="16" viewBox="0 0 16 16" fill="#555" style="flex-shrink:0;">'
        f'<path d="M2 2.5A2.5 2.5 0 0 1 4.5 0h8.75a.75.75 0 0 1 .75.75v12.5a.75.75 0 0 1-.75.75h-2.5a.75.75 0 0 1 0-1.5h1.75v-2h-8a1 1 0 0 0-.714 1.7.75.75 0 1 1-1.072 1.05A2.495 2.495 0 0 1 2 11.5Zm10.5-1h-8a1 1 0 0 0-1 1v6.708A2.486 2.486 0 0 1 4.5 9h8Z"/>'
        f'</svg>'
        f'<span style="font-size:0.9rem;font-weight:600;color:#0969da;">{display_label}</span>'
        f'</div>'
        f'{desc_html}'
        f'<div style="display:flex;align-items:center;gap:16px;flex-wrap:wrap;">'
        f'{lang_html}'
        f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:0.78rem;color:#9aa0a6;">'
        f'<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M8 .25a.75.75 0 0 1 .673.418l1.882 3.815 4.21.612a.75.75 0 0 1 .416 1.279l-3.046 2.97.719 4.192a.751.751 0 0 1-1.088.791L8 12.347l-3.766 1.98a.75.75 0 0 1-1.088-.79l.72-4.194L.818 6.374a.75.75 0 0 1 .416-1.28l4.21-.611L7.327.668A.75.75 0 0 1 8 .25Z"/></svg>'
        f'{stars}</span>'
        f'<span style="display:inline-flex;align-items:center;gap:4px;font-size:0.78rem;color:#9aa0a6;">'
        f'<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor"><path d="M5 5.372v.878c0 .414.336.75.75.75h4.5a.75.75 0 0 0 .75-.75v-.878a2.25 2.25 0 1 1 1.5 0v.878a2.25 2.25 0 0 1-2.25 2.25h-1.5v2.128a2.251 2.251 0 1 1-1.5 0V8.5h-1.5A2.25 2.25 0 0 1 3.5 6.25v-.878a2.25 2.25 0 1 1 1.5 0ZM5 3.25a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Zm6.75.75a.75.75 0 1 0 0-1.5.75.75 0 0 0 0 1.5Zm-3 8.75a.75.75 0 1 0-1.5 0 .75.75 0 0 0 1.5 0Z"/></svg>'
        f'{forks}</span>'
        f'{updated_html}'
        f'</div></div></a>'
    )


def _render_repo_links(b: dict) -> str:
    items = "".join(
        f'<li><strong>{l["label"]}:</strong> <a href="{l["url"]}">{l["url"].replace("https://","")}</a></li>'
        for l in b.get("links", [])
    )
    return f'<ul style="list-style:none;padding:0;">{items}</ul>'


def _render_before_after(b: dict) -> str:
    """Before/after code comparison — two panels side by side with clear visual distinction."""
    before_label = b.get("before_label", "Before")
    after_label  = b.get("after_label",  "After")
    language     = b.get("language", "")
    before_code  = b.get("before", "").replace("<", "&lt;").replace(">", "&gt;")
    after_code   = b.get("after",  "").replace("<", "&lt;").replace(">", "&gt;")
    caption      = b.get("caption", "")
    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">{caption}</p>' if caption else ""

    def panel(label, code, color, bg):
        return (
            f'<div style="flex:1;min-width:0;">'
            f'<div style="padding:6px 14px;background:{color};border-radius:6px 6px 0 0;display:flex;align-items:center;gap:8px;">'
            f'<span style="font-size:0.78rem;font-weight:700;color:#fff;font-family:monospace;letter-spacing:0.05em;">{label}</span>'
            f'</div>'
            f'<pre style="margin:0;padding:16px;background:{bg};border-radius:0 0 6px 6px;'
            f'overflow-x:auto;font-size:0.84rem;line-height:1.6;">'
            f'<code class="language-{language}">{code}</code>'
            f'</pre></div>'
        )

    return (
        f'<div style="display:flex;gap:12px;margin:1.5rem 0;align-items:flex-start;">'
        f'{panel(f"✗ {before_label}", before_code, "#c5221f", "#fff8f7")}'
        f'{panel(f"✓ {after_label}", after_code, "#137333", "#f0faf4")}'
        f'</div>'
        f'{caption_html}'
    )


def _render_api_reference(b: dict) -> str:
    """API / function reference block — name, description, parameters table, returns, example."""
    name        = b.get("name", "")
    kind        = b.get("kind", "function")   # function, endpoint, class, method
    description = b.get("description", "")
    params      = b.get("parameters", [])
    returns     = b.get("returns", "")
    example     = b.get("example", {})
    http_method = b.get("method", "")         # GET, POST etc. for endpoints
    deprecated  = b.get("deprecated", False)

    # Header badge
    kind_colors = {
        "function": ("#e8f0fe", "#1a73e8"),
        "endpoint": ("#e6f4ea", "#137333"),
        "class":    ("#fef7e0", "#e37400"),
        "method":   ("#f3e8fd", "#8430ce"),
    }
    bg, color = kind_colors.get(kind, kind_colors["function"])
    method_badge = f'<span style="background:#137333;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;font-weight:700;margin-right:8px;">{http_method}</span>' if http_method else ""
    deprecated_html = '<span style="background:#c5221f;color:#fff;padding:2px 8px;border-radius:4px;font-size:0.75rem;margin-left:8px;">DEPRECATED</span>' if deprecated else ""

    # Parameters table
    param_rows = ""
    if params:
        def _param_row(i, p):
            bg = "background:#f8f9fa;" if i % 2 else ""
            req = "✓" if p.get("required") else ""
            default_val = p.get("default")
            default_html = f'<br/><code style="color:#34a853;font-size:0.9em;">default: {default_val}</code>' if default_val is not None else ""
            return (
                f'<tr style="{bg}">'
                f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82em;color:#1a73e8;white-space:nowrap;">{p.get("name","")}</td>'
                f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82em;color:#e37400;">{p.get("type","")}</td>'
                f'<td style="padding:8px 12px;font-size:0.82em;color:#c5221f;text-align:center;">{req}</td>'
                f'<td style="padding:8px 12px;font-size:0.82em;color:#5f6368;">{_md_inline(p.get("description",""))}{default_html}</td>'
                f'</tr>'
            )
        rows = "".join(_param_row(i, p) for i, p in enumerate(params))
        param_rows = (
            f'<div style="margin-top:12px;">'
            f'<p style="font-size:0.8rem;font-weight:600;color:#5f6368;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">Parameters</p>'
            f'<div style="overflow-x:auto;border-radius:6px;border:1px solid #e0e0e0;">'
            f'<table style="border-collapse:collapse;width:100%;font-size:0.9em;">'
            f'<thead><tr style="background:#f1f3f4;">'
            f'<th style="padding:8px 12px;text-align:left;font-size:0.78rem;color:#5f6368;">Name</th>'
            f'<th style="padding:8px 12px;text-align:left;font-size:0.78rem;color:#5f6368;">Type</th>'
            f'<th style="padding:8px 12px;text-align:center;font-size:0.78rem;color:#5f6368;">Req</th>'
            f'<th style="padding:8px 12px;text-align:left;font-size:0.78rem;color:#5f6368;">Description</th>'
            f'</tr></thead>'
            f'<tbody>{rows}</tbody>'
            f'</table></div></div>'
        )

    # Returns
    returns_html = ""
    if returns:
        returns_html = (
            f'<div style="margin-top:12px;">'
            f'<p style="font-size:0.8rem;font-weight:600;color:#5f6368;margin-bottom:4px;text-transform:uppercase;letter-spacing:0.05em;">Returns</p>'
            f'<p style="font-size:0.88em;color:#3c4043;">{_md_inline(returns)}</p>'
            f'</div>'
        )

    # Example
    example_html = ""
    if example:
        ex_code = example.get("code", "").replace("<", "&lt;").replace(">", "&gt;")
        ex_lang = example.get("language", "")
        ex_label = example.get("label", "Example")
        example_html = (
            f'<div style="margin-top:12px;">'
            f'<p style="font-size:0.8rem;font-weight:600;color:#5f6368;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.05em;">{ex_label}</p>'
            f'<pre style="margin:0;padding:14px;background:#f8f9fa;border-radius:6px;overflow-x:auto;font-size:0.84rem;line-height:1.6;">'
            f'<code class="language-{ex_lang}">{ex_code}</code>'
            f'</pre></div>'
        )

    return (
        f'<div style="border:1px solid #e0e0e0;border-radius:10px;overflow:hidden;margin:1.5rem 0;">'
        f'<div style="background:{bg};padding:14px 18px;border-bottom:1px solid #e0e0e0;">'
        f'{method_badge}'
        f'<code style="font-size:1rem;font-weight:700;color:{color};">{name}</code>'
        f'{deprecated_html}'
        f'<span style="font-size:0.78rem;color:#5f6368;margin-left:10px;text-transform:uppercase;letter-spacing:0.05em;">{kind}</span>'
        f'</div>'
        f'<div style="padding:14px 18px;">'
        f'<p style="color:#3c4043;margin-bottom:8px;">{_md_inline(description)}</p>'
        f'{param_rows}'
        f'{returns_html}'
        f'{example_html}'
        f'</div></div>'
    )


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


def _render_gallery(b: dict) -> str:
    """Image gallery — responsive grid with CSS-only lightbox on click."""
    images  = b.get("images", [])
    cols    = b.get("cols", 3)
    caption = b.get("caption", "")
    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:10px;text-align:center;">{caption}</p>' if caption else ""

    # Unique ID per gallery instance
    import hashlib
    gid = "g" + hashlib.md5("".join(i.get("url","") for i in images).encode()).hexdigest()[:6]

    lightbox_css = f"""
<style>
.{gid}-wrap{{display:grid;grid-template-columns:repeat({cols},1fr);gap:10px;margin:1.5rem 0;}}
@media(max-width:600px){{.{gid}-wrap{{grid-template-columns:repeat(2,1fr);}}}}
.{gid}-item{{position:relative;overflow:hidden;border-radius:8px;cursor:zoom-in;aspect-ratio:16/10;background:#f1f3f4;}}
.{gid}-item img{{width:100%;height:100%;object-fit:cover;display:block;transition:transform 0.2s ease;}}
.{gid}-item:hover img{{transform:scale(1.04);}}
.{gid}-item figcaption{{position:absolute;bottom:0;left:0;right:0;padding:6px 10px;
  background:linear-gradient(transparent,rgba(0,0,0,0.6));color:#fff;font-size:0.75rem;
  opacity:0;transition:opacity 0.2s ease;}}
.{gid}-item:hover figcaption{{opacity:1;}}
.{gid}-lb{{display:none;position:fixed;inset:0;background:rgba(0,0,0,0.92);z-index:9999;
  align-items:center;justify-content:center;padding:20px;}}
.{gid}-lb:target{{display:flex;}}
.{gid}-lb img{{max-width:90vw;max-height:88vh;border-radius:8px;box-shadow:0 20px 60px rgba(0,0,0,0.5);}}
.{gid}-lb-close{{position:absolute;top:16px;right:24px;color:#fff;font-size:2rem;
  text-decoration:none;line-height:1;opacity:0.7;}}
.{gid}-lb-close:hover{{opacity:1;}}
.{gid}-lb figcaption{{position:absolute;bottom:20px;left:50%;transform:translateX(-50%);
  color:rgba(255,255,255,0.7);font-size:0.85rem;text-align:center;}}
</style>"""

    items_html = []
    lightboxes_html = []

    for i, img in enumerate(images):
        url     = img.get("url", "")
        alt     = img.get("alt", "")
        cap     = img.get("caption", "")
        lb_id   = f"{gid}-lb{i}"
        cap_html = f"<figcaption>{cap}</figcaption>" if cap else ""

        items_html.append(
            f'<figure class="{gid}-item">'
            f'<a href="#{lb_id}" style="display:block;height:100%;">'
            f'<img src="{url}" alt="{alt}" loading="lazy"/>'
            f'</a>'
            f'{cap_html}'
            f'</figure>'
        )
        lightboxes_html.append(
            f'<div id="{lb_id}" class="{gid}-lb">'
            f'<a href="#" class="{gid}-lb-close">✕</a>'
            f'<img src="{url}" alt="{alt}"/>'
            f'{"<figcaption>" + cap + "</figcaption>" if cap else ""}'
            f'</div>'
        )

    return (
        f'{lightbox_css}'
        f'<div class="{gid}-wrap">{"".join(items_html)}</div>'
        f'{caption_html}'
        f'{"".join(lightboxes_html)}'
    )


def _render_video_pair(b: dict) -> str:
    """Two YouTube videos side by side with captions."""
    left  = b.get("left",  {})
    right = b.get("right", {})
    caption = b.get("caption", "")
    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">{caption}</p>' if caption else ""

    def video_cell(v):
        vid_id  = _youtube_id(v.get("url", ""))
        label   = v.get("label", "")
        label_html = f'<p style="font-size:0.82rem;font-weight:600;margin-bottom:6px;color:#3c4043;">{label}</p>' if label else ""
        return (
            f'<div style="flex:1;min-width:0;">'
            f'{label_html}'
            f'<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;">'
            f'<iframe src="https://www.youtube.com/embed/{vid_id}" '
            f'style="position:absolute;top:0;left:0;width:100%;height:100%;border:0;" allowfullscreen></iframe>'
            f'</div></div>'
        )

    return (
        f'<div style="display:flex;gap:14px;margin:1.5rem 0;align-items:flex-start;">'
        f'{video_cell(left)}{video_cell(right)}'
        f'</div>'
        f'{caption_html}'
    )


def _render_carousel(b: dict) -> str:
    """CSS-only image/content carousel with dot indicators and prev/next arrows."""
    slides  = b.get("slides", [])
    caption = b.get("caption", "")
    accent  = b.get("accent", "#1a73e8")
    if not slides:
        return ""

    import hashlib
    cid = "c" + hashlib.md5("".join(s.get("url", s.get("label","")) for s in slides).encode()).hexdigest()[:6]
    n   = len(slides)

    # CSS — scoped to this carousel instance
    css_parts = [f"""
<style>
.{cid}{{position:relative;overflow:hidden;border-radius:12px;background:#000;margin:1.5rem 0;
  box-shadow:0 4px 24px rgba(0,0,0,0.12);}}
.{cid} input[type=radio]{{display:none;}}
.{cid}-track{{display:flex;transition:transform 0.45s cubic-bezier(0.77,0,0.175,1);width:{n*100}%;}}
.{cid}-slide{{width:{100//n}%;flex:0 0 {100//n}%;position:relative;}}
.{cid}-slide img{{width:100%;display:block;max-height:480px;object-fit:cover;}}
.{cid}-caption{{position:absolute;bottom:0;left:0;right:0;padding:14px 18px;
  background:linear-gradient(transparent,rgba(0,0,0,0.72));color:#fff;}}
.{cid}-caption strong{{display:block;font-size:1rem;margin-bottom:2px;}}
.{cid}-caption span{{font-size:0.82rem;opacity:0.8;}}
.{cid}-dots{{display:flex;justify-content:center;gap:8px;padding:12px;background:#111;}}
.{cid}-dot{{width:8px;height:8px;border-radius:50%;background:rgba(255,255,255,0.3);
  cursor:pointer;transition:all 0.2s;display:block;border:none;}}
.{cid}-arrows{{position:absolute;top:50%;transform:translateY(-50%);width:100%;
  display:flex;justify-content:space-between;padding:0 12px;pointer-events:none;z-index:10;box-sizing:border-box;}}
.{cid}-arrow{{width:38px;height:38px;border-radius:50%;background:rgba(255,255,255,0.15);
  backdrop-filter:blur(4px);color:#fff;display:flex;align-items:center;justify-content:center;
  font-size:1.1rem;cursor:pointer;pointer-events:all;transition:background 0.2s;text-decoration:none;
  border:1px solid rgba(255,255,255,0.2);}}
.{cid}-arrow:hover{{background:rgba(255,255,255,0.28);}}
</style>"""]

    # Per-slide checked states — move track and highlight dot
    for i in range(1, n + 1):
        offset = (i - 1) * (100 // n)
        css_parts.append(
            f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-track'
            f'{{transform:translateX(-{offset}%);}}\n'
            f'#{cid}_s{i}:checked ~ .{cid}-dots .{cid}-dot:nth-child({i})'
            f'{{background:{accent};transform:scale(1.25);}}</style>'
        )

    # Radio inputs
    inputs = "".join(
        f'<input type="radio" id="{cid}_s{i}" name="{cid}" {"checked" if i == 1 else ""}>'
        for i in range(1, n + 1)
    )

    # Slides
    slides_html = ""
    for slide in slides:
        url        = slide.get("url", "")
        label      = slide.get("label", "")
        sub        = slide.get("subtitle", "")
        label_html = (
            f'<div class="{cid}-caption"><strong>{label}</strong>'
            f'{"<span>" + sub + "</span>" if sub else ""}</div>'
        ) if label else ""
        slides_html += (
            f'<div class="{cid}-slide">'
            f'<img src="{url}" alt="{label}" loading="lazy"/>'
            f'{label_html}'
            f'</div>'
        )

    # Arrow nav — labels pointing to adjacent slides (wrapping)
    def arrow(direction, target_idx):
        symbol = "‹" if direction == "prev" else "›"
        return (
            f'<label for="{cid}_s{target_idx}" class="{cid}-arrow">'
            f'{symbol}</label>'
        )

    arrows_html = []
    for i in range(1, n + 1):
        prev_i = n if i == 1 else i - 1
        next_i = 1 if i == n else i + 1
        css_parts.append(
            f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-arrows '
            f'.{cid}-prev{{display:flex;}} '
            f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-arrows '
            f'.{cid}-next{{display:flex;}}</style>'
        )
        arrows_html.append(
            f'<style>'
            f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-arrows '
            f'.{cid}-prev{{content:"";}} </style>'
        )

    # Build per-slide arrow labels via stacking — simpler: always show prev/next for checked
    prev_labels = "".join(
        f'<label for="{cid}_s{n if i==1 else i-1}" '
        f'class="{cid}-arrow" '
        f'style="display:{"flex" if True else "none"};">‹</label>'
        for i in range(1, n + 1)
    )

    # Simpler arrow approach — one prev, one next, update target via checked state CSS
    prev_arrows = "".join(
        f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-ap '
        f'{{display:none;}} '
        f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-ap[data-t="{n if i==1 else i-1}"]'
        f'{{display:flex;}}</style>'
        for i in range(1, n + 1)
    )
    next_arrows = "".join(
        f'<style>#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-an '
        f'{{display:none;}} '
        f'#{cid}_s{i}:checked ~ .{cid}-inner .{cid}-an[data-t="{1 if i==n else i+1}"]'
        f'{{display:flex;}}</style>'
        for i in range(1, n + 1)
    )

    all_prev = "".join(
        f'<label for="{cid}_s{i}" class="{cid}-arrow {cid}-ap" data-t="{i}">‹</label>'
        for i in range(1, n + 1)
    )
    all_next = "".join(
        f'<label for="{cid}_s{i}" class="{cid}-arrow {cid}-an" data-t="{i}">›</label>'
        for i in range(1, n + 1)
    )

    dots = "".join(
        f'<label for="{cid}_s{i}" class="{cid}-dot"></label>'
        for i in range(1, n + 1)
    )

    caption_html = f'<p style="font-size:0.82rem;opacity:0.6;margin-top:8px;text-align:center;">{caption}</p>' if caption else ""

    return (
        "".join(css_parts)
        + prev_arrows + next_arrows
        + f'<div class="{cid}">'
        + inputs
        + f'<div class="{cid}-inner">'
        + f'<div class="{cid}-track">{slides_html}</div>'
        + f'<div class="{cid}-arrows"><div style="display:flex;">{all_prev}</div>'
        + f'<div style="display:flex;">{all_next}</div></div>'
        + f'</div>'
        + f'<div class="{cid}-dots">{dots}</div>'
        + f'</div>'
        + caption_html
    )


def _render_timeline(b: dict) -> str:
    """Vertical timeline — date, title, body per event. Good for changelogs, journeys, release notes."""
    events = b.get("events", [])
    accent = b.get("accent", "#1a73e8")
    title  = b.get("title", "")
    title_html = f'<p style="font-weight:700;font-size:1.05rem;margin-bottom:20px;">{title}</p>' if title else ""

    items_html = []
    for i, event in enumerate(events):
        is_last = i == len(events) - 1
        date    = event.get("date", "")
        label   = event.get("label", "")
        text    = _md_inline(event.get("text", ""))
        tag     = event.get("tag", "")
        tag_html = (
            f'<span style="background:{accent}18;color:{accent};font-size:0.72rem;font-weight:700;'
            f'padding:2px 8px;border-radius:10px;margin-left:8px;vertical-align:middle;">{tag}</span>'
        ) if tag else ""

        connector = "" if is_last else '<div style="width:2px;background:#e0e0e0;flex:1;min-height:24px;margin-top:4px;"></div>'
        items_html.append(
            f'<div style="display:flex;gap:0;position:relative;">'
            # Left column — dot + line
            f'<div style="display:flex;flex-direction:column;align-items:center;width:40px;flex:0 0 40px;">'
            f'<div style="width:14px;height:14px;border-radius:50%;background:{accent};'
            f'border:3px solid #fff;box-shadow:0 0 0 2px {accent};flex:0 0 14px;margin-top:3px;z-index:1;"></div>'
            f'{connector}'
            f'</div>'
            # Right column — content
            f'<div style="padding-bottom:28px;padding-left:12px;flex:1;min-width:0;">'
            f'<div style="display:flex;align-items:baseline;flex-wrap:wrap;gap:6px;margin-bottom:4px;">'
            f'<span style="font-size:0.78rem;font-weight:600;color:{accent};font-family:monospace;letter-spacing:0.04em;">{date}</span>'
            f'{tag_html}'
            f'</div>'
            f'<p style="font-weight:700;font-size:0.95rem;margin:0 0 4px;">{label}</p>'
            f'<p style="color:#5f6368;font-size:0.88rem;line-height:1.6;margin:0;">{text}</p>'
            f'</div>'
            f'</div>'
        )

    return (
        f'<div style="margin:1.5rem 0;padding:20px 20px 0;background:#fafafa;border-radius:10px;border:1px solid #e0e0e0;">'
        f'{title_html}'
        f'{"".join(items_html)}'
        f'</div>'
    )


def _render_annotated_code(b: dict) -> str:
    """Code block with numbered callout bubbles on specific lines, plus explanation list below."""
    language    = b.get("language", "")
    code_lines  = b.get("code", "").split("\n")
    annotations = b.get("annotations", [])  # [{line: 3, text: "explanation"}]
    caption     = b.get("caption", "")

    # Build line-number → annotation-number map
    line_map = {a["line"]: i + 1 for i, a in enumerate(annotations)}

    # Render code with inline callout badges
    rendered_lines = []
    for i, line in enumerate(code_lines, 1):
        escaped = line.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        if i in line_map:
            num = line_map[i]
            badge = (
                f'<span style="display:inline-flex;align-items:center;justify-content:center;'
                f'width:18px;height:18px;border-radius:50%;background:#f9ab00;color:#fff;'
                f'font-size:0.7rem;font-weight:800;margin-left:8px;vertical-align:middle;'
                f'flex-shrink:0;line-height:1;">{num}</span>'
            )
            rendered_lines.append(f'<span style="display:block;">{escaped}{badge}</span>')
        else:
            rendered_lines.append(f'<span style="display:block;">{escaped}</span>')

    code_html = "".join(rendered_lines)
    caption_html = f'<p style="font-size:0.8rem;opacity:0.6;margin:6px 0 0;text-align:center;">{caption}</p>' if caption else ""

    # Annotation explanations
    annotation_items = "".join(
        f'<li style="display:flex;gap:12px;margin-bottom:12px;align-items:flex-start;">'
        f'<span style="flex:0 0 22px;height:22px;border-radius:50%;background:#f9ab00;color:#fff;'
        f'font-size:0.72rem;font-weight:800;display:flex;align-items:center;justify-content:center;">{i+1}</span>'
        f'<span style="font-size:0.88rem;color:#3c4043;line-height:1.6;padding-top:2px;">{_md_inline(a.get("text",""))}</span>'
        f'</li>'
        for i, a in enumerate(annotations)
    )

    return (
        f'<div style="margin:1.5rem 0;">'
        f'<pre style="margin:0;padding:18px;background:#1e1e2e;border-radius:10px 10px 0 0;'
        f'overflow-x:auto;font-size:0.84rem;line-height:1.7;color:#cdd6f4;">'
        f'<code class="language-{language}">{code_html}</code>'
        f'</pre>'
        f'{caption_html}'
        f'<ol style="list-style:none;padding:16px 20px;margin:0;background:#fffbf0;'
        f'border:1px solid #f9ab0033;border-top:none;border-radius:0 0 10px 10px;">'
        f'{annotation_items}'
        f'</ol>'
        f'</div>'
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
    "github_repo_card": _render_github_repo_card,
    "repo_links":   _render_repo_links,
    "closing":      _render_closing,
    "callout":      _render_callout,
    "steps":        _render_steps,
    "table":        _render_table,
    "tabs":          _render_tabs,
    "key_value":     _render_key_value,
    "before_after":   _render_before_after,
    "api_reference":  _render_api_reference,
    "timeline":       _render_timeline,
    "annotated_code": _render_annotated_code,
    "gallery":        _render_gallery,
    "video_pair":     _render_video_pair,
    "carousel":       _render_carousel,
}
