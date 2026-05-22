#!/usr/bin/env python3
"""
Validate an extract-design v1 extraction directory.

Exit codes:
    0: no errors
    1: validation errors found
    2: command or runtime error
"""

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


REQUIRED_FILES = [
    "guides/style-guide.md",
    "guides/evidence-manifest.md",
    "evidence/evidence-index.json",
    "artifacts/style-manifest.json",
    "artifacts/style-specimen.html",
    "artifacts/tokens.json",
    "artifacts/tokens.css",
]

TOP_LEVEL_REQUIRED = [
    "schemaVersion",
    "meta",
    "evidence",
    "rawSources",
    "design_system",
    "design_style",
    "components",
    "motion",
    "reuse_filter",
    "limitations",
]

DESIGN_SYSTEM_KEYS = ["colors", "typography", "spacing", "radii", "shadows", "borders"]
TOKEN_PATTERN = re.compile(r"--[a-zA-Z0-9_-]+")


@dataclass
class Finding:
    path: str
    severity: str
    code: str
    message: str
    line: Optional[int] = None

    def format(self):
        location = self.path if self.line is None else f"{self.path}:{self.line}"
        return f"{location} [{self.severity}] {self.code}: {self.message}"


class Validator:
    def __init__(self, root, strict=False):
        self.root = Path(root)
        self.strict = strict
        self.findings = []
        self.manifest = None
        self.evidence_index = None
        self.tokens_css = ""

    def add(self, path, severity, code, message, line=None):
        self.findings.append(Finding(path, severity, code, message, line))

    def error_or_warning(self):
        return "error" if self.strict else "warning"

    def load_json(self, relpath):
        path = self.root / relpath
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            self.add(relpath, "error", "missing-file", "file does not exist")
        except json.JSONDecodeError as exc:
            self.add(relpath, "error", "invalid-json", exc.msg, exc.lineno)
        return None

    def validate(self):
        if not self.root.exists() or not self.root.is_dir():
            self.add(str(self.root), "error", "missing-root", "extraction root does not exist")
            return self.findings

        self.check_required_files()
        self.manifest = self.load_json("artifacts/style-manifest.json")
        self.evidence_index = self.load_json("evidence/evidence-index.json")
        tokens_json = self.load_json("artifacts/tokens.json")
        tokens_css_path = self.root / "artifacts/tokens.css"
        if tokens_css_path.exists():
            self.tokens_css = tokens_css_path.read_text(encoding="utf-8")

        if self.manifest:
            self.check_manifest()
            self.check_raw_sources()
            self.check_evidence_refs()
            self.check_evidence_index_sync()
            self.check_components()
            self.check_motion()
            self.check_tokens(tokens_json)
            self.check_empty_arrays()

        self.check_specimen()
        return self.findings

    def check_required_files(self):
        for relpath in REQUIRED_FILES:
            if not (self.root / relpath).exists():
                self.add(relpath, "error", "missing-file", "required v1 output file is missing")

    def check_manifest(self):
        if self.manifest.get("schemaVersion") != "2.0":
            self.add("artifacts/style-manifest.json", "error", "schema-version", "schemaVersion must be 2.0")

        for key in TOP_LEVEL_REQUIRED:
            if key not in self.manifest:
                self.add("artifacts/style-manifest.json", "error", "missing-field", f"missing top-level field: {key}")

        meta = self.manifest.get("meta") or {}
        for key in ["name", "sourceUrl", "capturedAt", "mode"]:
            if not meta.get(key):
                self.add("artifacts/style-manifest.json", "error", "missing-field", f"missing meta.{key}")

        design_system = self.manifest.get("design_system") or {}
        for key in DESIGN_SYSTEM_KEYS:
            if key not in design_system:
                self.add("artifacts/style-manifest.json", "error", "missing-field", f"missing design_system.{key}")

    def check_raw_sources(self):
        for index, item in enumerate(self.manifest.get("rawSources") or []):
            item_path = item.get("path")
            if not item_path:
                self.add("artifacts/style-manifest.json", "error", "raw-source-path", f"rawSources[{index}] has no path")
                continue
            if not (self.root / item_path).exists():
                self.add("artifacts/style-manifest.json", "error", "missing-raw-source", f"rawSources[{index}] path does not exist: {item_path}")
            status = item.get("status")
            if status == "unavailable" and not item.get("unavailableReason"):
                self.add("artifacts/style-manifest.json", self.error_or_warning(), "raw-source-reason", f"rawSources[{index}] is unavailable without unavailableReason")

    def check_evidence_refs(self):
        index_ids = set()
        for item in (self.evidence_index or {}).get("items", []):
            item_id = item.get("id")
            if not item_id or not item_id.startswith("ev:"):
                self.add("evidence/evidence-index.json", "error", "evidence-id", "evidence item id must start with ev:")
                continue
            index_ids.add(item_id)
            item_path = item.get("path")
            if item_path and not (self.root / item_path).exists():
                self.add("evidence/evidence-index.json", self.error_or_warning(), "missing-evidence-path", f"referenced evidence path does not exist: {item_path}")

        refs = sorted(self.collect_evidence_refs(self.manifest))
        for ref in refs:
            if ref not in index_ids:
                self.add("artifacts/style-manifest.json", self.error_or_warning(), "missing-evidence-ref", f"evidence reference is not in evidence-index.json: {ref}")

    def check_evidence_index_sync(self):
        manifest_items = self.manifest.get("evidence", {}).get("items", [])
        index_items = (self.evidence_index or {}).get("items", [])
        manifest_ids = {item.get("id") for item in manifest_items if isinstance(item, dict)}
        index_ids = {item.get("id") for item in index_items if isinstance(item, dict)}

        for missing in sorted(manifest_ids - index_ids):
            self.add("evidence/evidence-index.json", "error", "evidence-index-sync", f"manifest evidence item missing from index: {missing}")
        for extra in sorted(index_ids - manifest_ids):
            self.add("artifacts/style-manifest.json", self.error_or_warning(), "evidence-index-sync", f"index evidence item missing from manifest: {extra}")

        for index, item in enumerate(index_items):
            if not isinstance(item, dict):
                self.add("evidence/evidence-index.json", "error", "evidence-item", f"items[{index}] must be an object")
                continue
            for key in ["id", "type", "path", "description", "capturedAt"]:
                if not item.get(key):
                    self.add("evidence/evidence-index.json", "error", "evidence-item-field", f"items[{index}] missing {key}")

    def collect_evidence_refs(self, value):
        refs = set()
        if isinstance(value, dict):
            for key, child in value.items():
                if key == "items" and isinstance(child, list):
                    continue
                if key == "evidence":
                    refs.update(self.refs_from_value(child))
                else:
                    refs.update(self.collect_evidence_refs(child))
        elif isinstance(value, list):
            for item in value:
                refs.update(self.collect_evidence_refs(item))
        return refs

    def refs_from_value(self, value):
        if isinstance(value, str) and value.startswith("ev:"):
            return {value}
        if isinstance(value, list):
            return {item for item in value if isinstance(item, str) and item.startswith("ev:")}
        if isinstance(value, dict):
            return self.collect_evidence_refs(value)
        return set()

    def check_components(self):
        for index, component in enumerate(self.manifest.get("components") or []):
            states = component.get("states") or []
            if not any(state.get("name") == "default" for state in states if isinstance(state, dict)):
                self.add("artifacts/style-manifest.json", "error", "component-default-state", f"components[{index}] has no default state")

    def check_motion(self):
        motion = self.manifest.get("motion") or {}
        present = motion.get("present")
        motion_guide = self.root / "guides/motion-guide.md"
        limitations = self.manifest.get("limitations") or []

        if present is True:
            patterns = motion.get("patterns") or []
            if not patterns:
                self.add("artifacts/style-manifest.json", "error", "motion-patterns", "motion.present is true but motion.patterns is empty")
            if not motion_guide.exists():
                self.add("guides/motion-guide.md", "error", "missing-motion-guide", "motion.present is true but motion-guide.md is missing")
        elif present is False:
            if motion_guide.exists():
                self.add("guides/motion-guide.md", self.error_or_warning(), "unexpected-motion-guide", "motion guide exists while motion.present is false")
            has_motion_limitation = any(item.get("area") == "motion" for item in limitations if isinstance(item, dict))
            if not has_motion_limitation:
                self.add("artifacts/style-manifest.json", "error", "motion-limitation", "motion.present is false but limitations has no motion entry")
        else:
            self.add("artifacts/style-manifest.json", "error", "motion-present", "motion.present must be boolean")

    def check_tokens(self, tokens_json):
        css_tokens = set(TOKEN_PATTERN.findall(self.tokens_css))
        manifest_tokens = set()

        def collect_tokens(value):
            if isinstance(value, dict):
                token = value.get("token")
                if isinstance(token, str) and token.startswith("--"):
                    manifest_tokens.add(token)
                tokens = value.get("tokens")
                if isinstance(tokens, list):
                    manifest_tokens.update(item for item in tokens if isinstance(item, str) and item.startswith("--"))
                for child in value.values():
                    collect_tokens(child)
            elif isinstance(value, list):
                for item in value:
                    collect_tokens(item)

        collect_tokens(self.manifest)

        for token in sorted(manifest_tokens):
            if token not in css_tokens:
                self.add("artifacts/tokens.css", self.error_or_warning(), "missing-css-token", f"manifest token is missing from tokens.css: {token}")

        if not isinstance(tokens_json, dict):
            self.add("artifacts/tokens.json", "error", "tokens-json", "tokens.json must be an object")

    def check_empty_arrays(self):
        limitations = self.manifest.get("limitations") or []
        has_manual_limitation = any(item.get("area") in ("manual-judgment", "schema", "motion") for item in limitations if isinstance(item, dict))
        if has_manual_limitation:
            return

        for key in DESIGN_SYSTEM_KEYS:
            values = (self.manifest.get("design_system") or {}).get(key)
            if values == []:
                self.add("artifacts/style-manifest.json", self.error_or_warning(), "empty-array", f"design_system.{key} is empty without an explanatory limitation")

    def check_specimen(self):
        relpath = "artifacts/style-specimen.html"
        path = self.root / relpath
        if not path.exists():
            return
        text = path.read_text(encoding="utf-8", errors="ignore")
        for line_number, line in enumerate(text.splitlines(), start=1):
            if "/* REPLACE */" in line or "[REPLACE]" in line:
                self.add(relpath, "error", "placeholder", "placeholder marker found", line_number)


def main():
    parser = argparse.ArgumentParser(description="Validate an extract-design v1 extraction directory")
    parser.add_argument("root", help="Extraction root directory")
    parser.add_argument("--strict", action="store_true", help="Treat evidence and token gaps as errors")
    args = parser.parse_args()

    validator = Validator(args.root, strict=args.strict)
    findings = validator.validate()
    for finding in findings:
        print(finding.format())

    if any(finding.severity == "error" for finding in findings):
        raise SystemExit(1)
    raise SystemExit(0)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        raise
    except SystemExit:
        raise
    except Exception as exc:
        print(f"[runtime-error] {exc}", file=sys.stderr)
        raise SystemExit(2)
