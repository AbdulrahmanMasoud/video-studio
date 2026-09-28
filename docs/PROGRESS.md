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

## Phase 1 — Engine productisation — DONE (2026-09-27)

### What was done
Engine (`engine/video-engine`, CLI stays backward compatible; details in `CHANGELOG.md`):
- edge-tts removed → `TTSProvider` (`openai`, `espeak` for tests; default `none`). `vt.py tts` writes `tts.mp3`, timings come from `transcribe`.
- `mux`/`build`: `--watermark PNG --watermark-pos --watermark-opacity --watermark-scale`, `--max-height` (short-side cap). QA now checks the *delivered* size.
- `init --duration-limit`, non-media inputs rejected, typed `error_code`s (`intake_missing`, `input_too_long`, `input_invalid`, `asset_invalid`, `tts_*`).
- `--json` / `VT_JSON=1` structured logs with `progress` events; `VT_OFFLINE=1` socket guard (loopback only) + `HF_HUB_OFFLINE`.
- `fonts --precache`: 92 Google Fonts families for 29 scripts × 7 roles baked into the image (78 MB), parallel downloads with retries.
- Assets: HEIC/HEIF/AVIF/WebP via pillow-heif, EXIF rotation applied + metadata stripped, alpha kept (PNG, `--fit contain`), 40 MP guard,
  clip `--start/--duration/--max-duration`, audio dropped unless `--keep-audio` (mixed at the scene), `vt.py assets --manifest` → `media/index.json`.
- SIGTERM/SIGINT handler terminates ffmpeg/Chromium children and exits 143/130; `run()` has a timeout.
- Mix true-peak ceiling −1.5 dBTP (was −1.2) so AAC output stays under −1 dBTP.

Worker (`apps/worker`, package `vs_worker`):
- `Pipeline(spec, workdir)`: `prepare_preview()` (init → tts? → transcribe → analyze/edit → cam media → assets → plan → stills),
  `apply_plan()` (re-validate with stills), `render()` (render → sfx → music → mix → mux → qa), `cleanup()`; step events, per-step timeouts,
  `PipelineError(code, transient, user_error)`.
- `EngineRunner`: JSON-event subprocess driver, process-group kill on timeout.
- Deterministic fallback planner (`steps`, `mirror`, generic `text` for the other 22) with sentence/pause sectioning, 4–6-word titles,
  announced-count detection (en/ar), en/ar labels.
- Offline fixtures: espeak-ng voice (3 sentences), testsrc2 screen recording / talking-head stand-in, HEIC with EXIF orientation, transparent PNG, 90 s clip.
- Pinned deps via `uv pip compile` (`apps/worker/requirements.txt`), `Makefile`, GitHub Actions `ci.yml` (build image → doctor → ruff/mypy → smoke all → pytest).

### What was tested (image `vs-worker:phase1`, whisper `small`)
| check | command | result |
|---|---|---|
| lint | `ruff check . && mypy vs_worker` (in image) | clean |
| unit + CLI + assets + mux + TTS + planner | `pytest apps/worker -m "not slow"` | 36 passed, 1 skipped (OpenAI TTS: no key) |
| **DoD pipeline** | `pytest apps/worker/tests/test_pipeline.py` | 5 passed: espeak fixture → transcribe (`small`, autodetect `en`) → edit → fallback plan → stills → render `--draft` → mux with watermark + `--max-height 720` → MP4 exists, has audio, −14.0 LUFS (±2 LU asserted), TP −1.2, no QA issues; video-input `mirror` job registers `cam`; `apply_plan` rejects bad anchor / unknown scene with `plan_invalid`; user errors non-transient; TTS script job |
| full suite | `pytest apps/worker` | 41 passed, 1 skipped in 93 s |
| engine smoke | `smoke.py --sizes 9:16,16:9` with `VT_OFFLINE=1` | 48/48 ok (24 templates × 2 sizes), no browser errors |
| SIGTERM | `test_sigterm_stops_cli_cleanly` | exit 143, children gone |

### Findings / open items
1. Google Fonts occasionally refuses a few subset files under parallel load (12/119 for one CJK family before retries were added);
   the build now retries 3× with backoff. If a family still misses files, the render falls back per glyph range: watch the build log line `failed to download`.
2. HEIC decoding relies on pillow-heif (libheif/libde265, LGPL) → license/patent question for the owner (DECISIONS #9).
3. `--keep-audio` clip audio is mixed at −6 dB under the voice for the scene length only; there is no per-clip gain control yet.
4. The fallback planner ignores the brief except `title`; brand palette/fonts are applied by the engine from `init`.
5. Next (Phase 2): LLM planner with the validation loop, editable fields, asset slots, edit-decision step, MockLLM; the `Planner` protocol in `pipeline.py` is the plug-in point.

## Phase 2 — LLM planner — DONE (2026-09-27), pending the owner's real-model run

### What was done (`apps/worker/vs_worker/llm/`, `planner/`)
- `LLMClient` (LiteLLM) with JSON mode / JSON-only + repair, vision input, fallback chain, timeouts, cost accounting (LiteLLM map → `plans.yaml`).
- `LLMSettings`: per-task routing with env defaults (first provider with a key wins: Anthropic → OpenAI → Ollama), `app_settings` overrides,
  free/paid tier models, `provider_status()` for `/admin/llm`.
- `LLMPlanner`: prompt builder (role, template SKILL.md, plan schema, hard rules, asset rules, brief, assets, shortened example — Arabic when
  the video is Arabic —, indexed transcript), validation loop (Pydantic + whitelist + anchors + asset names → engine stills), ≤ 3 attempts →
  `plan_failed`, fallback planner when the LLM is unreachable, optional vision review, `editable_fields`, `asset_slots`, `unused_assets`,
  usage/cost on the job (`llm.*` in job.json, `PreviewResult.llm`).
- Edit-decision step (fast model → validated `--drop` ranges) and asset auto-description (vision) wired into the pipeline.
- `Pipeline.apply_texts()` / `apply_assets()` (swap, remove, insert a full-frame `media` scene at a word, interrupted scene resumes).
- `MockLLM` (example plan re-anchored to the transcript, media slots filled, scripted queue) and `python -m vs_worker.cli`.
- `packages/shared/plans.yaml` (plans, limits, basic templates, LLM price table).

### What was tested (image `vs-worker:phase2`)
| check | result |
|---|---|
| `ruff` + `mypy` | clean (21 source files) |
| `pytest apps/worker` (full) | 80 passed, 7 skipped (6 real-provider smokes without keys, 1 OpenAI TTS) in 101 s |
| DoD: valid plan accepted | `test_mock_plan_accepted_and_usage_recorded` |
| DoD: bad word index repaired within 3 attempts (mock: bad then good) | `test_bad_anchor_repaired_within_attempts`, engine errors loop: `test_engine_errors_feed_the_repair_loop` |
| DoD: unknown scene type / unknown asset rejected | `test_unknown_scene_type_and_asset_rejected_then_plan_failed` (→ `plan_failed` after 3) |
| DoD: editable fields + asset slots round-trip | `test_apply_text_edits_roundtrip…`, `test_asset_slots_and_swap_remove_insert`, engine-backed `test_top_five_places_each_image_in_its_rank` (edit → swap → remove → insert → stills) |
| DoD: top-five with 5 Pillow images placed in ranks, contact sheet shows them | same test: ≥ 20 % of each rank still's pixels are the asset colour |
| every provider through the same code path | `test_every_provider_same_code_path[6 providers]` (fake transport; Ollama `api_base`, JSON mode flag) |
| edit decisions | `test_edit_decision_validation`, pipeline `test_mock_planner_full_pipeline_with_llm_edit_decision` (2 words dropped end to end) |
| Arabic example / RTL plan | `test_arabic_example_plan_is_used_for_arabic` (quiz, labels in Arabic, stills render) |
| engine smoke after the `edit.py` change | 48/48 ok |

### Not done / needs the owner
1. **Manual run with a real model** (DoD): no provider key is available in this environment. Run
   `docker run --rm -e ANTHROPIC_API_KEY -v $PWD/jobs:/jobs vs-worker:dev python -m vs_worker.cli run --input /jobs/voice.m4a --template steps --lang ar --size 9:16 --out /jobs`
   on the espeak fixture and on your Arabic sample and share `qa/contact_sheet.jpg` + `plan.json`. `tests/test_llm_real.py` also runs per key.
2. Vision review is off by default (`PLANNER_VISION_REVIEW=1` to enable); cost is one extra vision call per plan.
3. The fallback chain is empty by default; set `LLM_FALLBACK_CHAIN` (e.g. `openai/gpt-4o,groq/llama-3.3-70b-versatile`).

## Phase 3 — API and database — not started
