# The Voice AI Index — build continuation (2026-06-08)

**Gap proven + data layer DONE.** Voice & speech AI — `voice.kymatalabs.com`. Fleet index **#12**.
Scaffolded from `~/diffusion-index`; `build_data.py` fully adapted to the voice domain + precision-tightened.

## DONE
- `build_data.py` — QUERIES / `_VOICE_TOPICS` / `_VOICE_PHRASES` / `_DENY` / `_ANTI` / `categorize`
  all adapted to the spoken-language stack. `is_voice()` (renamed from is_gen). Run:
  `GITHUB_TOKEN=$(gh auth token) ~/agent-os/.venv/bin/python build_data.py`.
- `data.json` — **299 tools, 6 categories** (Speech-to-Text 72, Voice Cloning & Conversion 51,
  Toolkits & Frameworks 47, Voice Agents & Realtime 47, Text-to-Speech 45, Enhancement & Analysis 38).
  Precision-tightened 325→299: dropped general-ML/LLM libs (transformers, unsloth, LocalAI, NeMo-zoo
  bleed), ChatGPT-voice wrappers, model zoos, DL courses, video/OCR/ebook tools via `_DENY` (~30 repos).
  Top 5 verified legit: whisper.cpp, VoxCPM, fish-speech, OmniVoice-Studio, Handy. Trustworthy — do NOT re-loosen.
- SEO (sitemap/rss/robots/llms.txt) generated with `SITE_URL=https://voice.kymatalabs.com`.
- `.github/workflows/update.yml` present BUT still says "Diffusion" — **must swap to voice** (name,
  `VERCEL_PROJECT: voice-index`, bot name, commit msg) like the diffusion handoff did.
- `deploy.py` copied (defaults need `VERCEL_PROJECT=voice-index`).

## REMAINING (in order — same proven recipe as diffusion #11; see `~/diffusion-index/CONTINUE.md`)
1. **Distinct design** — a NEW identity the fleet doesn't have yet. Used already: warm-almanac,
   dark-scoreboard, light-blueprint, riso-zine, light-vector-field (RAG), industrial-forge,
   dark-launchpad, **darkroom/spectral (diffusion #11)**. **Recommended for voice: an "acoustic /
   waveform studio" face** — a horizontal animated audio-waveform / VU-meter motif as the hero,
   a recording-console palette (warm ink + a single confident accent, OR a clean light "studio
   paper"), a distinctive display font NOT yet used (e.g. Hanken/Schibsted Grotesk or a characterful
   serif) + a mono for the data. Cards could show the owner avatar (image-forward worked great on #11).
   Create `index.html` + `app.js` + `style.css` + `favicon.svg` fresh (use diffusion/rag as a
   STRUCTURAL template only — do NOT copy the darkroom/spectral look). All copy "Diffusion"→"Voice AI".
2. `gen_details.py` + `gen_og.py` (run with `~/agent-os/.venv/bin/python` for Pillow). New identity,
   `SITE_URL=https://voice.kymatalabs.com`, `SITE_NAME="The Voice AI Index"`, theme key `vfx-theme`.
3. `deploy.py` first deploy (Vercel REST — CLI hangs in CC). Env: `VERCEL_TOKEN` (from ~/agent-os/.env),
   `VERCEL_TEAM_ID=team_L6hpqgg8pEHznOzrnU66JuoW`, `VERCEL_PROJECT=voice-index`. Resolve the real alias.
4. Assign subdomain `voice.kymatalabs.com` (Vercel domains API, POST
   `v10/projects/voice-index/domains?teamId=<team>` body `{"name":"voice.kymatalabs.com"}` → verified ~5s).
   Recanonicalize if alias ≠ SITE_URL → rebuild → redeploy → verify live `?z=<epoch>` (quote the URL —
   zsh globs `?`) + Playwright (cards render, 0 console errors, screenshot).
5. `git init -b main` + `gh repo create tekvisions/voice-index --public` + `gh secret set VERCEL_TOKEN`
   + trigger the cron once (verify green). Commit as `tekvisions <techtalevisions@gmail.com>`. Lock repo
   (`gh repo edit --enable-issues=false --enable-wiki=false --enable-projects=false`). Pro README.
6. **Integrate** (index #12): hub (`~/living-indexes` build_data.py INDEXES + index.html footer; bump
   "Eleven"→"Twelve"), homepage (`~/kymatalabs` branch **master**, `src/data/portfolio.ts`
   flagshipTrackers, commit as tekvisions, bump hub "11 living indexes"→"12"), and `/live`
   (`src/app/live/page.tsx` products + "Twelve"→"Thirteen" copy + hub "11 indexes"→"12 indexes").
   **WATCH the kymatalabs Vercel deploy STATE → READY** (the flagship freeze-scar mitigation).
7. Telegram one-liner + Hive fact (`POST /admin/hive`, `X-Admin-Token` from ~/agent-os/.env ADMIN_TOKEN).

Identity reminder: this is index #12 — give it a face the fleet doesn't have yet. See the shipped
diffusion playbook in memory: `project_diffusion_index_shipped.md`.
