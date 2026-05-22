#!/usr/bin/env python3
"""
Extract computed CSS design evidence from a live webpage.

Default output:
    outputs/extractions/<name>/

Examples:
    python3 scripts/extract-styles.py https://example.com --name example
    python3 scripts/extract-styles.py https://example.com --out-dir /tmp/example-extraction
    python3 scripts/extract-styles.py https://example.com --out raw.json
"""

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from html import escape
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


JS_EXTRACT = """
() => {
  const value = (style, prop) => style.getPropertyValue(prop).trim();
  const shortClass = (el) => el.className?.toString().substring(0, 100) || "";
  const styleFor = (el) => {
    if (!el) return null;
    const s = getComputedStyle(el);
    const before = getComputedStyle(el, "::before");
    const after = getComputedStyle(el, "::after");
    return {
      tag: el.tagName,
      cls: shortClass(el),
      text: (el.textContent || "").trim().replace(/\\s+/g, " ").substring(0, 120),
      color: s.color,
      backgroundColor: s.backgroundColor,
      backgroundImage: s.backgroundImage,
      backgroundSize: s.backgroundSize,
      backgroundRepeat: s.backgroundRepeat,
      border: s.border,
      borderColor: s.borderColor,
      borderRadius: s.borderRadius,
      boxShadow: s.boxShadow,
      filter: s.filter,
      backdropFilter: s.backdropFilter,
      maskImage: s.maskImage,
      padding: s.padding,
      margin: s.margin,
      display: s.display,
      gap: s.gap,
      width: s.width,
      maxWidth: s.maxWidth,
      minHeight: s.minHeight,
      fontFamily: s.fontFamily,
      fontSize: s.fontSize,
      fontWeight: s.fontWeight,
      lineHeight: s.lineHeight,
      letterSpacing: s.letterSpacing,
      transition: s.transition,
      animation: s.animation,
      before: {
        content: before.content,
        background: before.background,
        backgroundImage: before.backgroundImage,
        border: before.border,
        boxShadow: before.boxShadow,
        display: before.display
      },
      after: {
        content: after.content,
        background: after.background,
        backgroundImage: after.backgroundImage,
        border: after.border,
        boxShadow: after.boxShadow,
        display: after.display
      }
    };
  };

  const cssVars = {};
  for (const sheet of document.styleSheets) {
    try {
      for (const rule of sheet.cssRules) {
        if (rule.style) {
          for (const prop of rule.style) {
            if (prop.startsWith("--")) cssVars[prop] = rule.style.getPropertyValue(prop).trim();
          }
        }
      }
    } catch (e) {}
  }

  const htmlStyle = getComputedStyle(document.documentElement);
  const bodyStyle = getComputedStyle(document.body);
  const selectors = {
    containers: "main, .container, [class*=container], [class*=wrapper]",
    sections: "section, header, footer, [class*=section], [class*=hero]",
    buttons: "button, a[role=button], .button, [class*=button], [class*=Button]",
    cards: "[class*=card], [class*=Card], article, [class*=panel], [class*=Panel]",
    nav: "nav, [class*=nav], [class*=Nav]",
    forms: "input, textarea, select, label, form",
    code: "pre, code, [class*=code], [class*=Code]"
  };

  const samples = {};
  for (const [name, selector] of Object.entries(selectors)) {
    samples[name] = [...document.querySelectorAll(selector)].slice(0, 12).map(styleFor);
  }

  const typography = {};
  for (const selector of ["h1", "h2", "h3", "p", "a", "button", "label", "code"]) {
    typography[selector] = styleFor(document.querySelector(selector));
  }

  const backgroundImages = [...document.querySelectorAll("*")]
    .filter(el => getComputedStyle(el).backgroundImage !== "none")
    .slice(0, 30)
    .map(styleFor);

  const transitions = [...document.querySelectorAll("*")]
    .map(styleFor)
    .filter(item => item && item.transition && item.transition !== "all" && item.transition !== "all 0s ease 0s")
    .slice(0, 40);

  return {
    meta: {
      url: location.href,
      title: document.title,
      viewport: { width: window.innerWidth, height: window.innerHeight },
      dataTheme: document.documentElement.getAttribute("data-theme"),
      htmlClass: document.documentElement.className.substring(0, 200),
      hasDarkClass: document.documentElement.classList.contains("dark"),
      colorScheme: htmlStyle.colorScheme,
      reducedMotion: window.matchMedia("(prefers-reduced-motion: reduce)").matches,
      shadowDomCount: [...document.querySelectorAll("*")].filter(el => el.shadowRoot).length,
      canvasCount: document.querySelectorAll("canvas").length,
      videoCount: document.querySelectorAll("video").length
    },
    page: {
      html: styleFor(document.documentElement),
      body: styleFor(document.body)
    },
    cssVars,
    libraries: {
      gsap: Boolean(window.gsap),
      framerMotion: Boolean(window.Motion || window.framerMotion),
      lottie: Boolean(window.lottie),
      swiper: Boolean(window.Swiper),
      aos: Boolean(window.AOS),
      three: Boolean(window.THREE),
      anime: Boolean(window.anime)
    },
    typography,
    samples,
    backgroundImages,
    transitions
  };
}
"""


JS_FIND_DARK_TOGGLE = """
() => {
  return [...document.querySelectorAll('button, [role="button"]')].filter(el => {
    const label = (el.getAttribute('aria-label') || el.textContent || '').toLowerCase();
    return label.includes('dark') || label.includes('theme') || label.includes('mode');
  }).map(el => ({
    ariaLabel: el.getAttribute('aria-label'),
    text: el.textContent.trim().substring(0, 40)
  }));
}
"""


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def slug_from_url(url):
    host = urlparse(url).netloc or "extraction"
    host = host.split("@")[-1].split(":")[0]
    host = host[4:] if host.startswith("www.") else host
    slug = re.sub(r"[^a-zA-Z0-9]+", "-", host).strip("-").lower()
    return slug or "extraction"


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def first_value(*values, fallback="unknown"):
    for item in values:
        if item not in (None, "", "none", "rgba(0, 0, 0, 0)"):
            return item
    return fallback


def confidence(evidence, level="medium", method="measured"):
    return {"level": level, "method": method, "evidence": evidence}


def css_var_name(token):
    return token if token.startswith("--") else f"--{token}"


def build_tokens(raw):
    light = raw["light"]
    body = light["page"]["body"] or {}
    html = light["page"]["html"] or {}
    button = (light["samples"].get("buttons") or [{}])[0] or {}
    card = (light["samples"].get("cards") or [{}])[0] or {}

    return {
        "color": {
            "bg": {"page": {"value": first_value(html.get("backgroundColor"), body.get("backgroundColor"), fallback="#ffffff")}},
            "text": {"primary": {"value": first_value(body.get("color"), fallback="#111111")}},
            "surface": {"card": {"value": first_value(card.get("backgroundColor"), fallback=first_value(body.get("backgroundColor"), fallback="#ffffff"))}},
            "border": {"default": {"value": first_value(card.get("borderColor"), button.get("borderColor"), fallback="#dddddd")}},
            "accent": {"value": first_value(button.get("backgroundColor"), fallback="#111111")}
        },
        "font": {
            "body": {"value": first_value(body.get("fontFamily"), fallback="system-ui, sans-serif")}
        },
        "type": {
            "body": {
                "size": {"value": first_value(body.get("fontSize"), fallback="16px")},
                "lineHeight": {"value": first_value(body.get("lineHeight"), fallback="24px")},
                "weight": {"value": first_value(body.get("fontWeight"), fallback="400")},
                "letterSpacing": {"value": first_value(body.get("letterSpacing"), fallback="0px")}
            }
        },
        "space": {
            "4": {"value": "16px"},
            "6": {"value": "24px"}
        },
        "radius": {
            "md": {"value": first_value(button.get("borderRadius"), card.get("borderRadius"), fallback="8px")}
        },
        "shadow": {
            "none": {"value": "none"},
            "surface": {"value": first_value(card.get("boxShadow"), fallback="none")}
        },
        "border": {
            "default": {"value": first_value(card.get("border"), button.get("border"), fallback="1px solid #dddddd")}
        }
    }


def flatten_css_tokens(tokens):
    return {
        "--color-bg-page": tokens["color"]["bg"]["page"]["value"],
        "--color-text-primary": tokens["color"]["text"]["primary"]["value"],
        "--color-surface-card": tokens["color"]["surface"]["card"]["value"],
        "--color-border-default": tokens["color"]["border"]["default"]["value"],
        "--color-accent": tokens["color"]["accent"]["value"],
        "--font-body": tokens["font"]["body"]["value"],
        "--type-body-size": tokens["type"]["body"]["size"]["value"],
        "--type-body-line-height": tokens["type"]["body"]["lineHeight"]["value"],
        "--type-body-weight": tokens["type"]["body"]["weight"]["value"],
        "--type-body-letter-spacing": tokens["type"]["body"]["letterSpacing"]["value"],
        "--space-4": tokens["space"]["4"]["value"],
        "--space-6": tokens["space"]["6"]["value"],
        "--radius-md": tokens["radius"]["md"]["value"],
        "--shadow-none": tokens["shadow"]["none"]["value"],
        "--shadow-surface": tokens["shadow"]["surface"]["value"],
        "--border-default": tokens["border"]["default"]["value"]
    }


def build_tokens_css(tokens):
    lines = [":root {"]
    for name, value in flatten_css_tokens(tokens).items():
        lines.append(f"  {css_var_name(name)}: {value};")
    lines.append("}")
    return "\n".join(lines) + "\n"


def parse_duration_ms(transition):
    match = re.search(r"([\d.]+)(ms|s)", transition or "")
    if not match:
        return "unknown"
    duration = float(match.group(1))
    return int(duration if match.group(2) == "ms" else duration * 1000)


def parse_transition_properties(transition):
    properties = []
    for part in (transition or "").split(","):
        tokens = part.strip().split()
        if not tokens:
            continue
        prop = tokens[0]
        if not re.match(r"^[a-zA-Z-]+$", prop):
            continue
        if prop not in ("0s", "0ms", "none"):
            properties.append(prop)
    return sorted(set(properties)) or ["all"]


def parse_easing(transition):
    match = re.search(r"(cubic-bezier\([^)]+\)|linear|ease-in-out|ease-in|ease-out|ease)", transition or "")
    return match.group(1) if match else "unknown"


def build_transition_scan(raw, captured_at):
    transitions = raw["light"].get("transitions") or []
    clusters = {}
    for item in transitions:
        transition = item.get("transition")
        if not transition or transition == "all 0s ease 0s":
            continue
        duration = parse_duration_ms(transition)
        if duration == "unknown" or duration == 0:
            continue
        clusters.setdefault(transition, []).append({
            "tag": item.get("tag"),
            "cls": item.get("cls"),
            "text": item.get("text")
        })

    patterns = []
    for index, (transition, samples) in enumerate(sorted(clusters.items()), start=1):
        patterns.append({
            "id": f"motion.transition.{index}",
            "transition": transition,
            "properties": parse_transition_properties(transition),
            "durationMs": parse_duration_ms(transition),
            "easing": parse_easing(transition),
            "source": "transition",
            "sampleCount": len(samples),
            "samples": samples[:5],
            "capturedAt": captured_at
        })

    return {
        "capturedAt": captured_at,
        "patterns": patterns,
        "limitations": [] if patterns else [
            {
                "area": "motion",
                "message": "No non-zero transition patterns were found in computed styles."
            }
        ]
    }


def build_library_detection(raw, captured_at):
    libraries = raw["light"].get("libraries") or {}
    detected = [
        {"name": name, "present": bool(present)}
        for name, present in sorted(libraries.items())
    ]
    return {
        "capturedAt": captured_at,
        "detected": detected,
        "present": [item["name"] for item in detected if item["present"]]
    }


def motion_patterns_from_scan(transition_scan):
    evidence = ["ev:animation/transition-scan"]
    patterns = []
    for item in transition_scan.get("patterns", [])[:8]:
        patterns.append({
            "id": item["id"],
            "trigger": "state-change",
            "properties": item.get("properties") or ["all"],
            "durationMs": item.get("durationMs", "unknown"),
            "easing": item.get("easing", "unknown"),
            "source": "transition",
            "evidence": evidence,
            "confidence": confidence(evidence, "low", "measured"),
            "usage": "Measured transition declaration. Confirm actual interaction trigger manually."
        })
    return patterns


def evidence_items(captured_at, include_motion=False):
    items = [
        {
            "id": "ev:screenshot/home",
            "type": "screenshot",
            "path": "evidence/screenshots/home.png",
            "description": "Baseline page screenshot at extraction viewport.",
            "capturedAt": captured_at
        },
        {
            "id": "ev:computed/body",
            "type": "computed-style",
            "path": "raw/computed-styles.json",
            "description": "Computed style extraction for page and sampled components.",
            "capturedAt": captured_at
        },
        {
            "id": "ev:script/library-detect",
            "type": "script",
            "path": "raw/library-detect.json",
            "description": "Client-side animation and UI library detection.",
            "capturedAt": captured_at
        }
    ]
    if include_motion:
        items.append({
            "id": "ev:animation/transition-scan",
            "type": "animation",
            "path": "raw/transition-scan.json",
            "description": "Computed transition pattern scan.",
            "capturedAt": captured_at
        })
    return items


def build_manifest(name, url, captured_at, raw, tokens, transition_scan, library_detection):
    evidence = ["ev:computed/body"]
    screenshot_evidence = ["ev:screenshot/home"]
    motion_patterns = motion_patterns_from_scan(transition_scan)
    motion_present = bool(motion_patterns)
    color_conf = confidence(evidence, "medium")
    type_conf = confidence(evidence, "medium")
    limitations = []
    if not motion_present:
        limitations.append({
            "id": "limitation.motion.not-detected",
            "severity": "info",
            "area": "motion",
            "message": "No non-zero transition pattern was detected in computed styles.",
            "impact": "Run extract-keyframes.py and manual interaction review if visible motion exists."
        })
    else:
        limitations.append({
            "id": "limitation.motion.trigger-unconfirmed",
            "severity": "warning",
            "area": "motion",
            "message": "Transition declarations were measured, but interaction triggers still need manual confirmation.",
            "impact": "Review hover, focus, active, open, and scroll states before final reuse."
        })
    if not library_detection.get("present"):
        limitations.append({
            "id": "limitation.library-detect.none",
            "severity": "info",
            "area": "assets",
            "message": "No known animation library was detected on window.",
            "impact": "This does not rule out bundled or scoped animation code."
        })

    return {
        "schemaVersion": "2.0",
        "meta": {
            "name": name,
            "sourceUrl": url,
            "capturedAt": captured_at,
            "generator": "extract-design",
            "mode": "single-url"
        },
        "evidence": {"items": evidence_items(captured_at, include_motion=motion_present)},
        "rawSources": [
            {
                "id": "raw:computed/styles",
                "type": "computed-styles",
                "path": "raw/computed-styles.json",
                "generatedBy": "extract-styles.py",
                "capturedAt": captured_at,
                "evidence": evidence,
                "sourceUrl": url,
                "status": "available"
            },
            {
                "id": "raw:transition/scan",
                "type": "transition-scan",
                "path": "raw/transition-scan.json",
                "generatedBy": "extract-styles.py",
                "capturedAt": captured_at,
                "evidence": ["ev:animation/transition-scan"] if motion_present else [],
                "sourceUrl": url,
                "status": "available" if motion_present else "partial",
                "unavailableReason": None if motion_present else "No non-zero transition patterns found."
            },
            {
                "id": "raw:script/library-detect",
                "type": "script",
                "path": "raw/library-detect.json",
                "generatedBy": "extract-styles.py",
                "capturedAt": captured_at,
                "evidence": ["ev:script/library-detect"],
                "sourceUrl": url,
                "status": "available"
            }
        ],
        "design_system": {
            "colors": [
                {
                    "id": "color.bg.page",
                    "value": tokens["color"]["bg"]["page"]["value"],
                    "role": "background",
                    "usage": "Page background.",
                    "token": "--color-bg-page",
                    "confidence": color_conf
                },
                {
                    "id": "color.text.primary",
                    "value": tokens["color"]["text"]["primary"]["value"],
                    "role": "text",
                    "usage": "Primary readable text.",
                    "token": "--color-text-primary",
                    "confidence": color_conf
                },
                {
                    "id": "color.accent",
                    "value": tokens["color"]["accent"]["value"],
                    "role": "accent",
                    "usage": "Primary interactive accent when detectable.",
                    "token": "--color-accent",
                    "confidence": color_conf
                }
            ],
            "typography": [
                {
                    "id": "type.body",
                    "role": "body",
                    "fontFamily": tokens["font"]["body"]["value"],
                    "fontSize": tokens["type"]["body"]["size"]["value"],
                    "lineHeight": tokens["type"]["body"]["lineHeight"]["value"],
                    "fontWeight": tokens["type"]["body"]["weight"]["value"],
                    "letterSpacing": tokens["type"]["body"]["letterSpacing"]["value"],
                    "token": "type.body",
                    "confidence": type_conf
                }
            ],
            "spacing": [
                {
                    "id": "space.4",
                    "value": tokens["space"]["4"]["value"],
                    "role": "scale",
                    "usage": "Starter component gap.",
                    "token": "--space-4",
                    "evidence": evidence,
                    "confidence": confidence(evidence, "low", "inferred")
                }
            ],
            "radii": [
                {
                    "id": "radius.md",
                    "value": tokens["radius"]["md"]["value"],
                    "role": "medium",
                    "usage": "Starter component radius.",
                    "token": "--radius-md",
                    "evidence": evidence,
                    "confidence": confidence(evidence, "medium")
                }
            ],
            "shadows": [
                {
                    "id": "shadow.surface",
                    "value": tokens["shadow"]["surface"]["value"],
                    "role": "surface",
                    "usage": "Starter surface elevation.",
                    "token": "--shadow-surface",
                    "evidence": evidence,
                    "confidence": confidence(evidence, "medium")
                }
            ],
            "borders": [
                {
                    "id": "border.default",
                    "value": tokens["border"]["default"]["value"],
                    "role": "surface",
                    "usage": "Starter surface boundary.",
                    "token": "--border-default",
                    "evidence": evidence,
                    "confidence": confidence(evidence, "medium")
                }
            ]
        },
        "design_style": {
            "mood": ["requires-manual-summary"],
            "composition": ["requires-manual-summary"],
            "density": "unknown",
            "visual_language": ["Initial extraction generated from computed styles."],
            "generation_guidance": ["Refine this manifest before using it as a final design guide."]
        },
        "visual_effects": [],
        "components": [
            {
                "id": "component.button.primary",
                "name": "Primary Button",
                "category": "button",
                "description": "Initial button archetype from the first detected button-like element.",
                "anatomy": ["container", "label"],
                "states": [
                    {
                        "name": "default",
                        "properties": {
                            "background": "var(--color-accent)",
                            "color": "var(--color-bg-page)",
                            "borderRadius": "var(--radius-md)"
                        },
                        "evidence": evidence,
                        "confidence": confidence(evidence, "low", "inferred")
                    }
                ],
                "tokens": ["--color-accent", "--color-bg-page", "--radius-md", "--space-4"],
                "evidence": evidence,
                "confidence": confidence(evidence, "low", "inferred")
            }
        ],
        "motion": {
            "present": motion_present,
            "patterns": motion_patterns
        },
        "responsive_rules": [],
        "accessibility_notes": ["Validate generated color contrast before reuse."],
        "reuse_filter": [
            {
                "feature": "Source page content and brand assets",
                "decision": "Discarded",
                "reason": "Extraction should preserve visual language, not source content or trademarked assets.",
                "evidence": screenshot_evidence
            }
        ],
        "limitations": limitations + [
            {
                "id": "limitation.manual-refinement",
                "severity": "warning",
                "area": "manual-judgment",
                "message": "Initial manifest is script-generated and requires manual semantic refinement.",
                "impact": "Do not treat this as a final extraction without review."
            }
        ]
    }


def build_style_specimen(name, manifest, tokens_css):
    title = escape(name)
    manifest_json = json.dumps(manifest, indent=2, ensure_ascii=False).replace("</", "<\\/")
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <title>{title} Style Specimen</title>
  <style>
{tokens_css}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--color-bg-page);
      color: var(--color-text-primary);
      font-family: var(--font-body);
      font-size: var(--type-body-size);
      line-height: var(--type-body-line-height);
      letter-spacing: var(--type-body-letter-spacing);
    }}
    main {{
      max-width: 960px;
      margin: 0 auto;
      padding: 48px 24px;
    }}
    section {{ margin-top: 32px; }}
    .swatches {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr)); gap: var(--space-4); }}
    .swatch, .surface {{
      background: var(--color-surface-card);
      border: var(--border-default);
      border-radius: var(--radius-md);
      box-shadow: var(--shadow-surface);
      padding: var(--space-6);
    }}
    .chip {{
      display: inline-flex;
      align-items: center;
      min-height: 36px;
      padding: 0 var(--space-4);
      background: var(--color-accent);
      color: var(--color-bg-page);
      border-radius: var(--radius-md);
      border: 0;
      font: inherit;
    }}
    code {{
      font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
      font-size: 0.9em;
    }}
  </style>
</head>
<body>
  <main>
    <h1>{title} Style Specimen</h1>
    <p>Reusable starter specimen generated from measured design tokens.</p>

    <section>
      <h2>Color</h2>
      <div class="swatches">
        <div class="swatch"><code>--color-bg-page</code></div>
        <div class="swatch"><code>--color-text-primary</code></div>
        <div class="swatch"><code>--color-accent</code></div>
      </div>
    </section>

    <section>
      <h2>Components</h2>
      <div class="surface">
        <button class="chip">Primary action</button>
      </div>
    </section>
  </main>
  <script type="application/json" id="extract-design-manifest">
{manifest_json}
  </script>
</body>
</html>
"""


def build_style_guide(name, url, captured_at, motion_present=False, detected_libraries=None):
    motion_text = (
        "Transition patterns were detected in computed styles. Review `guides/motion-guide.md` and confirm interaction triggers manually."
        if motion_present
        else "No non-zero transition pattern was detected by `extract-styles.py`. Run `extract-keyframes.py` and manual interaction review if visible motion exists."
    )
    library_text = ", ".join(detected_libraries or []) if detected_libraries else "none detected"
    return f"""# Style Guide: {name}

## Source

- URL: {url}
- Captured: {captured_at}

## Design Character

Initial script-generated guide. Review screenshots and raw data before using this as a final style system.

## Tokens

Starter tokens are available in `artifacts/tokens.json` and `artifacts/tokens.css`.

## Components

The initial extraction includes a starter button archetype when a button-like element is detectable.

## Motion

{motion_text}

Detected animation libraries: {library_text}.

## Generation Guidance

- Preserve semantic tokens.
- Do not copy source page text, information architecture, logo, screenshots, or brand assets.
- Validate contrast and responsive behavior before reuse.

## Limitations

- This guide needs manual semantic refinement.
- Complex component states are not fully captured in this first-pass extraction.
"""


def build_motion_guide(name, transition_scan):
    rows = []
    for pattern in transition_scan.get("patterns", []):
        rows.append(
            f"| `{pattern['id']}` | state-change | {', '.join(pattern.get('properties') or [])} | {pattern.get('durationMs')} | {pattern.get('easing')} | `ev:animation/transition-scan` |"
        )
    table = "\n".join(rows) if rows else "|  |  |  |  |  |  |"
    return f"""# Motion Guide: {name}

## Summary

Computed transition declarations were found. Trigger mapping is not confirmed by this script and should be reviewed against hover, focus, active, open, and scroll states.

## Patterns

| Pattern | Trigger | Properties | Duration | Easing | Evidence |
| --- | --- | --- | --- | --- | --- |
{table}

## Reduced Motion

Check `prefers-reduced-motion` behavior manually before reuse.

## Limitations

- Transition declarations do not prove the exact interaction trigger.
- Keyframes and JS-driven animation still require `extract-keyframes.py` and manual review.
"""


def build_evidence_manifest(name, url, captured_at, transition_scan, library_detection):
    motion_inventory = ""
    if transition_scan.get("patterns"):
        motion_inventory = "| `ev:animation/transition-scan` | animation | `raw/transition-scan.json` | Computed transition patterns |\n"
    library_text = ", ".join(library_detection.get("present") or []) or "none detected"
    return f"""# Evidence Manifest: {name}

## Source

- URL: {url}
- Captured: {captured_at}
- Mode: single-url

## Inventory

| Evidence | Type | Path | Purpose |
| --- | --- | --- | --- |
| `ev:screenshot/home` | screenshot | `evidence/screenshots/home.png` | Baseline visual reference |
| `ev:computed/body` | computed-style | `raw/computed-styles.json` | Computed style and component samples |
| `ev:script/library-detect` | script | `raw/library-detect.json` | Animation and UI library detection |
{motion_inventory}

## Interactions Tested

- Hover: transition declaration scan only; trigger not confirmed
- Focus-visible: transition declaration scan only; trigger not confirmed
- Active: transition declaration scan only; trigger not confirmed
- Open/close: not tested by `extract-styles.py`
- Scroll: not tested by `extract-styles.py`

## Gaps

- CORS-protected stylesheets may not expose all CSS variables.
- Complex motion requires `extract-keyframes.py` and manual review.
- Third-party assets need review before distribution.
- Detected libraries: {library_text}.

## Reuse Decisions

| Feature | Decision | Reason | Evidence |
| --- | --- | --- | --- |
| Source page content and brand assets | Discarded | Preserve visual language only | `ev:screenshot/home` |
"""


def build_evidence_index(captured_at, include_motion=False):
    return {"items": evidence_items(captured_at, include_motion=include_motion)}


def write_extraction(out_dir, name, url, raw):
    captured_at = now_iso()
    out_dir = Path(out_dir)
    for subdir in [
        "guides",
        "evidence/screenshots",
        "evidence/assets",
        "evidence/notes",
        "artifacts",
        "raw"
    ]:
        (out_dir / subdir).mkdir(parents=True, exist_ok=True)

    write_json(out_dir / "raw/computed-styles.json", raw)
    transition_scan = build_transition_scan(raw, captured_at)
    library_detection = build_library_detection(raw, captured_at)
    write_json(out_dir / "raw/transition-scan.json", transition_scan)
    write_json(out_dir / "raw/library-detect.json", library_detection)
    tokens = build_tokens(raw)
    tokens_css = build_tokens_css(tokens)
    manifest = build_manifest(name, url, captured_at, raw, tokens, transition_scan, library_detection)
    motion_present = manifest["motion"]["present"]

    write_json(out_dir / "artifacts/tokens.json", tokens)
    (out_dir / "artifacts/tokens.css").write_text(tokens_css, encoding="utf-8")
    write_json(out_dir / "artifacts/style-manifest.json", manifest)
    (out_dir / "artifacts/style-specimen.html").write_text(
        build_style_specimen(name, manifest, tokens_css),
        encoding="utf-8"
    )
    write_json(out_dir / "evidence/evidence-index.json", build_evidence_index(captured_at, include_motion=motion_present))
    (out_dir / "guides/style-guide.md").write_text(
        build_style_guide(name, url, captured_at, motion_present, library_detection.get("present")),
        encoding="utf-8"
    )
    (out_dir / "guides/evidence-manifest.md").write_text(
        build_evidence_manifest(name, url, captured_at, transition_scan, library_detection),
        encoding="utf-8"
    )
    motion_guide = out_dir / "guides/motion-guide.md"
    if motion_present:
        motion_guide.write_text(build_motion_guide(name, transition_scan), encoding="utf-8")
    elif motion_guide.exists():
        motion_guide.unlink()


def extract(url, switch_dark=False, out_path=None, out_dir=None, name=None, stdout=False):
    name = name or slug_from_url(url)
    if out_dir is None and not out_path and not stdout:
        out_dir = Path.cwd() / "outputs" / "extractions" / name
    elif out_dir is not None:
        out_dir = Path(out_dir)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})

        print(f"[extract-styles] Navigating to {url}", file=sys.stderr)
        page.goto(url, wait_until="networkidle", timeout=30000)

        light_data = page.evaluate(JS_EXTRACT)
        light_data["_mode"] = "light"

        if out_dir:
            screenshot_path = out_dir / "evidence/screenshots/home.png"
            screenshot_path.parent.mkdir(parents=True, exist_ok=True)
            page.screenshot(path=str(screenshot_path), full_page=True)

        dark_data = None
        if switch_dark:
            toggles = page.evaluate(JS_FIND_DARK_TOGGLE)
            clicked = False
            for toggle in toggles:
                label = (toggle.get("ariaLabel") or "").lower()
                if "dark" in label and toggle.get("ariaLabel"):
                    try:
                        page.get_by_role("button", name=toggle["ariaLabel"]).click()
                        page.wait_for_timeout(500)
                        clicked = True
                        print(f"[extract-styles] Switched to dark via: {toggle['ariaLabel']}", file=sys.stderr)
                        break
                    except Exception:
                        pass

            if not clicked:
                page.emulate_media(color_scheme="dark")
                page.wait_for_timeout(300)
                print("[extract-styles] Forced dark via prefers-color-scheme emulation", file=sys.stderr)

            dark_data = page.evaluate(JS_EXTRACT)
            dark_data["_mode"] = "dark"

        browser.close()

    result = {
        "light": light_data,
        "dark": dark_data
    }

    if out_dir:
        write_extraction(out_dir, name, url, result)
        print(f"[extract-styles] Saved extraction to {out_dir}", file=sys.stderr)
    elif out_path:
        write_json(Path(out_path), result)
        print(f"[extract-styles] Saved raw JSON to {out_path}", file=sys.stderr)
    else:
        print(json.dumps(result, indent=2, ensure_ascii=False))


def main():
    parser = argparse.ArgumentParser(description="Extract computed CSS design evidence from a webpage")
    parser.add_argument("url", help="URL to extract from")
    parser.add_argument("--name", help="Extraction name. Defaults to URL host slug.")
    parser.add_argument("--dark", action="store_true", help="Also extract dark mode")
    parser.add_argument("--out", help="Legacy raw JSON output file path")
    parser.add_argument("--out-dir", help="Extraction output directory")
    parser.add_argument("--stdout", action="store_true", help="Print raw JSON to stdout instead of creating an extraction directory")
    args = parser.parse_args()

    extract(args.url, switch_dark=args.dark, out_path=args.out, out_dir=args.out_dir, name=args.name, stdout=args.stdout)


if __name__ == "__main__":
    main()
