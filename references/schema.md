# Manifest Schema v1

`artifacts/style-manifest.json` uses `schemaVersion: "2.0"`.

This document is the validation source for v1. The validator implements deterministic checks from this file. Human judgment remains a warning-level review item.

## Top Level

Required fields:

- `schemaVersion`: string, must be `"2.0"`.
- `meta`: object.
- `evidence.items`: array.
- `rawSources`: array.
- `design_system`: object.
- `design_style`: object.
- `components`: array.
- `motion.present`: boolean.
- `reuse_filter`: array.
- `limitations`: array.

Optional fields:

- `visual_effects`: array.
- `motion.patterns`: array.
- `responsive_rules`: array.
- `accessibility_notes`: array.

## Minimal Shape

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

Empty arrays are allowed only when a related `limitations[]` entry explains the absence, or when the field is optional and irrelevant.

## Evidence References

Reference format:

```text
ev:<category>/<id>
```

Every evidence reference must resolve to `evidence.items[].id`.

`evidence.items[]` fields:

- `id`: required string, format `ev:<category>/<id>`.
- `type`: required enum: `screenshot`, `computed-style`, `stylesheet`, `script`, `interaction`, `animation`, `manual-note`.
- `path`: required path relative to extraction root.
- `description`: required string.
- `capturedAt`: required ISO 8601 string.

## Confidence

Normalized tokens, components, states, motion patterns, and visual effects require `confidence`.

```json
{
  "level": "high",
  "method": "measured",
  "evidence": ["ev:computed/body"]
}
```

`level`: `high`, `medium`, `low`.

`method`: `measured`, `inferred`, `manual`, `unavailable`.

## Item Contracts

### `rawSources[]`

Required:

- `id`: `raw:<category>/<id>`.
- `type`: `computed-styles`, `stylesheet`, `script`, `keyframes`, `transition-scan`, `interaction-diff`, `screenshot-index`.
- `path`: relative extraction path.
- `generatedBy`: script name or `manual`.
- `capturedAt`: ISO 8601 string.
- `evidence`: evidence reference array.

Optional:

- `sourceUrl`
- `status`: `available`, `partial`, `unavailable`.
- `unavailableReason`

### `design_system.colors[]`

Required:

- `id`
- `value`
- `role`: `background`, `surface`, `text`, `muted-text`, `border`, `accent`, `state`, `overlay`, `decorative`.
- `usage`
- `token`
- `confidence`

Optional:

- `aliases`
- `contrastOn`
- `sourceCount`

Token rule: `token` must exist in `artifacts/tokens.css` and map to an equivalent path in `artifacts/tokens.json`.

### `design_system.typography[]`

Required:

- `id`
- `role`: `display`, `heading`, `body`, `caption`, `label`, `code`.
- `fontFamily`
- `fontSize`
- `lineHeight`
- `fontWeight`
- `letterSpacing`
- `token`
- `confidence`

Optional:

- `textTransform`
- `fontStyle`
- `sampleText`
- `sourceCount`

### `design_system.spacing[]`

Required:

- `id`
- `value`: `px`, `rem`, `em`, or `0`.
- `role`: `scale`, `gap`, `padding`, `margin`, `section`, `layout`, `component`.
- `usage`
- `token`
- `evidence`
- `confidence`

Optional:

- `sourceCount`
- `aliases`
- `axis`: `x`, `y`, `both`.
- `responsiveVariants`

### `design_system.radii[]`

Required:

- `id`
- `value`: `px`, `rem`, `em`, `0`, percent, or `mixed` when `cornerValues` is present.
- `role`: `none`, `small`, `medium`, `large`, `pill`, `circle`, `component`.
- `usage`
- `token`
- `evidence`
- `confidence`

Optional:

- `sourceCount`
- `aliases`
- `cornerValues`
- `responsiveVariants`

### `design_system.shadows[]`

Required:

- `id`
- `value`: valid `box-shadow` value or `none`.
- `role`: `none`, `surface`, `raised`, `floating`, `overlay`, `focus`, `ambient`, `component-state`.
- `usage`
- `token`
- `evidence`
- `confidence`

Optional:

- `sourceCount`
- `aliases`
- `layers`
- `state`: `default`, `hover`, `active`, `focus-visible`, `open`.

### `design_system.borders[]`

Required:

- `id`
- `value`: valid border shorthand or `none`.
- `role`: `none`, `divider`, `outline`, `control`, `surface`, `focus`, `state`, `decorative`.
- `usage`
- `token`
- `evidence`
- `confidence`

Optional:

- `sourceCount`
- `aliases`
- `width`
- `style`
- `color`
- `sides`
- `state`: `default`, `hover`, `active`, `focus-visible`, `disabled`, `invalid`.

### `components[]`

Required:

- `id`
- `name`
- `category`: `navigation`, `button`, `card`, `form`, `surface`, `content`, `feedback`, `overlay`, `custom`.
- `description`
- `anatomy`
- `states`
- `tokens`
- `evidence`
- `confidence`

Optional:

- `selectors`
- `responsiveBehavior`
- `antiCloneNotes`

### `components[].states[]`

Required:

- `name`: `default`, `hover`, `active`, `focus-visible`, `disabled`, `loading`, `selected`, `invalid`, `open`, `closed`.
- `properties`
- `evidence`
- `confidence`

Optional:

- `motion`
- `unavailableReason`

Every component must include a `default` state.

### `motion.patterns[]`

Required when `motion.present` is true:

- `id`
- `trigger`: `hover`, `focus`, `click`, `scroll`, `load`, `route-change`, `state-change`, `ambient`.
- `properties`
- `durationMs`: number or `unknown`.
- `easing`
- `source`: `transition`, `keyframes`, `web-animation`, `library`, `manual-observation`.
- `evidence`
- `confidence`

Optional:

- `delayMs`
- `keyframeName`
- `library`
- `usage`
- `reducedMotionBehavior`

### `visual_effects[]`

Required:

- `id`
- `type`: `canvas`, `webgl`, `shader`, `scroll-effect`, `cursor-effect`, `texture`, `noise`, `glow`, `mask`, `blend-mode`, `backdrop-filter`, `video`, `other`.
- `description`
- `reusableDecision`: `Reusable`, `Adapted`, `Discarded`.
- `evidence`
- `confidence`

Optional:

- `implementationHint`
- `performanceRisk`
- `antiCloneNotes`

### `limitations[]`

Required:

- `id`
- `severity`: `info`, `warning`, `error`.
- `area`: `access`, `cors`, `dynamic-rendering`, `motion`, `assets`, `privacy`, `schema`, `manual-judgment`, `other`.
- `message`
- `impact`

Optional:

- `evidence`
- `nextStep`

No meaningful motion requires a `limitations[]` entry with `area: "motion"`.

## Complete Example

```json
{
  "schemaVersion": "2.0",
  "meta": {
    "name": "sample-motion",
    "sourceUrl": "https://example.com",
    "capturedAt": "2026-05-22T00:00:00Z",
    "generator": "extract-design",
    "mode": "single-url"
  },
  "evidence": {
    "items": [
      {
        "id": "ev:screenshot/home",
        "type": "screenshot",
        "path": "evidence/screenshots/home.png",
        "description": "Homepage baseline screenshot",
        "capturedAt": "2026-05-22T00:00:00Z"
      },
      {
        "id": "ev:computed/body",
        "type": "computed-style",
        "path": "raw/computed-styles.json",
        "description": "Measured body and component styles",
        "capturedAt": "2026-05-22T00:00:00Z"
      },
      {
        "id": "ev:animation/hover-lift",
        "type": "animation",
        "path": "raw/keyframes.json",
        "description": "Hover transition evidence",
        "capturedAt": "2026-05-22T00:00:00Z"
      }
    ]
  },
  "rawSources": [
    {
      "id": "raw:computed/styles",
      "type": "computed-styles",
      "path": "raw/computed-styles.json",
      "generatedBy": "extract-styles.py",
      "capturedAt": "2026-05-22T00:00:00Z",
      "evidence": ["ev:computed/body"],
      "status": "available"
    }
  ],
  "design_system": {
    "colors": [
      {
        "id": "color.text.primary",
        "value": "#111111",
        "role": "text",
        "usage": "Primary body and heading text",
        "token": "--color-text-primary",
        "confidence": {
          "level": "high",
          "method": "measured",
          "evidence": ["ev:computed/body"]
        }
      }
    ],
    "typography": [
      {
        "id": "type.body",
        "role": "body",
        "fontFamily": "Inter, sans-serif",
        "fontSize": "16px",
        "lineHeight": "24px",
        "fontWeight": "400",
        "letterSpacing": "0px",
        "token": "type.body",
        "confidence": {
          "level": "high",
          "method": "measured",
          "evidence": ["ev:computed/body"]
        }
      }
    ],
    "spacing": [
      {
        "id": "space.4",
        "value": "16px",
        "role": "scale",
        "usage": "Common component gap",
        "token": "--space-4",
        "evidence": ["ev:computed/body"],
        "confidence": {
          "level": "medium",
          "method": "measured",
          "evidence": ["ev:computed/body"]
        }
      }
    ],
    "radii": [
      {
        "id": "radius.md",
        "value": "8px",
        "role": "medium",
        "usage": "Card and button radius",
        "token": "--radius-md",
        "evidence": ["ev:computed/body"],
        "confidence": {
          "level": "medium",
          "method": "measured",
          "evidence": ["ev:computed/body"]
        }
      }
    ],
    "shadows": [
      {
        "id": "shadow.none",
        "value": "none",
        "role": "none",
        "usage": "Flat surfaces",
        "token": "--shadow-none",
        "evidence": ["ev:computed/body"],
        "confidence": {
          "level": "high",
          "method": "measured",
          "evidence": ["ev:computed/body"]
        }
      }
    ],
    "borders": [
      {
        "id": "border.default",
        "value": "1px solid #dddddd",
        "role": "surface",
        "usage": "Default surface boundary",
        "token": "--border-default",
        "evidence": ["ev:computed/body"],
        "confidence": {
          "level": "medium",
          "method": "measured",
          "evidence": ["ev:computed/body"]
        }
      }
    ]
  },
  "design_style": {
    "mood": ["quiet", "technical"],
    "composition": ["centered content"],
    "density": "medium",
    "visual_language": ["flat surfaces", "clear typographic hierarchy"],
    "generation_guidance": ["Use semantic tokens and avoid copying source copy."]
  },
  "visual_effects": [
    {
      "id": "effect.subtle-grid",
      "type": "texture",
      "description": "Subtle background grid texture.",
      "reusableDecision": "Adapted",
      "evidence": ["ev:screenshot/home"],
      "confidence": {
        "level": "low",
        "method": "manual",
        "evidence": ["ev:screenshot/home"]
      }
    }
  ],
  "components": [
    {
      "id": "component.button.primary",
      "name": "Primary Button",
      "category": "button",
      "description": "Compact primary action.",
      "anatomy": ["container", "label"],
      "states": [
        {
          "name": "default",
          "properties": {
            "background": "var(--color-accent)",
            "color": "var(--color-bg-page)"
          },
          "evidence": ["ev:computed/body"],
          "confidence": {
            "level": "medium",
            "method": "measured",
            "evidence": ["ev:computed/body"]
          },
          "motion": "motion.hover.lift"
        }
      ],
      "tokens": ["--color-text-primary", "--space-4", "--radius-md"],
      "evidence": ["ev:computed/body"],
      "confidence": {
        "level": "medium",
        "method": "measured",
        "evidence": ["ev:computed/body"]
      }
    }
  ],
  "motion": {
    "present": true,
    "patterns": [
      {
        "id": "motion.hover.lift",
        "trigger": "hover",
        "properties": ["transform", "box-shadow"],
        "durationMs": 180,
        "easing": "ease-out",
        "source": "transition",
        "evidence": ["ev:animation/hover-lift"],
        "confidence": {
          "level": "medium",
          "method": "measured",
          "evidence": ["ev:animation/hover-lift"]
        }
      }
    ]
  },
  "responsive_rules": [],
  "accessibility_notes": ["Check generated contrast before reuse."],
  "reuse_filter": [
    {
      "feature": "Source brand logo",
      "decision": "Discarded",
      "reason": "Trademarked asset.",
      "evidence": ["ev:screenshot/home"]
    }
  ],
  "limitations": [
    {
      "id": "limitation.assets",
      "severity": "info",
      "area": "assets",
      "message": "Third-party screenshots require review before distribution.",
      "impact": "Do not publish evidence assets without review."
    }
  ]
}
```

## Minimal Static Example

```json
{
  "schemaVersion": "2.0",
  "meta": {
    "name": "static",
    "sourceUrl": "https://example.com",
    "capturedAt": "2026-05-22T00:00:00Z",
    "generator": "extract-design",
    "mode": "single-url"
  },
  "evidence": {
    "items": [
      {
        "id": "ev:computed/body",
        "type": "computed-style",
        "path": "raw/computed-styles.json",
        "description": "Measured computed styles",
        "capturedAt": "2026-05-22T00:00:00Z"
      }
    ]
  },
  "rawSources": [
    {
      "id": "raw:computed/styles",
      "type": "computed-styles",
      "path": "raw/computed-styles.json",
      "generatedBy": "extract-styles.py",
      "capturedAt": "2026-05-22T00:00:00Z",
      "evidence": ["ev:computed/body"],
      "status": "available"
    }
  ],
  "design_system": {
    "colors": [],
    "typography": [],
    "spacing": [],
    "radii": [],
    "shadows": [],
    "borders": []
  },
  "design_style": {
    "mood": ["static"],
    "composition": ["unknown"],
    "density": "unknown",
    "visual_language": ["manual refinement required"],
    "generation_guidance": ["Complete semantic mapping before reuse."]
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
  "limitations": [
    {
      "id": "limitation.motion.none",
      "severity": "info",
      "area": "motion",
      "message": "No meaningful motion was observed.",
      "impact": "No motion guide is generated."
    },
    {
      "id": "limitation.manual-refinement",
      "severity": "warning",
      "area": "manual-judgment",
      "message": "Semantic mapping requires manual refinement.",
      "impact": "Generated starter artifacts should be reviewed before reuse."
    }
  ]
}
```
