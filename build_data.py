#!/usr/bin/env python3
"""The Voice AI Index — recompute the living index of voice & speech AI tooling from live
GitHub signals, and write data.json + SEO (sitemap, rss, robots, llms.txt).

Scope = the spoken-language stack: text-to-speech (TTS), speech-to-text (ASR/STT), voice
cloning & conversion (RVC), realtime voice agents & assistants, speech toolkits/frameworks,
and enhancement/analysis (diarization, VAD, separation, wake-word). Excludes music/audio
*generation* (a sibling space), image/diffusion repos, LLM/chat tooling, prompt and
awesome-list repos. Gathered, deduped, FILTERED (precision over recall), categorized, scored.

Only the GitHub *search* payload is used. Env: GITHUB_TOKEN (required for a usable rate limit).
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

HERE = os.path.dirname(os.path.abspath(__file__))
API = "https://api.github.com"
SITE_URL = "https://voice.kymatalabs.com"   # fixed to the real alias after first deploy
SITE_NAME = "The Voice AI Index"

QUERIES = [
    "topic:text-to-speech stars:>120",
    "topic:speech-to-text stars:>120",
    "topic:tts stars:>120",
    "topic:asr stars:>150",
    "topic:speech-recognition stars:>200",
    "topic:speech-synthesis stars:>100",
    "topic:voice-cloning stars:>70",
    "topic:voice-conversion stars:>70",
    "topic:voice-assistant stars:>150",
    "topic:speech stars:>300",
    "topic:speaker-diarization stars:>60",
    "text to speech in:name,description stars:>200",
    "speech recognition in:name,description stars:>250",
    "voice cloning in:name,description stars:>100",
    "voice agent in:name,description stars:>80",
]


def token() -> str:
    return (os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN") or "").strip()


HEADERS = {"Accept": "application/vnd.github+json", "User-Agent": "voice-index"}
if token():
    HEADERS["Authorization"] = f"Bearer {token()}"

_VOICE_TOPICS = {"text-to-speech", "tts", "speech-synthesis", "speech-to-text", "stt", "asr",
                 "speech-recognition", "voice-cloning", "voice-conversion", "voice-changer",
                 "voice-assistant", "voice-agent", "speech", "voice", "whisper", "speech-processing",
                 "speaker-diarization", "speaker-recognition", "wake-word", "wakeword", "vad",
                 "speech-enhancement", "voice-activity-detection", "tacotron", "vits", "rvc",
                 "speech-separation", "speech-emotion-recognition", "transcription", "stt-tts"}
_VOICE_PHRASES = re.compile(
    r"\b(text[- ]to[- ]speech|speech[- ]to[- ]text|speech recognition|speech synthesis"
    r"|voice clon(e|ing)|voice conversion|voice chang(er|ing)|voice assistant|voice agent"
    r"|voice ai|conversational (voice|speech)|real[- ]?time (voice|speech)|\btts\b|\basr\b|\bstt\b"
    r"|transcrib(e|ing)|transcription|speaker (diariz|recogni|verif)|diarization|wake[- ]?word"
    r"|voice activity|speech enhancement|speech separation|speech emotion|vocoder"
    r"|on[- ]device speech|whisper|phoneme|forced alignment)\b", re.I)
# Music/audio GENERATION (sibling space), image/diffusion, LLM/chat, prompt/awesome/paper repos,
# and generic media apps that match a voice phrase but aren't voice-AI tools. Lowercased
# full_name (is_voice lowercases before the lookup); _ANTI (name+desc) catches the rest.
_DENY = {  # sibling-index / general-ML / LLM / wrapper repos that match but aren't voice-AI tools
    "f/awesome-chatgpt-prompts", "dair-ai/prompt-engineering-guide", "ggerganov/llama.cpp",
    "open-webui/open-webui", "facebookresearch/audiocraft", "comfyanonymous/comfyui",
    "automatic1111/stable-diffusion-webui", "huggingface/diffusers",
    # general ML / model frameworks & zoos (mention speech among many modalities)
    "huggingface/transformers", "unslothai/unsloth", "mudler/localai", "mastra-ai/mastra",
    "mozilla-ai/llamafile", "huggingface/datasets", "openvinotoolkit/openvino",
    "modelscope/modelscope", "paddlepaddle/models", "nvidia/deeplearningexamples",
    "kmario23/deep-learning-drizzle", "graniet/llm", "voltagent/voltagent",
    "qwenlm/qwen2.5-omni", "fosowl/agenticseek",
    # not voice-AI: video/short-video engines, translation/OCR, ebook readers, screen recorders
    "aidc-ai/pixelle-video", "modelscope/funclip", "pot-app/pot-desktop", "readest/readest",
    "screenpipe/screenpipe", "morettt/my-neuro", "peterh0323/streamer-sales",
    "calesthio/openmontage",
    # ChatGPT/LLM voice-frontend wrappers (belong to LLM/agent space, not the voice stack)
    "hahahumble/speechgpt", "cogentapps/chat-with-gpt", "ibm-cloud/chatbot-watson-android"}
_ANTI = re.compile(
    r"\b(awesome|curated|prompt engineering|prompt (collection|library)|list of|tutorial|course"
    r"|roadmap|cheat ?sheet|paper[- ]?(list|survey)|reading list|survey (on|of)|interview"
    r"|music generation|musicgen|audiocraft|text[- ]to[- ]music|song generation|melody|\bdaw\b"
    r"|sound effects?|beat maker|stable diffusion|text[- ]to[- ]image|image generation|comfyui"
    r"|lip[- ]?sync|talking[- ]?(head|avatar|face)|model context protocol|\bmcp\b|second brain"
    r"|chatgpt clone|llm chat(bot)?|\bbook\b|podcast player|audiobook reader)\b", re.I)


def gh(url: str, *, retries: int = 4):
    last = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=HEADERS), timeout=30) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = e
            if e.code in (403, 429):
                reset = e.headers.get("X-RateLimit-Reset")
                wait = 5 * (attempt + 1)
                if reset:
                    try:
                        wait = max(wait, min(60, int(reset) - int(time.time()) + 2))
                    except ValueError:
                        pass
                print(f"  rate-limited — sleeping {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            if 500 <= e.code < 600:
                time.sleep(3 * (attempt + 1))
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(3 * (attempt + 1))
    if last:
        raise last
    raise RuntimeError(f"gh failed: {url}")


def search(q: str, per_page: int = 40) -> list[dict]:
    url = (f"{API}/search/repositories?q={urllib.parse.quote(q)}"
           f"&sort=stars&order=desc&per_page={per_page}")
    try:
        return gh(url).get("items", [])
    except Exception as e:
        print(f"  query failed [{q}]: {e}", file=sys.stderr)
        return []


def is_voice(r: dict) -> bool:
    full = (r.get("full_name") or "").lower()
    if full in _DENY:
        return False
    name = r.get("name") or ""
    desc = r.get("description") or ""
    if _ANTI.search(f"{name} {desc}"):       # name+desc → catches awesome-*/music-gen/diffusion names
        return False
    topics = {t.lower() for t in (r.get("topics") or [])}
    if topics & _VOICE_TOPICS:
        return True
    return bool(_VOICE_PHRASES.search(f"{r.get('name','')} {desc}"))


def categorize(r: dict) -> str:
    topics = {t.lower() for t in (r.get("topics") or [])}
    blob = f"{(r.get('name') or '').lower()} {(r.get('description') or '').lower()} {' '.join(topics)}"
    # toolkits/frameworks FIRST (so espnet/nemo/speechbrain don't fall into TTS/STT via a topic)
    if re.search(r"\b(espnet|speechbrain|kaldi|nemo|sherpa|wenet|fairseq|k2|icefall|toolkit"
                 r"|framework|\bsdk\b|inference (engine|server|library))\b", blob):
        return "Toolkits & Frameworks"
    if re.search(r"voice (clon|conver|chang)|\brvc\b|voice[- ]?changer|so[- ]?vits|singing voice"
                 r"|timbre|voice swap", blob):
        return "Voice Cloning & Conversion"
    if re.search(r"real[- ]?time|voice (agent|assistant|bot)|conversational|telephony|\bsip\b"
                 r"|pipecat|livekit|\bagent\b|voice interface|wake[- ]?word|wakeword|hotword", blob):
        return "Voice Agents & Realtime"
    if re.search(r"diariz|speaker (recogn|verif|id)|separation|denois|enhanc|\bvad\b|voice activity"
                 r"|emotion|forced alignment|noise (suppress|reduc)", blob):
        return "Enhancement & Analysis"
    if re.search(r"speech[- ]?to[- ]?text|\bstt\b|\basr\b|speech recognition|transcrib|transcription"
                 r"|\bwhisper\b|subtitle|caption|dictation", blob):
        return "Speech-to-Text"
    if re.search(r"text[- ]?to[- ]?speech|\btts\b|speech synthesis|vocoder|tacotron|\bvits\b"
                 r"|voice synthesis|neural voice|narrat", blob):
        return "Text-to-Speech"
    if re.search(r"awesome|curated|collection|directory|dataset|corpus", blob):
        return "Datasets & Collections"
    return "Speech-to-Text"


def days_since(iso: str | None) -> float | None:
    if not iso:
        return None
    try:
        return (datetime.now(timezone.utc) - datetime.fromisoformat(iso.replace("Z", "+00:00"))).total_seconds() / 86400.0
    except ValueError:
        return None


def momentum(r: dict, max_stars: int) -> int:
    stars = r.get("stargazers_count", 0) or 0
    star_norm = math.log10(stars + 1) / math.log10(max(max_stars, 10) + 1)
    pushed = days_since(r.get("pushed_at"))
    recency = 0.2 if pushed is None else max(0.0, 1.0 - max(0.0, pushed) / 180.0)
    created = days_since(r.get("created_at"))
    young = (1.0 - created / 120.0) if (created is not None and created < 120 and stars >= 20) else 0.0
    return max(1, min(100, round((0.55 * star_norm + 0.32 * recency + 0.13 * young) * 100)))


def slugify(full_name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", full_name.lower()).strip("-")


def build_items() -> list[dict]:
    seen: dict[str, dict] = {}
    for q in QUERIES:
        for r in search(q):
            full = r.get("full_name")
            if full and full not in seen and is_voice(r):
                seen[full] = r
        time.sleep(0.7)
    raw = list(seen.values())
    max_stars = max((r.get("stargazers_count", 0) or 0) for r in raw) if raw else 10
    items = []
    for r in raw:
        owner = r.get("owner") or {}
        items.append({
            "name": r.get("name", ""), "full_name": r.get("full_name", ""),
            "slug": slugify(r.get("full_name", "")), "url": r.get("html_url", ""),
            "owner": owner.get("login", ""), "owner_avatar": owner.get("avatar_url", ""),
            "stars": r.get("stargazers_count", 0) or 0, "forks": r.get("forks_count", 0) or 0,
            "open_issues": r.get("open_issues_count", 0) or 0, "language": r.get("language") or "",
            "license": ((r.get("license") or {}) or {}).get("spdx_id") or "",
            "pushed_at": r.get("pushed_at"), "created_at": r.get("created_at"),
            "description": (r.get("description") or "").strip(), "topics": r.get("topics") or [],
            "category": categorize(r), "momentum": momentum(r, max_stars),
        })
    items.sort(key=lambda x: (x["momentum"], x["stars"]), reverse=True)
    for i, it in enumerate(items, 1):
        it["rank"] = i
    return items


def write_json(items: list[dict]) -> dict:
    cats: dict[str, int] = {}
    for it in items:
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    data = {"generated_at": datetime.now(timezone.utc).isoformat(), "count": len(items),
            "categories": [{"name": k, "count": v} for k, v in sorted(cats.items(), key=lambda x: -x[1])],
            "items": items}
    with open(os.path.join(HERE, "data.json"), "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    return data


def write_seo(data: dict) -> None:
    items = data["items"]
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    urls = [f"  <url><loc>{SITE_URL}/</loc><lastmod>{now}</lastmod><changefreq>daily</changefreq><priority>1.0</priority></url>"]
    for it in items:
        urls.append(f"  <url><loc>{SITE_URL}/p/{it['slug']}/</loc><lastmod>{now}</lastmod>"
                    f"<changefreq>weekly</changefreq><priority>0.6</priority></url>")
    open(os.path.join(HERE, "sitemap.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        + "\n".join(urls) + "\n</urlset>\n")
    open(os.path.join(HERE, "robots.txt"), "w", encoding="utf-8").write(
        f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    def esc(s):
        return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    rss_items = [
        f"    <item><title>{esc(it['full_name'])} — momentum {it['momentum']}</title>"
        f"<link>{SITE_URL}/p/{it['slug']}/</link><guid isPermaLink=\"false\">{esc(it['full_name'])}</guid>"
        f"<description>{esc(it['description'][:300])}</description></item>" for it in items[:30]]
    open(os.path.join(HERE, "rss.xml"), "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0">\n  <channel>\n'
        f"    <title>{SITE_NAME}</title>\n    <link>{SITE_URL}</link>\n"
        "    <description>The living index of voice &amp; speech AI tooling — TTS, speech recognition, voice cloning, realtime voice agents, toolkits.</description>\n"
        + "\n".join(rss_items) + "\n  </channel>\n</rss>\n")

    lines = [f"# {SITE_NAME}", "",
             "> The living index of voice & speech AI tooling — text-to-speech, speech recognition,",
             "> voice cloning & conversion, realtime voice agents, toolkits — ranked daily by GitHub momentum.", "",
             f"Updated: {data['generated_at']}", f"Tools indexed: {data['count']}", "",
             "## Top voice & speech tools by momentum", ""]
    for it in items[:40]:
        lines.append(f"- [{it['full_name']}]({it['url']}) — momentum {it['momentum']}, "
                     f"⭐{it['stars']} — {it['category']} — {it['description'][:100]}")
    open(os.path.join(HERE, "llms.txt"), "w", encoding="utf-8").write("\n".join(lines) + "\n")


def main() -> int:
    if not token():
        print("WARNING: no GITHUB_TOKEN — low rate limit, partial results", file=sys.stderr)
    items = build_items()
    if not items:
        print("ERROR: no voice tools found — refusing to write empty data.json", file=sys.stderr)
        return 1
    data = write_json(items)
    write_seo(data)
    print(f"wrote data.json: {len(items)} voice tools across {len(data['categories'])} categories")
    print("  top 5:", ", ".join(f"{it['full_name']}({it['momentum']})" for it in items[:5]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
