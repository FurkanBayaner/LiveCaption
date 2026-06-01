## LIVE CAPTION - UI DESIGN SPECIFICATION ##

# 1. Control Panel
# 1.1 Window
| Property | Value |
|---|---|
| Title bar text | `Live Caption` |
| Background color | `#1e1e1e` dark black |
| Title bar color | Dark/black, forced through Windows DWM dark mode |
| Window size | Fixed, not resizable |
| Large internal heading | NONE, settings start directly from the top |

# 1.2 General Layout
```text
+-------------------------------------+
|  Font Family        Font Size        |
|  [ComboBox]         [ComboBox]       |
|                                      |
|  Letter Spacing     Line Spacing     |
|  [ComboBox]         [ComboBox]       |
|                                      |
|  Speaker Color      Text Color       |
|  [ComboBox]         [ComboBox]       |
|                                      |
|  Font Weight        Translation      |
|  [Toggle Switch]    [ComboBox]       |
|                                      |
|  Background Opacity              %0  |
|  [===========o==================]    |
|                                      |
|  [STOP] [START ASR] [START OCR]      |
+-------------------------------------+
```

**Rules:**
- 2 columns, both columns have equal width.
- Each group has a small gray label on top and the control component below it.
- Vertical spacing between all groups is equal.
- Background Opacity row: label + percentage value on the top row, full-width slider below.
- Buttons are at the bottom, 3 equal-width buttons side by side.

# 1.3 Control Components
- All ComboBoxes use the same style.

| Control | Default | Options |
|---|---|---|
| **Font Family** | Arial | Arial, Tahoma, Segoe UI, Verdana, Calibri, Bahnschrift |
| **Font Size** | 20px | 12px to 40px, step 2 (12, 14, 16 ... 40) |
| **Letter Spacing** | 0px | -2px to 10px, step 1 (-2, -1, 0, 1 ... 10) |
| **Line Spacing** | 1.2 | 1.0 to 2.5, step 0.1 (1.0, 1.1, 1.2 ... 2.5) |
| **Speaker Color** | Light Yellow | White, Light Yellow, Light Gray, Black, Dark Gray, Blue, Green, Red |
| **Text Color** | White | White, Light Yellow, Light Gray, Black, Dark Gray, Blue, Green, Red |
| **Translation Engine** | Qwen3 1.7B | Qwen3 1.7B, Qwen3.5 2B, Gemma 2 2B, Qwen2.5 Coder 1.5B, Gemma 3 1B, Llama 3.2 1B, MarianMT |

**ComboBox visual rules:**
- Background: `#2b2b2b`
- Border: `1px solid #3a3a3a`
- Hover border: `1px solid #0078d7` blue
- Dropdown background: `#252525`
- Selected item: `#0078d7`
- Hover item: `#3a3a3a`
- Arrow icon: none, plain appearance

# Toggle Switch - Font Weight
- Default: **off**
- Appearance: horizontal pill-shaped switch (`40px x 20px`, border radius `10px`)
- Off background: `#3d3d3d`, border: `#555555`
- On background: `#0078d7`, border: `#005a9e`
- Label (`Active`) is on the left of the switch, indicator is on the right
- PyQt5 component: `QCheckBox`; `setLayoutDirection(Qt.RightToLeft)` places the indicator on the right, and CSS gives it the pill shape

# Slider - Background Opacity
- Default: **0%**
- Range: 0-100
- Row layout:
  - Top row: `"Background Opacity"` label on the left, dynamic `"%0"` value label on the right
  - Bottom row: full-width slider spanning both columns
- Slider behavior: **Jump**; clicking any point immediately jumps there, dragging also works
- Visual: thin `4px` groove, `16px` circular handle, filled section in blue (`#0078d7`)
- PyQt5 component: `QSlider`; jump behavior is added by overriding `mousePressEvent`

### 1.4 Buttons
| Button | Position | Default color | Hover color |
|---|---|---|---|
| **STOP** | Left | Dark red background `#3a1a1a`, text `#e05555` | Full red `#c0392b`, white text |
| **START ASR** | Middle | Dark blue background `#1a2a3a`, text `#5599dd` | Full blue `#0078d7`, white text |
| **START OCR** | Right | Dark green background `#1a3020`, text `#55aa77` | Full green `#28a745`, white text |

**Disabled state** - ASR button while OCR is running, OCR button while ASR is running:
- Background: `#252525`
- Text: `#555555`
- Border: `#333333`

**General button style:**
- Padding: `11px 0px`
- Border radius: `5px`
- Font: bold, `13px`
- Three equal-width buttons side by side

### 1.5 Color Palette
| Name | HEX | Outline |
|---|---|---|
| White | `#FFFFFF` | `#000000` |
| Light Yellow | `#BCA21F` | `#000000` |
| Light Gray | `#A0A0A0` | `#000000` |
| Black | `#000000` | `#FFFFFF` |
| Dark Gray | `#414141` | `#FFFFFF` |
| Blue | `#1450C7` | `#FFFFFF` |
| Green | `#079444` | `#FFFFFF` |
| Red | `#B32F2F` | `#FFFFFF` |

These colors are used for both `Speaker Color` and `Text Color`.
When text is rendered in the overlay, both the HEX color and the outline color are applied.
The color name to HEX + outline mapping is defined in code as a `dict`; the ComboBox displays only the names.

### 1.6 General Typography and Color
| Element | Value |
|---|---|
| Window background | `#1e1e1e` |
| General text color | `#e0e0e0` |
| Label color | `#888888` gray, muted |
| Font family | `Segoe UI`, fallback `Arial` |
| Label font size | `12px` |
| Control font size | `13px` |

# 2. OCR Selection Screen
# 2.1 Behavior
It opens when the `START OCR` button is clicked. It is a full-screen, frameless window.

# 2.2 Visual Structure
```text
+--------------------------------------------------+
|  [............... DIMMED AREA .................] |
|                                                  |
|      +------------------------------------+      |
|      |   TRANSLATION AREA (Orange)        |      |
|      +------------------------------------+      |  <- seam line, thin double line
|      |   SUBTITLE AREA (Blue)             |      |
|      +------------------------------------+      |
|                                                  |
|                 [CANCEL] [CONFIRM]              |
+--------------------------------------------------+
```

# 2.3 Rules
**Screen dimming:**
- Outside the selected area: semi-transparent black `rgba(0,0,0,150)`
- Selected two-box region: transparent, normal view

**Two boxes:**
- The user drags with the mouse to select the **SUBTITLE** area
- The **TRANSLATION** area is created automatically: directly above the subtitle box, with exactly the same width and height
- Subtitle box: blue border `#2980B9` (`2.5px`)
- Translation box: orange border `#D35400` (`2.5px`)

**Seam line, the connection point between the two boxes:**
- On the horizontal line where the two boxes meet, a thin orange and blue line appears side by side (`1.5px`)
- Visually indicates that the two boxes are attached to each other

**Dynamic title label:**
- When selection starts, a dark draggable label box appears at the top-left of the selection box
- It contains `SUBTITLE` in blue, `-` in white, and `TRANSLATION` in orange
- Font: `Segoe UI`, bold, `11px`
- Label background: `rgba(44, 62, 80, 230)`
- Border radius: `6px`

**Mouse cursor:** `CrossCursor` while the selection screen is open

# 2.4 Buttons
After the selection is completed, buttons appear at the bottom-right corner of the selection box:

| Button | Color | Function |
|---|---|---|
| **CANCEL** | Red `#c0392b` | Close the selection screen and return to the control panel |
| **CONFIRM** | Green `#27ae60` | Send coordinates to the system and start the pipeline |

- Fixed size: `80px x 32px`
- Font: bold
- Border radius: `4px`
- Position: aligned to the bottom-right corner of the selection box, with boundary protection against screen overflow

# 3. ASR Selection Screen
# 3.1 Behavior
It opens when the `START ASR` button is clicked. It is a full-screen, frameless window.
Difference from OCR selection screen: **one box** is selected, only the translation overlay area.

# 3.2 Visual Structure
```text
+--------------------------------------------------+
|  [............... DIMMED AREA .................] |
|                                                  |
|      +------------------------------------+      |
|      |     TRANSLATION OVERLAY AREA       |      |
|      +------------------------------------+      |
|                                                  |
|                 [CANCEL] [CONFIRM]              |
+--------------------------------------------------+
```

# 3.3 Rules
- Screen dimming: same as OCR (`rgba(0,0,0,150)`)
- Single box: orange border (`#D35400`, `2.5px`), same style as the OCR translation box
- There is no subtitle box, because ASR does not read text from the screen
- Mouse cursor: `CrossCursor`
- Buttons: exactly the same as OCR (`CANCEL` / `CONFIRM`)

# 4. Overlay Windows (General Rules)
Both OCR and ASR overlays follow the same technical rules:

| Property | Value / Method |
|---|---|
| Frame | None (`FramelessWindowHint`) |
| Always on top | `WindowStaysOnTopHint` |
| Transparent background | `WA_TranslucentBackground` |
| Click-through | `WindowTransparentForInput`; mouse clicks pass through the overlay |
| 2K DPI drift prevention | `QScreen.devicePixelRatio()` is queried and coordinates are corrected accordingly |
| Sentence background | Only behind the text; it does not cover the whole box, only the area behind that sentence |
| Sentence background opacity | Changes instantly between `0%-100%` with the control panel slider |

# 5. General Design Rules
- Design changes are made only in `theme.qss`; `.py` files are not touched for styling changes
- Every setting change from the control panel is instantly reflected in the active overlay; the pipeline is not restarted
- While OCR is running, the `START ASR` button switches to the `disabled` appearance and its text does not change; only the style changes, managed by `pipeline_manager`
- While ASR is running, the `START OCR` button becomes disabled in the same way
- After a selection is made and `CONFIRM` is clicked, the control panel remains minimized in the taskbar and does not close
