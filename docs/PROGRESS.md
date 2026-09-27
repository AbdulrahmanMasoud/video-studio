# Progress

## Phase 0 — Understand and verify the engine — DONE (2026-09-27)

### What was done
- Unzipped `video-studio.zip`; `plugins/video-studio/skills` → `engine/` (verbatim, plus the upstream
  `LICENSE`), `dev/` → `engine-dev/`, `docs/previews` → `docs/previews`.
- Fixed skill paths in `engine-dev/smoke.py`, `mkplan.py`, `gen_skills.py` (`SK = ROOT / "engine"`,
  smoke output in `engine-dev/_smoke/`) and in `references/template-authoring.md`.
- Read `vt.py`, all of `vtlib/`, `runtime/engine.js`, `video-engine/SKILL.md`, all `references/*.md`,
  `steps/SKILL.md`, `mirror/SKILL.md`, every `template.json`.
- Wrote `docs/ARCHITECTURE.md` (§5 diagram, service table, pipeline mapping, verified engine facts) and
  `docs/DECISIONS.md`.
- `infra/docker/worker.Dockerfile`: python 3.12-slim + ffmpeg + Playwright Chromium + faster-whisper
  with the model baked in (`WHISPER_MODEL` build arg) + espeak-ng + tini, non-root. Image: 3.7 GB.
- `engine-dev/e2e_build.py`: LLM-free end-to-end check (espeak-ng voice → transcribe → analyze → edit →
  simple `steps` plan anchored to real word indices → stills → build).

### What was tested (inside the Docker image, `vs-worker:phase0`)
| check | command | result |
|---|---|---|
| dependencies | `vt.py doctor` | `ALL GOOD` (numpy, scipy, soundfile, PIL, playwright, faster_whisper, ffmpeg, ffprobe, headless chromium) |
| catalog | `vt.py templates` | 24 templates listed |
| intake guard | `vt.py init JOB --template steps` (no lang/size) | exit 2 with the documented error |
| stills smoke | `smoke.py steps quiz --sizes 9:16,16:9` | `ok` ×4, `FAILED: none`; contact sheets inspected |
| full build | `e2e_build.py /jobs/smoke --draft` | 33 words transcribed (`small`), edit 13.7 s → 13.1 s, 5 stills, 393 frames rendered, 15 SFX cues, lofi music, mix −14.0 LUFS / TP −1.1 dBTP, `final.mp4` h264+aac 540×960, QA report written |

### Findings to carry into Phase 1
1. `build --draft` renders at half resolution and QA then reports `resolution 540x960 != requested
   1080x1920`. Expected for drafts; the worker must treat this issue as informational in draft mode
   (or QA should know the render scale).
2. Fonts are fetched from Google Fonts at render time; the image has no font cache, so an offline
   render silently falls back to system fonts. Phase 1 pre-caches all script/role combinations at
   build time and adds `VT_OFFLINE=1`.
3. `[vt]` log lines are plain text; Phase 1 adds `--json`.
4. Whisper `small` on espeak-ng speech yields clean word timings (33/33 words kept), good enough for
   fixtures.
5. `engine.js` does not fail on an unknown media name (draws a placeholder), so asset-name validation
   must live in the planner.
6. The first `transcribe` in a fresh container spends ~1 s on a HF Hub metadata request even with the
   model baked in; set `HF_HUB_OFFLINE=1` in the worker image (Phase 1).

### Open questions for the owner
1. **Repo root**: the monorepo is this repository root (not a nested `video-saas/`). OK?
2. **Whisper in prod**: `medium` int8 on CPU is slow for 10-minute inputs (roughly real time or slower
   on 2 vCPU). Do you want GPU workers as an option, or is CPU with a 15-minute timeout acceptable?
3. **Arabic sample**: please provide one Arabic recording (voice note, 30–90 s) for the Phase 2
   manual planner run.
4. **LLM keys**: which provider keys will exist in dev? (Anthropic is the default; others are only
   smoke-tested when a key is present.)
5. **Draft quality for previews**: should the user-facing preview be stills only (fast, current design)
   or also a low-res draft MP4 (costs a render)?

## Phase 1 — Engine productisation — not started
