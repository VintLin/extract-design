---
name: extract-web-style
description: Use this skill when the user wants to extract a webpage's design language into a reusable HTML style reference file, including typography, colors, spacing, surfaces, components, states, themes, motion, and code-block styles. The output should be a universal style specimen HTML for future AI-generated pages, not a 1:1 copy of the original page.
---

# Extract Web Style

## When to use

Use this skill when the user wants to:

- 提取某个网页的视觉风格
- 让 AI 学习一个网站的设计语言并生成同风格页面
- 从网页中抽取字体、字号、字色、背景样式、动画、卡片样式、代码块样式
- 将网页风格沉淀为一个可复用的 HTML 参考文件
- 构建“设计样张页 / style specimen / design reference file”
- 将一个具体网页抽象成更通用的设计系统表达

Do **not** use this skill if the user wants:

- 仅截图网页
- 仅复制页面 DOM 或下载页面资源
- 仅修复某个单独 CSS 问题
- 仅做像素级 1:1 复刻

This skill is for **style system extraction**, not page cloning.

---

## Core principle

Your task is **not** to reproduce the page structure.

Your task is to extract the page's **visual system** and represent it as:

1. **Primitive tokens**
2. **Semantic tokens**
3. **Component archetypes**
4. **Interaction rules**
5. **A universal style specimen HTML**

The final result must be a **general-purpose reference file** that another AI can read and use to generate new pages in the same style.

Think in terms of:

- design tokens
- semantic roles
- theme layers
- component patterns
- state behavior
- motion language
- responsive rules

Do **not** think in terms of:

- copying all classes
- mirroring page DOM
- dumping raw CSS blindly
- preserving irrelevant content text

---

## Output contract

When using this skill, produce **three outputs**:

### Output A — Extraction summary
A concise explanation of the extracted style system:

- overall design character
- typography system
- color system
- spacing/layout rhythm
- surface/elevation language
- motion language
- component family
- theme/responsive behavior
- extraction confidence
- limitations

### Output B — Structured style manifest
A machine-readable structure describing:

- meta
- primitives
- semantic tokens
- themes
- motion tokens
- component archetypes
- responsive rules
- accessibility notes
- limitations

Use JSON or JSON-like structured data when useful.

### Output C — Universal style specimen HTML
A single HTML file containing:

- CSS tokens
- theme layers
- component styles
- specimen sections
- a design manifest in `<script type="application/json">`
- optional minimal demo scripts for theme switching / state preview

This HTML file should be general and reusable.

---

## Required extraction dimensions

You must extract the following categories.

### 1. Meta context
Capture:

- source URL if available
- page title
- capture time/context
- viewport size
- whether dark mode exists
- whether reduced motion behavior exists
- whether the page uses heavy canvas/WebGL/video-only visuals
- whether shadow DOM/custom elements are present
- whether the extraction is from live render or static code

### 2. Typography
Extract:

- primary font family
- fallback stack
- mono/code font family
- font weights
- size scale
- line heights
- letter spacing
- paragraph rhythm
- link styles
- prose/body styles
- heading hierarchy
- button/label/input text styles

Do not only report raw values. Abstract them into roles such as:

- `--font-family-sans`
- `--font-family-mono`
- `--font-size-body`
- `--font-size-heading-lg`
- `--line-height-body`
- `--font-weight-semibold`

### 3. Color system
Extract:

- page background
- surface/background layers
- card backgrounds
- overlay/scrim
- primary text
- secondary text
- inverse text
- muted text
- borders/dividers
- brand/accent colors
- interactive colors
- success/warning/error/info
- code block background and syntax colors
- gradients
- translucent layers
- blur/frosted surface styles

Abstract colors into semantic roles, not just raw hex values.

Examples:

- `--color-bg-page`
- `--color-surface-card`
- `--color-text-primary`
- `--color-text-secondary`
- `--color-border-default`
- `--color-brand-primary`
- `--color-code-bg`

### 4. Spacing and layout
Extract:

- container widths
- grid behavior
- gutter
- section spacing
- component padding
- gap rhythm
- common stack spacing
- alignment preferences
- desktop/tablet/mobile changes

Abstract into spacing and layout tokens.

### 5. Surface / shape / elevation
Extract:

- border radius scale
- border treatments
- shadow scale
- backdrop blur
- surface layering
- z-index/elevation feel
- outline/focus ring style

Examples:

- `--radius-sm`
- `--radius-card`
- `--shadow-sm`
- `--shadow-elevated`
- `--focus-ring`

### 6. Motion
Extract:

- transition durations
- easing curves
- delays
- common hover motion
- enter/exit animation styles
- transform language
- opacity motion
- reduced motion fallback
- loading/skeleton movement
- scroll-linked effects if visually important

Abstract into motion tokens.

Examples:

- `--motion-duration-fast`
- `--motion-duration-normal`
- `--motion-ease-standard`
- `--motion-ease-emphasized`

Also summarize animation archetypes such as:

- fade in
- slide up
- scale in
- subtle glow
- hover lift
- underline reveal

### 7. Component archetypes
Extract reusable component families rather than page-specific instances.

At minimum inspect:

- page/container sections
- nav/header/footer
- buttons
- links
- cards
- badges/tags/chips
- inputs/textareas/selects
- switches/checkboxes/radios
- tabs/accordions
- tables
- alerts/callouts
- modals/drawers/popovers/tooltips
- lists/media rows
- empty states
- stat cards
- code blocks
- inline code
- toasts/skeletons if present

For each component archetype record:

- structure/slots
- visual DNA
- spacing
- radius
- border/shadow
- default state
- hover
- focus-visible
- active
- selected
- disabled
- loading
- theme variants
- compact/comfortable variants if visible

### 8. Code block system
This is mandatory if code blocks exist or may matter later.

Extract:

- code font
- code size
- line height
- block background
- border/radius
- padding
- title bar / filename strip
- line-number style
- inline code style
- syntax color family
- copy button / toolbar style
- highlighted line style

### 9. Responsive and theme rules
Capture:

- breakpoints
- type scaling across breakpoints
- spacing changes across breakpoints
- layout collapse/stack behavior
- theme variants
- dark mode
- reduced motion handling
- print behavior if visible or inferable

---

## Extraction method

### Rule 1: Prefer rendered reality over source intent
Use the final rendered/computed result as the ground truth.

Prioritize:

- actual visible DOM
- computed styles
- pseudo elements
- measured layout
- live states
- effective animations

Do not rely solely on authored CSS.

### Rule 2: Cluster before naming
Do not emit a token for every distinct observed value.

Instead:

1. collect raw values
2. group near-equivalent visual values
3. infer the system
4. assign semantic names

Example:

Bad:
- `--blue-1`
- `--blue-2`
- `--blue-3`
- `--text-gray-7`

Better:
- `--color-brand-primary`
- `--color-link-default`
- `--color-link-hover`
- `--color-text-secondary`

### Rule 3: Extract semantic roles, not only raw values
A useful reference file must explain **what a value does**, not only **what the value is**.

Always try to map raw observations into roles.

### Rule 4: Extract states actively
Do not assume the static DOM shows all relevant UI states.

If possible, inspect or infer:

- hover
- focus-visible
- active
- selected
- open
- disabled
- loading

If a state cannot be reliably observed, label it as inferred or unavailable.

### Rule 5: Build archetypes, not clones
If you see 11 cards, do not export 11 card classes unless they are meaningfully distinct.

Instead compress them into a small set of archetypes, for example:

- card/plain
- card/bordered
- card/elevated
- card/interactive
- card/stat

### Rule 6: Separate content from style
The specimen file should use neutral placeholder content.

Do not preserve source page copy unless the user explicitly asks.

### Rule 7: Report uncertainty honestly
If some styles are not reliably extractable, say so.

Typical limitations include:

- cross-origin stylesheet access issues
- canvas/WebGL-only visuals
- video-only backgrounds
- runtime-only transitions not visible in current state
- visited-link privacy behavior
- hard-to-observe interaction states

---

## Recommended extraction workflow

### Step 1 — Characterize the page
Summarize:

- minimal / editorial / dashboard / marketing / docs / product / playful / brutalist / glassmorphism / etc.
- density
- contrast
- tone
- motion intensity
- component complexity

### Step 2 — Gather raw observations
Collect all observed values for:

- fonts
- colors
- spacing
- radius
- shadows
- borders
- durations
- easings
- layout widths

### Step 3 — Normalize into primitives
Reduce noise and create primitive tokens.

### Step 4 — Map to semantic tokens
Assign role-based names.

### Step 5 — Build component archetypes
Identify reusable component families.

### Step 6 — Derive interaction rules
Summarize the state transitions and motion behavior.

### Step 7 — Build the specimen HTML
Create a general-purpose design reference page.

### Step 8 — Validate usefulness
Ask:
- Could another AI use this to generate a new page in the same style?
- Does it capture the system rather than only one page?
- Does it include tokens, themes, components, states, motion, and code blocks?

If not, revise.

---

## Required HTML specimen structure

The final universal reference HTML should generally contain:

1. `:root` primitive tokens
2. semantic theme blocks such as:
   - `[data-theme="light"]`
   - `[data-theme="dark"]`
3. component archetype CSS
4. specimen sections showing:
   - colors
   - typography
   - spacing/layout
   - surfaces
   - buttons
   - cards
   - forms
   - navigation
   - tables
   - prose/content
   - code blocks
   - overlays
   - alerts/toasts
   - motion examples
5. a machine-readable manifest:
   - `<script type="application/json" id="design-manifest">...</script>`

The specimen file should act as both:
- a human-readable design guide
- a machine-readable style source

---

## Required specimen sections

The HTML should include these sections whenever possible:

- Color board
- Typography scale
- Spacing/layout board
- Surface/elevation board
- Buttons
- Cards
- Forms
- Navigation
- Table/content/prose
- Code blocks
- Alerts/callouts
- Overlay components
- Motion preview
- Theme switch demo

---

## Quality bar

A good extraction should satisfy all of the following:

- It explains the style system clearly
- It uses semantic naming
- It separates primitives from semantic roles
- It includes major states and variants
- It supports theme/responsive behavior where relevant
- It contains a reusable specimen HTML
- It is useful for future AI page generation
- It explicitly reports limitations and uncertainty

A bad extraction usually looks like:

- raw CSS dump
- copied DOM
- no semantic tokens
- no component abstraction
- no states
- no dark mode / responsive thinking
- no machine-readable manifest
- no code-block treatment

---

## Response format

When responding, prefer this structure:

### 1. 风格判断
Brief summary of the page’s visual character.

### 2. 提取结果
Structured extraction summary by category.

### 3. 设计清单
A structured manifest of tokens/components/rules.

### 4. 通用 HTML 参考文件
Provide the HTML specimen file.

### 5. 局限与风险
Explain what could not be reliably extracted.

---

## Special instruction

If the user asks for “通用化、可复用、可给 AI 参考”的输出:

- prioritize abstraction over exact fidelity
- prefer semantic tokens over raw CSS
- include placeholders rather than original page content
- include representative components beyond what appears on the page when they are clearly implied by the style system
- make the reference file broad enough for future page generation, but do not fabricate wildly inconsistent UI

The goal is:
**same design language, not same page.**