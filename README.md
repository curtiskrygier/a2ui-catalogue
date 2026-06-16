<div align="center">

<img src="examples/efficiency-claim.png" alt="A2UI — 35× fewer output tokens. Identical UI." width="100%">

# A2UI Catalogue

**A component vocabulary for agent-driven interfaces.**  
The model names an atom. The renderer compiles the HTML, CSS, SVG, and animation.

[![Atoms](https://img.shields.io/badge/atoms-193-00f2ff?style=flat-square&labelColor=04060f)](atoms/)
[![Surfaces](https://img.shields.io/badge/surfaces-5-a78bfa?style=flat-square&labelColor=04060f)](spec/)
[![License](https://img.shields.io/badge/license-MIT-34d399?style=flat-square&labelColor=04060f)](LICENSE)
[![A2UI](https://img.shields.io/badge/spec-v0.9_draft-f472b6?style=flat-square&labelColor=04060f)](spec/)

</div>

---

## The idea

Rather than asking an agent to generate custom UI every turn — expensive, fragile, unpredictable — give it a stable vocabulary of atoms and let it compose from those.

```
Raw HTML   609 tok  ████████████████████████████████████████
OpenUI     287 tok  ███████████████████
A2UI        68 tok  ████
```

**35× fewer output tokens. Identical UI.** The renderer expands a 68-token atom reference into 2,395 tokens of compiled HTML server-side — it never re-enters the model's context window.

---

## What's in this repo

| Directory | Contents |
|---|---|
| `atoms/` | Atom schema definitions (193 atoms, `schema.yaml`) |
| `renderers/` | Surface renderers — web article, meet stage, Google Chat |
| `web-article/` | Web article renderer (`renderer.py`) |
| `components/` | Lit Web Components for the meet-stage surface |
| `scripts/` | Publishing pipeline to Firestore |
| `vendors/` | Landscape analysis of 9 UI libraries mapped to A2UI atoms |
| `benchmarks/` | OpenUI comparison benchmark — token counts across 7 scenarios |
| `spec/` | A2UI v0.9 draft spec and gdm-v0.2 component contract |
| `examples/` | Playbook YAML examples |

---

## 193 atoms across 5 surfaces

Atoms declare which surfaces they support at the schema level. An agent picks an atom by name, supplies parameters, and the renderer handles the rest.

```json
[{
  "type": "stat_card",
  "label": "Output tokens saved",
  "value": "97%",
  "delta": "+35×"
}]
```

Agents **never** write HTML. They compose from the vocabulary.

---

## Surface compatibility

| Symbol | Meaning |
|---|---|
| ✅ | Full support |
| ⚠️ | Renders with caveats |
| ❌ | Incompatible — do not use |
| — | Not applicable |

<details>
<summary><strong>View full compatibility matrix (193 atoms)</strong></summary>

| Atom | web | meet-stage | googlechat | email | pdf | Source |
|---|---|---|---|---|---|---|
| `intro` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `body` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `heading` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `subheading` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `quote` | ✅ | ✅ | ⚠️ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `code` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `pipeline` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `bullet_list` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `divider` | ✅ | ✅ | ⚠️ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `youtube` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `image` | ✅ | ✅ | ⚠️ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `image_pair` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `diagram` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `github_repo_card` | ✅ | ⚠️ | ⚠️ | ⚠️ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `repo_links` | ✅ | ✅ | ⚠️ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `closing` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `callout` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `steps` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `table` | ✅ | ✅ | ⚠️ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `tabs` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `key_value` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `before_after` | ✅ | ✅ | ❌ | ❌ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `api_reference` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `gallery` | ✅ | ⚠️ | ❌ | ❌ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `video_pair` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `carousel` | ✅ | ✅ | ❌ | ❌ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `timeline` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `annotated_code` | ✅ | ✅ | ❌ | ❌ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `stat_card` | ✅ | ✅ | ❌ | ❌ | ⚠️ | [UIverse.io community](https://uiverse.io) |
| `progress_bar` | ✅ | ✅ | ❌ | ❌ | ⚠️ | [UIverse.io community](https://uiverse.io) |
| `badge_group` | ✅ | ✅ | ❌ | ⚠️ | ⚠️ | [UIverse.io community](https://uiverse.io) |
| `sparkline` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `heatmap` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `punch_card` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `sankey_flow` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `cohort_retention` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `donut_stat` | ✅ | ✅ | ⚠️ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `metric_delta` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `task_list` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `sentiment_summary` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `trend_indicator` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `breadcrumb` | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `pagination` | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `stepper` | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `tab_bar` | ✅ | ✅ | ⚠️ | ⚠️ | ⚠️ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `anchor_list` | ✅ | ✅ | ⚠️ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `faq_accordion` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `glossary_term` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `footnote` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `blockquote_with_avatar` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `pull_stat` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `accordion_item` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `tooltip` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `hover_card` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `collapsible_panel` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `css_modal` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `audio_player` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `audio_link` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `pdf_preview` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `document_link` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `video_thumbnail` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `video_card` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `code_diff` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `code_snippet_pair` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `framed_screenshot` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `image_with_caption` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `alert_banner` | ✅ | ✅ | ⚠️ | ❌ | — | [UIverse.io community](https://uiverse.io) |
| `toast_notification` | ✅ | ✅ | ❌ | ❌ | — | [UIverse.io community](https://uiverse.io) |
| `loading_skeleton` | ✅ | ✅ | ❌ | ❌ | — | [UIverse.io community](https://uiverse.io) |
| `empty_state` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `spinner` | ✅ | ✅ | ❌ | ❌ | — | [UIverse.io community](https://uiverse.io) |
| `status_pill` | ✅ | ✅ | ⚠️ | ⚠️ | — | [UIverse.io community](https://uiverse.io) |
| `inline_feedback_message` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `rating_stars` | ✅ | ✅ | ⚠️ | ⚠️ | — | [UIverse.io community](https://uiverse.io) |
| `progress_circle` | ✅ | ✅ | ❌ | ❌ | — | [UIverse.io community](https://uiverse.io) |
| `action_required_card` | ✅ | ✅ | ✅ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `feature_matrix` | ✅ | ✅ | ⚠️ | ❌ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `pricing_tier_card` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `pricing_tier_group` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `pros_cons_list` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `side_by_side_spec` | ✅ | ✅ | ⚠️ | ❌ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `product_spec_table` | ✅ | ✅ | ⚠️ | ❌ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `comparison_grid` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `versus_block` | ✅ | ✅ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `rating_comparison` | ✅ | ✅ | ✅ | ✅ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `capability_checklist` | ✅ | ✅ | ⚠️ | ❌ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `toggle_switch` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `expandable_text` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `flip_card` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `image_hotspots` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `css_dropdown_menu` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `star_rating_input` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `segmented_control` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `zoomable_image` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `custom_checkbox_group` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `css_slide_panel` | ✅ | ✅ | ❌ | ❌ | ❌ | [UIverse.io community](https://uiverse.io) |
| `testimonial_card` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `star_rating_display` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [UIverse.io community](https://uiverse.io) |
| `avatar_group` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [UIverse.io community](https://uiverse.io) |
| `contributor_list` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `customer_logo_grid` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `social_proof_banner` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [UIverse.io community](https://uiverse.io) |
| `media_mention_card` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `expert_endorsement` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `review_callout` | ✅ | ✅ | ⚠️ | ⚠️ | ✅ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `social_feed_embed` | ✅ | ✅ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `terminal_block` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `file_tree` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `tabbed_code` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `http_request_block` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `env_var_list` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `prerequisite_checklist` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `keyboard_shortcut` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `api_param_table` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `version_badge` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `deprecation_notice` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `experimental_banner` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `cli_command` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [UIverse.io community](https://uiverse.io/) |
| `copy_code_button` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [UIverse.io community](https://uiverse.io/) |
| `log_output` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `json_tree_viewer` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `key_takeaways` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `summary_box` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `learning_objectives` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `changelog_entry` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `release_notes` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `further_reading` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `resources_list` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `sidebar_note` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `difficulty_badge` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `caution_block` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `checklist_interactive` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `glossary_inline` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `time_estimate` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `progress_checkpoint` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `social_share_bar` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [UIverse.io community](https://uiverse.io/) |
| `newsletter_cta` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `author_bio_card` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `related_posts_grid` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `series_overview_card` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `reaction_group` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [UIverse.io community](https://uiverse.io/) |
| `share_quote` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `follow_cta` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `follow_button` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [UIverse.io community](https://uiverse.io/) |
| `reading_progress_bar` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `table_of_contents` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `article_hero` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `scroll_to_top` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `article_series_nav` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `embed_codepen` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `embed_stackblitz` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `embed_gist` | ✅ | — | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `embed_tweet` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `embed_google_slides` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `lottie_animation` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `figma_embed` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `color_swatch_grid` | ✅ | ✅ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `live_demo_embed` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `benchmark_comparison` | ✅ | ✅ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `chartjs_bar` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `chartjs_line` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `data_table_sortable` | ✅ | ⚠️ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `metric_comparison_card` | ✅ | ✅ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `mini_sparkline_set` | ✅ | ✅ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `status_dashboard` | ✅ | ✅ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `uptime_timeline` | ✅ | ✅ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `command_palette` | ✅ | ⚠️ | ⚠️ | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `search_result_card` | ✅ | ✅ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `post_metadata_bar` | ✅ | ⚠️ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `footnote_group` | ✅ | ⚠️ | — | ✅ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `notification_badge` | ✅ | ⚠️ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `expandable_list` | ✅ | ⚠️ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `poll_block` | ✅ | ⚠️ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `abbr_tooltip` | ✅ | ⚠️ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `copy_to_clipboard` | ✅ | ⚠️ | — | ⚠️ | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `conversion_funnel` | ✅ | ✅ | ❌ | — | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `gauge_sla` | ✅ | ✅ | ❌ | — | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `stacked_area` | ✅ | ✅ | ❌ | — | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `scatter_trend` | ✅ | ✅ | ❌ | — | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `call_mood_board` | ✅ | ✅ | ❌ | — | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `github_activity_grid` | ✅ | ✅ | ❌ | — | — | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `form` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `form_input` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `form_select` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `form_radio_group` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `form_checkbox_group` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `form_switch_group` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `form_slider` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `form_date_picker` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `modal` | ✅ | ✅ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `follow_up_chips` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [Thesys](https://github.com/thesysdev/openui) |
| `choicebox_group` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |
| `feedback_prompt` | ✅ | ⚠️ | ❌ | ❌ | ❌ | [a2ui-catalogue](https://github.com/curtiskrygier/a2ui-catalogue) |

</details>

---

## Vendor landscape

Nine UI libraries benchmarked against the A2UI atom vocabulary — gaps identified, licences checked, adaptation priority set. See [`vendors/LANDSCAPE.md`](vendors/LANDSCAPE.md) for the full analysis.

| Tier | Libraries |
|---|---|
| Tier 1 — act now | AI-native patterns, Microsoft Fluent UI |
| Tier 2 — delivered | Shopify Polaris, Atlassian Design System, IBM Carbon |
| Tier 3 — monitor | Tailwind UI, Radix UI, MagicUI / Aceternity, Vercel Geist |

---

## Using this vocabulary

1. Copy `spec/schema.yaml` into your agent's system prompt or tool definition
2. Teach your agent the composition pattern — pick atoms by name, supply parameters
3. Parse the agent's output and render using:
   - The renderers in this repo (`renderers/`, `web-article/`)
   - Your own renderer — the spec is framework-agnostic

The renderer handles HTML, CSS, SVG, and animation. The model never touches them.

---

## Related work

| Source | Relevance |
|---|---|
| [A2UI v0.9 — Google Developers Blog](https://developers.googleblog.com/a2ui-v0-9-generative-ui/) | Separates structure (agent) from implementation (renderer) — no surface compatibility layer yet |
| [MCP-UI — Interactive UI for MCP](https://mcpui.dev/guide/introduction) | Capability negotiation at client handshake level, not component level |
| [The State of Agentic UI — CopilotKit](https://www.copilotkit.ai/blog/the-state-of-agentic-ui-comparing-ag-ui-mcp-ui-and-a2ui-protocols) | Compares AG-UI, MCP-UI, A2UI — none have atom-level surface tagging |
| [W3C UI Specification Schema CG](https://www.w3.org/community/uispec/) | Machine-readable meta-model for cross-platform UI constraints — closest to this approach |

---

## License

MIT. See [LICENSE](LICENSE) for details.

---

Built for and maintained by **Google Meet Studio**.
