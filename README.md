# A2UI Catalogue — Component Vocabulary for Agent Composition

A public component vocabulary for building agent-driven interfaces across surfaces — Google Meet, Google Chat, web articles, and beyond.

**What this is:** A fixed set of composable primitives that agents use to reason about and compose presentation surfaces. Agents don't generate new components; they compose from this vocabulary. Each atom declares which surfaces it works on — agents assume compatibility and check exceptions.

**What this is not:** A UI kit, a component showcase, or a finished design system. These are the primitives. The power is in the constraint.

---

## The Idea

Rather than asking an AI agent to invent custom UI every turn (expensive, fragile, slow), we give it a stable vocabulary of primitives and let it compose from those. The vocabulary is:

- **Flat and discoverable** — agents see all 45 components in their system prompt
- **Atomic** — each component does one thing well
- **Composable** — layout containers and data sources let agents build complex surfaces from simple pieces
- **Aligned to the A2UI v0.9 draft**

---

## A2UI Version

This catalogue targets **A2UI v0.9 (draft)**, the direction of travel for the specification.

If you need a more stable reference point, start with v0.8.

---

## The Vocabulary

**45 components across 5 groups:**

| Group | Purpose | Examples |
|---|---|---|
| **Atoms** | Text, badges, icons, dividers | `gdm-text`, `gdm-badge`, `gdm-icon` |
| **Layout** | Containers, grids, scrollers | `gdm-container`, `gdm-stage-grid`, `gdm-scroller` |
| **Panels** | Content surfaces | `gdm-image-panel`, `gdm-video-panel`, `gdm-diagram-view` |
| **Molecules** | Composed mini-products | `gdm-market-ticker`, `gdm-3d-airspace` |
| **Overlays** | Chrome floating above | `gdm-captions`, `gdm-chyron`, `gdm-chat-bubble` |

See `spec/gdm-v0.2.json` for the complete contract.

---

## Three Representative Components

### 1. **gdm-text** — The Atom

A rich typography component with optional animations (flip on change, pulse glow, matrix-style glitch).

See `components/gdm-text.ts` for the full implementation.

### 2. **gdm-container** — The Layout Primitive

A flexible flexbox container with glassmorphism, multi-column support, and entrance animations.

See `components/gdm-container.ts` for the full implementation.

### 3. **gdm-stat** — Data-Bound Presentation

A metric atom: label + large value + optional delta (change pill).

See `components/gdm-stat.ts` for the full implementation.

---

## Composition Pattern

Every agent-composed surface follows this shape:

```json
{
  "slide_id": "unique_name",
  "children": [
    { "element": "gdm-text", "content": "..." },
    {
      "element": "gdm-container",
      "direction": "row",
      "children": [
        { "element": "gdm-stat", "label": "..." },
        { "element": "gdm-stat", "label": "..." }
      ]
    }
  ]
}
```

Agents **never** create custom components. They pick from the 45 in the vocabulary, nest them in layout containers, and bind data sources.

See `examples/playbook-simple.yaml` for a real composition.

---

## Full Implementation

This repository contains the specification, three representative components, and a minimal playbook showing composition.

The full **Google Meet Studio** add-on — FastAPI backend, WebSocket protocol, Gemini Live integration, and all 45 components — is at [github.com/curtiskrygier/meet-studio](https://github.com/curtiskrygier/meet-studio).

---

## Using This Vocabulary in Your Own Project

1. Copy `spec/gdm-v0.2.json` into your agent's system prompt or knowledge base
2. Teach your agent the composition pattern (see above)
3. Parse the agent's output and render using:
   - The Lit components here (Web Components)
   - Your own renderer (React, Vue, Angular, etc. — the spec is framework-agnostic)

---

## Surface Compatibility

Atoms declare surface compatibility at the schema level. The tagging model uses three states:

- **`works_on`** — full support, use freely
- **`degraded_on`** — renders but with caveats, agent should note the tradeoff
- **`incompatible_on`** — do not use on this surface, substitute hint provided

This approach — universal by default, exceptions declared explicitly — is ahead of current industry practice. Related work and prior art:

| Source | Relevance |
|---|---|
| [A2UI v0.9 — Google Developers Blog](https://developers.googleblog.com/a2ui-v0-9-generative-ui/) | Separates structure (agent) from implementation (renderer) — no surface compatibility layer yet |
| [MCP-UI — Interactive UI for MCP](https://mcpui.dev/guide/introduction) | Capability negotiation at client handshake level, not component level |
| [MCP Apps — Model Context Protocol Blog](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/) | `io.modelcontextprotocol/ui` capability flag — server decides what to expose per client |
| [W3C UI Specification Schema CG](https://www.w3.org/community/uispec/) | Machine-readable meta-model for cross-platform UI constraints — closest to this approach |
| [The State of Agentic UI — CopilotKit](https://www.copilotkit.ai/blog/the-state-of-agentic-ui-comparing-ag-ui-mcp-ui-and-a2ui-protocols) | Compares AG-UI, MCP-UI, A2UI — none have atom-level surface tagging |
| [MCP UI Discussion — GitHub](https://github.com/orgs/modelcontextprotocol/discussions/522) | Declarative UI + action protocol proposal — rendering constraints left to host |

---

## License

MIT. See LICENSE for details.

---

Built for and maintained by **Google Meet Studio**.
