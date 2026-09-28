"""Manual runner: produce a video from a recording (or script) with the LLM, mock or fallback planner.

    python -m vs_worker.cli run --input voice.m4a --template steps --lang ar --size 9:16 --out ./jobs/manual \
        [--planner llm|mock|fallback] [--tier free|paid] [--asset path[:description] ...] [--draft] [--brief-title "..."]
    python -m vs_worker.cli providers          # which LLM providers have credentials, current routing
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import cast

from .llm.settings import LLMSettings, provider_status
from .pipeline import Pipeline, Planner
from .planner.llm_planner import make_planner
from .spec import AssetSpec, JobSpec, RenderOptions, StepEvent


def _print_event(e: StepEvent):
    if e.status == "progress":
        print(f"  {e.step}: {e.progress * 100:.0f}% {e.message}", flush=True)
    else:
        print(f"[{e.step}] {e.status}" + (f" ({e.error_code}: {e.message})" if e.status == "failed" else ""), flush=True)


def cmd_run(a):
    assets = []
    for i, item in enumerate(a.asset or [], 1):
        path, _, desc = item.partition(":")
        assets.append(AssetSpec(name=f"asset_{i}", path=Path(path), description=desc))
    spec = JobSpec(job_id=a.name, template=a.template, size=a.size, lang=a.lang, platform=a.platform, input_path=Path(a.input) if a.input else None,
                   script=Path(a.script).read_text(encoding="utf-8") if a.script else None, tts_provider=a.tts_provider, whisper_model=a.model,
                   brief={"title": a.brief_title} if a.brief_title else {}, assets=assets, tier=a.tier,
                   render=RenderOptions(draft=a.draft, watermark=Path(a.watermark) if a.watermark else None, max_height=a.max_height))
    planner = cast(Planner, make_planner(a.planner, tier=a.tier))
    pipe = Pipeline(spec, Path(a.out), on_event=_print_event, planner=planner)
    preview = pipe.prepare_preview()
    print(f"\nplanner={preview.planner} lang={preview.detected_lang} words={len(preview.words)} scenes={len(preview.plan['scenes'])}")
    print(f"llm={json.dumps(preview.llm)}")
    print(f"contact sheet: {preview.contact_sheet}")
    if preview.unused_assets:
        print("unused assets:", preview.unused_assets)
    if a.preview_only:
        return 0
    result = pipe.render()
    print(f"final: {result.final_mp4} {result.output_size} qa_issues={result.qa_report.get('issues')}")
    return 0


def cmd_providers(a):
    st = provider_status()
    s = LLMSettings.from_env()
    for prov, row in st.items():
        print(f"  {prov:<11} {'available' if row['available'] else 'no credentials'}   ({row['env']})")
    print("routing:", json.dumps(s.to_dict(), indent=2))
    print("planner mode:", os.environ.get("PLANNER_MODE", "llm"))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sp = ap.add_subparsers(dest="cmd", required=True)
    r = sp.add_parser("run")
    r.add_argument("--input"); r.add_argument("--script"); r.add_argument("--tts-provider")
    r.add_argument("--template", required=True); r.add_argument("--lang"); r.add_argument("--size", default="9:16")
    r.add_argument("--platform", default="tiktok")
    r.add_argument("--out", default="./jobs"); r.add_argument("--name", default="manual"); r.add_argument("--planner", default=None)
    r.add_argument("--tier", default="paid", choices=["free", "paid"]); r.add_argument("--model", default=os.environ.get("WHISPER_MODEL", "small"))
    r.add_argument("--asset", action="append", help="path[:description], repeatable"); r.add_argument("--brief-title")
    r.add_argument("--draft", action="store_true"); r.add_argument("--watermark"); r.add_argument("--max-height", type=int)
    r.add_argument("--preview-only", action="store_true")
    r.set_defaults(fn=cmd_run)
    p = sp.add_parser("providers"); p.set_defaults(fn=cmd_providers)
    a = ap.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
