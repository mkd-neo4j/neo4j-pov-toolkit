# Neo4j Brand CSS

Drop-in CSS custom properties implementing the Neo4j brand system. Include these files in any project to get the full color palette, fonts, theme tokens, and specialized color sets.

## Quick Start

Link the convenience bundle to get everything:

```html
<link rel="stylesheet" href="neo4j-branding/css/neo4j-brand.css" />
```

For better performance (parallel loading), use individual `<link>` tags:

```html
<link rel="stylesheet" href="neo4j-branding/css/palettes.css" />
<link rel="stylesheet" href="neo4j-branding/css/fonts.css" />
<link rel="stylesheet" href="neo4j-branding/css/theme-light.css" />
<link rel="stylesheet" href="neo4j-branding/css/theme-dark.css" />
```

## Files

| File               | Contents                                           | When to Include                         |
| ------------------ | -------------------------------------------------- | --------------------------------------- |
| `palettes.css`     | All 10 base palettes (~144 shade variables)        | Always — foundation for everything      |
| `fonts.css`        | `@font-face` for SyneNeo + Public Sans (8 weights) | When using Neo4j brand fonts            |
| `theme-light.css`  | Light theme semantic tokens (`:root` default)      | For light or auto-switching UIs         |
| `theme-dark.css`   | Dark theme tokens (`@media` + `[data-theme]`)      | For dark or auto-switching UIs          |
| `code-light.css`   | Cypher syntax highlighting (light)                 | When rendering code blocks              |
| `code-dark.css`    | Cypher syntax highlighting (dark)                  | When rendering code blocks in dark mode |
| `graph-colors.css` | 12 graph node visualization colors                 | For Neo4j graph visualizations          |
| `chart-colors.css` | 12 categorical chart colors                        | For data charts (line, bar, pie)        |
| `neo4j-brand.css`  | `@import` bundle of all the above                  | Convenience — imports everything        |

## Variable Naming

All variables are namespaced with `--neo4j-` to avoid collisions.

### Base Palette Shades

Pattern: `--neo4j-{palette}-{shade}`

```css
var(--neo4j-baltic-20)    /* #8FE3E8 */
var(--neo4j-lemon-35)     /* #F4C318 */
var(--neo4j-neutral-75)   /* #1A1B1D */
```

Palettes: `baltic`, `hibiscus`, `forest`, `lemon`, `lavender`, `marigold`, `earth`, `neutral`, `beige`
Shades: `10` through `80` (in steps of 5). Beige has fewer shades.

Highlights: `--neo4j-highlight-yellow`, `--neo4j-highlight-periwinkle`

### Semantic Theme Tokens

Pattern: `--neo4j-{category}-{property}`

Categories: `neutral`, `primary`, `danger`, `warning`, `success`, `discovery`

```css
var(--neo4j-neutral-text-default)    /* Main text color */
var(--neo4j-neutral-bg-default)      /* Page background */
var(--neo4j-primary-text)            /* Link / primary action text */
var(--neo4j-danger-border-strong)    /* Error border */
```

### Code Highlighting Tokens

Pattern: `--neo4j-code-{token}`

```css
var(--neo4j-code-keyword)   /* Keywords, operators */
var(--neo4j-code-function)  /* Functions, procedures */
var(--neo4j-code-string)    /* String literals */
var(--neo4j-code-label)     /* Node/relationship labels */
var(--neo4j-code-property)  /* Property keys */
```

### Visualization Colors

Pattern: `--neo4j-graph-{n}` or `--neo4j-chart-{n}` (1-12)

```css
var(--neo4j-graph-1)   /* First node color */
var(--neo4j-chart-3)   /* Third chart series color */
```

## Theme Switching

### Automatic (OS preference)

Include both `theme-light.css` and `theme-dark.css`. The browser switches automatically based on the user's OS dark/light mode setting.

### Manual override

Set `data-theme` on any ancestor element to force a theme:

```html
<html data-theme="dark">
    <!-- Force dark -->
    <html data-theme="light">
        <!-- Force light -->
    </html>
</html>
```

The `data-theme` attribute always wins over the OS preference.

### Dark-only projects

If your project is always dark (e.g., presentations), skip both theme files and define your own semantic variables that reference the palette:

```css
:root {
    --my-bg: var(--neo4j-baltic-70);
    --my-accent: var(--neo4j-lemon-35);
}
```

## Font Paths

The `fonts.css` file uses relative paths (`../typography/fonts/`) to locate WOFF2 files. **Do not reorganize the internal directory structure** of the `neo4j-branding/` package — the CSS depends on the relative position of the `css/` and `typography/fonts/` directories.

### Adding Font Weights

`fonts.css` declares the 8 recommended weights. Additional WOFF2 files are available in `typography/fonts/` for all Public Sans variants (Thin through Black, including Italics). To add a weight, copy an existing `@font-face` block and change the filename and `font-weight` value.

## Preloading Fonts

For best performance, preload the fonts you use most:

```html
<link
    rel="preload"
    href="neo4j-branding/typography/fonts/PublicSans-Regular.woff2"
    as="font"
    type="font/woff2"
    crossorigin
/>
<link
    rel="preload"
    href="neo4j-branding/typography/fonts/SyneNeo-SemiBold.woff2"
    as="font"
    type="font/woff2"
    crossorigin
/>
```
