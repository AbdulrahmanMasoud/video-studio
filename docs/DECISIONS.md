# Decisions

Format: date, decision, why. Newest at the bottom. The brief (`VIDEO_STUDIO_SAAS_BRIEF.md`) is the
source of requirements; this file records the defaults we picked where the brief left room.

## 2026-09-27 — Phase 0

1. **Monorepo root is this repository** (`video-studoi/`), not a nested `video-saas/` folder. The
   brief's layout is applied at the repo root. Why: the owner already initialised git here; nesting
   would add a pointless level.
2. **`engine/` is `plugins/video-studio/skills` verbatim**, plus the upstream `LICENSE` copied in as
   `engine/LICENSE`. The empty stray directory `video-engine/{scripts` from the zip was dropped.
   `docs/previews/*.jpg` from the zip were kept (used by the landing page gallery).
3. **`engine-dev/` path fix**: `SK = ROOT / "engine"` and smoke output in `engine-dev/_smoke/`
   (git-ignored). The `examples/*.py` helpers import `mkplan` relatively and needed no change.
4. **Whisper model in the image is a build arg** (`WHISPER_MODEL`, default `small`). Prod builds pass
   `medium`. Why: the brief wants `small` in tests and `medium` in prod from one Dockerfile.
5. **Worker base image**: `python:3.12-slim-bookworm` + Debian ffmpeg + Playwright's own Chromium
   (`playwright install --with-deps chromium`). Why: the Playwright pip version pins the browser build,
   avoiding a mismatch with a distro Chromium.
6. **`espeak-ng` and `tini` are installed in the worker image** already in Phase 0. espeak-ng is the
   offline speech source for test fixtures (Phase 1); tini gives clean SIGTERM handling for the CLI.
7. **Non-root worker** (`uid 10001`), caches under `/cache` (`VT_CACHE`, `HF_HOME`), jobs under `/jobs`.

## 2026-09-27 — Phase 1

8. **`--max-height` caps the short side**, not literally the height: `720` gives 1280×720 for landscape and
   720×1280 for portrait. Why: the plans speak of "720p" for the free tier and a portrait video with a 720 px
   height would be unusably small. Documented in the CLI help and SKILL.md.
9. **Copyleft tooling policy.** ffmpeg (Debian build, GPL) and espeak-ng (GPL) run as separate processes and
   are never linked into our code; pillow-heif bundles LGPL decoders. The brief's "MIT/Apache/OFL only" is
   applied to code and fonts shipped in the product; process-level tools are recorded in `docs/THIRD_PARTY.md`.
   Flagged to the owner as a question (HEVC/HEIC decoding also has patent implications for a commercial service).
10. **TTS timings come from transcription**, never from the provider. The espeak provider exists only for
    offline tests and fixtures; the default is `TTS_PROVIDER=none` so the product cannot accidentally use it.
11. **Clip audio (`--keep-audio`)** is stored as `media/<name>.wav` and mixed in by `vt.py mix` at the start of the
    scene whose `media` field names the clip, at −6 dB, trimmed to the scene length. The engine's frame-sequence
    media has no audio otherwise.
12. **Fallback planner covers all templates**: dedicated storyboards for `steps` and `mirror` (as required) and
    the common `text` scene per section for the other 22, so a job can always reach `preview_ready`.
13. **The pipeline never skips a step on re-run**; the engine overwrites its outputs deterministically, which is
    what makes retries safe. Idempotency is tested by rendering twice into the same folder.
14. **Font pre-cache is its own Docker layer** built from only `fonts.py` + `common.py`, so ordinary engine edits
    do not trigger the slow network-bound download again.
15. **Asset validation lives in two places**: real-content and size checks in the engine (`media`/`assets`, error
    `asset_invalid`), asset-*name* validation in the planner (Phase 2) because `engine.js` draws a placeholder for
    unknown media instead of failing.
16. **`VS_ENGINE_DIR` / `VS_REPO_ROOT`** env vars let the worker find the engine outside the repo layout (Docker).
17. **Mix true-peak ceiling lowered from −1.2 to −1.5 dBTP.** The AAC encoder in `mux` overshoots by about
    0.3 dB, so the delivered file measured −0.9 dBTP against the documented “≤ −1 dBTP” standard. With −1.5 the
    final lands around −1.2. The QA threshold itself (−0.5) is unchanged.

## 2026-09-27 — Phase 2

18. **Two validators, in order.** A cheap in-process validator (Pydantic shape, template scene whitelist, anchor range, asset names) rejects
    most bad plans without touching Chromium; only plans that pass it go to `vt.py stills --auto`, whose errors (missing word index, unknown
    scene type, short-scene warnings are not errors) feed the repair message. Both share the same error wording as the engine.
19. **The planner owns the validation loop, the pipeline owns the engine.** `PlanContext.validate` is a closure the pipeline injects (writes
    `plan.json`, runs stills); the planner never shells out. When the accepted plan was already validated, the pipeline skips the extra stills run.
20. **Mock strategy.** `MockLLM` returns the template's example plan re-anchored to the real transcript by scaling word indices from the
    demo script length to the real word count (monotonic) and fills media slots with the job's assets in order. Tests that need specific
    failures use its scripted queue. Provider-specific request building is tested through `LLMClient` with a fake `completion` for all six
    providers; real calls run only when a credential is present (`tests/test_llm_real.py`).
21. **Editable fields are derived, not asked for.** Every string in `scenes[*]`/`labels` that is not a time anchor, enum-like key (type,
    icon, kind, media, …) or empty becomes `{path, label, value, maxLen}`; labels are deterministic ("step #2 · card · text") so the web app
    can localise by key. The fast model is not used for labels (cost, determinism).
22. **Inserting a media scene resumes the interrupted scene.** `insert` at word *w* for *d* seconds adds a `media` scene with an explicit
    `end` and, if the next scene starts later, a copy of the interrupted scene starting at the insert's end, so the frame never goes empty.
23. **Edit decisions are conservative by construction.** Ranges must be in bounds, non-overlapping, ≤ 15 words each and ≤ 25 % of the words
    in total; any violation drops nothing. The step runs only when the planner exposes `decide_edits` and `JobSpec.llm_edit_decisions` is on.
24. **Free vs paid model choice is a `JobSpec.tier`**, resolved by `LLMSettings.planner_for_tier`; the API sets it from the user's plan.
25. **Word survival after a cut is decided by the word's midpoint** (engine `edit.py`). With the old "start survives" rule a word whose first
    20 ms fell inside the crossfade padding stayed in the transcript although its audio was cut, which broke `--drop` accounting.
26. **The font pre-cache layer is strict.** `ensure_family` no longer writes `font.css` for a family with missing subset files, and the
    Dockerfile step exits non-zero when any family is incomplete. Why: an overnight build lost DNS mid-download, Docker cached the
    "successful" but degraded layer, and every later build would have shipped it silently.
