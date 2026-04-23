# Neo4j Color System

The complete Neo4j brand color system — base palettes, UI theme tokens, syntax highlighting, and visualization colors. All color decisions across Neo4j products trace back to this system.

## System Overview

The base palettes below are the foundation. They are consumed by theme tokens and applied contexts documented in the following files:


| Document                                                                      | Purpose                                                      |
| ----------------------------------------------------------------------------- | ------------------------------------------------------------ |
| [Light Theme Tokens](light-themes/LIGHT-THEME.md)                             | Semantic UI tokens (text, bg, border, hover) for light theme |
| [Dark Theme Tokens](dark-themes/DARK-THEME.md)                                | Semantic UI tokens (text, bg, border, hover) for dark theme  |
| [Light Code Highlighting](code-highlighting/light/LIGHT-CODE-HIGHLIGHTING.md) | Cypher syntax highlighting colors for light theme            |
| [Dark Code Highlighting](code-highlighting/dark/DARK-CODE-HIGHLIGHTING.md)    | Cypher syntax highlighting colors for dark theme             |
| [Graph Colors](graph-colours/GRAPH-COLOURS.md)                                | 12 node colors for graph visualizations (standalone)         |
| [Categorical Colors](categorical-colours/CATEGORICAL-COLOURS.md)              | 12 chart colors for data visualization (standalone)          |


---

## Base Palettes

Each palette runs from lightest (10) to darkest (80) in 15 steps.

---

## Baltic (Brand Primary)

The core Neo4j brand color. Dark Baltic (`--dark-baltic`) is the primary logo and UI color.


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#E7FAFB` | 35    | `#51A6B1` | 60    | `#014063` |
| 15    | `#C3F8FB` | 40    | `#4C99A4` | 65    | `#262F31` |
| 20    | `#8FE3E8` | 45    | `#30839D` | 70    | `#081E2B` |
| 25    | `#5CC3C9` | 50    | `#0A6190` | 75    | `#041823` |
| 30    | `#5DB3BF` | 55    | `#02507B` | 80    | `#01121C` |


**Key values:** Dark Baltic = `#014063` (shade 60), Mid Baltic = `#0A6190` (shade 50)

---

## Hibiscus


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#FFE9E7` | 35    | `#E84E2C` | 60    | `#432520` |
| 15    | `#FFD7D2` | 40    | `#D43300` | 65    | `#4E0900` |
| 20    | `#FFAA97` | 45    | `#BB2D00` | 70    | `#3F0800` |
| 25    | `#FF8E6A` | 50    | `#961200` | 75    | `#360700` |
| 30    | `#F96746` | 55    | `#730E00` | 80    | `#280500` |


---

## Forest


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#E7FCD7` | 35    | `#5B992B` | 60    | `#0C4D31` |
| 15    | `#BCF194` | 40    | `#4D8622` | 65    | `#0A4324` |
| 20    | `#90CB62` | 45    | `#3F7824` | 70    | `#262D24` |
| 25    | `#80BB53` | 50    | `#296127` | 75    | `#052618` |
| 30    | `#6FA646` | 55    | `#145439` | 80    | `#021D11` |


---

## Lemon


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#FFFAD1` | 35    | `#F4C318` | 60    | `#614600` |
| 15    | `#FFF8BD` | 40    | `#D7AA0A` | 65    | `#4D3700` |
| 20    | `#FFF178` | 45    | `#B48409` | 70    | `#312E1A` |
| 25    | `#FFE500` | 50    | `#996E00` | 75    | `#2E2100` |
| 30    | `#FFD600` | 55    | `#765500` | 80    | `#251B00` |


---

## Lavender


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#F7F3FF` | 35    | `#8C68D9` | 60    | `#2C2A34` |
| 15    | `#E9DEFF` | 40    | `#754EC8` | 65    | `#220954` |
| 20    | `#CCB4FF` | 45    | `#5A34AA` | 70    | `#170146` |
| 25    | `#B38EFF` | 50    | `#4B2894` | 75    | `#0E002D` |
| 30    | `#A07BEC` | 55    | `#3B1982` | 80    | `#09001C` |


---

## Marigold


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#FFF0D2` | 35    | `#FFA901` | 60    | `#795000` |
| 15    | `#FFDE9D` | 40    | `#EC9C00` | 65    | `#624100` |
| 20    | `#FFCF72` | 45    | `#DA9105` | 70    | `#543800` |
| 25    | `#FFC450` | 50    | `#BA7A00` | 75    | `#422C00` |
| 30    | `#FFB422` | 55    | `#986400` | 80    | `#251900` |


---

## Earth


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#FFF7F0` | 35    | `#E0AE7F` | 60    | `#66310B` |
| 15    | `#FDEDDA` | 40    | `#D19660` | 65    | `#5B2B09` |
| 20    | `#FFE1C5` | 45    | `#AF7C4D` | 70    | `#481F01` |
| 25    | `#F8D1AE` | 50    | `#8D5D31` | 75    | `#361700` |
| 30    | `#ECBF96` | 55    | `#763F18` | 80    | `#220E00` |


---

## Neutral


| Shade | Hex       | Shade | Hex       | Shade | Hex       |
| ----- | --------- | ----- | --------- | ----- | --------- |
| 10    | `#FFFFFF` | 35    | `#A8ACB2` | 60    | `#4D5157` |
| 15    | `#F5F6F6` | 40    | `#959AA1` | 65    | `#3C3F44` |
| 20    | `#E2E3E5` | 45    | `#818790` | 70    | `#212325` |
| 25    | `#CFD1D4` | 50    | `#6F757E` | 75    | `#1A1B1D` |
| 30    | `#BBBEC3` | 55    | `#5E636A` | 80    | `#09090A` |


---

## Beige

A shorter warm-neutral palette.


| Shade | Hex       |
| ----- | --------- |
| 10    | `#FFFCF4` |
| 20    | `#FFF7E3` |
| 30    | `#F2EAD4` |
| 40    | `#C1B9A0` |
| 50    | `#999384` |
| 60    | `#666050` |
| 70    | `#3F3824` |


---

## Highlight Colors

Standalone accent colors for special emphasis.


| Name       | Hex       | Usage                              |
| ---------- | --------- | ---------------------------------- |
| Yellow     | `#FAFF00` | High-visibility highlights, alerts |
| Periwinkle | `#6A82FF` | Secondary accent, links, callouts  |


---

## Presentation CSS Mapping

How the brand palette maps to this project's CSS custom properties:


| CSS Variable       | Brand Color         | Hex                      |
| ------------------ | ------------------- | ------------------------ |
| `--accent-lemon`   | Lemon 35            | `#F4C318`                |
| `--accent-baltic`  | Baltic 20           | `#8FE3E8`                |
| `--accent-forest`  | Forest 20           | `#90CB62`                |
| `--slide-bg`       | Baltic (custom)     | `#08162A`                |
| `--dark-baltic`    | Baltic 60           | `#014063`                |
| `--mid-baltic`     | Baltic 50           | `#0A6190`                |
| `--text-primary`   | Neutral 10          | `#FFFFFF`                |
| `--text-secondary` | Neutral (65% white) | `rgba(255,255,255,0.65)` |
| `--text-muted`     | Neutral (35% white) | `rgba(255,255,255,0.35)` |


