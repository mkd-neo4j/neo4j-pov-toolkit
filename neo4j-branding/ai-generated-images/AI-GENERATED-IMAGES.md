# AI-Generated Images

A guide to creating AI-generated images that feel distinctly Neo4j — not generic stock art. Whether you're using Midjourney, OpenAI (DALL-E / ChatGPT), or another generator, these principles ensure your output aligns with the brand.

---

## Core Principles

Every AI-generated image prompt should address five things, in this order:

1. **Define a Style** — set the visual language (illustration, photo, 3D render)
2. **Add an Idea** — describe the concept or subject
3. **Add Nodes** — incorporate graph elements where appropriate
4. **Define Color** — anchor the palette to Neo4j brand colors
5. **Add a Visual Reference** _(optional)_ — attach a reference image for tone or composition

Getting these right prevents the flat, clip-art feel that plagues most AI-generated brand imagery.

---

## Step 1: Define a Style

The style keyword is the single most important part of your prompt. It sets the entire visual register before anything else is interpreted.

### Recommended Styles

| Use Case                         | Style Keyword(s)                                  |
| -------------------------------- | ------------------------------------------------- |
| Conceptual / thought-leadership  | `a minimalist illustration`                       |
| Graph / node visualizations      | `a minimalist illustration` or `photo`            |
| DevRel / developer content       | `a minimalist illustration` + `dark color scheme` |
| Marketing / campaign hero images | `a cinematic photograph` or `3D render`           |
| Social media cards               | `a clean, flat vector illustration`               |

### Style Tips

**Do:**

- Lead with the style keyword — it anchors the model's interpretation of everything that follows
- Combine styles when appropriate (e.g., `a minimalist illustration with photographic lighting`)
- Use `minimalist` liberally — it steers output away from overloaded, busy compositions

**Don't:**

- Use `realistic photo` without a clear compositional concept — you'll get generic stock imagery
- Mix too many styles in one prompt — pick one primary style and let it dominate
- Omit the style entirely — the model will default to its own aesthetic, which varies unpredictably

---

## Step 2: Add an Idea

Describe the subject and concept clearly. Be specific about what the image should communicate, not just what objects should appear.

### Writing Effective Subject Descriptions

Think in terms of **subject + action + context**:

| Weak Prompt        | Strong Prompt                                                                           |
| ------------------ | --------------------------------------------------------------------------------------- |
| `a graph database` | `an abstract knowledge graph floating in space, nodes pulsing with data`                |
| `AI and data`      | `a neural pathway illuminating connections between data clusters in a dark environment` |
| `fraud detection`  | `interlinked financial pathways revealing hidden patterns, glowing anomaly nodes`       |
| `Neo4j logo`       | Never generate the Neo4j logo — use official assets instead                             |

### Useful Subject Keywords

These keywords consistently produce results aligned with Neo4j's visual identity:

- **Graph concepts:** `knowledge graph`, `connected data`, `interlinked pathways`, `node clusters`, `relationship network`
- **Tech / AI:** `AI visualization`, `futuristic data network`, `neural connections`, `data topology`
- **Nature metaphors:** `mycelium network`, `neural pathways`, `constellation map`, `river delta branches`
- **Composition details:** `glowing nodes`, `holographic effects`, `translucent layers`, `depth of field`
- **Mood:** `clean`, `tech-driven`, `immersive`, `contemplative`, `precise`

---

## Step 3: Add Nodes

Where appropriate, weave graph-like visual elements into the image. This is what makes the output feel like _Neo4j_ and not generic data visualization.

### Node Integration Strategies

- **Literal nodes and edges:** Ask for `spheres connected by luminous lines` or `nodes with visible relationships`
- **Abstract graph structure:** Ask for `interconnected clusters`, `web-like topology`, or `branching pathways`
- **Subtle integration:** Even non-technical images can include node motifs — `bokeh circles connected by faint light trails` in a cityscape, for example

### Examples

```
a minimalist illustration of glowing data nodes connected by thin luminous
edges, floating in a deep Baltic blue environment, clean composition,
wide negative space
```

```
a dark, cinematic photograph of a city at night where streetlights form
a network of glowing nodes connected by light trails, Baltic blue tones,
atmospheric depth
```

---

## Step 4: Define Color

Anchor every prompt to the Neo4j brand palette. Without explicit color direction, AI generators default to their own color biases (usually oversaturated purples and magentas).

### Brand Color Keywords for Prompts

| Brand Color | Hex       | Prompt Keyword                         |
| ----------- | --------- | -------------------------------------- |
| Dark Baltic | `#014063` | `deep navy blue`, `dark Baltic blue`   |
| Mid Baltic  | `#0A6190` | `rich teal blue`, `Baltic blue`        |
| Baltic 20   | `#8FE3E8` | `light cyan`, `pale teal`              |
| Forest 20   | `#90CB62` | `fresh green`, `bright lime green`     |
| Lemon 35    | `#F4C318` | `golden yellow`, `warm amber`          |
| Hibiscus 35 | `#E84E2C` | `warm coral red`, `vibrant orange-red` |
| Lavender 30 | `#A07BEC` | `soft purple`, `muted lavender`        |
| Neutral 70  | `#212325` | `near black`, `charcoal`               |
| White       | `#FFFFFF` | `white`, `bright white`                |

### Application-Specific Color Direction

| Application         | Color Direction in Prompt                                                             |
| ------------------- | ------------------------------------------------------------------------------------- |
| DevRel / developer  | Add `dark color scheme` — emphasize deep navies, near-black, with bright node accents |
| Marketing / general | Stay within the brand palette — Baltic blues, Lemon gold, Forest green                |
| Thought leadership  | Muted, desaturated variants — `subdued Baltic blue tones`, `atmospheric haze`         |
| Social media        | Higher contrast — pair a single bright accent against a dark or neutral ground        |

### Color Tips

**Do:**

- Name specific colors: `deep navy (#014063) background with golden (#F4C318) accent nodes`
- Include hex codes when the generator supports them (Midjourney v6+ interprets hex hints)
- Specify what is light vs dark: `bright nodes against a dark environment`

**Don't:**

- Let the generator pick its own palette — you'll get generic blues and purples
- Use more than 2–3 accent colors — Neo4j imagery should feel focused, not chaotic
- Forget to specify background color — it's the largest color field and sets the tone

---

## Step 5: Add a Visual Reference (Optional)

Most generators accept a reference image that influences composition, color, and mood without being copied directly.

### How to Use References

- **Midjourney:** Upload the image to Discord, then include its URL in the prompt or use `/blend`
- **OpenAI (DALL-E / ChatGPT):** Attach the image in the conversation and describe what you want to keep or change
- **Stable Diffusion:** Use img2img mode or IP-Adapter for style transfer

### Good Reference Sources

- Neo4j's existing AI image library on Bynder
- Screenshots from the presentation decks themselves (for color and mood matching)
- Abstract photography of light, networks, or natural branching structures

---

## Platform-Specific Parameters

### Midjourney

Midjourney parameters control composition, quality, and artistic style. Append them to the end of your prompt.

| Parameter     | Purpose                   | Recommended Values                                                         |
| ------------- | ------------------------- | -------------------------------------------------------------------------- |
| `--ar`        | Aspect ratio              | `16:9` for blog/presentation headers, `1:1` for social, `9:16` for stories |
| `--v`         | Model version             | Use the latest available (currently `--v 6.1` or higher)                   |
| `--q`         | Quality / detail level    | `--q 2` for final assets, `--q 1` for drafts and exploration               |
| `--stylize`   | Creativity vs fidelity    | `--stylize 500–750` for structured-yet-creative output                     |
| `--no`        | Negative prompt           | `--no text, watermark, logo` (always include this)                         |
| `--chaos`     | Variation between results | `--chaos 0–30` for brand work (keep it low for consistency)                |
| `--style raw` | Less Midjourney "opinion" | Use when you want the prompt to dominate over Midjourney's defaults        |

#### Example Midjourney Prompt

```
a minimalist illustration of an abstract knowledge graph, glowing teal
and gold nodes connected by thin luminous edges, floating in a deep
dark Baltic blue (#014063) environment, clean composition, wide
negative space, atmospheric depth --ar 16:9 --v 6.1 --q 2
--stylize 650 --no text watermark logo
```

### OpenAI (DALL-E / ChatGPT)

OpenAI's image generation doesn't use flag-style parameters. Instead, control output through natural language and API settings.

| Control          | How to Apply                                                             |
| ---------------- | ------------------------------------------------------------------------ |
| Aspect ratio     | Specify in the prompt: `wide format, 16:9 aspect ratio`                  |
| Style            | Describe explicitly: `minimalist illustration style`, `photographic`     |
| Quality          | Use `hd` quality setting in the API, or ask for `high detail` in ChatGPT |
| Negative prompts | State exclusions: `no text, no watermarks, no logos, no people`          |
| Iteration        | Describe what to change: `same composition but with darker background`   |

#### Example OpenAI Prompt

```
Create a minimalist illustration of an abstract knowledge graph. Glowing
teal and gold nodes are connected by thin luminous edges, floating in a
deep dark navy blue (#014063) environment. The composition is clean with
wide negative space and atmospheric depth. No text, no watermarks, no
logos. Wide format, 16:9 aspect ratio.
```

---

## Prompt Construction Template

Use this template as a starting point. Fill in each section, then combine into a single prompt.

```
[STYLE]: a minimalist illustration / cinematic photograph / 3D render
[SUBJECT]: of [concept], [key visual elements], [composition details]
[NODES]: [graph elements — nodes, edges, connections, pathways]
[COLOR]: [brand colors — backgrounds, accents, lighting]
[MOOD]: [atmosphere — clean, immersive, contemplative, precise]
[EXCLUSIONS]: no text, no watermarks, no logos, no people
[PARAMETERS]: --ar 16:9 --v 6.1 --q 2 --stylize 650
```

### Assembled Example

```
a minimalist illustration of a fraud detection network revealing hidden
financial pathways, glowing anomaly nodes highlighted in golden yellow
(#F4C318) connected by thin edges, deep dark Baltic blue (#014063)
background, scattered data points in muted teal (#0A6190), clean
composition, atmospheric depth, no text, no watermarks, no logos
--ar 16:9 --v 6.1 --q 2 --stylize 650
```

---

## Do and Don't

**Do:**

- Lead every prompt with a style keyword
- Anchor colors to the Neo4j brand palette — especially Baltic blues and Lemon gold
- Include `no text, no watermarks, no logos` in every prompt
- Generate at `--q 2` (Midjourney) or `hd` (OpenAI) for final assets
- Use the Bynder image library as a reference for what "on-brand" looks like
- Iterate — generate 4+ variations and refine the best one
- Save your working prompts for reuse and team sharing

**Don't:**

- Generate the Neo4j logo — always use official logo assets
- Include people's faces without explicit review (AI faces carry ethical and legal risk)
- Use default generator palettes — they will not match Neo4j brand colors
- Over-describe — prompts longer than ~60 words tend to lose coherence
- Use generated images without reviewing for artifacts (extra fingers, garbled text, distorted geometry)
- Skip the style keyword — it's the difference between "on-brand" and "generic AI art"

---

## Quick-Reference: Prompt Recipes

### Blog Header (16:9, Dark Theme)

```
a minimalist illustration of interconnected data nodes forming a
constellation pattern, glowing golden (#F4C318) nodes on thin teal
(#0A6190) edges, deep navy (#014063) background, atmospheric haze,
wide composition, no text --ar 16:9 --v 6.1 --q 2 --stylize 600
```

### Social Media Card (1:1)

```
a clean flat illustration of a single luminous graph node radiating
connections outward, golden yellow center fading to Baltic blue edges,
dark background, centered composition, no text --ar 1:1 --v 6.1
--q 2 --stylize 500
```

### DevRel / Developer Content (Dark)

```
a dark minimalist illustration of a knowledge graph query traversing
connected nodes, neon teal (#0A6190) paths on near-black (#081E2B)
background, subtle grid lines, terminal aesthetic, no text --ar 16:9
--v 6.1 --q 2 --stylize 700
```

### Conference / Event Banner (21:9, Wide)

```
a cinematic wide-angle view of an abstract data network stretching
across the horizon, thousands of tiny golden nodes connected by faint
blue pathways, deep space atmosphere, Baltic blue tones, epic scale,
no text --ar 21:9 --v 6.1 --q 2 --stylize 750
```

### Nature / Organic Graph (Bioluminescent)

This real-world example blends graph concepts with organic nature metaphors — a strong Neo4j pattern:

```
A surreal 3D Blender render of a knowledge graph forming an intricate
web of glowing, bioluminescent nodes and connections, floating over a
lush green forest at night. The graph appears to be alive, with a soft
organic glow, mimicking fungal mycelium or neural networks. Ethereal
mist in the background, cinematic lighting, hyper-detailed
--ar 16:9 --q 2 --stylize 500
```

**Why this works:**

- **Style** is defined upfront (`surreal 3D Blender render`)
- **Idea** is specific and evocative (`knowledge graph forming an intricate web`)
- **Nodes** are present (`bioluminescent nodes and connections`)
- **Color** comes from the natural subject (forest greens, organic glow) rather than explicit hex — acceptable when the nature metaphor itself carries the brand's visual DNA
- **Mood** is layered (`ethereal mist`, `cinematic lighting`, `hyper-detailed`)
- **Parameters** are appropriate: `16:9` for wide format, `--q 2` for final quality, `--stylize 500` for balanced creativity

---

## Resources

- **Neo4j AI Image Library:** Hosted on Bynder — browse existing on-brand generated images before creating new ones
- **Midjourney Parameters Guide:** [docs.midjourney.com/docs/parameter-list](https://docs.midjourney.com/docs/parameter-list)
- **Brand Colors Reference:** See [COLORS.md](../colors/COLORS.md) for the complete Neo4j color system
- **Typography Reference:** See [TYPOGRAPHY.md](../typography/TYPOGRAPHY.md) for font usage guidelines
