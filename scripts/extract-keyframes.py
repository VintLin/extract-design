#!/usr/bin/env python3
"""
Extract @keyframes and animation hints from a URL or saved CSS folder.

Examples:
    python3 scripts/extract-keyframes.py https://example.com --out raw/keyframes.json
    python3 scripts/extract-keyframes.py evidence/assets --out raw/keyframes.json
"""

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright


def now_iso():
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def is_url(value):
    parsed = urlparse(value)
    return parsed.scheme in ("http", "https")


def extract_from_url(url):
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url, wait_until="networkidle", timeout=30000)

        result = page.evaluate("""() => {
          const keyframes = [];
          const unavailable = [];

          for (const sheet of document.styleSheets) {
            try {
              for (const rule of sheet.cssRules || []) {
                if (rule.type === CSSRule.KEYFRAMES_RULE) {
                  keyframes.push({
                    name: rule.name,
                    cssText: rule.cssText,
                    source: sheet.href || "inline"
                  });
                }
              }
            } catch (error) {
              unavailable.push({
                source: sheet.href || "inline",
                reason: "Stylesheet rules unavailable, likely CORS-restricted."
              });
            }
          }

          const animationVars = {};
          const rootStyle = getComputedStyle(document.documentElement);
          for (const prop of rootStyle) {
            if (prop.includes("animation") || prop.includes("motion") || prop.includes("transition") || prop.includes("duration") || prop.includes("ease")) {
              animationVars[prop] = rootStyle.getPropertyValue(prop).trim();
            }
          }

          const activeAnimations = document.getAnimations().slice(0, 50).map(animation => ({
            playState: animation.playState,
            currentTime: animation.currentTime,
            effectTiming: animation.effect ? animation.effect.getTiming() : null
          }));

          return { keyframes, animationVars, activeAnimations, unavailable };
        }""")

        browser.close()
        return {
            "source": url,
            "mode": "url",
            "capturedAt": now_iso(),
            **result
        }


def extract_from_folder(folder):
    folder = Path(folder)
    if not folder.exists() or not folder.is_dir():
        raise SystemExit(f"Folder not found: {folder}")

    keyframes = []
    pattern = re.compile(r"@keyframes\s+([^{\s]+)\s*{", re.MULTILINE)
    for css_file in folder.rglob("*.css"):
        text = css_file.read_text(encoding="utf-8", errors="ignore")
        for match in pattern.finditer(text):
            name = match.group(1)
            keyframes.append({
                "name": name,
                "cssText": extract_balanced_block(text, match.start()),
                "source": str(css_file)
            })

    return {
        "source": str(folder),
        "mode": "folder",
        "capturedAt": now_iso(),
        "keyframes": keyframes,
        "animationVars": {},
        "activeAnimations": [],
        "unavailable": []
    }


def extract_balanced_block(text, start):
    depth = 0
    end = start
    in_block = False
    for index in range(start, len(text)):
        char = text[index]
        if char == "{":
            depth += 1
            in_block = True
        elif char == "}":
            depth -= 1
            if in_block and depth == 0:
                end = index + 1
                break
    return text[start:end].strip()


def main():
    parser = argparse.ArgumentParser(description="Extract @keyframes and animation hints")
    parser.add_argument("source", help="URL or folder containing saved CSS files")
    parser.add_argument("--out", required=True, help="Output JSON file path")
    args = parser.parse_args()

    data = extract_from_url(args.source) if is_url(args.source) else extract_from_folder(args.source)
    write_json(args.out, data)
    print(f"Saved keyframe extraction to {args.out}")
    print(f"Found {len(data.get('keyframes', []))} @keyframes rules")


if __name__ == "__main__":
    main()
