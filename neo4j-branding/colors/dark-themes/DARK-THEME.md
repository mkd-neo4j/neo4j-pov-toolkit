# Dark Theme — Neo4j Design System Color Tokens

Semantic color tokens for the Neo4j dark theme UI. Each token maps to a shade from the [brand color palettes](../COLORS.md). Tokens are organized by category: **Neutral**, **Primary/Info**, **Danger**, **Warning**, **Success**, and **Discovery**.

---

## Neutral

All tokens reference the **Neutral** palette.

### Text & Icon

| Token        | Hex       | Palette Ref |
| ------------ | --------- | ----------- |
| text-weakest | `#818790` | Neutral-45  |
| text-weaker  | `#A8ACB2` | Neutral-35  |
| text-weak    | `#CFD1D4` | Neutral-25  |
| text-default | `#F5F6F6` | Neutral-15  |
| icon         | `#CFD1D4` | Neutral-25  |
| text-inverse | `#1A1B1D` | Neutral-75  |

### Background

| Token        | Hex       | Opacity | Palette Ref |
| ------------ | --------- | ------- | ----------- |
| bg-weak      | `#212325` | —       | Neutral-70  |
| bg-default   | `#1A1B1D` | —       | Neutral-75  |
| on-bg-weak   | `#818790` | 8%      | Neutral-45  |
| bg-strong    | `#3C3F44` | —       | Neutral-65  |
| bg-stronger  | `#6F757E` | —       | Neutral-50  |
| bg-strongest | `#F5F6F6` | —       | Neutral-15  |
| bg-status    | `#A8ACB2` | —       | Neutral-35  |

### Border

| Token            | Hex       | Palette Ref |
| ---------------- | --------- | ----------- |
| border-weak      | `#3C3F44` | Neutral-65  |
| border-strong    | `#5E636A` | Neutral-55  |
| border-strongest | `#BBBEC3` | Neutral-30  |

### Hover & Pressed

| Token   | Hex       | Opacity | Palette Ref |
| ------- | --------- | ------- | ----------- |
| hover   | `#959AA1` | 10%     | Neutral-40  |
| pressed | `#959AA1` | 20%     | Neutral-40  |

---

## Primary / Info

All tokens reference the **Baltic** palette. Hover-weak and pressed-weak use opacity overlays; hover-strong, pressed-strong, and focus use solid hex values.

### Text & Icon

| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#8FE3E8` | Baltic-20   |
| icon  | `#8FE3E8` | Baltic-20   |

### Background

| Token       | Hex       | Palette Ref |
| ----------- | --------- | ----------- |
| bg-weak     | `#262F31` | Baltic-65   |
| bg-strong   | `#8FE3E8` | Baltic-20   |
| bg-status   | `#5DB3BF` | Baltic-30   |
| bg-selected | `#262F31` | Baltic-65   |

### Border

| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#02507B` | Baltic-55   |
| border-strong | `#8FE3E8` | Baltic-20   |

### Hover & Pressed

| Token          | Hex       | Opacity | Palette Ref |
| -------------- | --------- | ------- | ----------- |
| hover-weak     | `#8FE3E8` | 8%      | Baltic-20   |
| pressed-weak   | `#8FE3E8` | 12%     | Baltic-20   |
| hover-strong   | `#5DB3BF` | —       | Baltic-30   |
| pressed-strong | `#4C99A4` | —       | Baltic-40   |
| focus          | `#5DB3BF` | —       | Baltic-30   |

---

## Danger

All tokens reference the **Hibiscus** palette. Hover-weak and pressed-weak use opacity overlays.

### Text & Icon

| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#FFAA97` | Hibiscus-20 |
| icon  | `#FFAA97` | Hibiscus-20 |

### Background

| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#432520` | Hibiscus-60 |
| bg-strong | `#FFAA97` | Hibiscus-20 |
| bg-status | `#F96746` | Hibiscus-30 |

### Border

| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#730E00` | Hibiscus-55 |
| border-strong | `#FFAA97` | Hibiscus-20 |

### Hover & Pressed

| Token          | Hex       | Opacity | Palette Ref |
| -------------- | --------- | ------- | ----------- |
| hover-weak     | `#FFAA97` | 8%      | Hibiscus-20 |
| pressed-weak   | `#FFAA97` | 12%     | Hibiscus-20 |
| hover-strong   | `#F96746` | —       | Hibiscus-30 |
| pressed-strong | `#E84E2C` | —       | Hibiscus-35 |

---

## Warning

All tokens reference the **Lemon** palette. No hover/pressed states defined.

### Text & Icon

| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#FFD600` | Lemon-30    |
| icon  | `#FFD600` | Lemon-30    |

### Background

| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#312E1A` | Lemon-70    |
| bg-strong | `#FFD600` | Lemon-30    |
| bg-status | `#D7AA0A` | Lemon-40    |

### Border

| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#765500` | Lemon-55    |
| border-strong | `#FFD600` | Lemon-30    |

---

## Success

All tokens reference the **Forest** palette. No hover/pressed states defined.

### Text & Icon

| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#90CB62` | Forest-20   |
| icon  | `#90CB62` | Forest-20   |

### Background

| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#262D24` | Forest-70   |
| bg-strong | `#90CB62` | Forest-20   |
| bg-status | `#6FA646` | Forest-30   |

### Border

| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#296127` | Forest-50   |
| border-strong | `#90CB62` | Forest-20   |

---

## Discovery

All tokens reference the **Lavender** palette. No hover/pressed states defined.

### Text & Icon

| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#CCB4FF` | Lavender-20 |
| icon  | `#CCB4FF` | Lavender-20 |

### Background

| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#2C2A34` | Lavender-60 |
| bg-strong | `#CCB4FF` | Lavender-20 |
| bg-status | `#A07BEC` | Lavender-30 |

### Border

| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#4B2894` | Lavender-50 |
| border-strong | `#CCB4FF` | Lavender-20 |
