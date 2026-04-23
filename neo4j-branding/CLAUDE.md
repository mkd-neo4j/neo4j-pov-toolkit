# Neo4j Brand Assets

This folder contains the **official Neo4j brand standards**. These are not suggestions, templates, or starting points — they are the canonical source of truth for Neo4j's visual identity as defined by the brand team.

## Important: These Standards Are Not Negotiable

Everything in this folder — colors, typography, logo usage, image generation guidelines — represents approved Neo4j brand decisions. When working with any Neo4j project:

- **Conform to these standards.** Do not invent new colors, substitute fonts, or improvise logo treatments.
- **Do not modify these files** unless explicitly updating them to reflect a new brand decision from the Neo4j brand team.
- **Reference before creating.** Before choosing a color, font weight, or logo variant, check the relevant guide below first.
- **When in doubt, follow the guide.** If a design decision isn't covered here, err on the side of existing patterns rather than introducing something new.

---

## Folder Structure

Each folder has a root markdown file that serves as the entry point. **Always read that file first** — it explains the system, links to any sub-documents, and provides the rules for usage.

| Folder                 | Entry Point                                                          | What It Contains                                                                                                                                     |
| ---------------------- | -------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------- |
| `css/`                 | [CSS.md](css/CSS.md)                                                 | Drop-in CSS files: palettes, fonts, light/dark themes, code highlighting, graph/chart colors. `<link>` them into any project.                        |
| `colors/`              | [COLORS.md](colors/COLORS.md)                                        | The complete Neo4j color system — 10 base palettes, light/dark UI theme tokens, Cypher syntax highlighting, graph visualization colors, chart colors |
| `logos/`               | [LOGOS.md](logos/LOGOS.md)                                           | All Neo4j logo assets (full logo, mark, lockups) in SVG, PNG, JPG, EPS, PDF across RGB, CMYK, and Pantone color spaces                               |
| `typography/`          | [TYPOGRAPHY.md](typography/TYPOGRAPHY.md)                            | Font families (Public Sans + Syne Neo), approved weights, hierarchy rules, combining type, and platform-specific caveats. WOFF2 + TTF/OTF font files |
| `ai-generated-images/` | [AI-GENERATED-IMAGES.md](ai-generated-images/AI-GENERATED-IMAGES.md) | Guidelines for creating on-brand AI-generated imagery using Midjourney, OpenAI/DALL-E, or other generators                                           |

---

## How to Use This System

### 1. Colors

Start with [COLORS.md](colors/COLORS.md). It defines the 10 base palettes (Baltic, Hibiscus, Forest, Lemon, Lavender, Marigold, Earth, Neutral, Beige, plus highlight colors) and links to six sub-documents:

- **Light/Dark Theme Tokens** — semantic UI tokens (text, background, border, hover/pressed) mapped to palette shades
- **Light/Dark Code Highlighting** — Cypher syntax highlighting colors for each theme
- **Graph Colors** — 12 ordered node colors for graph visualizations (standalone, not palette-derived)
- **Categorical Colors** — 12 ordered chart colors for data visualization (standalone, not palette-derived)

When building UI or slides, use the theme tokens and CSS custom properties — never hardcode raw hex values that aren't from this system.

### 2. Logos

Start with [LOGOS.md](logos/LOGOS.md). It explains the three color variants (Brand Blue, Black, White), clear space rules, monogram usage, and a quick-reference table for which file to use in which context. The logo files themselves live alongside the markdown in the same folder.

Key rules: never distort, crop, recolor, or apply effects to the logo. Use official assets only.

### 3. Typography

Start with [TYPOGRAPHY.md](typography/TYPOGRAPHY.md). Two fonts:

- **Public Sans** — the workhorse font for body, captions, subheadings (Regular and Medium weights primary)
- **Syne Neo** — reserved for large headlines, titles, and eyebrows only (Medium, SemiBold, Bold weights)

Never use Syne Neo for body text. Never use the two fonts in the same sentence. Watch the Syne "j" issue (indistinguishable from "i") and numeral settings.

### 4. AI-Generated Images

Start with [AI-GENERATED-IMAGES.md](ai-generated-images/AI-GENERATED-IMAGES.md). A five-step prompt framework (Style, Idea, Nodes, Color, Reference) ensures AI-generated imagery feels distinctly Neo4j. Includes platform-specific parameters for Midjourney and OpenAI, ready-to-use prompt recipes, and brand color keywords for prompts.

Key rule: never generate the Neo4j logo — always use official logo assets.
