"""web-article renderer — block list → clean HTML.

Takes a list of typed block dicts (conforming to schema.yaml) and returns
a single HTML string ready to store in Firestore or any web CMS.

No markdown conversion. No Quill. No stripping surprises.
"""

from typing import List, Dict, Any
import re, base64, urllib.request, urllib.error, json as _json
from datetime import datetime, timezone


_DARK_OVERRIDES = """
<style>
  /* meet-stage dark theme overrides */
  body { background: transparent !important; color: #e8eaed !important; }
  h2, h3 { color: #00f2ff !important; }
  p, li, td, th, span { color: #e8eaed !important; }
  pre, code { background: #0d1117 !important; color: #cdd6f4 !important; }
  blockquote { border-color: #00f2ff !important; color: #9aa0a6 !important; }
  table { background: transparent !important; }
  th { background: rgba(0,242,255,0.1) !important; color: #00f2ff !important; border-color: rgba(255,255,255,0.1) !important; }
  td { background: transparent !important; color: #e8eaed !important; border-color: rgba(255,255,255,0.08) !important; }
  tr:nth-child(even) td { background: rgba(255,255,255,0.03) !important; }
  .tm-tabs { border-color: rgba(255,255,255,0.1) !important; }
  .tm-tab-labels { background: #0d1117 !important; border-color: rgba(255,255,255,0.08) !important; }
  .tm-tab-label { color: #9aa0a6 !important; border-color: rgba(255,255,255,0.06) !important; }
  .tm-tab-panels { background: #0d1117 !important; }
</style>
"""

def render(blocks: List[Dict[str, Any]], theme: str = "light") -> str:
    """Render a list of blocks to HTML.

    Args:
        blocks: List of block dicts conforming to atoms/schema.yaml
        theme: 'light' (default, web/blog) or 'dark' (meet-stage)
    """
    parts = []
    for block in blocks:
        btype = block.get("type")
        fn = _RENDERERS.get(btype)
        if fn:
            parts.append(fn(block))
        else:
            parts.append(f'<!-- unknown block type: {btype} -->')
    html = "\n\n".join(parts)
    if theme == "dark":
        html = _DARK_OVERRIDES + html
    return html


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


def _img_src(url: str) -> str:
    """Fetch an image URL and return a base64 data URI, falling back to the URL on error."""
    if not url or url.startswith("data:"):
        return url
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            mime = resp.headers.get_content_type() or "image/png"
            data = base64.b64encode(resp.read()).decode()
            return f"data:{mime};base64,{data}"
    except Exception:
        return url


def _render_image(b: dict) -> str:
    width = b.get("width", "100%")
    caption = f'<p style="font-size:0.8rem;opacity:0.6;margin-top:6px;text-align:center;">{b.get("caption","")}</p>' if b.get("caption") else ""
    src = _img_src(b["url"])
    return (
        f'<div style="margin:1.2rem 0;text-align:center;">'
        f'<img src="{src}" alt="{b.get("alt","")}" '
        f'style="width:{width};height:auto;border-radius:8px;display:block;margin:0 auto;"/>'
        f'{caption}</div>'
    )


def _render_image_pair(b: dict) -> str:
    def cell(side):
        caption = f'<p style="font-size:0.78rem;opacity:0.6;margin-top:6px;">{side.get("caption","")}</p>' if side.get("caption") else ""
        src = _img_src(side["url"])
        return (
            f'<td style="width:50%;padding:0 8px;vertical-align:top;text-align:center;">'
            f'<img src="{src}" alt="{side.get("alt","")}" '
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
    """Fetch repo metadata from GitHub API and render a self-contained card."""
    repo = b.get("repo", "")          # e.g. "curtiskrygier/a2ui-catalogue"
    label = b.get("label", "")        # optional override label
    description_override = b.get("description", "")

    # Defaults for fallback
    name = repo.split("/")[-1] if "/" in repo else repo
    description = description_override or ""
    stars = forks = 0
    language = ""
    updated = ""
    url = f"https://github.com/{repo}" if repo else b.get("url", "#")

    if repo:
        try:
            api_req = urllib.request.Request(
                f"https://api.github.com/repos/{repo}",
                headers={"User-Agent": "a2ui-renderer", "Accept": "application/vnd.github+json"}
            )
            with urllib.request.urlopen(api_req, timeout=8) as resp:
                data = _json.loads(resp.read())
                name        = data.get("name", name)
                description = description_override or data.get("description", "")
                stars       = data.get("stargazers_count", 0)
                forks       = data.get("forks_count", 0)
                language    = data.get("language", "")
                url         = data.get("html_url", url)
                pushed      = data.get("pushed_at", "")
                if pushed:
                    dt = datetime.fromisoformat(pushed.replace("Z", "+00:00"))
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
        f'<a href="{url}" target="_blank" rel="noopener" style="display:block;text-decoration:none;margin:0.8rem 0;">'
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


def _render_stat_card(b: dict) -> str:
    """Glowing neon stat card — large value with label and optional delta.

    Inspired by UIverse.io neon card patterns (uiverse.io).
    Credit: UIverse.io community — MIT License
    """
    value   = b.get("value", "—")
    label   = b.get("label", "")
    delta   = b.get("delta", "")
    accent  = b.get("accent", "#00f2ff")
    is_up   = b.get("is_up", True)
    delta_color = "#00ff88" if is_up else "#ff4444"
    delta_arrow = "▲" if is_up else "▼"
    delta_html = (
        f'<span style="font-size:0.85rem;font-weight:700;color:{delta_color};margin-left:10px;">'
        f'{delta_arrow} {delta}</span>'
    ) if delta else ""

    return (
        f'<div style="display:inline-block;background:linear-gradient(135deg,#0d1117 0%,#1a1f2e 100%);'
        f'border:1px solid {accent}44;border-radius:12px;padding:24px 32px;margin:1rem 0;'
        f'box-shadow:0 0 20px {accent}22,inset 0 0 20px {accent}08;min-width:200px;text-align:center;">'
        f'<div style="font-size:0.75rem;font-weight:700;color:{accent};letter-spacing:0.12em;'
        f'text-transform:uppercase;margin-bottom:8px;">{label}</div>'
        f'<div style="font-size:2.8rem;font-weight:900;color:#ffffff;line-height:1;font-family:monospace;">'
        f'{value}{delta_html}'
        f'</div>'
        f'</div>'
    )


def _render_progress_bar(b: dict) -> str:
    """Animated CSS progress bar with glow effect.

    Inspired by UIverse.io animated loader patterns (uiverse.io).
    Credit: UIverse.io community — MIT License
    """
    import hashlib
    pid     = "p" + hashlib.md5(b.get("label","").encode()).hexdigest()[:6]
    value   = min(100, max(0, int(b.get("value", 0))))
    label   = b.get("label", "")
    accent  = b.get("accent", "#00f2ff")
    show_pct = b.get("show_percent", True)
    caption = b.get("caption", "")

    pct_html = f'<span style="font-size:0.8rem;font-weight:700;color:{accent};">{value}%</span>' if show_pct else ""
    caption_html = f'<p style="font-size:0.78rem;opacity:0.5;margin-top:4px;">{caption}</p>' if caption else ""

    return (
        f'<style>'
        f'@keyframes {pid}-glow{{0%,100%{{box-shadow:0 0 6px {accent}88;}}50%{{box-shadow:0 0 16px {accent};}} }}'
        f'</style>'
        f'<div style="margin:1rem 0;">'
        f'<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">'
        f'<span style="font-size:0.85rem;font-weight:600;">{label}</span>'
        f'{pct_html}'
        f'</div>'
        f'<div style="background:rgba(255,255,255,0.08);border-radius:100px;height:10px;overflow:hidden;">'
        f'<div style="width:{value}%;height:100%;border-radius:100px;background:linear-gradient(90deg,{accent},{accent}99);'
        f'animation:{pid}-glow 2s ease-in-out infinite;transition:width 0.8s ease;"></div>'
        f'</div>'
        f'{caption_html}'
        f'</div>'
    )


def _render_badge_group(b: dict) -> str:
    """Group of status badges with optional pulse animation.

    Inspired by UIverse.io badge and chip patterns (uiverse.io).
    Credit: UIverse.io community — MIT License
    """
    badges  = b.get("badges", [])
    title   = b.get("title", "")
    title_html = f'<p style="font-size:0.82rem;font-weight:600;margin-bottom:8px;opacity:0.7;">{title}</p>' if title else ""

    COLOR_MAP = {
        "green":  ("#00ff88", "#003322"),
        "cyan":   ("#00f2ff", "#002233"),
        "blue":   ("#4285f4", "#001a44"),
        "yellow": ("#f9ab00", "#332200"),
        "red":    ("#ff4444", "#330011"),
        "purple": ("#a855f7", "#1a0033"),
        "grey":   ("#9aa0a6", "#1a1a1a"),
    }

    badges_html = []
    for badge in badges:
        text   = badge.get("text", "")
        color  = badge.get("color", "grey")
        pulse  = badge.get("pulse", False)
        fg, bg = COLOR_MAP.get(color, COLOR_MAP["grey"])

        import hashlib
        bid = "b" + hashlib.md5(text.encode()).hexdigest()[:5]
        pulse_css = (
            f'<style>@keyframes {bid}-p{{0%,100%{{box-shadow:0 0 0 0 {fg}66;}}70%{{box-shadow:0 0 0 6px transparent;}} }}</style>'
            f'<style>.{bid}{{animation:{bid}-p 1.5s infinite;}}</style>'
        ) if pulse else ""
        dot = f'<span style="width:7px;height:7px;border-radius:50%;background:{fg};display:inline-block;margin-right:6px;"></span>' if pulse else ""

        badges_html.append(
            f'{pulse_css}'
            f'<span class="{bid}" style="display:inline-flex;align-items:center;background:{bg};color:{fg};'
            f'border:1px solid {fg}44;border-radius:100px;padding:4px 12px;font-size:0.78rem;'
            f'font-weight:700;letter-spacing:0.04em;margin:3px;">'
            f'{dot}{text}</span>'
        )

    return (
        f'<div style="margin:1rem 0;">'
        f'{title_html}'
        f'<div style="display:flex;flex-wrap:wrap;gap:4px;">{"".join(badges_html)}</div>'
        f'</div>'
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


# ── Auto-generated stubs ─────────────────────────────────────────────────────

def _render_sparkline(b: dict) -> str:
    """TODO: Renders a small, simple line chart without axes or coordinates, showing general """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ sparkline ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_heatmap(b: dict) -> str:
    """TODO: Renders a graphical representation of data where individual values are represent"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ heatmap ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_donut_stat(b: dict) -> str:
    """TODO: Renders a single key metric with a surrounding donut chart indicating its propor"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ donut_stat ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_metric_delta(b: dict) -> str:
    """TODO: Renders a key performance indicator with its current value and a numerical or pe"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ metric_delta ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_trend_indicator(b: dict) -> str:
    """TODO: Renders a simple visual indicator (e.g., arrow, icon) representing the direction"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ trend_indicator ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_breadcrumb(b: dict) -> str:
    """TODO: A navigation aid indicating the user's current location within a hierarchical st"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ breadcrumb ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pagination(b: dict) -> str:
    """TODO: A control for navigating through a series of pages or results."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pagination ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_stepper(b: dict) -> str:
    """TODO: A component that displays progress through a sequence of logical and numbered st"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ stepper ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_tab_bar(b: dict) -> str:
    """TODO: A horizontal navigation component displaying a set of clickable tabs, typically """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ tab_bar ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_anchor_list(b: dict) -> str:
    """TODO: A list of links that navigate to specific sections within the current document o"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ anchor_list ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_faq_accordion(b: dict) -> str:
    """TODO: Renders a list of questions and answers, where answers are hidden until the ques"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ faq_accordion ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_glossary_term(b: dict) -> str:
    """TODO: Renders a term with its definition, often with an optional link for more details"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ glossary_term ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_footnote(b: dict) -> str:
    fid  = b.get("id", "1")
    text = b.get("text", "")
    return (f'<div style="margin:0.5rem 0;font-size:0.78rem;color:#6b7280;padding-left:1.2rem;'
            f'border-left:2px solid #e5e7eb;">'
            f'<sup style="color:#7c3aed;font-weight:600;">[{fid}]</sup> {text}'
            f'</div>')

def _render_footnote_group(b: dict) -> str:
    footnotes = b.get("footnotes", [])
    rows = "".join(
        f'<div style="margin:4px 0;font-size:0.78rem;color:#6b7280;padding-left:1.2rem;">'
        f'<sup style="color:#7c3aed;font-weight:600;">[{fn.get("id","?")}]</sup> {fn.get("text","")}'
        f'</div>'
        for fn in footnotes
    )
    return (f'<div style="margin:1.5rem 0;padding:12px 16px;border-top:1px solid #e5e7eb;">'
            f'<div style="font-size:0.72rem;font-weight:600;color:#9ca3af;text-transform:uppercase;'
            f'letter-spacing:0.05em;margin-bottom:8px;">Footnotes</div>'
            f'{rows}</div>')

def _render_blockquote_with_avatar(b: dict) -> str:
    """TODO: Renders a blockquote with an associated avatar and attribution."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ blockquote_with_avatar ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pull_stat(b: dict) -> str:
    """TODO: Renders a prominent, large statistic or number, often with a brief descriptive l"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pull_stat ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_accordion_item(b: dict) -> str:
    """TODO: Renders a single section of content that can be expanded or collapsed by clickin"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ accordion_item ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_tooltip(b: dict) -> str:
    text   = b.get("text", "")
    target = b.get("target", "hover me")
    return (f'<div style="margin:1rem 0;display:inline-block;position:relative;">'
            f'<span style="border-bottom:1px dashed #7c3aed;cursor:help;color:#7c3aed;">{target}</span>'
            f'<div style="margin-top:6px;padding:6px 10px;background:#1f2937;color:#f9fafb;'
            f'border-radius:6px;font-size:0.78rem;max-width:240px;line-height:1.4;">{text}</div>'
            f'</div>')

def _render_hover_card(b: dict) -> str:
    trigger  = b.get("trigger", "Hover")
    blocks   = b.get("blocks", [])
    content  = render(blocks) if blocks else ""
    return (f'<div style="margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">'
            f'<div style="padding:10px 14px;background:#f3f4f6;font-size:0.85rem;font-weight:600;'
            f'color:#374151;border-bottom:1px solid #e5e7eb;">{trigger}</div>'
            f'<div style="padding:12px 14px;font-size:0.85rem;">{content}</div>'
            f'</div>')

def _render_collapsible_panel(b: dict) -> str:
    title  = b.get("title", "Panel")
    blocks = b.get("blocks", [])
    content = render(blocks) if blocks else ""
    return (f'<details style="margin:1rem 0;border:1px solid #e5e7eb;border-radius:8px;overflow:hidden;">'
            f'<summary style="padding:10px 14px;background:#f3f4f6;font-weight:600;font-size:0.85rem;'
            f'color:#374151;cursor:pointer;list-style:none;">▶ {title}</summary>'
            f'<div style="padding:12px 14px;font-size:0.85rem;">{content}</div>'
            f'</details>')

def _render_css_modal(b: dict) -> str:
    trigger = b.get("trigger_text", "Open modal")
    blocks  = b.get("blocks", [])
    content = render(blocks) if blocks else ""
    return (f'<div style="margin:1rem 0;">'
            f'<button style="padding:8px 16px;background:#7c3aed;color:#fff;border:none;border-radius:6px;'
            f'font-size:0.85rem;cursor:pointer;">{trigger}</button>'
            f'<div style="margin-top:8px;padding:16px;border:1px solid #e5e7eb;border-radius:8px;'
            f'background:#fff;box-shadow:0 4px 12px rgba(0,0,0,0.08);font-size:0.85rem;">{content}</div>'
            f'</div>')

def _render_audio_player(b: dict) -> str:
    """TODO: Renders an embedded audio player for a given URL."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ audio_player ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_audio_link(b: dict) -> str:
    """TODO: Renders a clickable link to an audio file, often with an audio icon."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ audio_link ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pdf_preview(b: dict) -> str:
    """TODO: Renders an image thumbnail of a PDF document with a link to the full PDF."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pdf_preview ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_document_link(b: dict) -> str:
    """TODO: Renders a clickable link to a document (e.g., PDF, DOCX), often with a document """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ document_link ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_video_thumbnail(b: dict) -> str:
    """TODO: Renders a static image thumbnail for a video, with a play icon overlay and a lin"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ video_thumbnail ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_video_card(b: dict) -> str:
    """TODO: Renders a card with a video thumbnail, title, and description, linking to the vi"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ video_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_code_diff(b: dict) -> str:
    """TODO: Renders a side-by-side or inline comparison of two code blocks, highlighting add"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ code_diff ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_code_snippet_pair(b: dict) -> str:
    """TODO: Renders two distinct code snippets side-by-side or stacked, without diff highlig"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ code_snippet_pair ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_framed_screenshot(b: dict) -> str:
    """TODO: Renders an image within a decorative frame, simulating a device (e.g., browser, """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ framed_screenshot ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_image_with_caption(b: dict) -> str:
    """TODO: Renders a single image with a descriptive caption below it."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ image_with_caption ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_alert_banner(b: dict) -> str:
    """TODO: A prominent banner displaying a message, often with an icon and an optional acti"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ alert_banner ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_toast_notification(b: dict) -> str:
    """TODO: A small, temporary, non-intrusive message that appears and disappears automatica"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ toast_notification ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_loading_skeleton(b: dict) -> str:
    """TODO: A placeholder UI that shows the structure of content while it's loading, indicat"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ loading_skeleton ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_empty_state(b: dict) -> str:
    """TODO: A UI pattern displayed when there is no data to show, often with an image, messa"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ empty_state ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_spinner(b: dict) -> str:
    """TODO: A simple rotating animation indicating that content is loading or an operation i"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ spinner ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_status_pill(b: dict) -> str:
    """TODO: A small, colored label or "pill" used to display a concise status for an item."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ status_pill ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_inline_feedback_message(b: dict) -> str:
    """TODO: A small, contextual message displayed inline with content, often used for valida"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ inline_feedback_message ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_rating_stars(b: dict) -> str:
    """TODO: A visual component allowing users to rate an item using a series of stars, or di"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ rating_stars ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_progress_circle(b: dict) -> str:
    """TODO: A circular progress indicator, often with a percentage or value displayed in the"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ progress_circle ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_action_required_card(b: dict) -> str:
    """TODO: A card highlighting an important status or issue that requires immediate user at"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ action_required_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_feature_matrix(b: dict) -> str:
    """TODO: Renders a table comparing features across multiple products or versions."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ feature_matrix ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pricing_tier_card(b: dict) -> str:
    """TODO: Renders a single pricing plan with its name, price, key features, and an optiona"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pricing_tier_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pricing_tier_group(b: dict) -> str:
    """TODO: Renders a collection of pricing tier cards, typically for comparing different su"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pricing_tier_group ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_pros_cons_list(b: dict) -> str:
    """TODO: Renders a two-column list itemizing advantages and disadvantages for a single su"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ pros_cons_list ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_side_by_side_spec(b: dict) -> str:
    """TODO: Renders a detailed comparison of two items, displaying their attributes and valu"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ side_by_side_spec ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_product_spec_table(b: dict) -> str:
    """TODO: Renders a table detailing technical specifications or features for a single prod"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ product_spec_table ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_comparison_grid(b: dict) -> str:
    """TODO: Renders a grid comparing multiple products or services with features, often usin"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ comparison_grid ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_versus_block(b: dict) -> str:
    """TODO: Renders a block explicitly comparing two entities with a prominent "VS" separato"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ versus_block ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_rating_comparison(b: dict) -> str:
    """TODO: Renders a comparison of multiple items based on star ratings or numerical scores"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ rating_comparison ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_capability_checklist(b: dict) -> str:
    """TODO: Renders a list of capabilities, indicating which items possess each capability u"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ capability_checklist ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_toggle_switch(b: dict) -> str:
    """TODO: Renders a visual on/off switch."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ toggle_switch ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_expandable_text(b: dict) -> str:
    """TODO: Renders a block of text that can be expanded or collapsed to reveal more content"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ expandable_text ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_flip_card(b: dict) -> str:
    front = render(b.get("front_blocks", []))
    back  = render(b.get("back_blocks", []))
    return (f'<div style="margin:1rem 0;display:grid;grid-template-columns:1fr 1fr;gap:8px;">'
            f'<div style="padding:12px;border:2px solid #7c3aed;border-radius:8px;background:#faf5ff;">'
            f'<div style="font-size:0.7rem;font-weight:600;color:#7c3aed;margin-bottom:6px;text-transform:uppercase;">Front</div>'
            f'{front}</div>'
            f'<div style="padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#f9fafb;">'
            f'<div style="font-size:0.7rem;font-weight:600;color:#6b7280;margin-bottom:6px;text-transform:uppercase;">Back (flipped)</div>'
            f'{back}</div>'
            f'</div>')

def _render_image_hotspots(b: dict) -> str:
    """TODO: Renders an image with interactive points that display information on hover."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ image_hotspots ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_css_dropdown_menu(b: dict) -> str:
    """TODO: Renders a menu that appears when a trigger element is hovered or focused."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ css_dropdown_menu ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_star_rating_input(b: dict) -> str:
    """TODO: Renders an interactive star rating component for user input."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ star_rating_input ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_segmented_control(b: dict) -> str:
    """TODO: Renders a group of mutually exclusive buttons for selection, styled as a single """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ segmented_control ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_zoomable_image(b: dict) -> str:
    """TODO: Renders an image that magnifies when hovered over."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ zoomable_image ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_custom_checkbox_group(b: dict) -> str:
    """TODO: Renders a group of custom-styled checkboxes allowing multiple selections."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ custom_checkbox_group ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_css_slide_panel(b: dict) -> str:
    trigger = b.get("trigger_text", "Open panel")
    blocks  = b.get("blocks", [])
    content = render(blocks) if blocks else ""
    return (f'<div style="margin:1rem 0;display:flex;gap:12px;align-items:flex-start;">'
            f'<button style="padding:8px 14px;background:#374151;color:#fff;border:none;border-radius:6px;'
            f'font-size:0.82rem;cursor:pointer;white-space:nowrap;">{trigger} →</button>'
            f'<div style="flex:1;padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#fff;'
            f'border-left:3px solid #374151;font-size:0.85rem;">{content}</div>'
            f'</div>')

def _render_testimonial_card(b: dict) -> str:
    """TODO: Renders a single customer testimonial with text, author details, and an optional"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ testimonial_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_star_rating_display(b: dict) -> str:
    """TODO: Renders a visual representation of a star rating, optionally with a total review"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ star_rating_display ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_avatar_group(b: dict) -> str:
    """TODO: Renders a stack or row of small user avatars, often indicating a group or commun"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ avatar_group ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_contributor_list(b: dict) -> str:
    """TODO: Renders a list of individuals who have contributed to a project or community, wi"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ contributor_list ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_customer_logo_grid(b: dict) -> str:
    """TODO: Renders a grid or row of logos from featured customers or partners."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ customer_logo_grid ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_social_proof_banner(b: dict) -> str:
    """TODO: Renders a prominent banner highlighting a key social proof metric or achievement"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ social_proof_banner ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_media_mention_card(b: dict) -> str:
    """TODO: Renders a card showcasing a mention or feature in a media publication."""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ media_mention_card ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_expert_endorsement(b: dict) -> str:
    """TODO: Renders an endorsement from an industry expert, including their quote, name, and"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ expert_endorsement ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_review_callout(b: dict) -> str:
    """TODO: Renders a short, impactful quote from a customer review, often accompanied by a """
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ review_callout ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'

def _render_social_feed_embed(b: dict) -> str:
    """TODO: Renders an embedded snippet of a social media post, such as a tweet or Instagram"""
    label = b.get("label", b.get("title", b.get("name", "")))
    text  = b.get("text", b.get("content", b.get("value", "")))
    inner = (f"<strong>{label}</strong><br/>" if label else "") + (f"{text}" if text else f"<em style='color:#999;'>[ social_feed_embed ]</em>")
    return f'<div style="margin:1rem 0;padding:12px 16px;border:1px solid #e0e0e0;border-radius:8px;">{inner}</div>'


def _render_terminal_block(b: dict) -> str:
    shell   = b.get("shell", "bash")
    command = b.get("command", "").replace("<", "&lt;").replace(">", "&gt;")
    output  = b.get("output",  "").replace("<", "&lt;").replace(">", "&gt;")
    prompt  = {"zsh": "%", "powershell": "PS>", "cmd": ">"}.get(shell, "$")
    out_html = f'<div style="color:#9ca3af;white-space:pre-wrap;margin-top:8px;">{output}</div>' if output else ""
    return (
        f'<div style="background:#1e1e2e;border-radius:10px;overflow:hidden;margin:1.2rem 0;'
        f'font-family:\'JetBrains Mono\',monospace;font-size:0.82rem;">'
        f'<div style="background:#2a2a3e;padding:8px 14px;display:flex;align-items:center;gap:6px;">'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#ff5f56;display:inline-block;"></span>'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#ffbd2e;display:inline-block;"></span>'
        f'<span style="width:10px;height:10px;border-radius:50%;background:#27c93f;display:inline-block;"></span>'
        f'<span style="margin-left:8px;color:#9ca3af;font-size:0.75rem;">{shell}</span>'
        f'</div>'
        f'<div style="padding:14px 18px;">'
        f'<span style="color:#a78bfa;">{prompt}</span> '
        f'<span style="color:#e2e8f0;">{command}</span>'
        f'{out_html}</div></div>'
    )


def _render_file_tree(b: dict) -> str:
    def _node(item, depth=0):
        indent  = "  " * depth
        icon    = "📁 " if item.get("type") == "dir" else "📄 "
        name    = item.get("name", "")
        color   = "#60a5fa" if item.get("type") == "dir" else "#e2e8f0"
        html    = f'<div style="padding:1px 0;color:{color};font-size:0.82rem;">{indent}{icon}{name}</div>'
        for child in item.get("children", []):
            html += _node(child, depth + 1)
        return html
    nodes    = b.get("nodes", [])
    title    = b.get("title", "")
    title_html = f'<div style="font-size:0.78rem;color:#9ca3af;margin-bottom:8px;">{title}</div>' if title else ""
    inner    = "".join(_node(n) for n in nodes)
    return (
        f'<div style="background:#1e1e2e;border-radius:10px;padding:16px 20px;margin:1.2rem 0;'
        f'font-family:\'JetBrains Mono\',monospace;">'
        f'{title_html}{inner}</div>'
    )


def _render_tabbed_code(b: dict) -> str:
    tabs = b.get("tabs", [])
    if not tabs:
        return ""
    uid = abs(hash(str(tabs))) % 100000
    labels = "".join(
        f'<label for="tc-{uid}-{i}" style="padding:6px 14px;cursor:pointer;font-size:0.78rem;'
        f'font-weight:600;border-bottom:2px solid {"#7c3aed" if i==0 else "transparent"};'
        f'color:{"#7c3aed" if i==0 else "#9ca3af"};">{t.get("label", t.get("language","Tab"))}</label>'
        for i, t in enumerate(tabs)
    )
    panels = "".join(
        f'<div style="{"display:block" if i==0 else "display:none"}">'
        f'<pre style="margin:0;padding:16px;background:#1e1e2e;font-size:0.82rem;color:#e2e8f0;overflow:auto;">'
        f'<code>{t.get("code","").replace("<","&lt;").replace(">","&gt;")}</code></pre></div>'
        for i, t in enumerate(tabs)
    )
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">'
        f'<div style="display:flex;background:#f9fafb;border-bottom:1px solid #e5e7eb;gap:0;">{labels}</div>'
        f'{panels}</div>'
    )


def _render_http_request_block(b: dict) -> str:
    method  = b.get("method", "GET").upper()
    url     = b.get("url", "")
    headers = b.get("headers", {})
    body    = b.get("body", "")
    colors  = {"GET":"#2563eb","POST":"#16a34a","PUT":"#d97706","DELETE":"#dc2626","PATCH":"#7c3aed"}
    color   = colors.get(method, "#6b7280")
    hdrs_html = "".join(
        f'<div style="font-size:0.78rem;font-family:monospace;color:#374151;">'
        f'<span style="color:#6b7280;">{k}:</span> {v}</div>'
        for k, v in (headers or {}).items()
    )
    body_html = (
        f'<pre style="background:#f9fafb;border-radius:6px;padding:10px;margin-top:10px;'
        f'font-size:0.78rem;overflow:auto;color:#374151;">{body}</pre>'
    ) if body else ""
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">'
        f'<div style="padding:10px 16px;display:flex;align-items:center;gap:10px;background:#f9fafb;">'
        f'<span style="background:{color};color:#fff;font-weight:700;font-size:0.75rem;'
        f'padding:3px 10px;border-radius:5px;font-family:monospace;">{method}</span>'
        f'<span style="font-family:monospace;font-size:0.85rem;color:#374151;">{url}</span>'
        f'</div>'
        f'{"<div style=padding:10px 16px;>" + hdrs_html + "</div>" if hdrs_html else ""}'
        f'{body_html}</div>'
    )


def _render_env_var_list(b: dict) -> str:
    variables = b.get("variables", [])
    rows = "".join(
        f'<tr>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82rem;color:#7c3aed;'
        f'white-space:nowrap;border-bottom:1px solid #f3f4f6;">{v.get("key","")}</td>'
        f'<td style="padding:8px 12px;font-size:0.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">{v.get("description","")}</td>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#6b7280;border-bottom:1px solid #f3f4f6;">{v.get("default","—")}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">'
        f'{"<span style=color:#dc2626;font-size:0.72rem;font-weight:700;>required</span>" if v.get("required") else "<span style=color:#9ca3af;font-size:0.72rem;>optional</span>"}'
        f'</td></tr>'
        for v in variables
    )
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;">'
        f'<table style="width:100%;border-collapse:collapse;">'
        f'<thead><tr style="background:#f9fafb;">'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Variable</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Description</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Default</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Required</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def _render_prerequisite_checklist(b: dict) -> str:
    title = b.get("title", "Before you start")
    items = b.get("items", [])
    lis = "".join(
        f'<li style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:0.88rem;">'
        f'<span style="color:#16a34a;flex-shrink:0;margin-top:1px;">✓</span>'
        f'<span style="color:#374151;">{item}</span></li>'
        for item in items
    )
    return (
        f'<div style="border:1px solid #bbf7d0;border-radius:10px;padding:16px 20px;'
        f'background:#f0fdf4;margin:1.2rem 0;">'
        f'<div style="font-weight:700;color:#15803d;margin-bottom:10px;">{title}</div>'
        f'<ul style="list-style:none;padding:0;margin:0;">{lis}</ul></div>'
    )


def _render_keyboard_shortcut(b: dict) -> str:
    keys   = b.get("keys", [])
    action = b.get("action", "")
    key_html = " + ".join(
        f'<kbd style="display:inline-block;padding:2px 8px;font-family:monospace;font-size:0.8rem;'
        f'border:1px solid #d1d5db;border-bottom:3px solid #9ca3af;border-radius:4px;'
        f'background:#f9fafb;color:#374151;">{k}</kbd>'
        for k in keys
    )
    action_html = f'<span style="margin-left:10px;font-size:0.85rem;color:#6b7280;">{action}</span>' if action else ""
    return f'<div style="margin:0.5rem 0;display:inline-flex;align-items:center;">{key_html}{action_html}</div>'


def _render_api_param_table(b: dict) -> str:
    params = b.get("parameters", [])
    rows = "".join(
        f'<tr>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.82rem;color:#7c3aed;border-bottom:1px solid #f3f4f6;">{p.get("name","")}</td>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#2563eb;border-bottom:1px solid #f3f4f6;">{p.get("type","")}</td>'
        f'<td style="padding:8px 12px;border-bottom:1px solid #f3f4f6;">'
        f'{"<span style=color:#dc2626;font-size:0.72rem;font-weight:700;>required</span>" if p.get("required") else "<span style=color:#9ca3af;font-size:0.72rem;>optional</span>"}'
        f'</td>'
        f'<td style="padding:8px 12px;font-family:monospace;font-size:0.78rem;color:#6b7280;border-bottom:1px solid #f3f4f6;">{p.get("default","—")}</td>'
        f'<td style="padding:8px 12px;font-size:0.82rem;color:#374151;border-bottom:1px solid #f3f4f6;">{p.get("description","")}</td>'
        f'</tr>'
        for p in params
    )
    return (
        f'<div style="border:1px solid #e5e7eb;border-radius:10px;overflow:hidden;margin:1.2rem 0;overflow-x:auto;">'
        f'<table style="width:100%;border-collapse:collapse;min-width:600px;">'
        f'<thead><tr style="background:#f9fafb;">'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Parameter</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Type</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Required</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Default</th>'
        f'<th style="padding:8px 12px;text-align:left;font-size:0.75rem;color:#6b7280;text-transform:uppercase;letter-spacing:0.05em;">Description</th>'
        f'</tr></thead><tbody>{rows}</tbody></table></div>'
    )


def _render_reading_progress_bar(b):
    color = b.get("color", "#7c3aed")
    pct   = b.get("percentage", 45)
    return (f'<div style="margin:1rem 0;">'
            f'<div style="font-size:0.75rem;color:#6b7280;margin-bottom:4px;">Reading progress</div>'
            f'<div style="height:3px;background:#e5e7eb;border-radius:2px;">'
            f'<div style="height:100%;width:{pct}%;background:{color};border-radius:2px;"></div>'
            f'</div>'
            f'<div style="font-size:0.7rem;color:#9ca3af;margin-top:2px;">{pct}% complete — fixed to top of page while scrolling</div>'
            f'</div>')

def _render_table_of_contents(b):
    items = b.get("items", b.get("headings", []))
    rows = ""
    for item in items:
        text  = item.get("text", item.get("title", ""))
        level = item.get("level", 1)
        indent = "padding-left:1.2rem;" if level > 1 else ""
        rows += (f'<li style="margin:4px 0;{indent}">'
                 f'<a href="#" style="color:#7c3aed;text-decoration:none;font-size:{0.9 if level==1 else 0.85}rem;">'
                 f'{"└ " if level > 1 else ""}{text}</a></li>')
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;'
            f'background:#f9fafb;margin:1.5rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:10px;font-size:0.85rem;">Contents</div>'
            f'<ul style="list-style:none;padding:0;margin:0;">{rows}</ul></div>')

def _render_article_hero(b):
    title    = b.get("title", "")
    subtitle = b.get("subtitle", b.get("overline", ""))
    img_url  = b.get("image", b.get("image_url", ""))
    img_html = (f'<img src="{_img_src(img_url)}" alt="{title}" '
                f'style="width:100%;height:220px;object-fit:cover;border-radius:12px;margin-bottom:16px;display:block;">'
                if img_url else "")
    sub_html = (f'<p style="margin:0 0 4px;font-size:0.78rem;font-weight:600;color:#7c3aed;'
                f'text-transform:uppercase;letter-spacing:0.05em;">{subtitle}</p>'
                if subtitle else "")
    return (f'<div style="margin:1.5rem 0;">{img_html}{sub_html}'
            f'<h1 style="margin:0;font-size:2rem;font-weight:800;color:#111827;line-height:1.2;">{title}</h1>'
            f'</div>')

def _render_scroll_to_top(b):
    return (f'<div style="margin:1rem 0;display:flex;align-items:center;gap:10px;">'
            f'<button style="width:40px;height:40px;border-radius:50%;background:#7c3aed;color:#fff;'
            f'border:none;cursor:pointer;font-size:1rem;display:flex;align-items:center;justify-content:center;">'
            f'↑</button>'
            f'<span style="font-size:0.8rem;color:#6b7280;">Scroll-to-top button — appears fixed bottom-right after scrolling 300px</span>'
            f'</div>')

def _render_article_series_nav(b):
    title = b.get("title", "This series")
    prev  = b.get("prev", "")
    nxt   = b.get("next", "")
    url   = b.get("url", "#")
    nav = ""
    if prev:
        nav += f'<a href="#" style="color:#7c3aed;text-decoration:none;font-size:0.82rem;">← {prev}</a>'
    if prev and nxt:
        nav += '<span style="margin:0 8px;color:#d1d5db;">|</span>'
    if nxt:
        nav += f'<a href="#" style="color:#7c3aed;text-decoration:none;font-size:0.82rem;">{nxt} →</a>'
    return (f'<div style="border:1px solid #ede9fe;border-radius:10px;padding:14px 18px;'
            f'background:#faf5ff;margin:1.5rem 0;display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;">'
            f'<div style="font-weight:600;color:#7c3aed;font-size:0.85rem;">📚 <a href="{url}" style="color:#7c3aed;text-decoration:none;">{title}</a></div>'
            f'<div>{nav}</div>'
            f'</div>')

def _render_embed_codepen(b):
    pen_id = b.get("pen_id","")
    user = b.get("user_handle","")
    return (f'<p><iframe height="600" style="width:100%;border:1px solid #e5e7eb;border-radius:8px;'
            f'margin:1.2rem 0;" src="https://codepen.io/{user}/embed/{pen_id}?default-tab=result" '
            f'loading="lazy" allowtransparency="true" allowfullscreen="true"></iframe></p>')

def _render_embed_stackblitz(b):
    project_id = b.get("project_id","")
    return (f'<iframe src="https://stackblitz.com/edit/{project_id}?embed=1" '
            f'style="width:100%;height:500px;border:1px solid #e5e7eb;border-radius:8px;margin:1.2rem 0;" '
            f'loading="lazy"></iframe>')

def _render_embed_gist(b):
    gist_id = b.get("gist_id","")
    return (f'<script src="https://gist.github.com/{gist_id}.js"></script>')

def _render_embed_tweet(b):
    tweet_id = b.get("tweet_id","")
    return (f'<blockquote class="twitter-tweet" style="margin:1.2rem 0;"><a href="https://twitter.com/twitter/status/{tweet_id}"></a></blockquote>'
            f'<script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>')

def _render_embed_google_slides(b):
    pres_id = b.get("presentation_id","")
    return (f'<iframe src="https://docs.google.com/presentation/d/{pres_id}/embed" '
            f'frameborder="0" width="100%" height="569" allowfullscreen="true" mozallowfullscreen="true" '
            f'webkitallowfullscreen="true" style="border:1px solid #e5e7eb;border-radius:8px;margin:1.2rem 0;"></iframe>')

def _render_lottie_animation(b):
    url = b.get("src_url","")
    loop = b.get("loop",True)
    return (f'<script src="https://unpkg.com/@lottiefiles/lottie-player@latest/dist/lottie-player.js"></script>'
            f'<lottie-player src="{url}" background="transparent" speed="1" style="width:100%;max-height:400px;margin:1.2rem 0;" '
            f'{"loop" if loop else ""} autoplay></lottie-player>')

def _render_figma_embed(b):
    url = b.get("embed_url","")
    return (f'<iframe style="border:1px solid #e5e7eb;border-radius:8px;width:100%;height:500px;margin:1.2rem 0;" '
            f'src="{url}" allowfullscreen></iframe>')


def _render_difficulty_badge(b):
    level = b.get("level", "beginner")
    cfg = {"beginner": ("#16a34a","#f0fdf4","Beginner"), "intermediate": ("#d97706","#fffbeb","Intermediate"), "advanced": ("#dc2626","#fef2f2","Advanced")}
    color, bg, label = cfg.get(level, cfg["beginner"])
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;border:1px solid {color}44;'
            f'border-radius:100px;padding:3px 12px;font-size:0.75rem;font-weight:700;'
            f'color:{color};background:{bg};">{"⚡" if level=="beginner" else "🔧" if level=="intermediate" else "🚀"} {label}</span>')

def _render_caution_block(b):
    msg = b.get("message","")
    return (f'<div style="border:1px solid #fca5a5;border-left:4px solid #ef4444;border-radius:8px;'
            f'padding:14px 18px;background:#fef2f2;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#991b1b;margin-bottom:6px;">⚠ Caution</div>'
            f'<p style="margin:0;font-size:0.88rem;color:#7f1d1d;">{msg}</p></div>')

def _render_checklist_interactive(b):
    items = b.get("items", [])
    lis = "".join(
        f'<li style="display:flex;align-items:center;gap:10px;padding:6px 0;border-bottom:1px solid #f3f4f6;">'
        f'<input type="checkbox" style="width:16px;height:16px;accent-color:#7c3aed;cursor:pointer;">'
        f'<span style="font-size:0.88rem;color:#374151;">{item}</span></li>'
        for item in items
    )
    return (f'<ul style="list-style:none;padding:0;margin:1.2rem 0;'
            f'border:1px solid #e5e7eb;border-radius:10px;padding:12px 18px;">{lis}</ul>')

def _render_glossary_inline(b):
    term = b.get("term","")
    defn = b.get("definition","").replace('"','&quot;')
    return (f'<span style="position:relative;display:inline-block;">'
            f'<span style="border-bottom:2px dotted #7c3aed;cursor:help;color:#7c3aed;font-weight:600;" '
            f'title="{defn}">{term}</span></span>')

def _render_time_estimate(b):
    mins = b.get("minutes", 5)
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'font-size:0.78rem;color:#6b7280;background:#f3f4f6;'
            f'padding:3px 10px;border-radius:100px;">🕐 {mins} min read</span>')

def _render_progress_checkpoint(b):
    current = b.get("current_step", 1)
    total   = b.get("total_steps", 1)
    pct     = int(current / total * 100) if total else 0
    steps   = "".join(
        f'<div style="width:28px;height:28px;border-radius:50%;display:flex;align-items:center;'
        f'justify-content:center;font-size:0.75rem;font-weight:700;'
        f'background:{"#7c3aed" if i < current else "#e5e7eb"};'
        f'color:{"#fff" if i < current else "#9ca3af"};">{i}</div>'
        for i in range(1, total + 1)
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:14px 18px;margin:1.2rem 0;">'
            f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;flex-wrap:wrap;">{steps}</div>'
            f'<div style="background:#f3f4f6;border-radius:100px;height:6px;overflow:hidden;">'
            f'<div style="height:100%;background:#7c3aed;width:{pct}%;border-radius:100px;"></div>'
            f'</div>'
            f'<div style="font-size:0.78rem;color:#6b7280;margin-top:6px;">Step {current} of {total}</div>'
            f'</div>')

def _render_social_share_bar(b):
    platforms = b.get("platforms", ["twitter","linkedin"])
    url       = b.get("url", "")
    cfg = {
        "twitter":  ("#1da1f2", "X / Twitter", f"https://twitter.com/intent/tweet?url={url}"),
        "linkedin": ("#0a66c2", "LinkedIn",     f"https://www.linkedin.com/sharing/share-offsite/?url={url}"),
        "facebook": ("#1877f2", "Facebook",     f"https://www.facebook.com/sharer/sharer.php?u={url}"),
        "reddit":   ("#ff4500", "Reddit",       f"https://reddit.com/submit?url={url}"),
    }
    btns = "".join(
        f'<a href="{cfg[p][2]}" target="_blank" rel="noopener" '
        f'style="display:inline-flex;align-items:center;gap:6px;padding:7px 14px;border-radius:6px;'
        f'background:{cfg[p][0]};color:#fff;font-size:0.8rem;font-weight:600;text-decoration:none;">'
        f'{cfg[p][1]}</a>'
        for p in platforms if p in cfg
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1.2rem 0;">{btns}</div>'

def _render_newsletter_cta(b):
    headline    = b.get("headline", "Stay in the loop")
    button_label = b.get("button_label", "Subscribe")
    return (f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:24px 28px;'
            f'background:linear-gradient(135deg,#f9fafb,#f3f4f6);margin:1.5rem 0;text-align:center;">'
            f'<div style="font-size:1.1rem;font-weight:700;color:#111827;margin-bottom:8px;">{headline}</div>'
            f'<div style="display:flex;gap:8px;max-width:400px;margin:12px auto 0;">'
            f'<input type="email" placeholder="you@example.com" '
            f'style="flex:1;padding:8px 14px;border:1px solid #d1d5db;border-radius:6px;font-size:0.88rem;">'
            f'<button style="padding:8px 18px;background:#7c3aed;color:#fff;border:none;'
            f'border-radius:6px;font-weight:600;font-size:0.88rem;cursor:pointer;">{button_label}</button>'
            f'</div></div>')

def _render_author_bio_card(b):
    name   = b.get("name","")
    avatar = b.get("image", b.get("avatar_url", b.get("avatar","")))
    bio    = b.get("bio","")
    links  = b.get("links",{}) or {}
    avatar_html = (f'<img src="{_img_src(avatar)}" alt="{name}" '
                   f'style="width:56px;height:56px;border-radius:50%;object-fit:cover;flex-shrink:0;">'
                   if avatar else
                   f'<div style="width:56px;height:56px;border-radius:50%;background:#e5e7eb;'
                   f'display:flex;align-items:center;justify-content:center;font-size:1.4rem;flex-shrink:0;">👤</div>')
    links_html = "".join(
        f'<a href="{v}" target="_blank" rel="noopener" '
        f'style="font-size:0.78rem;color:#6b7280;text-decoration:none;margin-right:10px;">{k}</a>'
        for k, v in links.items()
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:18px 22px;'
            f'display:flex;gap:16px;align-items:flex-start;margin:1.5rem 0;">'
            f'{avatar_html}'
            f'<div><div style="font-weight:700;color:#111827;margin-bottom:4px;">{name}</div>'
            f'<p style="margin:0 0 8px;font-size:0.85rem;color:#6b7280;line-height:1.5;">{bio}</p>'
            f'{"<div>" + links_html + "</div>" if links_html else ""}'
            f'</div></div>')

def _render_related_posts_grid(b):
    posts = b.get("posts",[])
    cards = "".join(
        f'<a href="{p.get("url","#")}" style="display:block;border:1px solid #e5e7eb;border-radius:8px;'
        f'padding:14px 16px;text-decoration:none;transition:box-shadow 0.15s;" '
        f'onmouseover="this.style.boxShadow=\'0 2px 8px rgba(0,0,0,0.08)\'" '
        f'onmouseout="this.style.boxShadow=\'none\'">'
        f'{"<div style=font-size:0.7rem;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#7c3aed;margin-bottom:4px;>" + p.get("topic","") + "</div>" if p.get("topic") else ""}'
        f'<div style="font-size:0.88rem;font-weight:600;color:#111827;line-height:1.4;">{p.get("title","")}</div>'
        f'</a>'
        for p in posts
    )
    return (f'<div style="margin:1.5rem 0;">'
            f'<div style="font-size:0.78rem;font-weight:700;text-transform:uppercase;'
            f'letter-spacing:0.08em;color:#6b7280;margin-bottom:10px;">Related reading</div>'
            f'<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:10px;">'
            f'{cards}</div></div>')

def _render_series_overview_card(b):
    name  = b.get("series_name","")
    parts = b.get("parts",[])
    items = "".join(
        f'<a href="{p.get("url","#")}" style="display:flex;align-items:center;gap:10px;padding:8px 0;'
        f'border-bottom:1px solid #f3f4f6;text-decoration:none;">'
        f'<span style="width:22px;height:22px;border-radius:50%;display:flex;align-items:center;'
        f'justify-content:center;font-size:0.7rem;font-weight:700;flex-shrink:0;'
        f'background:{"#7c3aed" if p.get("current") else "#f3f4f6"};'
        f'color:{"#fff" if p.get("current") else "#6b7280"};">{i+1}</span>'
        f'<span style="font-size:0.85rem;{"font-weight:700;color:#7c3aed;" if p.get("current") else "color:#374151;"}">'
        f'{p.get("title","")}</span></a>'
        for i, p in enumerate(parts)
    )
    return (f'<div style="border:1px solid #ede9fe;border-radius:10px;padding:16px 20px;'
            f'background:#faf5ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#7c3aed;margin-bottom:10px;">📖 {name}</div>'
            f'{items}</div>')

def _render_reaction_group(b):
    emojis_cfg = {"thumbs_up":("👍","0"),"heart":("❤️","0"),"rocket":("🚀","0"),"mind_blown":("🤯","0")}
    enabled = b.get("enabled_emojis", list(emojis_cfg.keys()))
    btns = "".join(
        f'<button onclick="this.querySelector(\'span\').textContent=String(parseInt(this.querySelector(\'span\').textContent)+1)" '
        f'style="display:inline-flex;align-items:center;gap:4px;padding:6px 12px;border:1px solid #e5e7eb;'
        f'border-radius:100px;background:#f9fafb;cursor:pointer;font-size:0.88rem;">'
        f'{emojis_cfg[e][0]} <span style="font-size:0.78rem;color:#6b7280;">{emojis_cfg[e][1]}</span></button>'
        for e in enabled if e in emojis_cfg
    )
    return f'<div style="display:flex;flex-wrap:wrap;gap:8px;margin:1rem 0;">{btns}</div>'

def _render_share_quote(b):
    text   = b.get("text","")
    author = b.get("author","")
    tweet_text = f"{text[:200]} — {author}" if author else text[:200]
    return (f'<div style="border-left:4px solid #7c3aed;padding:16px 20px;background:#faf5ff;'
            f'border-radius:0 10px 10px 0;margin:1.5rem 0;position:relative;">'
            f'<p style="font-size:1rem;font-style:italic;color:#1e1b4b;line-height:1.6;margin:0 0 10px;">"{text}"</p>'
            f'{"<div style=font-size:0.8rem;color:#7c3aed;font-weight:600;>— " + author + "</div>" if author else ""}'
            f'<a href="https://twitter.com/intent/tweet?text={tweet_text.replace(" ","+")}" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:5px;font-size:0.75rem;color:#6b7280;'
            f'text-decoration:none;margin-top:8px;">Share this →</a></div>')

def _render_follow_cta(b):
    msg   = b.get("message","Follow for more")
    links = b.get("platform_links",{}) or {}
    btns  = "".join(
        f'<a href="{v}" target="_blank" rel="noopener" '
        f'style="padding:8px 18px;border:1px solid #d1d5db;border-radius:6px;font-size:0.85rem;'
        f'font-weight:600;color:#374151;text-decoration:none;">{k}</a>'
        for k, v in links.items()
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:12px;padding:20px 24px;'
            f'display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;'
            f'gap:12px;margin:1.5rem 0;background:#f9fafb;">'
            f'<span style="font-size:0.95rem;font-weight:600;color:#111827;">{msg}</span>'
            f'<div style="display:flex;gap:8px;flex-wrap:wrap;">{btns}</div></div>')

def _render_follow_button(b):
    handle   = b.get("target_handle","")
    platform = b.get("platform","twitter")
    urls = {"twitter": f"https://twitter.com/{handle}", "github": f"https://github.com/{handle}", "linkedin": f"https://linkedin.com/in/{handle}"}
    url = urls.get(platform, "#")
    return (f'<a href="{url}" target="_blank" rel="noopener" '
            f'style="display:inline-flex;align-items:center;gap:6px;padding:8px 18px;'
            f'border:1px solid #d1d5db;border-radius:6px;font-size:0.85rem;font-weight:600;'
            f'color:#374151;text-decoration:none;background:#f9fafb;">Follow @{handle}</a>')


def _render_version_badge(b):
    v = b.get("version","")
    status = b.get("status","stable")
    colors = {"stable":"#16a34a","beta":"#2563eb","alpha":"#d97706","rc":"#7c3aed"}
    c = colors.get(status,"#6b7280")
    return (f'<span style="display:inline-flex;align-items:center;gap:5px;border:1px solid {c};'
            f'border-radius:100px;padding:2px 10px;font-size:0.75rem;font-weight:700;color:{c};'
            f'font-family:monospace;">v{v}'
            f'{"<span style=opacity:0.7;font-weight:400;margin-left:2px;> · " + status + "</span>" if status != "stable" else ""}'
            f'</span>')

def _render_deprecation_notice(b):
    alt = b.get("alternative","")
    rv  = b.get("removal_version","")
    rv_html = f'<div style="margin-top:6px;font-size:0.8rem;color:#991b1b;">Removed in: <code>{rv}</code></div>' if rv else ""
    alt_html = f'<div style="margin-top:4px;font-size:0.85rem;">Use instead: <code style="background:#fef2f2;padding:1px 6px;border-radius:4px;">{alt}</code></div>' if alt else ""
    return (f'<div style="border:1px solid #fca5a5;border-left:4px solid #ef4444;border-radius:8px;'
            f'padding:14px 18px;background:#fef2f2;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#991b1b;margin-bottom:4px;">⚠ Deprecated</div>'
            f'{alt_html}{rv_html}</div>')

def _render_experimental_banner(b):
    msg = b.get("message","")
    return (f'<div style="border:1px solid #fbbf24;border-left:4px solid #f59e0b;border-radius:8px;'
            f'padding:14px 18px;background:#fffbeb;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#92400e;margin-bottom:4px;">🧪 Experimental</div>'
            f'{"<p style=font-size:0.85rem;color:#78350f;margin:0;>" + msg + "</p>" if msg else ""}</div>')

def _render_cli_command(b):
    cmd = b.get("command","").replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="display:flex;align-items:center;background:#1e1e2e;border-radius:8px;'
            f'padding:10px 16px;margin:0.8rem 0;font-family:\'JetBrains Mono\',monospace;font-size:0.85rem;">'
            f'<span style="color:#a78bfa;margin-right:10px;user-select:none;">$</span>'
            f'<code style="color:#e2e8f0;flex:1;">{cmd}</code></div>')

def _render_copy_code_button(b):
    text = b.get("text_to_copy","").replace('"','&quot;').replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="display:inline-block;margin:0.5rem 0;">'
            f'<button onclick="navigator.clipboard.writeText(\'{text}\')" '
            f'style="display:inline-flex;align-items:center;gap:6px;padding:6px 14px;'
            f'border:1px solid #d1d5db;border-radius:6px;background:#f9fafb;cursor:pointer;'
            f'font-size:0.82rem;color:#374151;">'
            f'<svg width="14" height="14" viewBox="0 0 16 16" fill="currentColor">'
            f'<path d="M0 6.75C0 5.784.784 5 1.75 5h1.5a.75.75 0 0 1 0 1.5h-1.5a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-1.5a.75.75 0 0 1 1.5 0v1.5A1.75 1.75 0 0 1 9.25 16h-7.5A1.75 1.75 0 0 1 0 14.25Z"/>'
            f'<path d="M5 1.75C5 .784 5.784 0 6.75 0h7.5C15.216 0 16 .784 16 1.75v7.5A1.75 1.75 0 0 1 14.25 11h-7.5A1.75 1.75 0 0 1 5 9.25Zm1.75-.25a.25.25 0 0 0-.25.25v7.5c0 .138.112.25.25.25h7.5a.25.25 0 0 0 .25-.25v-7.5a.25.25 0 0 0-.25-.25Z"/>'
            f'</svg>Copy</button></div>')

def _render_log_output(b):
    logs = b.get("logs","").replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="background:#0d1117;border-radius:8px;padding:14px 18px;margin:1.2rem 0;'
            f'max-height:300px;overflow-y:auto;">'
            f'<pre style="margin:0;font-family:\'JetBrains Mono\',monospace;font-size:0.78rem;'
            f'color:#9ca3af;white-space:pre-wrap;word-break:break-all;">{logs}</pre></div>')

def _render_json_tree_viewer(b):
    import json as _json2
    raw = b.get("data","")
    try:
        pretty = _json2.dumps(_json2.loads(raw), indent=2)
    except Exception:
        pretty = raw
    pretty = pretty.replace("<","&lt;").replace(">","&gt;")
    return (f'<div style="background:#1e1e2e;border-radius:10px;padding:16px;margin:1.2rem 0;'
            f'max-height:400px;overflow:auto;">'
            f'<pre style="margin:0;font-family:\'JetBrains Mono\',monospace;font-size:0.8rem;'
            f'color:#e2e8f0;">{pretty}</pre></div>')

def _render_key_takeaways(b):
    raw = b.get("items", b.get("points", []))
    points = [p.get("text", p) if isinstance(p, dict) else p for p in raw]
    lis = "".join(f'<li style="margin-bottom:6px;font-size:0.88rem;color:#1e3a5f;">{p}</li>' for p in points)
    return (f'<div style="border:1px solid #bfdbfe;border-left:4px solid #2563eb;border-radius:8px;'
            f'padding:16px 20px;background:#eff6ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#1d4ed8;margin-bottom:10px;">🔑 Key takeaways</div>'
            f'<ul style="margin:0;padding-left:1.2em;">{lis}</ul></div>')

def _render_summary_box(b):
    text = b.get("text","")
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px 22px;'
            f'background:#f9fafb;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:8px;font-size:0.82rem;'
            f'text-transform:uppercase;letter-spacing:0.08em;">Summary</div>'
            f'<p style="margin:0;color:#4b5563;font-size:0.9rem;line-height:1.6;">{text}</p></div>')

def _render_learning_objectives(b):
    objs = b.get("objectives",[])
    lis = "".join(
        f'<li style="display:flex;align-items:flex-start;gap:8px;margin-bottom:6px;font-size:0.88rem;">'
        f'<span style="color:#2563eb;flex-shrink:0;margin-top:1px;">→</span>'
        f'<span style="color:#1e3a5f;">{o}</span></li>'
        for o in objs
    )
    return (f'<div style="border:1px solid #bfdbfe;border-radius:10px;padding:16px 20px;'
            f'background:#eff6ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#1d4ed8;margin-bottom:10px;">🎯 What you\'ll learn</div>'
            f'<ul style="list-style:none;padding:0;margin:0;">{lis}</ul></div>')

def _render_changelog_entry(b):
    version = b.get("version","")
    date    = b.get("date","")
    changes = b.get("changes",[])
    tag_colors = {"added":"#16a34a","fixed":"#2563eb","changed":"#d97706","removed":"#dc2626","deprecated":"#7c3aed"}
    items_html = "".join(
        f'<div style="display:flex;gap:8px;align-items:flex-start;margin-bottom:4px;">'
        f'<span style="font-size:0.7rem;font-weight:700;padding:2px 6px;border-radius:4px;flex-shrink:0;'
        f'background:{tag_colors.get(str(c.get("type","changed")).lower(),"#6b7280")}22;'
        f'color:{tag_colors.get(str(c.get("type","changed")).lower(),"#6b7280")};">{c.get("type","changed").upper()}</span>'
        f'<span style="font-size:0.85rem;color:#374151;">{c.get("text","")}</span></div>'
        for c in changes
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">'
            f'<span style="font-family:monospace;font-weight:700;font-size:0.95rem;color:#374151;">v{version}</span>'
            f'{"<span style=font-size:0.8rem;color:#9ca3af;>" + date + "</span>" if date else ""}'
            f'</div>{items_html}</div>')

def _render_release_notes(b):
    title   = b.get("title","Release Notes")
    added   = b.get("added",[])
    fixed   = b.get("fixed",[])
    changed = b.get("changed",[])
    def section(label, items, color):
        if not items: return ""
        lis = "".join(f'<li style="font-size:0.85rem;color:#374151;margin-bottom:3px;">{i}</li>' for i in items)
        return (f'<div style="margin-bottom:14px;">'
                f'<div style="font-weight:700;font-size:0.78rem;text-transform:uppercase;'
                f'letter-spacing:0.08em;color:{color};margin-bottom:6px;">{label}</div>'
                f'<ul style="margin:0;padding-left:1.2em;">{lis}</ul></div>')
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:18px 22px;margin:1.2rem 0;">'
            f'<div style="font-weight:700;font-size:1rem;color:#111827;margin-bottom:14px;">{title}</div>'
            f'{section("Added", added, "#16a34a")}'
            f'{section("Fixed", fixed, "#2563eb")}'
            f'{section("Changed", changed, "#d97706")}'
            f'</div>')

def _render_further_reading(b):
    links = b.get("links",[])
    items = "".join(
        f'<a href="{l.get("url","#")}" target="_blank" rel="noopener" '
        f'style="display:flex;align-items:flex-start;gap:10px;padding:10px 0;'
        f'border-bottom:1px solid #f3f4f6;text-decoration:none;">'
        f'<span style="color:#2563eb;flex-shrink:0;margin-top:2px;">→</span>'
        f'<div><div style="font-size:0.88rem;font-weight:600;color:#1d4ed8;">{l.get("title","")}</div>'
        f'{"<div style=font-size:0.78rem;color:#6b7280;margin-top:2px;>" + l.get("annotation","") + "</div>" if l.get("annotation") else ""}'
        f'</div></a>'
        for l in links
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:4px;">📚 Further reading</div>'
            f'{items}</div>')

def _render_resources_list(b):
    items = b.get("items",[])
    rows = "".join(
        f'<a href="{i.get("url","#")}" target="_blank" rel="noopener" '
        f'style="display:flex;align-items:center;justify-content:space-between;padding:10px 0;'
        f'border-bottom:1px solid #f3f4f6;text-decoration:none;">'
        f'<span style="font-size:0.88rem;color:#1d4ed8;font-weight:500;">{i.get("title","")}</span>'
        f'<div style="display:flex;align-items:center;gap:8px;">'
        f'{"<span style=font-size:0.75rem;color:#9ca3af;>" + i.get("size","") + "</span>" if i.get("size") else ""}'
        f'{"<span style=font-size:0.72rem;background:#f3f4f6;padding:2px 6px;border-radius:4px;color:#6b7280;>" + i.get("type","").upper() + "</span>" if i.get("type") else ""}'
        f'</div></a>'
        for i in items
    )
    return (f'<div style="border:1px solid #e5e7eb;border-radius:10px;padding:16px 20px;margin:1.2rem 0;">'
            f'<div style="font-weight:700;color:#374151;margin-bottom:4px;">📎 Resources</div>'
            f'{rows}</div>')

def _render_sidebar_note(b):
    title   = b.get("title","Note")
    content = b.get("content","")
    return (f'<div style="border-left:3px solid #7c3aed;border-radius:0 8px 8px 0;padding:12px 16px;'
            f'background:#faf5ff;margin:1.2rem 0;">'
            f'<div style="font-weight:700;font-size:0.8rem;color:#7c3aed;margin-bottom:4px;">{title}</div>'
            f'<p style="margin:0;font-size:0.85rem;color:#4b5563;">{content}</p></div>')


def _render_color_swatch_grid(b: dict) -> str:
    colors = b.get("colors", [])
    items = "".join(
        f'<div style="display:flex;flex-direction:column;gap:4px;">'
        f'<div style="width:100%;height:40px;background:{c.get("hex","#e5e7eb")};border-radius:4px;"></div>'
        f'<div style="font-size:0.65rem;color:#6b7280;text-align:center;">{c.get("name","")}</div>'
        f'<div style="font-size:0.6rem;color:#9ca3af;text-align:center;font-family:monospace;">{c.get("hex","")}</div>'
        f'</div>'
        for c in colors
    )
    cols = min(len(colors), 6) if colors else 4
    return f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:8px;margin:1rem 0;">{items}</div>'

def _render_live_demo_embed(b: dict) -> str:
    url = b.get("url", "#")
    return f'<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#f9fafb;"><a href="{url}" target="_blank">Live Demo</a></div>'

def _render_benchmark_comparison(b: dict) -> str:
    return '<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;"><div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;"><div style="padding:8px;background:#f0f9ff;border-radius:4px;">Benchmark A: 95ms</div><div style="padding:8px;background:#f0fdf4;border-radius:4px;">Benchmark B: 120ms</div></div></div>'

def _render_chartjs_bar(b: dict) -> str:
    datasets = b.get("datasets", [])
    labels   = b.get("labels", [])
    if not datasets:
        return ""
    
    # Flatten datasets to find global max
    all_vals = []
    for ds in datasets:
        all_vals.extend(ds.get("data", []))
    if not all_vals:
        return ""
        
    mx = max(all_vals) or 1
    mn = min(all_vals)
    
    # SVG canvas coordinate dimensions
    w, h = 500, 200
    pad_l, pad_r, pad_t, pad_b = 60, 20, 30, 40
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b
    
    chart_id = f"bar_{id(b)}"
    
    # Y-axis ticks and horizontal grid lines
    grid_lines = ""
    for grid_idx in range(5):
        grid_y = pad_t + (grid_idx / 4) * chart_h
        grid_v = mx - (grid_idx / 4) * (mx - mn if mx != mn else mx)
        val_str = f"{grid_v:,.1f}" if grid_v % 1 != 0 else f"{grid_v:,.0f}"
        grid_lines += f"""
        <line x1="{pad_l}" y1="{grid_y}" x2="{pad_l + chart_w}" y2="{grid_y}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <text x="{pad_l - 10}" y="{grid_y + 3}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{val_str}</text>
        """
        
    # Draw bars and X axis labels
    num_labels = len(labels)
    num_series = len(datasets)
    
    colors = [
        {"fill": "#3b82f6", "stop": "#2563eb"}, # blue
        {"fill": "#10b981", "stop": "#059669"}, # emerald green
        {"fill": "#a855f7", "stop": "#7c3aed"}, # purple
        {"fill": "#f59e0b", "stop": "#d97706"}, # amber
    ]
    
    defs = []
    for di in range(num_series):
        color_set = colors[di % len(colors)]
        grad_id = f"bar_grad_{chart_id}_{di}"
        glow_id = f"bar_glow_{chart_id}_{di}"
        defs.append(f"""
        <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{color_set['fill']}" />
          <stop offset="100%" stop-color="{color_set['stop']}" stop-opacity="0.3" />
        </linearGradient>
        <filter id="{glow_id}" x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        """)
        
    bars_html = []
    x_labels = ""
    
    # Calculate group widths
    group_width_ratio = 0.7  # 70% of available slot
    slot_width = chart_w / (num_labels if num_labels > 0 else 1)
    bar_group_w = slot_width * group_width_ratio
    single_bar_w = bar_group_w / (num_series if num_series > 0 else 1)
    
    for i, lbl in enumerate(labels):
        group_x_start = pad_l + i * slot_width + (slot_width - bar_group_w) / 2
        
        # Add label text
        x_labels += f'<text x="{pad_l + i * slot_width + slot_width/2}" y="{pad_t + chart_h + 20}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="middle">{lbl}</text>'
        
        for di, ds in enumerate(datasets):
            data = ds.get("data", [])
            if i < len(data):
                val = data[i]
                bar_h = (val / mx) * chart_h if mx > 0 else 0
                bar_x = group_x_start + di * single_bar_w
                bar_y = pad_t + chart_h - bar_h
                
                grad_id = f"bar_grad_{chart_id}_{di}"
                glow_id = f"bar_glow_{chart_id}_{di}"
                
                # Draw rounded top bars using path or rect with rx
                bars_html.append(f"""
                <rect x="{bar_x}" y="{bar_y}" width="{max(2, single_bar_w - 2)}" height="{max(1, bar_h)}" fill="url(#{grad_id})" rx="3" ry="3" filter="url(#{glow_id})" />
                """)
                
    svg_defs = "\n".join(defs)
    bars_markup = "\n".join(bars_html)
    
    label = datasets[0].get("label", "") if datasets else ""
    label_html = f'<div style="font-size:0.75rem;font-weight:700;color:#94a3b8;margin-bottom:8px;font-family:monospace;letter-spacing:0.05em;text-transform:uppercase;">{label}</div>' if label else ""
    
    return f"""
    <div style="margin:1.5rem 0;padding:20px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {label_html}
      <div style="width:100%;height:200px;">
        <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
          <defs>
            {svg_defs}
          </defs>
          <!-- Grid & Y-Axes -->
          {grid_lines}
          <!-- X-Axes -->
          {x_labels}
          <!-- Bars -->
          {bars_markup}
        </svg>
      </div>
    </div>
    """

def _render_chartjs_line(b: dict) -> str:
    datasets = b.get("datasets", [])
    labels   = b.get("labels", [])
    if not datasets:
        return ""
    
    # Flatten data to get global min/max for scale matching across datasets
    all_vals = []
    for ds in datasets:
        all_vals.extend(ds.get("data", []))
    if not all_vals:
        return ""
        
    mn, mx = min(all_vals), max(all_vals)
    rng = (mx - mn) or 1
    
    # SVG canvas dimensions: 500x200
    w, h = 500, 200
    pad_l, pad_r, pad_t, pad_b = 60, 20, 30, 40
    chart_w = w - pad_l - pad_r
    chart_h = h - pad_t - pad_b
    
    chart_id = f"line_{id(b)}"
    
    # Draw horizontal grid lines (e.g., 4 intervals)
    grid_lines = ""
    for grid_idx in range(5):
        grid_y = pad_t + (grid_idx / 4) * chart_h
        grid_v = mx - (grid_idx / 4) * rng
        val_str = f"{grid_v:,.1f}" if grid_v % 1 != 0 else f"{grid_v:,.0f}"
        grid_lines += f"""
        <line x1="{pad_l}" y1="{grid_y}" x2="{pad_l + chart_w}" y2="{grid_y}" stroke="rgba(255,255,255,0.06)" stroke-dasharray="3,3" />
        <text x="{pad_l - 10}" y="{grid_y + 3}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{val_str}</text>
        """
        
    # Draw x-axis labels
    x_labels = ""
    n_labels = len(labels)
    if n_labels > 1:
        for i, lbl in enumerate(labels):
            # Only render some labels if there are too many (e.g., max 8 labels)
            if n_labels > 8 and i % (n_labels // 4) != 0 and i != n_labels - 1:
                continue
            x = pad_l + (i / (n_labels - 1)) * chart_w
            x_labels += f'<text x="{x}" y="{pad_t + chart_h + 20}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="middle">{lbl}</text>'
            
    # Draw paths for datasets
    colors = [
        {"stroke": "#3b82f6", "stop": "#3b82f6"}, # blue
        {"stroke": "#10b981", "stop": "#10b981"}, # emerald green
        {"stroke": "#a855f7", "stop": "#a855f7"}, # purple
        {"stroke": "#f59e0b", "stop": "#f59e0b"}, # amber
        {"stroke": "#ec4899", "stop": "#ec4899"}, # pink
    ]
    
    defs = []
    series_elements = []
    
    for di, ds in enumerate(datasets):
        vals = ds.get("data", [])
        if not vals:
            continue
        n = len(vals)
        coords = []
        for i, v in enumerate(vals):
            x = pad_l + (i / (n - 1) if n > 1 else 0.5) * chart_w
            y = pad_t + (1 - (v - mn) / rng) * chart_h
            coords.append((x, y))
            
        color_set = colors[di % len(colors)]
        stroke_color = color_set["stroke"]
        stop_color = color_set["stop"]
        
        grad_id = f"grad_{chart_id}_{di}"
        glow_id = f"glow_{chart_id}_{di}"
        
        defs.append(f"""
        <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{stop_color}" stop-opacity="0.22" />
          <stop offset="100%" stop-color="{stop_color}" stop-opacity="0.0" />
        </linearGradient>
        <filter id="{glow_id}" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
        """)
        
        path_pts = " ".join(f"{x},{y}" for x, y in coords)
        area_pts = f"{pad_l},{pad_t + chart_h} " + path_pts + f" {pad_l + chart_w},{pad_t + chart_h}"
        
        series_elements.append(f'<polygon points="{area_pts}" fill="url(#{grad_id})" />')
        series_elements.append(f'<polyline points="{path_pts}" fill="none" stroke="{stroke_color}" stroke-width="2.5" filter="url(#{glow_id})" stroke-linecap="round" stroke-linejoin="round" />')
        for x, y in coords:
            series_elements.append(f'<circle cx="{x}" cy="{y}" r="3.5" fill="#0f172a" stroke="{stroke_color}" stroke-width="2" />')
            
    svg_defs = "\n".join(defs)
    series_html = "\n".join(series_elements)
    
    label = datasets[0].get("label", "") if datasets else ""
    label_html = f'<div style="font-size:0.75rem;font-weight:700;color:#94a3b8;margin-bottom:8px;font-family:monospace;letter-spacing:0.05em;text-transform:uppercase;">{label}</div>' if label else ""
    
    return f"""
    <div style="margin:1.5rem 0;padding:20px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {label_html}
      <div style="width:100%;height:200px;">
        <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
          <defs>
            {svg_defs}
          </defs>
          <!-- Grid & Y-Axes -->
          {grid_lines}
          <!-- X-Axes -->
          {x_labels}
          <!-- Series -->
          {series_html}
        </svg>
      </div>
    </div>
    """

def _render_data_table_sortable(b: dict) -> str:
    return '<table style="width:100%;margin:1rem 0;border-collapse:collapse;"><thead><tr style="background:#f3f4f6;"><th style="padding:8px;text-align:left;border:1px solid #e5e7eb;">Header 1</th><th style="padding:8px;text-align:left;border:1px solid #e5e7eb;">Header 2</th></tr></thead><tbody><tr><td style="padding:8px;border:1px solid #e5e7eb;">Data 1</td><td style="padding:8px;border:1px solid #e5e7eb;">Data 2</td></tr></tbody></table>'

def _render_metric_comparison_card(b: dict) -> str:
    label    = b.get("label", "Metric")
    current  = b.get("value", 0)
    previous = b.get("previous", 0)
    try:
        pct = round((float(current) - float(previous)) / float(previous) * 100, 1) if previous else 0
        delta_color = "#059669" if pct <= 0 else "#dc2626"  # lower is better for response time etc
        delta_str = f"{'↓' if pct <= 0 else '↑'} {abs(pct)}%"
    except Exception:
        delta_str = ""
        delta_color = "#6b7280"
    return (f'<div style="margin:1rem 0;padding:14px;border:1px solid #e5e7eb;border-radius:8px;">'
            f'<div style="font-size:0.72rem;color:#6b7280;margin-bottom:8px;">{label}</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:12px;">'
            f'<div><div style="font-size:0.65rem;color:#9ca3af;">Now</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:#7c3aed;">{current}</div></div>'
            f'<div><div style="font-size:0.65rem;color:#9ca3af;">Before</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:#9ca3af;">{previous}</div></div>'
            f'</div>'
            f'<div style="margin-top:6px;font-size:0.72rem;color:{delta_color};font-weight:600;">{delta_str}</div>'
            f'</div>')

def _render_mini_sparkline_set(b: dict) -> str:
    series = b.get("series", [])
    cols = min(len(series), 4) if series else 2
    cards = []
    
    chart_id = f"spark_{id(b)}"
    
    for si, s in enumerate(series):
        label = s.get("label", "")
        data  = s.get("data", [])
        if not data: continue
        n = len(data); mn = min(data); mx = max(data); rng = (mx - mn) or 1
        
        # SVG dimensions: 150x40
        w, h = 150, 40
        pad_x, pad_y = 5, 5
        chart_w = w - 2 * pad_x
        chart_h = h - 2 * pad_y
        
        coords = []
        for i, v in enumerate(data):
            x = pad_x + (i / (n - 1) if n > 1 else 0.5) * chart_w
            y = pad_y + (1 - (v - mn) / rng) * chart_h
            coords.append((x, y))
            
        path_pts = " ".join(f"{x:.1f},{y:.1f}" for x, y in coords)
        area_pts = f"{pad_x},{pad_y + chart_h} " + path_pts + f" {pad_x + chart_w},{pad_y + chart_h}"
        
        latest = data[-1]
        
        # Color of sparkline
        colors = ["#a855f7", "#10b981", "#3b82f6", "#f59e0b"]
        stroke_color = colors[si % len(colors)]
        
        grad_id = f"spark_grad_{chart_id}_{si}"
        glow_id = f"spark_glow_{chart_id}_{si}"
        
        cards.append(f"""
        <div style="padding:16px;background:rgba(15,23,42,0.4);border:1px solid rgba(255,255,255,0.05);border-radius:10px;backdrop-filter:blur(8px);-webkit-backdrop-filter:blur(8px);display:flex;flex-direction:column;justify-content:space-between;gap:8px;">
          <div style="display:flex;justify-content:space-between;align-items:flex-start;">
            <span style="font-size:0.75rem;font-weight:600;color:#94a3b8;font-family:monospace;letter-spacing:0.02em;">{label}</span>
            <span style="font-size:1.1rem;font-weight:800;color:#f1f5f9;font-family:monospace;">{latest}</span>
          </div>
          <div style="width:100%;height:40px;">
            <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
              <defs>
                <linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stop-color="{stroke_color}" stop-opacity="0.25" />
                  <stop offset="100%" stop-color="{stroke_color}" stop-opacity="0.0" />
                </linearGradient>
                <filter id="{glow_id}" x="-10%" y="-10%" width="120%" height="120%">
                  <feGaussianBlur stdDeviation="1.5" result="blur" />
                  <feMerge>
                    <feMergeNode in="blur" />
                    <feMergeNode in="SourceGraphic" />
                  </feMerge>
                </filter>
              </defs>
              <polygon points="{area_pts}" fill="url(#{grad_id})" />
              <polyline points="{path_pts}" fill="none" stroke="{stroke_color}" stroke-width="2" filter="url(#{glow_id})" stroke-linecap="round" stroke-linejoin="round" />
              <circle cx="{coords[-1][0]}" cy="{coords[-1][1]}" r="3" fill="#0f172a" stroke="{stroke_color}" stroke-width="2" />
            </svg>
          </div>
        </div>
        """)
        
    return f'<div style="margin:1.5rem 0;display:grid;grid-template-columns:repeat({cols},1fr);gap:12px;">{"".join(cards)}</div>'

def _render_donut_stat(b: dict) -> str:
    value     = b.get("value", 0)
    max_value = b.get("max_value", 100) or 100
    label     = b.get("label", "")
    unit      = b.get("unit", "")
    color     = b.get("color", "#10b981")
    size      = b.get("size", "140px")
    
    percentage = (value / max_value) * 100
    percentage = min(100, max(0, percentage))
    
    r = 40
    stroke_dasharray = 251.327
    stroke_dashoffset = stroke_dasharray - (percentage / 100) * stroke_dasharray
    
    donut_id = f"donut_{id(b)}"
    
    svg_html = f"""
    <svg viewBox="0 0 100 100" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <linearGradient id="{donut_id}_grad" x1="0" y1="0" x2="1" y2="1">
          <stop offset="0%" stop-color="{color}" />
          <stop offset="100%" stop-color="{color}" stop-opacity="0.6" />
        </linearGradient>
        <filter id="{donut_id}_glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="3" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      <circle cx="50" cy="50" r="{r}" fill="none" stroke="rgba(255,255,255,0.06)" stroke-width="10" />
      <circle cx="50" cy="50" r="{r}" fill="none" stroke="url(#{donut_id}_grad)" stroke-width="10" 
              stroke-dasharray="{stroke_dasharray}" stroke-dashoffset="{stroke_dashoffset}"
              stroke-linecap="round" transform="rotate(-90 50 50)" filter="url(#{donut_id}_glow)" />
      <text x="50" y="48" fill="#f1f5f9" font-size="16" font-weight="800" font-family="monospace" text-anchor="middle">{value:,.0f}{unit}</text>
      <text x="50" y="64" fill="rgba(255,255,255,0.4)" font-size="7" font-weight="600" font-family="monospace" text-anchor="middle">{percentage:.1f}%</text>
    </svg>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:20px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);display:flex;align-items:center;gap:24px;">
      <div style="width:{size};height:{size};flex-shrink:0;">
        {svg_html}
      </div>
      <div>
        <div style="font-size:0.75rem;font-weight:700;color:#94a3b8;font-family:monospace;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:4px;">{label}</div>
        <div style="font-size:1.5rem;font-weight:800;color:#f1f5f9;font-family:-apple-system,sans-serif;margin-bottom:6px;">
          {value:,.0f}{unit} <span style="font-size:0.9rem;font-weight:400;color:rgba(255,255,255,0.4);">/ {max_value:,.0f}{unit}</span>
        </div>
        <div style="font-size:0.8rem;color:#10b981;font-weight:600;display:flex;align-items:center;gap:4px;">
          <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};"></span>
          Progress Status: {percentage:.1f}% Target Met
        </div>
      </div>
    </div>
    """

def _interpolate_color(c1: str, c2: str, weight: float) -> str:
    c1 = c1.lstrip("#")
    r1, g1, b1 = int(c1[0:2], 16), int(c1[2:4], 16), int(c1[4:6], 16)
    c2 = c2.lstrip("#")
    r2, g2, b2 = int(c2[0:2], 16), int(c2[2:4], 16), int(c2[4:6], 16)
    r = int(r1 + (r2 - r1) * weight)
    g = int(g1 + (g2 - g1) * weight)
    b = int(b1 + (b2 - b1) * weight)
    return f"#{r:02x}{g:02x}{b:02x}"

def _get_color_from_scale(scale: list[str], weight: float) -> str:
    if not scale:
        return "#10b981"
    if len(scale) == 1:
        return scale[0]
    weight = min(1.0, max(0.0, weight))
    num_segments = len(scale) - 1
    segment = int(weight * num_segments)
    if segment >= num_segments:
        segment = num_segments - 1
    segment_w = 1.0 / num_segments
    segment_percent = (weight - (segment * segment_w)) / segment_w
    return _interpolate_color(scale[segment], scale[segment+1], segment_percent)

def _render_heatmap(b: dict) -> str:
    data        = b.get("data", [])
    labels_x    = b.get("labels_x", [])
    labels_y    = b.get("labels_y", [])
    color_scale = b.get("color_scale", ["#1e293b", "#10b981"])
    unit        = b.get("unit", "")
    
    if not data or not data[0]:
        return ""
        
    num_rows = len(data)
    num_cols = len(data[0])
    
    flat_data = [val for row in data for val in row]
    mn, mx = min(flat_data), max(flat_data)
    rng = (mx - mn) or 1
    
    cell_size = 32
    cell_gap = 6
    
    pad_l, pad_r, pad_t, pad_b = 80, 20, 30, 20
    
    grid_w = num_cols * cell_size + (num_cols - 1) * cell_gap
    grid_h = num_rows * cell_size + (num_rows - 1) * cell_gap
    
    w = pad_l + grid_w + pad_r
    h = pad_t + grid_h + pad_b
    
    y_labels = ""
    for r_idx, lbl in enumerate(labels_y):
        if r_idx < num_rows:
            y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2 + 3
            y_labels += f'<text x="{pad_l - 12}" y="{y}" fill="rgba(255,255,255,0.4)" font-size="10" font-family="monospace" text-anchor="end">{lbl}</text>'
            
    x_labels = ""
    for c_idx, lbl in enumerate(labels_x):
        if c_idx < num_cols:
            x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
            x_labels += f'<text x="{x}" y="{pad_t - 10}" fill="rgba(255,255,255,0.4)" font-size="10" font-family="monospace" text-anchor="middle">{lbl}</text>'
            
    cells_html = []
    heatmap_id = f"heat_{id(b)}"
    
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            weight = (val - mn) / rng if rng > 0 else 0.5
            cell_color = _get_color_from_scale(color_scale, weight)
            
            x = pad_l + c_idx * (cell_size + cell_gap)
            y = pad_t + r_idx * (cell_size + cell_gap)
            
            glow_attr = ""
            if weight > 0.7:
                glow_attr = f'filter="url(#{heatmap_id}_glow)"'
                
            cells_html.append(f"""
            <rect x="{x}" y="{y}" width="{cell_size}" height="{cell_size}" fill="{cell_color}" rx="4" ry="4" {glow_attr}>
              <title>{val:,.1f}{unit}</title>
            </rect>
            """)
            
    svg_html = f"""
    <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
      <defs>
        <filter id="{heatmap_id}_glow" x="-20%" y="-20%" width="140%" height="140%">
          <feGaussianBlur stdDeviation="1.5" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {y_labels}
      {x_labels}
      {"".join(cells_html)}
    </svg>
    """
    
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{w}px;max-width:100%;height:{h}px;margin:0 auto;">
          {svg_html}
        </div>
      </div>
    </div>
    """

def _render_status_dashboard(b: dict) -> str:
    return '<div style="margin:1rem 0;display:grid;grid-template-columns:repeat(2,1fr);gap:8px;"><div style="padding:8px;border:1px solid #e5e7eb;border-radius:4px;"><span style="display:inline-block;width:8px;height:8px;background:#059669;border-radius:50%;margin-right:6px;"></span>API: Online</div><div style="padding:8px;border:1px solid #e5e7eb;border-radius:4px;"><span style="display:inline-block;width:8px;height:8px;background:#059669;border-radius:50%;margin-right:6px;"></span>DB: Online</div></div>'

def _render_uptime_timeline(b: dict) -> str:
    uptime = float(b.get("uptime", 99.9))
    days   = b.get("days", 30)
    import random, hashlib
    seed = int(hashlib.md5(str(uptime).encode()).hexdigest()[:8], 16)
    random.seed(seed)
    outage_rate = (100 - uptime) / 100
    blocks = []
    for _ in range(days):
        r = random.random()
        if r < outage_rate:
            color = "#dc2626"
        elif r < outage_rate * 3:
            color = "#f59e0b"
        else:
            color = "#059669"
        blocks.append(f'<div style="background:{color};height:20px;border-radius:2px;" title="{color}"></div>')
    return (f'<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;">'
            f'<div style="display:grid;grid-template-columns:repeat({days},1fr);gap:2px;">{"".join(blocks)}</div>'
            f'<div style="font-size:0.7rem;color:#6b7280;margin-top:6px;">{days}-day uptime: {uptime}%</div>'
            f'</div>')

def _render_command_palette(b: dict) -> str:
    return '<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;background:#1f2937;color:#e5e7eb;"><div style="font-size:0.75rem;margin-bottom:6px;">⌘K to open</div><div style="font-size:0.8rem;padding:6px;background:#111827;border-radius:4px;margin-bottom:4px;">▶ Command 1</div><div style="font-size:0.8rem;padding:6px;background:#374151;border-radius:4px;">Command 2</div></div>'

def _render_search_result_card(b: dict) -> str:
    return '<div style="margin:1rem 0;padding:12px;border:1px solid #e5e7eb;border-radius:8px;"><div style="font-weight:600;font-size:0.9rem;color:#7c3aed;margin-bottom:4px;">Result Title</div><div style="font-size:0.8rem;color:#6b7280;margin-bottom:6px;">Example result description with relevant content snippet.</div><div style="font-size:0.7rem;color:#9ca3af;">example.com › category › result</div></div>'

def _render_punch_card(b: dict) -> str:
    data        = b.get("data", [])
    labels_days = b.get("labels_days", ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"])
    color       = b.get("color", "#00f2ff")
    title       = b.get("title", "")
    subtitle    = b.get("subtitle", "")
    
    if not data or not data[0]:
        return ""
        
    num_rows = len(data)
    num_cols = len(data[0])
    
    flat_data = [float(val) for row in data for val in row]
    mn, mx = min(flat_data), max(flat_data)
    rng = (mx - mn) or 1
    
    cell_size = 28
    cell_gap = 5
    
    pad_l, pad_r, pad_t, pad_b = 60, 25, 40, 25
    
    grid_w = num_cols * cell_size + (num_cols - 1) * cell_gap
    grid_h = num_rows * cell_size + (num_rows - 1) * cell_gap
    
    w = pad_l + grid_w + pad_r
    h = pad_t + grid_h + pad_b
    
    x_labels = ""
    for c_idx in range(num_cols):
        x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
        lbl = f"{c_idx:02d}"
        x_labels += f'<text x="{x}" y="{pad_t - 12}" fill="rgba(255,255,255,0.4)" font-size="8" font-family="monospace" text-anchor="middle">{lbl}</text>'
        
    y_labels = ""
    for r_idx, lbl in enumerate(labels_days):
        if r_idx < num_rows:
            y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2 + 3
            y_labels += f'<text x="{pad_l - 12}" y="{y}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{lbl}</text>'
            
    bubbles_html = []
    punch_id = f"punch_{id(b)}"
    
    for r_idx, row in enumerate(data):
        for c_idx, val in enumerate(row):
            if val <= 0:
                x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
                y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2
                bubbles_html.append(f'<circle cx="{x}" cy="{y}" r="2" fill="rgba(255,255,255,0.06)" />')
                continue
                
            weight = (val - mn) / rng if rng > 0 else 0.5
            r = 3 + weight * 10
            x = pad_l + c_idx * (cell_size + cell_gap) + cell_size / 2
            y = pad_t + r_idx * (cell_size + cell_gap) + cell_size / 2
            
            opacity = 0.3 + weight * 0.7
            
            glow_attr = ""
            if weight > 0.6:
                glow_attr = f'filter="url(#{punch_id}_glow)"'
                
            bubbles_html.append(f"""
            <circle cx="{x}" cy="{y}" r="{r:.1f}" fill="{color}" fill-opacity="{opacity:.2f}" {glow_attr}>
              <title>{labels_days[r_idx]} {c_idx:02d}:00 - {val:,.0f} commits</title>
            </circle>
            """)
            
    svg_html = f"""
    <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
      <defs>
        <filter id="{punch_id}_glow" x="-30%" y="-30%" width="160%" height="140%">
          <feGaussianBlur stdDeviation="2" result="blur" />
          <feMerge>
            <feMergeNode in="blur" />
            <feMergeNode in="SourceGraphic" />
          </feMerge>
        </filter>
      </defs>
      {y_labels}
      {x_labels}
      {"".join(bubbles_html)}
    </svg>
    """
    
    header_html = ""
    if title or subtitle:
        header_html = f"""
        <div style="margin-bottom:16px;display:flex;justify-content:space-between;align-items:flex-end;">
          <div>
            {f'<div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;margin-bottom:2px;">{title}</div>' if title else ''}
            {f'<div style="font-size:0.75rem;color:rgba(255,255,255,0.4);font-family:monospace;">{subtitle}</div>' if subtitle else ''}
          </div>
          <div style="display:flex;gap:12px;font-size:0.75rem;color:rgba(255,255,255,0.4);font-family:monospace;align-items:center;">
            <span>Less</span>
            <span style="display:inline-block;width:6px;height:6px;border-radius:50%;background:{color};opacity:0.3;"></span>
            <span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:{color};opacity:0.6;"></span>
            <span style="display:inline-block;width:12px;height:12px;border-radius:50%;background:{color};opacity:1.0;"></span>
            <span>More</span>
          </div>
        </div>
        """
        
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{w}px;max-width:100%;height:{h}px;margin:0 auto;">
          {svg_html}
        </div>
      </div>
    </div>
    """

def _render_sankey_flow(b: dict) -> str:
    raw_nodes = b.get("nodes", [])
    raw_links = b.get("links", [])
    title     = b.get("title", "")
    
    if not raw_links:
        return ""
        
    nodes_map = {n["id"]: n for n in raw_nodes}
    
    for link in raw_links:
        s, t = link["source"], link["target"]
        if s not in nodes_map:
            nodes_map[s] = {"id": s, "label": s.capitalize(), "column": 0}
        if t not in nodes_map:
            nodes_map[t] = {"id": t, "label": t.capitalize(), "column": 1}
            
    left_nodes = []
    right_nodes = []
    
    node_out_totals = {}
    node_in_totals = {}
    for link in raw_links:
        s, t, v = link["source"], link["target"], float(link.get("value", 1))
        node_out_totals[s] = node_out_totals.get(s, 0.0) + v
        node_in_totals[t] = node_in_totals.get(t, 0.0) + v
        
    for nid, node in nodes_map.items():
        col = node.get("column", 0)
        if "column" not in node:
            if nid in node_out_totals:
                col = 0
            else:
                col = 1
                
        node_item = {
            "id": nid,
            "label": node.get("label", nid),
            "color": node.get("color", "#38bdf8" if col == 0 else "#10b981"),
            "total_out": node_out_totals.get(nid, 0.0),
            "total_in": node_in_totals.get(nid, 0.0),
        }
        node_item["total"] = max(node_item["total_out"], node_item["total_in"], 1.0)
        
        if col == 0:
            left_nodes.append(node_item)
        else:
            right_nodes.append(node_item)
            
    left_nodes.sort(key=lambda x: x["total"], reverse=True)
    right_nodes.sort(key=lambda x: x["total"], reverse=True)
    
    w, h = 640, 340
    pad_l, pad_r, pad_t, pad_b = 60, 60, 50, 40
    usable_h = h - pad_t - pad_b
    
    x_left = pad_l
    node_w = 16
    x_right = w - pad_r - node_w
    
    gap_l = 16
    total_gaps_l = (len(left_nodes) - 1) * gap_l if len(left_nodes) > 1 else 0
    avail_h_l = max(usable_h - total_gaps_l, 100)
    sum_left_totals = sum(n["total"] for n in left_nodes) or 1.0
    scale_l = avail_h_l / sum_left_totals
    
    y = pad_t
    left_positions = {}
    for n in left_nodes:
        n_h = max(n["total"] * scale_l, 10.0)
        left_positions[n["id"]] = {
            "x": x_left,
            "y": y,
            "w": node_w,
            "h": n_h,
            "color": n["color"],
            "label": n["label"],
            "total": n["total"],
            "curr_offset": 0.0,
            "scale": scale_l,
        }
        y += n_h + gap_l
        
    gap_r = 16
    total_gaps_r = (len(right_nodes) - 1) * gap_r if len(right_nodes) > 1 else 0
    avail_h_r = max(usable_h - total_gaps_r, 100)
    sum_right_totals = sum(n["total"] for n in right_nodes) or 1.0
    scale_r = avail_h_r / sum_right_totals
    
    y = pad_t
    right_positions = {}
    for n in right_nodes:
        n_h = max(n["total"] * scale_r, 10.0)
        right_positions[n["id"]] = {
            "x": x_right,
            "y": y,
            "w": node_w,
            "h": n_h,
            "color": n["color"],
            "label": n["label"],
            "total": n["total"],
            "curr_offset": 0.0,
            "scale": scale_r,
        }
        y += n_h + gap_r
        
    gradients_html = []
    links_html = []
    
    sankey_id = f"sankey_{id(b)}"
    
    for idx, link in enumerate(raw_links):
        s, t, v = link["source"], link["target"], float(link.get("value", 1))
        
        if s not in left_positions or t not in right_positions:
            continue
            
        lp = left_positions[s]
        rp = right_positions[t]
        
        link_h_l = v * lp["scale"]
        link_h_r = rp["scale"] * v if rp["total"] > 0 else rp["scale"] * v
        # Ensure we don't scale by RP if total sum doesn't match
        link_h_r = v * rp["scale"]
        
        y_l = lp["y"] + lp["curr_offset"]
        y_r = rp["y"] + rp["curr_offset"]
        
        lp["curr_offset"] += link_h_l
        rp["curr_offset"] += link_h_r
        
        x0 = lp["x"] + lp["w"]
        x1 = rp["x"]
        dx = (x1 - x0) / 2
        
        top_curve = f"C {x0 + dx} {y_l}, {x1 - dx} {y_r}, {x1} {y_r}"
        bot_curve = f"C {x1 - dx} {y_r + link_h_r}, {x0 + dx} {y_l + link_h_l}, {x0} {y_l + link_h_l}"
        
        path_data = f"M {x0} {y_l} {top_curve} L {x1} {y_r + link_h_r} {bot_curve} Z"
        
        grad_id = f"{sankey_id}_grad_{idx}"
        link_color = link.get("color")
        
        if link_color:
            fill_val = link_color
            opacity = 0.35
        else:
            gradients_html.append(f"""
            <linearGradient id="{grad_id}" x1="0" y1="0" x2="1" y2="0">
              <stop offset="0%" stop-color="{lp['color']}" stop-opacity="0.3" />
              <stop offset="100%" stop-color="{rp['color']}" stop-opacity="0.3" />
            </linearGradient>
            """)
            fill_val = f"url(#{grad_id})"
            opacity = 1.0
            
        links_html.append(f"""
        <path d="{path_data}" fill="{fill_val}" opacity="{opacity}" style="transition: opacity 0.2s;" onmouseover="this.setAttribute('opacity', '0.65')" onmouseout="this.setAttribute('opacity', '{opacity}')">
          <title>{lp['label']} → {rp['label']}: {v:,.0f}</title>
        </path>
        """)
        
    nodes_html = []
    labels_html = []
    
    for nid, lp in left_positions.items():
        node_glow_id = f"{sankey_id}_node_glow_{nid}"
        gradients_html.append(f"""
        <linearGradient id="{node_glow_id}_grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{lp['color']}" />
          <stop offset="100%" stop-color="{lp['color']}" stop-opacity="0.6" />
        </linearGradient>
        """)
        
        nodes_html.append(f"""
        <rect x="{lp['x']}" y="{lp['y']}" width="{lp['w']}" height="{lp['h']}" fill="url(#{node_glow_id}_grad)" rx="3" ry="3" />
        """)
        
        labels_html.append(f"""
        <text x="{lp['x'] - 8}" y="{lp['y'] + lp['h']/2 + 4}" fill="#f1f5f9" font-size="11" font-weight="700" font-family="monospace" text-anchor="end">{lp['label']}</text>
        <text x="{lp['x'] - 8}" y="{lp['y'] + lp['h']/2 + 15}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="end">{lp['total']:,.0f}</text>
        """)
        
    for nid, rp in right_positions.items():
        node_glow_id = f"{sankey_id}_node_glow_{nid}"
        gradients_html.append(f"""
        <linearGradient id="{node_glow_id}_grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="{rp['color']}" />
          <stop offset="100%" stop-color="{rp['color']}" stop-opacity="0.6" />
        </linearGradient>
        """)
        
        nodes_html.append(f"""
        <rect x="{rp['x']}" y="{rp['y']}" width="{rp['w']}" height="{rp['h']}" fill="url(#{node_glow_id}_grad)" rx="3" ry="3" />
        """)
        
        labels_html.append(f"""
        <text x="{rp['x'] + rp['w'] + 8}" y="{rp['y'] + rp['h']/2 + 4}" fill="#f1f5f9" font-size="11" font-weight="700" font-family="monospace" text-anchor="start">{rp['label']}</text>
        <text x="{rp['x'] + rp['w'] + 8}" y="{rp['y'] + rp['h']/2 + 15}" fill="rgba(255,255,255,0.4)" font-size="9" font-family="monospace" text-anchor="start">{rp['total']:,.0f}</text>
        """)
        
    svg_html = f"""
    <svg viewBox="0 0 {w} {h}" width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" style="overflow:visible;">
      <defs>
        {"".join(gradients_html)}
      </defs>
      {"".join(links_html)}
      {"".join(nodes_html)}
      {"".join(labels_html)}
    </svg>
    """
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:16px;">
          <div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px;">{title}</div>
        </div>
        """
        
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{w}px;max-width:100%;height:{h}px;margin:0 auto;">
          {svg_html}
        </div>
      </div>
    </div>
    """

def _render_cohort_retention(b: dict) -> str:
    cohorts     = b.get("cohorts", [])
    periods     = b.get("periods", [])
    color_scale = b.get("color_scale", ["#1e293b", "#10b981"])
    title       = b.get("title", "")
    
    if not cohorts or not periods:
        return ""
        
    num_periods = len(periods)
    
    headers = []
    headers.append('<div style="font-weight:700;color:rgba(255,255,255,0.4);font-size:0.75rem;font-family:monospace;text-transform:uppercase;padding:12px;letter-spacing:0.05em;">Cohort</div>')
    headers.append('<div style="font-weight:700;color:rgba(255,255,255,0.4);font-size:0.75rem;font-family:monospace;text-transform:uppercase;padding:12px;letter-spacing:0.05em;text-align:right;">Size</div>')
    for p in periods:
        headers.append(f'<div style="font-weight:700;color:rgba(255,255,255,0.4);font-size:0.75rem;font-family:monospace;text-transform:uppercase;padding:12px;letter-spacing:0.05em;text-align:center;">{p}</div>')
        
    rows_html = []
    for row_idx, cohort in enumerate(cohorts):
        name = cohort.get("cohort_name", f"Cohort {row_idx}")
        size = cohort.get("original_size", "—")
        if isinstance(size, (int, float)):
            size_str = f"{size:,.0f}"
        else:
            size_str = str(size)
            
        rates = cohort.get("retention_rates", [])
        
        row_cells = []
        row_cells.append(f'<div style="font-weight:700;color:#f1f5f9;font-size:0.85rem;padding:12px;border-bottom:1px solid rgba(255,255,255,0.04);display:flex;align-items:center;">{name}</div>')
        row_cells.append(f'<div style="color:rgba(255,255,255,0.6);font-size:0.85rem;font-family:monospace;padding:12px;border-bottom:1px solid rgba(255,255,255,0.04);text-align:right;display:flex;align-items:center;justify-content:flex-end;">{size_str}</div>')
        
        for p_idx in range(num_periods):
            if p_idx < len(rates):
                rate = float(rates[p_idx])
                weight = rate / 100.0
                cell_bg = _get_color_from_scale(color_scale, weight)
                
                text_color = "#f1f5f9"
                if weight > 0.65:
                    text_color = "#0f172a"
                    
                cell_style = (
                    f"background:{cell_bg};"
                    f"color:{text_color};"
                    f"font-weight:700;"
                    f"font-size:0.8rem;"
                    f"font-family:monospace;"
                    f"text-align:center;"
                    f"margin:2px;"
                    f"border-radius:4px;"
                    f"display:flex;"
                    f"align-items:center;"
                    f"justify-content:center;"
                    f"transition:transform 0.15s, box-shadow 0.15s;"
                )
                
                row_cells.append(f"""
                <div style="{cell_style}" onmouseover="this.style.transform='scale(1.05)';this.style.boxShadow='0 4px 12px rgba(0,0,0,0.3)';" onmouseout="this.style.transform='scale(1)';this.style.boxShadow='none';">
                  {rate:.1f}%
                </div>
                """)
            else:
                row_cells.append('<div style="background:transparent;margin:2px;"></div>')
                
        rows_html.append("".join(row_cells))
        
    grid_cols_style = f"grid-template-columns: 140px 100px repeat({num_periods}, 1fr);"
    
    header_html = ""
    if title:
        header_html = f"""
        <div style="margin-bottom:16px;">
          <div style="font-size:1.1rem;font-weight:800;color:#f1f5f9;letter-spacing:-0.2px;">{title}</div>
        </div>
        """
        
    return f"""
    <div style="margin:1.5rem 0;padding:24px;background:rgba(15,23,42,0.6);border:1px solid rgba(255,255,255,0.06);border-radius:12px;backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);">
      {header_html}
      <div style="width:100%;overflow-x:auto;">
        <div style="min-width:{240 + num_periods * 80}px;max-width:100%;display:grid;{grid_cols_style};background:rgba(15,23,42,0.3);border-radius:8px;padding:8px;gap:2px;">
          {"".join(headers)}
          {"".join(rows_html)}
        </div>
      </div>
    </div>
    """


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
    "repo_links":              _render_repo_links,
    "github_repo_card":        _render_github_repo_card,
    "terminal_block":          _render_terminal_block,
    "file_tree":               _render_file_tree,
    "tabbed_code":             _render_tabbed_code,
    "http_request_block":      _render_http_request_block,
    "env_var_list":            _render_env_var_list,
    "prerequisite_checklist":  _render_prerequisite_checklist,
    "keyboard_shortcut":       _render_keyboard_shortcut,
    "api_param_table":         _render_api_param_table,
    "version_badge":           _render_version_badge,
    "deprecation_notice":      _render_deprecation_notice,
    "experimental_banner":     _render_experimental_banner,
    "cli_command":             _render_cli_command,
    "copy_code_button":        _render_copy_code_button,
    "log_output":              _render_log_output,
    "json_tree_viewer":        _render_json_tree_viewer,
    "key_takeaways":           _render_key_takeaways,
    "summary_box":             _render_summary_box,
    "learning_objectives":     _render_learning_objectives,
    "changelog_entry":         _render_changelog_entry,
    "release_notes":           _render_release_notes,
    "further_reading":         _render_further_reading,
    "resources_list":          _render_resources_list,
    "sidebar_note":            _render_sidebar_note,
    "difficulty_badge":        _render_difficulty_badge,
    "caution_block":           _render_caution_block,
    "checklist_interactive":   _render_checklist_interactive,
    "glossary_inline":         _render_glossary_inline,
    "time_estimate":           _render_time_estimate,
    "progress_checkpoint":     _render_progress_checkpoint,
    "social_share_bar":        _render_social_share_bar,
    "newsletter_cta":          _render_newsletter_cta,
    "author_bio_card":         _render_author_bio_card,
    "related_posts_grid":      _render_related_posts_grid,
    "series_overview_card":    _render_series_overview_card,
    "reaction_group":          _render_reaction_group,
    "share_quote":             _render_share_quote,
    "follow_cta":              _render_follow_cta,
    "follow_button":           _render_follow_button,
    "reading_progress_bar":    _render_reading_progress_bar,
    "table_of_contents":       _render_table_of_contents,
    "article_hero":            _render_article_hero,
    "scroll_to_top":           _render_scroll_to_top,
    "article_series_nav":      _render_article_series_nav,
    "embed_codepen":           _render_embed_codepen,
    "embed_stackblitz":        _render_embed_stackblitz,
    "embed_gist":              _render_embed_gist,
    "embed_tweet":             _render_embed_tweet,
    "embed_google_slides":     _render_embed_google_slides,
    "lottie_animation":        _render_lottie_animation,
    "figma_embed":             _render_figma_embed,
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
    "stat_card":      _render_stat_card,
    "progress_bar":   _render_progress_bar,
    "badge_group":    _render_badge_group,
    "sparkline": _render_sparkline,
    "heatmap": _render_heatmap,
    "donut_stat": _render_donut_stat,
    "metric_delta": _render_metric_delta,
    "trend_indicator": _render_trend_indicator,
    "breadcrumb": _render_breadcrumb,
    "pagination": _render_pagination,
    "stepper": _render_stepper,
    "tab_bar": _render_tab_bar,
    "anchor_list": _render_anchor_list,
    "faq_accordion": _render_faq_accordion,
    "glossary_term": _render_glossary_term,
    "footnote": _render_footnote,
    "blockquote_with_avatar": _render_blockquote_with_avatar,
    "pull_stat": _render_pull_stat,
    "accordion_item": _render_accordion_item,
    "tooltip": _render_tooltip,
    "hover_card": _render_hover_card,
    "collapsible_panel": _render_collapsible_panel,
    "css_modal": _render_css_modal,
    "audio_player": _render_audio_player,
    "audio_link": _render_audio_link,
    "pdf_preview": _render_pdf_preview,
    "document_link": _render_document_link,
    "video_thumbnail": _render_video_thumbnail,
    "video_card": _render_video_card,
    "code_diff": _render_code_diff,
    "code_snippet_pair": _render_code_snippet_pair,
    "framed_screenshot": _render_framed_screenshot,
    "image_with_caption": _render_image_with_caption,
    "alert_banner": _render_alert_banner,
    "toast_notification": _render_toast_notification,
    "loading_skeleton": _render_loading_skeleton,
    "empty_state": _render_empty_state,
    "spinner": _render_spinner,
    "status_pill": _render_status_pill,
    "inline_feedback_message": _render_inline_feedback_message,
    "rating_stars": _render_rating_stars,
    "progress_circle": _render_progress_circle,
    "action_required_card": _render_action_required_card,
    "feature_matrix": _render_feature_matrix,
    "pricing_tier_card": _render_pricing_tier_card,
    "pricing_tier_group": _render_pricing_tier_group,
    "pros_cons_list": _render_pros_cons_list,
    "side_by_side_spec": _render_side_by_side_spec,
    "product_spec_table": _render_product_spec_table,
    "comparison_grid": _render_comparison_grid,
    "versus_block": _render_versus_block,
    "rating_comparison": _render_rating_comparison,
    "capability_checklist": _render_capability_checklist,
    "toggle_switch": _render_toggle_switch,
    "expandable_text": _render_expandable_text,
    "flip_card": _render_flip_card,
    "image_hotspots": _render_image_hotspots,
    "css_dropdown_menu": _render_css_dropdown_menu,
    "star_rating_input": _render_star_rating_input,
    "segmented_control": _render_segmented_control,
    "zoomable_image": _render_zoomable_image,
    "custom_checkbox_group": _render_custom_checkbox_group,
    "css_slide_panel": _render_css_slide_panel,
    "testimonial_card": _render_testimonial_card,
    "star_rating_display": _render_star_rating_display,
    "avatar_group": _render_avatar_group,
    "contributor_list": _render_contributor_list,
    "customer_logo_grid": _render_customer_logo_grid,
    "social_proof_banner": _render_social_proof_banner,
    "media_mention_card": _render_media_mention_card,
    "expert_endorsement": _render_expert_endorsement,
    "review_callout": _render_review_callout,
    "social_feed_embed": _render_social_feed_embed,
    "footnote_group":    _render_footnote_group,
    "color_swatch_grid": _render_color_swatch_grid,
    "live_demo_embed": _render_live_demo_embed,
    "benchmark_comparison": _render_benchmark_comparison,
    "chartjs_bar": _render_chartjs_bar,
    "chartjs_line": _render_chartjs_line,
    "data_table_sortable": _render_data_table_sortable,
    "donut_stat": _render_donut_stat,
    "heatmap": _render_heatmap,
    "punch_card": _render_punch_card,
    "sankey_flow": _render_sankey_flow,
    "cohort_retention": _render_cohort_retention,
    "metric_comparison_card": _render_metric_comparison_card,
    "mini_sparkline_set": _render_mini_sparkline_set,
    "status_dashboard": _render_status_dashboard,
    "uptime_timeline": _render_uptime_timeline,
    "command_palette": _render_command_palette,
    "search_result_card": _render_search_result_card,
}
