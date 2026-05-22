# Extract Design

Extract Design 是一个 Codex / Claude Code skill，用于从公开网页中提取可复用的网页设计语言。它提取设计系统，而不是复制页面。

v1 面向单个公开 URL，输出证据、raw 数据、manifest、tokens、style guide 和 style specimen。默认输出到调用项目的 `outputs/extractions/<name>/`，可通过 `--out-dir` 覆盖。

## v1 范围

支持：

- 单 URL 提取。
- computed style、CSS variables、typography、color、spacing、surface、component 和基础 motion 证据。
- transition declaration scan 和常见前端动效库检测。
- 运行产物写入独立 extraction 目录。
- 版本化示例放在 `examples/<name>/`。
- 基础 validation，支持 warning mode 和 strict mode。

不支持：

- 多 URL 合成。
- 截图作为主输入。
- 登录态页面的默认采集。
- 完整组件库生成。
- 像素级复刻。
- 审计评分和参数化 specimen。

## 输出结构

默认结构：

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
    evidence-index.json
  artifacts/
    style-manifest.json
    style-specimen.html
    tokens.json
    tokens.css
  raw/
    computed-styles.json
    transition-scan.json
    library-detect.json
    keyframes.json
    interaction-diff.json
```

无有意义 motion 时，不生成 `guides/motion-guide.md`，但必须在 `guides/evidence-manifest.md` 和 `artifacts/style-manifest.json` 的 `limitations` 中说明。

`extract-styles.py` 会始终生成 `raw/transition-scan.json` 和 `raw/library-detect.json`。只有检测到可归类的 transition pattern 时，才会生成 `guides/motion-guide.md` 并将 `motion.present` 设为 `true`。

`outputs/` 是运行产物，默认被 `.gitignore` 忽略。`examples/` 是可维护示例，可以进入版本管理。

## 基本命令

安装运行依赖：

```bash
python3 -m pip install playwright
python3 -m playwright install chromium
```

提取 computed styles：

```bash
python3 scripts/extract-styles.py https://example.com --name example
```

指定输出目录：

```bash
python3 scripts/extract-styles.py https://example.com --out-dir /tmp/example-extraction
```

提取 keyframes：

```bash
python3 scripts/extract-keyframes.py https://example.com --out outputs/extractions/example/raw/keyframes.json
```

验证输出：

```bash
python3 scripts/validate-extraction.py outputs/extractions/example
python3 scripts/validate-extraction.py --strict outputs/extractions/example
```

验证 fixtures：

```bash
python3 scripts/test-validation-fixtures.py
```

## 运行环境

- Python 3.8+。
- `extract-styles.py` 和 URL 模式的 `extract-keyframes.py` 需要 Playwright 和 Chromium。
- `validate-extraction.py` 与 `test-validation-fixtures.py` 不需要网络。
- folder 模式的 `extract-keyframes.py` 只解析已保存 CSS 文件，不访问网络。

## 与相近工具的边界

- 类似 `extract-design-system`：保留 raw -> normalized -> tokens 分层，但 v1 只承诺 starter tokens 和设计参考，不生成完整组件库。
- 类似 `style-extractor`：每次运行生成独立目录，并保留 evidence、raw、guides 和 artifacts。
- 类似 `impeccable`：validation 区分确定性错误和人工判断风险。

## 第三方内容与隐私

v1 默认只处理公开页面。登录态页面需要用户明确确认。

提取结果可能包含第三方 CSS、截图、字体、图片或品牌资产。提交或分发输出前，应先审查 `evidence/` 和 `guides/evidence-manifest.md`。不要把 logo、商标、专属插图、摄影或原站文案当作可复用设计资产。

## 项目结构

```text
extract-design/
  SKILL.md
  README.md
  scripts/
  references/
  examples/
  REFACTOR_PLAN.md
```

`references/schema.md` 是 manifest 和 validation 的依据。`references/workflow.md` 描述 agent 提取流程。`references/output-contract.md` 描述目录和产物职责。
