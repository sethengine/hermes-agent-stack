---
name: baoyu-visual-content
description: "Generate consistent visual content with the Baoyu toolkit: article illustrations, knowledge comics, and infographics."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [creative, image-generation, article-illustration, comic, infographic, baoyu]
    homepage: https://github.com/JimLiu/baoyu-skills
---

# Baoyu Visual Content

Generate article illustrations, knowledge comics, and infographics with type × style × palette consistency. Adapted from the baoyu-skills collection for Hermes Agent.

---

## Article Illustrator

Analyze articles, identify illustration positions, and generate images with **Type × Style × Palette** consistency.

**When to use:** illustrate an article, add images to content, generate illustrations.

**Three dimensions:**
- **Type:** infographic, scene, flowchart, comparison, framework, timeline
- **Style:** notion, editorial, vector, watercolor, etc.
- **Palette:** neon, mono-ink, warm, macaron

**Detailed workflows, styles, and palettes:**
See `references/baoyu-article-illustrator/SKILL.md` and the `references/baoyu-article-illustrator/` directory.

---

## Knowledge Comic Creator

Create original knowledge comics with flexible art style × tone combinations.

**When to use:** educational comic, biography comic, tutorial comic, "知识漫画".

**Dimensions:**
- **Art style:** chalk, minimalist, ligne-claire, manga, realistic, ink-brush
- **Tone:** energetic, action, warm, dramatic, neutral, vintage, romantic
- **Layout:** four-panel, dense, standard, webtoon, cinematic, mixed, splash
- **Preset:** four-panel, ohmsha, concept-story, wuxia, shoujo

**Detailed workflows, templates, and presets:**
See `references/baoyu-comic/SKILL.md` and the `references/baoyu-comic/` directory.

---

## Infographic Generator

Create infographics with **layout × style** combinations.

**When to use:** infographic, visual summary, "信息图", "可视化".

**21 layouts:** bento-grid, funnel, iceberg, hierarchical-layers, structural-breakdown, isometric-map, comparison-matrix, bridge, jigsaw, hub-spoke, dense-modules, comic-strip, dashboard, binary-comparison, periodic-table, venn-diagram, story-mountain, circular-flow, winding-roadmap, tree-branching.

**21 styles:** craft-handmade, retro-pop-grid, bold-graphic, storybook-watercolor, lego-brick, chalkboard, corporate-memphis, ikea-manual, cyberpunk-neon, kawaii, pixel-art, subway-map, knolling, ui-wireframe, claymation, morandi-journal, origami, aged-academia, hand-drawn-edu, technical-schematic, pop-laboratory.

**Detailed workflows, layouts, and styles:**
See `references/baoyu-infographic/SKILL.md` and the `references/baoyu-infographic/` directory.

---

## Tooling Notes

Hermes' `image_generate` tool is **prompt-only** — it accepts a text prompt and an aspect ratio, and returns an image URL. It does **NOT** accept reference images. When the user supplies a reference image, extract traits in text and embed them in every prompt.

Supported aspect ratios: landscape (16:9), portrait (9:16), square (1:1), and custom ratios (3:4, 4:3, 2.35:1, etc.).
