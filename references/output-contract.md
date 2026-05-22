# Output Contract

## Default Directory

Runtime output goes to:

```text
<target-project-root>/outputs/extractions/<name>/
```

`--out-dir` may override this path. It can be absolute or relative to the current working directory.

## Required Structure

```text
<extraction-root>/
  guides/
    style-guide.md
    evidence-manifest.md
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
```

`guides/motion-guide.md` and motion raw files are required only when meaningful motion exists.

`transition-scan.json` records measured transition declarations. It can be present even when `motion.present` is `false`.

`library-detect.json` records window-level checks for common animation and UI libraries. A negative result does not prove the page has no bundled animation code.

## Responsibilities

- `raw/`: measured facts from scripts.
- `evidence/`: screenshots, saved source assets, notes, and machine-readable evidence index.
- `artifacts/`: reusable design-system outputs.
- `guides/`: human-readable interpretation and reuse guidance.

## Evidence References

Use:

```text
ev:<category>/<id>
```

Examples:

- `ev:screenshot/home`
- `ev:computed/body`
- `ev:animation/keyframes`

The referenced item must exist in `evidence/evidence-index.json`.

## Versioned Examples

Versioned examples live in:

```text
examples/<name>/
```

Do not write runtime extraction output into `examples/` unless creating or updating a maintained fixture.
