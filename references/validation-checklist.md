# Validation Checklist

- [ ] Manifest JSON parses.
- [ ] `schemaVersion` is `2.0`.
- [ ] Required files exist.
- [ ] `style-specimen.html` has no `/* REPLACE */` markers.
- [ ] `tokens.json` and `tokens.css` exist.
- [ ] CSS tokens referenced by manifest exist in `tokens.css`.
- [ ] Evidence references use `ev:<category>/<id>`.
- [ ] Evidence references resolve to `evidence/evidence-index.json`.
- [ ] `rawSources[].path` files exist.
- [ ] Manifest `evidence.items` and `evidence/evidence-index.json` are synchronized.
- [ ] Every component has a `default` state.
- [ ] Motion guide exists when `motion.present` is true.
- [ ] Motion guide is absent and limitations explain why when `motion.present` is false.
- [ ] Empty arrays or objects are explained by limitations.
- [ ] Third-party screenshots and assets are listed for review.
