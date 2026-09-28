#!/usr/bin/env python3
"""Generate packages/shared/templates.json (the template catalog the API and web app read) from the engine folders.

    python3 engine-dev/gen_catalog.py
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SK = ROOT / "engine"
sys.path.insert(0, str(ROOT / "apps/worker"))


def media_fields(name: str) -> list[str]:
    try:
        from vs_worker.planner.assets import media_fields as mf
        return mf(name, SK)
    except Exception:
        return ["media.media"]


def labels(name: str) -> list[str]:
    text = (SK / name / "SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"\*\*Translatable labels:\*\*\s*(.+)", text)
    return re.findall(r"`(\w+)`", m.group(1)) if m else []


def main():
    out = []
    for d in sorted(SK.iterdir()):
        tj = d / "template.json"
        if not tj.exists():
            continue
        m = json.loads(tj.read_text(encoding="utf-8"))
        out.append({"name": d.name, "title": m.get("title", d.name), "category": m.get("category", ""), "summary": m.get("summary", ""),
                    "scenes": m.get("scenes", []), "fonts": m.get("fonts", []), "captions": m.get("captions", {}), "music": m.get("music", {}),
                    "needs_media": m.get("needsMedia", []), "media_fields": media_fields(d.name), "labels": labels(d.name),
                    "has_ar_example": (d / "examples/plan.ar.json").exists(), "preview": f"/previews/{d.name}.jpg"})
    dst = ROOT / "packages/shared/templates.json"
    dst.write_text(json.dumps(out, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {dst} ({len(out)} templates)")


if __name__ == "__main__":
    main()
