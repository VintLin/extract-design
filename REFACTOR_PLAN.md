# Extract Design 重构计划

## 结论

`extract-design` 应从“单个 HTML style specimen 生成 skill”重构为“证据驱动的网页设计风格提取流水线”。

第一轮重构只做 v1：单 URL 输入、证据目录、稳定 manifest、style guide、style specimen、starter tokens、基础校验。  
多 URL、截图输入、DNA JSON 合成、DESIGN.md 导出、审计评分、参数化 specimen 放入 v2 backlog。

核心目标是让输出可追溯、可验证、可迁移，而不是扩大功能面。

## 范围

### v1 范围

v1 只支持：

- 单个公开 URL。
- 从目标页面采集静态样式、状态样式和有意义的 motion。
- 输出到调用时目标项目根目录下的 `outputs/extractions/<name>/`。
- 通过 `--out-dir` 覆盖输出目录。
- 生成 style guide、evidence manifest、style manifest、style specimen、starter tokens。
- 提供基础 validation，包含 strict / warning 两种模式。

v1 不支持：

- 多 URL 合成。
- 截图 / 图片作为主输入。
- URL + 截图混合输入。
- 已有 manifest / DNA JSON 合成。
- 完整组件库生成。
- 像素级复刻。
- 登录态页面的默认采集。

### v2 Backlog

以下内容有价值，但不进入第一轮重构验收：

- `artifacts/DESIGN.md` 和 `artifacts/design-sidecar.json` 导出。
- 多 URL / 多截图合成。
- conflict handling：`dominant` / `variant` / `rejected`。
- extraction audit 评分。
- 参数化 specimen：density、theme、motion on/off、radius scale、spacing scale。
- 从已有 manifest / DNA JSON 再生成。
- 面向代码项目的 `init` 模式。

v2 内容可以保留在设计文档中，但不得阻塞 v1 的实现和验收。

## 现状

当前项目结构：

```text
extract-design/
  SKILL.md
  README.md
  scripts/
    extract-styles.py
    extract-keyframes.py
  references/
    extraction-checklist.md
    style-specimen.html
  assets/
    theme/
      *-style-manifest.json
      *-style-specimen.html
```

当前优点：

- 目标明确：提取网页视觉系统，而不是复刻页面。
- 已覆盖 typography、colors、spacing、surfaces、components、states、themes、motion、background、motifs。
- `style-specimen.html` 的方向正确，适合作为后续生成页面的视觉参考。
- 现有示例 manifest 已能表达背景氛围、motif 和动效。

当前问题：

- `SKILL.md` 过长，混合触发条件、流程、schema、工具说明和质量标准。
- 输出写入 skill 自身的 `assets/theme/`，长期使用会污染 skill 仓库。
- 缺少证据目录，无法追溯截图、CSS/JS、交互记录和置信度。
- `extract-styles.py` 采样面较窄，只抽首个 button/card，状态矩阵不足。
- `extract-keyframes.py` 文档和实现不一致，文档写 `--out`，脚本实际使用位置参数。
- `extract-keyframes.py` shebang 绑定本机 Python 路径，不适合跨机器使用。
- manifest schema 尚未版本化，缺少 evidence 引用、confidence、raw / normalized 分层。
- 缺少自动校验，无法检查 placeholder、空对象、manifest/specimen 同步和状态遗漏。
- README 与 `SKILL.md` 的输出路径说明需要同步更新。

## 输出目录

### 默认位置

v1 默认输出到“调用时目标项目根目录”：

```text
<target-project-root>/outputs/extractions/<name>/
```

目标项目根目录的定义：

- 如果用户明确指定项目目录，以该目录为 root。
- 如果用户只给 URL，默认使用当前工作目录。
- CLI 和文档都必须支持 `--out-dir` 覆盖。
- `--out-dir` 可为绝对路径，也可为相对当前工作目录的路径。

不要再把真实提取产物写入：

```text
assets/theme/
```

### 目录结构

v1 输出结构：

```text
outputs/extractions/<name>/
  guides/
    style-guide.md
    evidence-manifest.md
    motion-guide.md
  evidence/
    screenshots/
    assets/
    notes/
  artifacts/
    style-manifest.json
    style-specimen.html
    tokens.json
    tokens.css
  raw/
    computed-styles.json
    keyframes.json
    transition-scan.json
    interaction-diff.json
```

合法例外：

- 无有意义 motion 时，不生成 `guides/motion-guide.md`。
- 无有意义 motion 时，仍必须在 `guides/evidence-manifest.md` 和 `artifacts/style-manifest.json` 的 `limitations` 中说明。
- CORS、权限或动态渲染导致无法保存 CSS/JS 时，必须在 `evidence-manifest.md` 记录缺口。

### `.gitignore` 策略

真实运行产物默认不进入版本管理：

```gitignore
/outputs/
```

可维护示例进入：

```text
examples/<name>/
```

迁移规则：

- 现有 `assets/theme/*` 中值得保留的示例迁移到 `examples/<name>/`。
- `assets/theme/` 不再作为默认输出目录。
- README 和 `SKILL.md` 必须说明 `outputs/` 是运行产物，`examples/` 是版本化示例。

## 产物职责边界

### 脚本生成

脚本负责可重复、可校验的数据：

- `raw/computed-styles.json`
- `raw/keyframes.json`
- `raw/transition-scan.json`
- `raw/interaction-diff.json`
- `artifacts/tokens.json`
- `artifacts/tokens.css`
- `artifacts/style-specimen.html` 的基础版本
- `evidence/evidence-index.json`
- `guides/evidence-manifest.md` 的基础 inventory
- validation 报告

脚本可以生成 `artifacts/style-manifest.json` 的初稿，但不得伪造判断。无法确定的字段用 `unavailable`、`unknown` 或 `limitations` 表达。

`evidence-index.json` 是机器可读清单，必须反映文件实际存在状态。`evidence-manifest.md` 可以由脚本从 index 生成基础版，至少列出截图、CSS/JS、raw 文件、交互记录、采集失败项和用途。

### Agent 撰写

agent 负责需要判断和抽象的内容：

- `guides/style-guide.md`
- `guides/evidence-manifest.md` 中的 interpretation、gaps、reuse decision
- `guides/motion-guide.md`（仅有 motion 时）
- `artifacts/style-manifest.json` 中的语义映射、风格描述、Reusable / Adapted / Discarded 判断
- 证据不足时的风险说明

### 模板半自动生成

`style-specimen.html` 使用模板 + manifest 生成：

- 视觉展示由模板负责。
- token 和组件数据来自 manifest / tokens。
- 生成后必须校验无 `/* REPLACE */`、无空白章节、无与 manifest 冲突的组件说明。

## v1 Manifest Schema

`references/schema.md` 是实现验证器的依据，不是说明性草图。Milestone 1 必须提供 JSON Schema；如果暂不引入 JSON Schema 文件，也必须提供等价字段表，覆盖字段名、类型、必填、枚举、默认值、数组 item contract、evidence 引用、tokens 映射和完整样例。

### 顶层结构

v1 schema 使用 `schemaVersion: "2.0"`。

```json
{
  "schemaVersion": "2.0",
  "meta": {
    "name": "example",
    "sourceUrl": "https://example.com",
    "capturedAt": "2026-05-22T00:00:00Z",
    "generator": "extract-design",
    "mode": "single-url"
  },
  "evidence": {
    "items": []
  },
  "rawSources": [],
  "design_system": {
    "colors": [],
    "typography": [],
    "spacing": [],
    "radii": [],
    "shadows": [],
    "borders": []
  },
  "design_style": {
    "mood": [],
    "composition": [],
    "density": "unknown",
    "visual_language": [],
    "generation_guidance": []
  },
  "visual_effects": [],
  "components": [],
  "motion": {
    "present": false,
    "patterns": []
  },
  "responsive_rules": [],
  "accessibility_notes": [],
  "reuse_filter": [],
  "limitations": []
}
```

### 必填字段

v1 必填：

- `schemaVersion`
- `meta.name`
- `meta.sourceUrl`
- `meta.capturedAt`
- `meta.mode`
- `evidence.items`
- `rawSources`
- `design_system`
- `design_style`
- `components`
- `motion.present`
- `reuse_filter`
- `limitations`

v1 可选：

- `responsive_rules`
- `accessibility_notes`
- `visual_effects`
- `motion.patterns`

可选字段为空时，应说明原因。不要留下无解释的 `{}` 或 `[]`。

### Schema 文档交付要求

`references/schema.md` 必须包含：

- JSON Schema 或等价字段表。
- 每个数组项的 item contract。
- 每个枚举字段的允许值。
- evidence 引用格式和校验规则。
- tokens 映射规则。
- 一个完整合法样例，覆盖 color、typography、component state、motion、visual effect、raw source、limitation。
- 一个最小合法样例，覆盖无 motion 的静态页面。

validation strict mode 只实现 schema 中已经定义的硬规则。人工判断类规则放入 warning。

### Evidence 引用格式

所有关键判断必须引用 evidence。

引用格式：

```text
ev:<category>/<id>
```

示例：

```json
{
  "id": "color.primary",
  "value": "#111827",
  "role": "text-primary",
  "confidence": {
    "level": "high",
    "method": "measured",
    "evidence": ["ev:computed/body-text", "ev:screenshot/home-hero"]
  }
}
```

`evidence.items[]` 最小结构：

```json
{
  "id": "ev:screenshot/home-hero",
  "type": "screenshot",
  "path": "evidence/screenshots/home-hero.png",
  "description": "Homepage hero area at 1440px viewport",
  "capturedAt": "2026-05-22T00:00:00Z"
}
```

允许的 `type`：

- `screenshot`
- `computed-style`
- `stylesheet`
- `script`
- `interaction`
- `animation`
- `manual-note`

### Item Contracts

以下字段必须在 `references/schema.md` 中完整定义。这里给出 v1 最小契约。

#### `rawSources[]`

必填字段：

- `id`：字符串，格式 `raw:<category>/<id>`。
- `type`：枚举，`computed-styles`、`stylesheet`、`script`、`keyframes`、`transition-scan`、`interaction-diff`、`screenshot-index`。
- `path`：相对 extraction 根目录的路径。
- `generatedBy`：脚本名或 `manual`。
- `capturedAt`：ISO 8601 时间。
- `evidence`：`ev:<category>/<id>` 数组。

可选字段：

- `sourceUrl`
- `status`：枚举，`available`、`partial`、`unavailable`。
- `unavailableReason`

#### `design_system.colors[]`

必填字段：

- `id`：稳定 ID，如 `color.text.primary`。
- `value`：颜色值，优先 hex 或 CSS Color 4 可解析格式。
- `role`：枚举，`background`、`surface`、`text`、`muted-text`、`border`、`accent`、`state`、`overlay`、`decorative`。
- `usage`：一句话说明适用位置。
- `token`：tokens 映射，如 `--color-text-primary`。
- `confidence`

可选字段：

- `aliases`：其他近似 token 名。
- `contrastOn`：与背景色的对比信息。
- `sourceCount`：测量样本数量。

tokens 映射规则：

- `token` 必须能在 `artifacts/tokens.css` 中找到同名 CSS custom property。
- `artifacts/tokens.json` 必须有等价路径，如 `color.text.primary.value`。
- 同一 `token` 不允许映射到多个不同 `value`，除非标注 theme。

#### `design_system.typography[]`

必填字段：

- `id`：稳定 ID，如 `type.heading.h1`。
- `role`：枚举，`display`、`heading`、`body`、`caption`、`label`、`code`。
- `fontFamily`
- `fontSize`
- `lineHeight`
- `fontWeight`
- `letterSpacing`
- `token`：tokens 映射前缀或对象路径。
- `confidence`

可选字段：

- `textTransform`
- `fontStyle`
- `sampleText`
- `sourceCount`

tokens 映射规则：

- 字号、行高、字重、字距要能映射到 `tokens.json`。
- `tokens.css` 至少输出常用 CSS 变量，如 `--font-body`、`--type-body-size`。

#### `design_system.spacing[]`

必填字段：

- `id`：稳定 ID，如 `space.4`、`space.section.md`。
- `value`：CSS 长度值，v1 只允许 `px`、`rem`、`em` 或 `0`。
- `role`：枚举，`scale`、`gap`、`padding`、`margin`、`section`、`layout`、`component`。
- `usage`：一句话说明适用位置，如 `card internal padding`、`grid column gap`。
- `token`：tokens 映射，如 `--space-4`。
- `evidence`
- `confidence`

可选字段：

- `sourceCount`：测量样本数量。
- `aliases`：其他近似 token 名。
- `axis`：枚举，`x`、`y`、`both`。
- `responsiveVariants`：断点到值的映射。

单位规则：

- `value` 必须是单一 CSS 长度值，不接受 `calc()`、百分比或多值 shorthand。
- `0` 不带单位；非零值必须带单位。
- 同一 spacing scale 中应优先统一单位。若原站混用 `px` 和 `rem`，normalized 值必须选择一种主单位，并在 `usage` 或 `limitations` 说明换算依据。

tokens 映射规则：

- `token` 必须能在 `artifacts/tokens.css` 中找到同名 CSS custom property。
- `artifacts/tokens.json` 必须有等价路径，如 `space.4.value`。
- 同一 `token` 不允许映射到多个不同 `value`，除非记录在 `responsiveVariants` 或 theme 结构中。

#### `design_system.radii[]`

必填字段：

- `id`：稳定 ID，如 `radius.sm`、`radius.button`。
- `value`：CSS border-radius 长度值，v1 只允许 `px`、`rem`、`em`、`0` 或百分比。
- `role`：枚举，`none`、`small`、`medium`、`large`、`pill`、`circle`、`component`。
- `usage`：一句话说明适用位置，如 `button radius`、`card radius`、`avatar radius`。
- `token`：tokens 映射，如 `--radius-sm`。
- `evidence`
- `confidence`

可选字段：

- `sourceCount`
- `aliases`
- `cornerValues`：对象，包含 `topLeft`、`topRight`、`bottomRight`、`bottomLeft`。
- `responsiveVariants`

单位规则：

- `value` 必须是单一 CSS 长度值或百分比，不接受多值 shorthand。
- 如果原样式使用不同角值，normalized 项必须使用 `cornerValues` 分解，`value` 可写为主导值或 `mixed`。
- `circle` 只允许用于圆形元素，通常为 `50%`；`pill` 应来自固定高度组件的大半径值。

tokens 映射规则：

- `token` 必须能在 `artifacts/tokens.css` 中找到同名 CSS custom property。
- `artifacts/tokens.json` 必须有等价路径，如 `radius.sm.value`。
- `cornerValues` 存在时，tokens 中必须保留分解后的四角值或明确标注 `mixed`。

#### `design_system.shadows[]`

必填字段：

- `id`：稳定 ID，如 `shadow.sm`、`shadow.card.hover`。
- `value`：可解析的 CSS `box-shadow` 值，或 `none`。
- `role`：枚举，`none`、`surface`、`raised`、`floating`、`overlay`、`focus`、`ambient`、`component-state`。
- `usage`：一句话说明适用位置，如 `card elevation`、`popover shadow`。
- `token`：tokens 映射，如 `--shadow-sm`。
- `evidence`
- `confidence`

可选字段：

- `sourceCount`
- `aliases`
- `layers`：分解后的阴影层数组。
- `state`：枚举，`default`、`hover`、`active`、`focus-visible`、`open`。

CSS 值格式规则：

- `value` 必须是合法 `box-shadow` 字符串，包含 offset、blur、spread 和 color，或为 `none`。
- 多层阴影允许用逗号分隔；为了便于验证，应同时提供 `layers` 分解。
- `layers[]` 建议字段：`x`、`y`、`blur`、`spread`、`color`、`inset`。长度值遵循 spacing 单位规则。
- 不能把 `filter: drop-shadow()` 写入 `shadows[]`；这类效果应进入 `visual_effects[]` 或单独 limitations。

tokens 映射规则：

- `token` 必须能在 `artifacts/tokens.css` 中找到同名 CSS custom property。
- `artifacts/tokens.json` 必须有等价路径，如 `shadow.sm.value`。
- 多层阴影在 `tokens.json` 中应保留 `layers`，避免只保存不可分析的字符串。

#### `design_system.borders[]`

必填字段：

- `id`：稳定 ID，如 `border.default`、`border.focus`。
- `value`：可解析的 CSS border shorthand，或 `none`。
- `role`：枚举，`none`、`divider`、`outline`、`control`、`surface`、`focus`、`state`、`decorative`。
- `usage`：一句话说明适用位置，如 `input default border`、`table divider`。
- `token`：tokens 映射，如 `--border-default`。
- `evidence`
- `confidence`

可选字段：

- `sourceCount`
- `aliases`
- `width`
- `style`
- `color`
- `sides`：分解后的边数组或对象。
- `state`：枚举，`default`、`hover`、`active`、`focus-visible`、`disabled`、`invalid`。

CSS 值格式规则：

- `value` 必须是合法 CSS border shorthand，格式应能分解为 `width`、`style`、`color`，或为 `none`。
- `width` 必须是 CSS 长度值，v1 只允许 `px`、`rem`、`em` 或 `0`。
- `style` 必须是 CSS border style 枚举，如 `solid`、`dashed`、`dotted`、`none`。
- `color` 必须引用 `design_system.colors[].token`，或使用可解析颜色值并说明未归入 color token 的原因。
- 四边不一致时必须使用 `sides` 分解，不应只保留 shorthand。

tokens 映射规则：

- `token` 必须能在 `artifacts/tokens.css` 中找到同名 CSS custom property。
- `artifacts/tokens.json` 必须有等价路径，如 `border.default.value`。
- 若 `width`、`style`、`color` 分别输出 token，`value` token 必须能由这些子 token 组合得到。

#### `components[]`

必填字段：

- `id`：稳定 ID，如 `component.button.primary`。
- `name`
- `category`：枚举，`navigation`、`button`、`card`、`form`、`surface`、`content`、`feedback`、`overlay`、`custom`。
- `description`
- `anatomy`：组成部分数组。
- `states`：至少包含 `default`。
- `tokens`：组件使用的 token 引用数组。
- `evidence`
- `confidence`

可选字段：

- `selectors`
- `responsiveBehavior`
- `antiCloneNotes`

#### `components[].states[]`

必填字段：

- `name`：枚举，`default`、`hover`、`active`、`focus-visible`、`disabled`、`loading`、`selected`、`invalid`、`open`、`closed`。
- `properties`：归一化样式对象，至少包含发生变化或核心定义的属性。
- `evidence`
- `confidence`

可选字段：

- `motion`：引用 `motion.patterns[].id`。
- `unavailableReason`

规则：

- `default` 必须存在。
- 交互态存在于页面时必须采集；无法采集时写入 `unavailableReason` 和 `limitations`。
- `motion` 只能引用已存在的 motion pattern。

#### `motion.patterns[]`

必填字段：

- `id`：稳定 ID，如 `motion.hover.lift`。
- `trigger`：枚举，`hover`、`focus`、`click`、`scroll`、`load`、`route-change`、`state-change`、`ambient`。
- `properties`：变化属性数组。
- `durationMs`
- `easing`
- `source`：枚举，`transition`、`keyframes`、`web-animation`、`library`、`manual-observation`。
- `evidence`
- `confidence`

可选字段：

- `delayMs`
- `keyframeName`
- `library`
- `usage`
- `reducedMotionBehavior`

规则：

- `motion.present` 为 `true` 时，必须有至少一个 `motion.patterns[]`，除非 `limitations` 明确说明采集失败。
- `durationMs` 必须是数字或 `unknown`，不能混用字符串单位。

#### `visual_effects[]`

必填字段：

- `id`
- `type`：枚举，`canvas`、`webgl`、`shader`、`scroll-effect`、`cursor-effect`、`texture`、`noise`、`glow`、`mask`、`blend-mode`、`backdrop-filter`、`video`、`other`。
- `description`
- `reusableDecision`：枚举，`Reusable`、`Adapted`、`Discarded`。
- `evidence`
- `confidence`

可选字段：

- `implementationHint`
- `performanceRisk`
- `antiCloneNotes`

#### `limitations[]`

必填字段：

- `id`
- `severity`：枚举，`info`、`warning`、`error`。
- `area`：枚举，`access`、`cors`、`dynamic-rendering`、`motion`、`assets`、`privacy`、`schema`、`manual-judgment`、`other`。
- `message`
- `impact`

可选字段：

- `evidence`
- `nextStep`

规则：

- 无有意义 motion 时必须有一条 `area: "motion"` 的 limitation 或说明性记录。
- 任何 `unavailable` 字段都应关联一条 limitation。

### Confidence 格式

所有 normalized token、组件判断、motion pattern、visual effect 都应带 `confidence`。

```json
{
  "level": "high",
  "method": "measured",
  "evidence": ["ev:computed/button-primary"]
}
```

`level` 枚举：

- `high`：直接测量，多处证据一致。
- `medium`：直接测量但样本有限，或需要轻度归纳。
- `low`：主要来自人工判断、不可完整采集，或证据冲突。

`method` 枚举：

- `measured`
- `inferred`
- `manual`
- `unavailable`

### Raw 到 Normalized 映射

v1 必须保留 raw 和 normalized 的边界：

```text
raw/computed-styles.json
  -> design_system.colors
  -> design_system.typography
  -> design_system.spacing
  -> design_system.radii
  -> design_system.shadows
  -> components[].states

raw/keyframes.json
  -> motion.patterns

raw/transition-scan.json
  -> motion.patterns
  -> components[].states[].motion

raw/interaction-diff.json
  -> components[].states
  -> motion.patterns

evidence/screenshots/*
  -> design_style
  -> visual_effects
  -> reuse_filter
```

raw 文件保存测量事实。manifest 保存归一化后的可复用结论。

### Motion 与 Visual Effects 边界

v1 不在 `design_system` 内放 `motion`，避免重复。

边界如下：

- `motion`：时间、缓动、触发器、动画模式、交互状态变化。
- `visual_effects`：Canvas、WebGL、shader、scroll effect、cursor effect、texture、noise、glow、mask、blend mode、backdrop-filter 等特殊视觉效果。
- `components[].states[].motion`：组件状态中引用的 motion pattern。
- `design_style`：定性描述，如 calm、dense、editorial、technical，不放具体动画参数。

有 motion 时：

- 必须生成 `guides/motion-guide.md`。
- `motion.present` 为 `true`。
- `motion.patterns[]` 至少有一项，或在 `limitations` 说明为何无法提取。

无有意义 motion 时：

- 不生成 `guides/motion-guide.md`。
- `motion.present` 为 `false`。
- `guides/evidence-manifest.md` 记录检查过的交互。
- `limitations` 写明“未观察到有意义动效”或具体缺口。

## Reusable / Adapted / Discarded 过滤

去产品化必须提前到 Phase 0 / Phase 1，而不是归一化之后才做。

每个主要特征都要进入 `reuse_filter[]`：

```json
{
  "feature": "Hero split layout with product-specific copy",
  "decision": "Discarded",
  "reason": "Information architecture and copy are source-specific",
  "evidence": ["ev:screenshot/home-hero"]
}
```

决策枚举：

- `Reusable`：可直接作为风格规则使用。
- `Adapted`：保留视觉语言，但去掉产品结构、文案或品牌专属内容。
- `Discarded`：不进入复用风格。

过滤原则：

- 保留视觉语言。
- 去掉产品文案。
- 去掉原站信息架构。
- 不复制页面结构。
- 不把单页局部误判为全站设计系统。
- 不把 logo、商标、特定插图、专属摄影作为可复用资产。

## 推荐工作流

### Phase 0: 输入确认和边界过滤

确认：

- 单个目标 URL。
- 输出名称 `<name>`。
- 目标项目根目录。
- 是否通过 `--out-dir` 覆盖输出目录。
- 是否需要 starter tokens。
- 页面是否公开可访问。
- 是否涉及登录态、账号数据、用户私有信息或商业敏感内容。

同时建立初始 reuse filter：

- 哪些视觉特征可复用。
- 哪些需要改写后复用。
- 哪些必须丢弃。
- 哪些证据不应保存或需要用户审查。

### Phase 1: 静态证据采集

采集：

- baseline screenshot。
- navigation / active state screenshot。
- button default / hover / pressed。
- form default / focus / invalid。
- card / panel / surface。
- modal / popover / tooltip（如存在）。
- `html` / `body` / main wrapper computed styles。
- CSS custom properties。
- background-image / mask / filter / pseudo-element layers。
- typography samples。
- color samples。
- spacing / radius / shadow samples。

输出：

```text
raw/computed-styles.json
evidence/screenshots/
evidence/notes/
```

### Phase 2: 动效证据采集

仅当页面有明显 motion 时执行。

采集：

- `@keyframes`
- transition patterns
- hover / click / open / close before-after diff
- `document.getAnimations()` snapshot
- JS 动效库检测
- 必要时的 rAF sampling

输出：

```text
raw/keyframes.json
raw/transition-scan.json
raw/interaction-diff.json
guides/motion-guide.md
```

无有意义 motion 时，不生成 `motion-guide.md`，但必须记录检查结果。

### Phase 3: 归一化

把 raw evidence 转成 normalized model：

- 聚类相似颜色。
- 聚类字体和字号。
- 聚类 spacing / radius / shadow。
- 映射 semantic roles。
- 标注每个值的 evidence source。
- 标注 `measured` / `inferred` / `manual` / `unavailable`。
- 维护 `confidence`。
- 更新 `reuse_filter`。

输出：

```text
artifacts/style-manifest.json
artifacts/tokens.json
artifacts/tokens.css
```

### Phase 4: 指南和样张生成

生成：

```text
guides/style-guide.md
guides/evidence-manifest.md
artifacts/style-specimen.html
```

如果有 motion，额外生成：

```text
guides/motion-guide.md
```

`style-guide.md` 应包含：

- 风格概述。
- token 使用规则。
- 组件 archetype。
- `Generation Guidance`：适合什么页面、不适合什么页面、生成时必须保留和可调整的变量。
- 常见误用风险。

### Phase 5: 验证

验证内容：

- manifest JSON 可解析。
- manifest 满足 v1 schema。
- specimen 中没有 `/* REPLACE */`。
- component archetypes 和 specimen 展示一致。
- 每个 component 有状态矩阵。
- motion 存在时有 motion guide。
- motion 不存在时有 limitations 说明。
- 没有无解释的空对象 `{}` 和空数组 `[]`。
- evidence index 与实际文件一致。
- evidence manifest 中列出截图、脚本、交互测试和缺口。
- tokens.json / tokens.css 存在且与 manifest 基本一致。

## 脚本重构

### 运行环境策略

v1 优先保持无锁文件脚本模式，不新增项目级依赖，除非实现时确认必须新增。

README 必须说明：

- Python 版本要求。
- Playwright 或浏览器自动化要求。
- 需要安装浏览器驱动时的命令。
- 哪些脚本可在无网络环境下运行。
- 哪些脚本需要访问目标 URL。

如果新增依赖，必须在对应 milestone 中明确：

- 为什么需要。
- 替代方案。
- 新增 `requirements.txt` 或 `package.json` 的维护成本。

### `scripts/extract-styles.py`

当前问题：

- 采样范围太小。
- 缺少状态采样。
- 缺少 pseudo-element。
- 缺少截图输出。
- 缺少 raw / normalized 分层。

v1 改造：

- 支持 `--out-dir`。
- 输出 `raw/computed-styles.json`。
- 支持 selector 配置。
- 支持批量组件采样。
- 采集 `::before` / `::after`。
- 采集 background / mask / filter / backdrop-filter。
- 采集 container / section / card / nav / form / button / code block。
- 输出 confidence 和 unavailable 字段。

### `scripts/extract-keyframes.py`

当前问题：

- shebang 不可移植。
- CLI 和文档不一致。
- 只能访问 live page 的可读 stylesheet，CORS 时容易漏。

v1 改造：

```python
#!/usr/bin/env python3
```

支持：

```bash
python3 scripts/extract-keyframes.py <url-or-folder> --out raw/keyframes.json
```

模式：

- URL 模式：浏览器提取。
- folder 模式：解析已保存 CSS 证据，仅作为内部 fallback 或调试入口，不作为 v1 skill 主输入模式。

输出：

- keyframe name
- full cssText
- source file / source url
- usage hints
- unavailable reason

### 新增 `scripts/transition-scanner.js`

用途：

- 扫描所有 transition。
- 按 property + duration + easing 聚类。
- 输出 transition pattern。

运行环境需在 README 说明：浏览器控制台、Playwright page context 或 Node + browser automation，不允许文档和实现不一致。

### 新增 `scripts/interaction-diff.js`

用途：

- 记录交互前后 computed style 差异。
- 捕捉 transition 窗口中的 `document.getAnimations()`。
- 用于 hover、click、tabs、modal、nav active、scroll section。

### 新增 `scripts/library-detect.js`

用途：

- 检测 GSAP、Framer Motion、Swiper、AOS、Lottie、Three.js 等。
- 尽可能读取实例配置。
- 检测不到时输出 `unavailable`，不要推断。

### 新增 `scripts/validate-extraction.py`

用途：

- 校验输出目录完整性。
- 校验 manifest/specimen/style guide/motion guide/evidence manifest。
- 校验 schema。
- 校验 tokens 与 manifest 的基础一致性。

建议命令：

```bash
python3 scripts/validate-extraction.py outputs/extractions/<name>
python3 scripts/validate-extraction.py --strict outputs/extractions/<name>
```

模式：

- warning mode：适合早期迁移和人工修复，输出 warnings 但可通过。
- strict mode：适合发布前检查，关键缺失直接失败。

### 新增 `scripts/test-validation-fixtures.py`

用途：

- 自动运行 good / bad fixtures。
- 断言 good fixtures 返回 `0`。
- 断言 bad fixtures 返回非 `0`，并包含可定位 `[error]` finding。
- 避免预期失败命令污染普通验证流程或 CI。

## 文档重构

### `README.md`

README 面向使用者，说明：

- 这个 skill 做什么。
- v1 支持和不支持什么。
- 输出目录默认相对目标项目根目录。
- `--out-dir` 用法。
- `.gitignore` 建议。
- 基本命令。
- 示例输出。
- 运行环境。
- 与 `extract-design-system` / `style-extractor` 的区别。
- 第三方内容和隐私边界。

### `SKILL.md`

`SKILL.md` 面向 agent，保留：

- frontmatter description，必须同步新输出路径和 v1 范围。
- 触发条件。
- 不适用场景。
- 必读 reference。
- 工作流顺序。
- 输出要求。
- 安全边界。

不要把完整 schema 和长 checklist 放进 `SKILL.md`。

### `references/`

建议拆分：

```text
references/
  workflow.md
  output-contract.md
  schema.md
  extraction-checklist.md
  style-guide-template.md
  motion-guide-template.md
  evidence-manifest-template.md
  style-specimen.html
  validation-checklist.md
```

职责：

- `workflow.md`：完整提取流程。
- `output-contract.md`：目录结构和交付物要求。
- `schema.md`：v1 manifest schema 和样例。
- `extraction-checklist.md`：采集维度检查表。
- `style-guide-template.md`：风格指南模板。
- `motion-guide-template.md`：动效指南模板。
- `evidence-manifest-template.md`：证据清单模板。
- `style-specimen.html`：HTML 样张模板。
- `validation-checklist.md`：交付前检查。

## 分阶段实施

### Milestone 1: 结构整理

目标：

- 不改变核心能力，先调整输出目录、文档结构和 schema。

任务：

- 新增 `references/output-contract.md`。
- 新增 `references/workflow.md`。
- 新增 `references/schema.md`，包含最小可用 schema 和完整样例。
- 新增 guide 模板。
- 精简 `SKILL.md`。
- 同步 `SKILL.md` frontmatter description。
- 输出路径从 `assets/theme/` 改为 `outputs/extractions/<name>/artifacts/`。
- README 同步更新。
- 新增 `.gitignore` 规则：`/outputs/`。
- 将可维护示例从 `assets/theme/` 迁移到 `examples/<name>/`。

验证：

- `SKILL.md` 能独立说明调用顺序。
- `references/schema.md` 有完整样例。
- 示例目录语义清晰：`examples/` 是版本化示例，`outputs/` 是运行产物。

### Milestone 2: 脚本修正

目标：

- 修复明显不一致和不可移植问题。

任务：

- 修正 `extract-keyframes.py` shebang。
- 修正 `extract-keyframes.py` CLI 参数。
- 给 `extract-styles.py` 增加 `--out-dir`。
- 输出 raw JSON 到固定目录。
- 明确运行环境，不一致的 JS / Python 脚本说明必须修正。
- 新增基础 validation 脚本。
- 新增 validation fixture 测试入口。

验证：

```bash
python3 -m py_compile scripts/*.py
python3 scripts/validate-extraction.py examples/<sample>
python3 scripts/validate-extraction.py --strict examples/<sample>
python3 scripts/test-validation-fixtures.py
```

### Milestone 3: 证据系统

目标：

- 让每次提取可追溯。

任务：

- 新增 `evidence-manifest.md` 模板。
- 新增脚本生成的 `evidence/evidence-index.json`。
- `evidence-manifest.md` 基础 inventory 由脚本生成，agent 只补 interpretation、gaps、reuse decision。
- 增加截图清单要求。
- 增加 CSS/JS 资产保存规则。
- 增加 interactions tested 记录。
- 增加 confidence / gaps 记录。
- 增加第三方内容审查提示。

验证：

- 每个关键结论都能追溯到 `ev:<category>/<id>`。
- evidence manifest 能说明缺失证据和原因。

### Milestone 4: 状态和动效增强

目标：

- 补齐当前最弱的 state 和 motion。

任务：

- 加入 transition scanner。
- 加入 interaction diff。
- 加入 library detection。
- component state matrix 强制包含：
  - default
  - hover
  - active
  - focus-visible
  - disabled
  - loading / selected / invalid（存在时）
- 明确 motion guide 规则：有 motion 必须生成，无 motion 不生成但记录 limitations。

验证：

- 检测到有意义 motion 的页面必须生成 motion guide。
- 无动效页面必须在 evidence manifest 和 limitations 中说明。
- `components[].states` 引用对应 evidence。

### Milestone 5: tokens 和 specimen 稳定化

目标：

- 让产物能被下游项目作为 starter 使用。

任务：

- 生成 `tokens.json`。
- 生成 `tokens.css`。
- specimen 引用同一份 manifest。
- 校验 manifest 和 specimen 组件一致。
- 增加 copy-paste component examples。

验证：

- `tokens.json` 和 `tokens.css` 存在。
- tokens 与 `style-manifest.json` 的核心 token 一致。
- `style-specimen.html` 无 placeholder。
- 下游前端能导入 `tokens.css` 作为起点。

## 可执行验证方案

### Fixtures

新增：

```text
examples/
  good-static/
  good-motion/
  bad-missing-evidence/
  bad-placeholder-specimen/
```

用途：

- `good-static`：无 motion 的合法样例。
- `good-motion`：有 motion guide 的合法样例。
- `bad-missing-evidence`：缺 evidence，应在 strict mode 失败。
- `bad-placeholder-specimen`：含 `/* REPLACE */`，应失败。

### 最小命令

```bash
python3 -m py_compile scripts/*.py
python3 scripts/validate-extraction.py examples/good-static
python3 scripts/validate-extraction.py --strict examples/good-static
python3 scripts/validate-extraction.py --strict examples/good-motion
python3 scripts/test-validation-fixtures.py
```

预期：

- good fixtures 通过。
- bad fixtures 必须返回非 0。
- `scripts/test-validation-fixtures.py` 负责断言 bad fixture 失败，不允许把预期失败命令直接串进普通验证脚本。

`scripts/test-validation-fixtures.py` 最小职责：

- 运行 `validate-extraction.py --strict examples/good-static`，期望 exit code `0`。
- 运行 `validate-extraction.py --strict examples/good-motion`，期望 exit code `0`。
- 运行 `validate-extraction.py --strict examples/bad-missing-evidence`，期望 exit code `1`。
- 运行 `validate-extraction.py --strict examples/bad-placeholder-specimen`，期望 exit code `1`。
- 检查 bad fixture 输出中至少包含一个 `[error]` finding。

错误码：

- `0`：通过，没有 strict error。
- `1`：validation finding 中存在 error。
- `2`：命令参数、路径不存在、manifest 无法解析等运行错误。

错误格式建议：

```text
artifacts/style-specimen.html:1 [error] placeholder marker found: /* REPLACE */
artifacts/style-manifest.json [error] missing evidence reference for design_system.colors[0]
```

finding 格式：

```text
<relative-path>[:line] [<severity>] <code>: <message>
```

`severity` 枚举：

- `error`
- `warning`
- `info`

## 第三方内容与隐私边界

v1 默认只处理公开页面。

规则：

- 登录态页面需要用户明确确认。
- 不主动保存账号页、后台页、私有文档、用户数据或商业敏感数据截图。
- 下载的 CSS/JS 只作为本地证据，不作为可再分发资产。
- 截图、字体、图片、视频、商标和品牌资产需要用户审查后再决定是否保留。
- 不把第三方 logo、商标、插图、摄影当作可复用设计资产。
- evidence manifest 必须记录保存了哪些第三方文件及用途。
- README 必须提醒用户检查输出目录再提交或分发。

## 参考吸收

### `extract-design-system`

采用：

- `raw -> normalized -> tokens` 分层。
- v1 只承诺 tokens 和 starter assets，不承诺完整组件库。
- 第三方输入视为 untrusted input。

暂不采用：

- `init` 模式。放入 v2 backlog。

### `style-extractor`

采用：

- 每次 extraction 创建独立目录。
- `guides/`、`evidence/`、`raw/`、`artifacts/` 分层。
- 必须输出 `style-guide.md` 和 `evidence-manifest.md`。
- motion 有意义时必须输出 `motion-guide.md`。
- `Reusable / Adapted / Discarded` 三分类。
- 状态矩阵。
- 明确 failure conditions。

### `impeccable`

采用：

- validation 中区分 deterministic check 和人工判断。
- 后续可做 DESIGN.md / sidecar。

v1 不采用：

- `PRODUCT.md` / `DESIGN.md` 双文档模型。
- 审计评分。
- live 参数化变体。

### `frontend-design`

采用：

- 在 style guide 中加入 `Generation Guidance`。
- 明确适用页面、不适用页面、可调整变量和误用风险。

### `web-design-guidelines`

采用：

- validation 输出可定位 finding。
- 用 severity 区分 error / warning。

### `design-dna`

采用：

- 三层表达：`design_system`、`design_style`、`visual_effects`。
- Generation Priority。

v1 不采用：

- 多参考合成。
- DNA JSON 输入。
- polish iteration 工作流。

## 保留、迁移与删除

保留：

- `references/style-specimen.html`，作为模板继续演进。
- `extraction-checklist.md`，拆分或补充为系统 checklist。

迁移：

- 现有示例 manifest/specimen 迁移到 `examples/<name>/`。
- 旧命令说明迁移到 README 的 migration note。

停止使用：

- `assets/theme/` 作为默认输出目录。
- `SKILL.md` 中的大段 schema。
- 和实际脚本不一致的命令说明。

新增：

- `outputs/`，但默认 gitignore。
- `examples/`。
- `references/output-contract.md`。
- `references/style-guide-template.md`。
- `references/motion-guide-template.md`。
- `references/evidence-manifest-template.md`。
- `scripts/validate-extraction.py`。
- `scripts/test-validation-fixtures.py`。

## 风险

- 一次性重构过大，容易破坏当前可用的 specimen 生成流程。
- 引入证据目录后，输出体积会变大。
- 状态采样和动效采样依赖浏览器自动化，稳定性低于静态 token 提取。
- 对动态站点、canvas/WebGL 站点，仍需要人工判断。
- 公开页面也可能包含受版权保护的 CSS、图片、字体、视频和品牌资产。
- 登录态页面可能包含用户数据、token、cookie 派生信息或商业敏感内容。
- 过度复用原站 IA、文案、商标或插图会提高侵权和克隆风险。

缓解：

- v1 限制为单公开 URL。
- 默认忽略 `outputs/`。
- evidence manifest 记录第三方文件用途。
- README 提醒用户审查截图和 assets。
- validation 加入 anti-clone warning。

## 建议执行策略

推荐顺序：

1. Milestone 1：结构整理。
2. Milestone 2：脚本修正。
3. Milestone 3：证据系统。
4. Milestone 4：状态和动效增强。
5. Milestone 5：tokens 和 specimen 稳定化。

不要第一步重写所有脚本。  
不要在 v1 中加入多参考合成、DESIGN.md、审计评分或参数化预览。

## 最小完成标准

v1 重构完成时至少满足：

- `SKILL.md` 精简，职责清晰。
- `SKILL.md` frontmatter description 与新输出路径一致。
- README 说明 v1 范围、输出目录、`--out-dir`、运行环境和第三方内容边界。
- 输出不再写入 skill 自身 `assets/theme/`。
- 每次提取有独立目录。
- 真实运行产物默认写入 `outputs/extractions/<name>/` 并被 gitignore。
- 可维护示例放在 `examples/<name>/`。
- 每次合法提取至少包含：
  - `guides/style-guide.md`
  - `guides/evidence-manifest.md`
  - `evidence/evidence-index.json`
  - `artifacts/style-manifest.json`
  - `artifacts/style-specimen.html`
  - `artifacts/tokens.json`
  - `artifacts/tokens.css`
- 有 motion 时包含 `guides/motion-guide.md`。
- 无 motion 时不生成 `motion-guide.md`，但在 evidence manifest 和 limitations 说明。
- manifest 符合 v1 schema。
- `references/schema.md` 含 JSON Schema 或等价字段表、item contracts 和完整样例。
- 关键结论有 evidence 引用和 confidence。
- 有 `validate-extraction.py`，支持 warning / strict mode。
- 有 `test-validation-fixtures.py`，能断言 bad fixtures 失败。
- good / bad fixtures 能验证正反例。
- 文档和脚本参数一致。
