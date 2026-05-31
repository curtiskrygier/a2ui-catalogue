# web-article

Block-based authoring layer for long-form web articles.

A post is defined as a list of typed blocks conforming to `schema.yaml`. The renderer materialises these into clean, predictable HTML — no markdown conversion, no Quill stripping, no surprises.

## The idea

Same principle as `googlechat/` — a fixed molecular vocabulary for a specific viewport. The viewport here is a long-form article in a web CMS.

Agents reference `schema.yaml` to draft posts as structured block lists. The renderer handles presentation.

## Usage

```python
import yaml
from web_article.renderer import render

with open("my-post.yaml") as f:
    post = yaml.safe_load(f)

html = render(post["blocks"])
```

## Example post

```yaml
title: "Substrate, Not Slides"
slug: substrate-not-slides
summary: "How a stable component catalogue replaces hardcoded UI."
topic: general

blocks:
  - type: intro
    series_label: "the first article"
    series_url: "https://techmusings.krygier.fr/post/how-i-got-to-a2ui"
    continuation: "I traced how I got from a broken WebSocket to A2UI. This article is what happened next."

  - type: youtube
    url: "https://youtu.be/DnGvNgftRGQ"

  - type: body
    text: "In the first version of this project, every meaningful UI change meant touching backend code."

  - type: heading
    text: "The Bottleneck"

  - type: pipeline
    steps: ["Modify main.py", "npm run build", "gcloud run deploy"]

  - type: image_pair
    left:
      url: "https://raw.githubusercontent.com/curtiskrygier/a2ui-catalogue/main/assets/MeetLandingQueue.png"
      alt: "Landing queue in Google Meet"
      caption: "Google Meet — Fullscreen"
    right:
      url: "https://raw.githubusercontent.com/curtiskrygier/a2ui-catalogue/main/assets/Chatlandingqueue.png"
      alt: "Landing queue in Google Chat"
      caption: "Google Chat — Card"

  - type: repo_links
    links:
      - label: "Catalogue"
        url: "https://github.com/curtiskrygier/a2ui-catalogue"
      - label: "Meet Studio"
        url: "https://github.com/curtiskrygier/meetstudio"

  - type: closing
    text: "The compositions will keep changing; the substrate is what compounds."
```

## Blocks

See `schema.yaml` for the full vocabulary. 15 block types covering text, media, and structure.
