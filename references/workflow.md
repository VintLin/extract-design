# Workflow

## Phase 0: Scope

- Confirm one public URL.
- Choose an output name.
- Decide target project root or `--out-dir`.
- Exclude private, authenticated, or sensitive pages unless the user explicitly confirms.
- Identify product-specific assets that must not become reusable design rules.

## Phase 1: Static Evidence

Collect:

- baseline screenshot.
- html/body/main computed styles.
- CSS custom properties.
- typography samples.
- color samples.
- spacing, radius, border, and shadow samples.
- button, card, nav, form, surface, code block, and content samples.
- pseudo-element, background-image, mask, filter, and backdrop-filter data when available.
- transition declarations.
- common animation library detection.

Write measured data to:

- `raw/computed-styles.json`
- `raw/transition-scan.json`
- `raw/library-detect.json`

## Phase 2: Motion Evidence

Only perform this phase when motion exists or is suspected.

Collect:

- readable `@keyframes`.
- transition declarations and transition clusters.
- animation variables.
- `document.getAnimations()` snapshots when practical.
- library hints such as GSAP, Framer Motion, Lottie, Swiper, AOS, or Three.js.

If no meaningful motion is found, record that in the evidence manifest and limitations.

## Phase 3: Normalize

Transform raw evidence into:

- semantic colors.
- typography roles.
- spacing, radius, shadow, and border tokens.
- component archetypes and state matrix.
- motion patterns.
- visual effects.
- reuse filter decisions.
- limitations and confidence.

Do not fabricate values. Use `unknown`, `unavailable`, or a limitation when evidence is insufficient.

## Phase 4: Guides and Specimen

Create:

- `guides/style-guide.md`
- `guides/evidence-manifest.md`
- `guides/motion-guide.md` when motion exists
- `artifacts/style-specimen.html`
- `artifacts/tokens.json`
- `artifacts/tokens.css`

The specimen must reflect the same tokens and component names as the manifest.

## Phase 5: Validation

Run validation in warning mode while drafting and strict mode before completion:

```bash
python3 scripts/validate-extraction.py <extraction-root>
python3 scripts/validate-extraction.py --strict <extraction-root>
```
