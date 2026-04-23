# Light Theme — Neo4j Design System Color Tokens

Semantic color tokens for the Neo4j light theme UI. Each token maps to a shade from the [brand color palettes](../COLORS.md). Tokens are organized by category: **Neutral**, **Primary/Info**, **Danger**, **Warning**, **Success**, and **Discovery**.

---

## Neutral

All tokens reference the **Neutral** palette.

### Text & Icon


| Token        | Hex       | Palette Ref |
| ------------ | --------- | ----------- |
| text-weakest | `#818790` | Neutral-45  |
| text-weaker  | `#5E636A` | Neutral-55  |
| text-weak    | `#4D5157` | Neutral-60  |
| text-default | `#1A1B1D` | Neutral-75  |
| icon         | `#4D5157` | Neutral-60  |
| text-inverse | `#FFFFFF` | Neutral-10  |


### Background


| Token        | Hex       | Palette Ref |
| ------------ | --------- | ----------- |
| bg-weak      | `#FFFFFF` | Neutral-10  |
| bg-default   | `#F5F6F6` | Neutral-15  |
| on-bg-weak   | `#F5F6F6` | Neutral-15  |
| bg-strong    | `#E2E3E5` | Neutral-20  |
| bg-stronger  | `#A8ACB2` | Neutral-35  |
| bg-strongest | `#3C3F44` | Neutral-65  |
| bg-status    | `#A8ACB2` | Neutral-35  |


### Border


| Token            | Hex       | Palette Ref |
| ---------------- | --------- | ----------- |
| border-weak      | `#E2E3E5` | Neutral-20  |
| border-strong    | `#BBBEC3` | Neutral-30  |
| border-strongest | `#6F757E` | Neutral-50  |


### Hover & Pressed


| Token   | Hex       | Opacity | Palette Ref |
| ------- | --------- | ------- | ----------- |
| hover   | `#6F757E` | 10%     | Neutral-50  |
| pressed | `#6F757E` | 20%     | Neutral-50  |


---

## Primary / Info

All tokens reference the **Baltic** palette. Hover-weak and pressed-weak use opacity overlays; hover-strong, pressed-strong, and focus use solid hex values.

### Text & Icon


| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#0A6190` | Baltic-50   |
| icon  | `#0A6190` | Baltic-50   |


### Background


| Token       | Hex       | Palette Ref |
| ----------- | --------- | ----------- |
| bg-weak     | `#E7FAFB` | Baltic-10   |
| bg-strong   | `#0A6190` | Baltic-50   |
| bg-status   | `#4C99A4` | Baltic-40   |
| bg-selected | `#E7FAFB` | Baltic-10   |


### Border


| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#8FE3E8` | Baltic-20   |
| border-strong | `#0A6190` | Baltic-50   |


### Hover & Pressed


| Token          | Hex       | Opacity | Palette Ref |
| -------------- | --------- | ------- | ----------- |
| hover-weak     | `#30839D` | 8%      | Baltic-45   |
| pressed-weak   | `#30839D` | 12%     | Baltic-45   |
| hover-strong   | `#02507B` | —       | Baltic-55   |
| pressed-strong | `#014063` | —       | Baltic-60   |
| focus          | `#30839D` | —       | Baltic-45   |


---

## Danger

All tokens reference the **Hibiscus** palette. Hover-weak and pressed-weak use opacity overlays.

### Text & Icon


| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#BB2D00` | Hibiscus-45 |
| icon  | `#BB2D00` | Hibiscus-45 |


### Background


| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#FFE9E7` | Hibiscus-10 |
| bg-strong | `#BB2D00` | Hibiscus-45 |
| bg-status | `#E84E2C` | Hibiscus-35 |


### Border


| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#FFAA97` | Hibiscus-20 |
| border-strong | `#BB2D00` | Hibiscus-45 |


### Hover & Pressed


| Token          | Hex       | Opacity | Palette Ref |
| -------------- | --------- | ------- | ----------- |
| hover-weak     | `#D43300` | 8%      | Hibiscus-40 |
| pressed-weak   | `#D43300` | 12%     | Hibiscus-40 |
| hover-strong   | `#961200` | —       | Hibiscus-50 |
| pressed-strong | `#730E00` | —       | Hibiscus-55 |


---

## Warning

All tokens reference the **Lemon** palette. No hover/pressed states defined.

### Text & Icon


| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#765500` | Lemon-55    |
| icon  | `#765500` | Lemon-55    |


### Background


| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#FFFAD1` | Lemon-10    |
| bg-strong | `#765500` | Lemon-55    |
| bg-status | `#D7AA0A` | Lemon-40    |


### Border


| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#FFD600` | Lemon-30    |
| border-strong | `#996E00` | Lemon-50    |


---

## Success

All tokens reference the **Forest** palette. No hover/pressed states defined.

### Text & Icon


| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#3F7824` | Forest-45   |
| icon  | `#3F7824` | Forest-45   |


### Background


| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#E7FCD7` | Forest-10   |
| bg-strong | `#3F7824` | Forest-45   |
| bg-status | `#5B992B` | Forest-35   |


### Border


| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#90CB62` | Forest-20   |
| border-strong | `#3F7824` | Forest-45   |


---

## Discovery

All tokens reference the **Lavender** palette. No hover/pressed states defined.

### Text & Icon


| Token | Hex       | Palette Ref |
| ----- | --------- | ----------- |
| text  | `#5A34AA` | Lavender-45 |
| icon  | `#5A34AA` | Lavender-45 |


### Background


| Token     | Hex       | Palette Ref |
| --------- | --------- | ----------- |
| bg-weak   | `#E9DEFF` | Lavender-15 |
| bg-strong | `#5A34AA` | Lavender-45 |
| bg-status | `#754EC8` | Lavender-40 |


### Border


| Token         | Hex       | Palette Ref |
| ------------- | --------- | ----------- |
| border-weak   | `#B38EFF` | Lavender-25 |
| border-strong | `#5A34AA` | Lavender-45 |


