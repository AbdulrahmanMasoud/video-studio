"""Pick fonts per writing system and font role, download them from Google Fonts once, cache them.

Roles used by templates: display, body, serif, mono, hand, rounded, condensed.
Every family listed here is open-licensed (SIL OFL / Apache) on Google Fonts.
"""
from __future__ import annotations

import re
import time
import urllib.request
from pathlib import Path

from .common import CACHE_DIR, OFFLINE, OfflineError, log, warn

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

# language code -> script key
LANG_SCRIPT = {
    **{k: "arabic" for k in ["ar", "ps", "sd", "ug", "ckb", "ku"]},
    "fa": "persian", "ur": "urdu",
    "he": "hebrew", "iw": "hebrew", "yi": "hebrew",
    **{k: "devanagari" for k in ["hi", "mr", "ne", "sa", "mai", "bho", "kok"]},
    "bn": "bengali", "as": "bengali", "ta": "tamil", "te": "telugu", "kn": "kannada", "ml": "malayalam",
    "gu": "gujarati", "pa": "gurmukhi", "si": "sinhala", "or": "oriya",
    "th": "thai", "lo": "lao", "km": "khmer", "my": "myanmar",
    "ja": "japanese", "ko": "korean", "zh": "sc", "zh-cn": "sc", "zh-hans": "sc", "zh-tw": "tc", "zh-hant": "tc", "zh-hk": "tc", "yue": "tc",
    "ka": "georgian", "hy": "armenian", "am": "ethiopic", "ti": "ethiopic",
    **{k: "cyrillic" for k in ["ru", "uk", "bg", "sr", "mk", "be", "kk", "ky", "mn", "tg"]},
    "el": "greek", "vi": "vietnamese",
}

# script -> role -> [family, weights]
FONTS = {
    "latin": {"display": ["Archivo", "400;700;800;900"], "body": ["Inter", "400;500;600;700;800"], "serif": ["Playfair Display", "400;700;900"],
              "mono": ["JetBrains Mono", "400;500;700"], "hand": ["Caveat", "400;700"], "rounded": ["Nunito", "400;700;800;900"], "condensed": ["Oswald", "400;500;700"]},
    "cyrillic": {"display": ["Montserrat", "400;700;800;900"], "body": ["Inter", "400;500;600;700;800"], "serif": ["Playfair Display", "400;700;900"],
                 "mono": ["JetBrains Mono", "400;500;700"], "hand": ["Caveat", "400;700"], "rounded": ["Nunito", "400;700;800;900"], "condensed": ["Oswald", "400;500;700"]},
    "greek": {"display": ["Montserrat", "400;700;800;900"], "body": ["Inter", "400;500;600;700;800"], "serif": ["Noto Serif", "400;700"],
              "mono": ["JetBrains Mono", "400;500;700"], "hand": ["Comfortaa", "400;700"], "rounded": ["Comfortaa", "400;700"], "condensed": ["Roboto Condensed", "400;700"]},
    "vietnamese": {"display": ["Be Vietnam Pro", "400;700;800;900"], "body": ["Be Vietnam Pro", "400;500;600;700"], "serif": ["Noto Serif", "400;700"],
                   "mono": ["JetBrains Mono", "400;500;700"], "hand": ["Patrick Hand", "400"], "rounded": ["Nunito", "400;700;800;900"], "condensed": ["Oswald", "400;500;700"]},
    "arabic": {"display": ["Alexandria", "400;600;700;800;900"], "body": ["IBM Plex Sans Arabic", "400;500;600;700"], "serif": ["Amiri", "400;700"],
               "mono": ["IBM Plex Sans Arabic", "400;500;700"], "hand": ["Reem Kufi Ink", "400"], "rounded": ["Tajawal", "400;500;700;800;900"], "condensed": ["Lalezar", "400"]},
    "persian": {"display": ["Vazirmatn", "400;700;800;900"], "body": ["Vazirmatn", "400;500;600;700"], "serif": ["Noto Naskh Arabic", "400;700"],
                "mono": ["Vazirmatn", "400;500;700"], "hand": ["Vazirmatn", "400;700"], "rounded": ["Vazirmatn", "400;700;900"], "condensed": ["Vazirmatn", "700;900"]},
    "urdu": {"display": ["Noto Nastaliq Urdu", "400;700"], "body": ["Noto Nastaliq Urdu", "400;700"], "serif": ["Noto Nastaliq Urdu", "400;700"],
             "mono": ["Noto Sans Arabic", "400;700"], "hand": ["Noto Nastaliq Urdu", "400;700"], "rounded": ["Noto Sans Arabic", "400;700;900"], "condensed": ["Noto Sans Arabic", "400;700;900"]},
    "hebrew": {"display": ["Rubik", "400;700;800;900"], "body": ["Heebo", "400;500;700;800"], "serif": ["Frank Ruhl Libre", "400;700;900"],
               "mono": ["Heebo", "400;500;700"], "hand": ["Karantina", "400;700"], "rounded": ["Varela Round", "400"], "condensed": ["Assistant", "400;700;800"]},
    "devanagari": {"display": ["Poppins", "400;600;700;800;900"], "body": ["Hind", "400;500;600;700"], "serif": ["Noto Serif Devanagari", "400;700"],
                   "mono": ["Noto Sans Devanagari", "400;700"], "hand": ["Kalam", "400;700"], "rounded": ["Baloo 2", "400;600;700;800"], "condensed": ["Hind", "400;600;700"]},
    "bengali": {"display": ["Baloo Da 2", "400;600;700;800"], "body": ["Hind Siliguri", "400;500;600;700"], "serif": ["Noto Serif Bengali", "400;700"],
                "mono": ["Noto Sans Bengali", "400;700"], "hand": ["Galada", "400"], "rounded": ["Baloo Da 2", "400;700;800"], "condensed": ["Hind Siliguri", "400;700"]},
    "tamil": {"display": ["Catamaran", "400;700;800;900"], "body": ["Noto Sans Tamil", "400;500;700"], "serif": ["Noto Serif Tamil", "400;700"],
              "mono": ["Noto Sans Tamil", "400;700"], "hand": ["Catamaran", "400;700"], "rounded": ["Baloo Thambi 2", "400;700;800"], "condensed": ["Catamaran", "400;700"]},
    "telugu": {"display": ["Baloo Tammudu 2", "400;600;700;800"], "body": ["Noto Sans Telugu", "400;500;700"], "serif": ["Noto Serif Telugu", "400;700"],
               "mono": ["Noto Sans Telugu", "400;700"], "hand": ["Gurajada", "400"], "rounded": ["Baloo Tammudu 2", "400;700"], "condensed": ["Noto Sans Telugu", "400;700"]},
    "kannada": {"display": ["Baloo Tamma 2", "400;600;700;800"], "body": ["Noto Sans Kannada", "400;500;700"], "serif": ["Noto Serif Kannada", "400;700"],
                "mono": ["Noto Sans Kannada", "400;700"], "hand": ["Baloo Tamma 2", "400"], "rounded": ["Baloo Tamma 2", "400;700"], "condensed": ["Noto Sans Kannada", "400;700"]},
    "malayalam": {"display": ["Baloo Chettan 2", "400;600;700;800"], "body": ["Noto Sans Malayalam", "400;500;700"], "serif": ["Noto Serif Malayalam", "400;700"],
                  "mono": ["Noto Sans Malayalam", "400;700"], "hand": ["Baloo Chettan 2", "400"], "rounded": ["Baloo Chettan 2", "400;700"], "condensed": ["Noto Sans Malayalam", "400;700"]},
    "gujarati": {"display": ["Baloo Bhai 2", "400;600;700;800"], "body": ["Hind Vadodara", "400;500;600;700"], "serif": ["Noto Serif Gujarati", "400;700"],
                 "mono": ["Noto Sans Gujarati", "400;700"], "hand": ["Baloo Bhai 2", "400"], "rounded": ["Baloo Bhai 2", "400;700"], "condensed": ["Hind Vadodara", "400;700"]},
    "gurmukhi": {"display": ["Baloo Paaji 2", "400;600;700;800"], "body": ["Mukta Mahee", "400;500;700"], "serif": ["Noto Serif Gurmukhi", "400;700"],
                 "mono": ["Noto Sans Gurmukhi", "400;700"], "hand": ["Baloo Paaji 2", "400"], "rounded": ["Baloo Paaji 2", "400;700"], "condensed": ["Mukta Mahee", "400;700"]},
    "thai": {"display": ["Kanit", "400;600;700;800;900"], "body": ["Noto Sans Thai", "400;500;700"], "serif": ["Noto Serif Thai", "400;700"],
             "mono": ["Noto Sans Thai", "400;700"], "hand": ["Sriracha", "400"], "rounded": ["Mitr", "400;500;700"], "condensed": ["Pridi", "400;700"]},
    "japanese": {"display": ["Noto Sans JP", "400;700;900"], "body": ["Noto Sans JP", "400;500;700"], "serif": ["Noto Serif JP", "400;700;900"],
                 "mono": ["M PLUS 1 Code", "400;700"], "hand": ["Yomogi", "400"], "rounded": ["M PLUS Rounded 1c", "400;700;800"], "condensed": ["Noto Sans JP", "700;900"]},
    "korean": {"display": ["Black Han Sans", "400"], "body": ["Noto Sans KR", "400;500;700;900"], "serif": ["Noto Serif KR", "400;700;900"],
               "mono": ["Noto Sans KR", "400;700"], "hand": ["Gamja Flower", "400"], "rounded": ["Jua", "400"], "condensed": ["Noto Sans KR", "700;900"]},
    "sc": {"display": ["Noto Sans SC", "400;700;900"], "body": ["Noto Sans SC", "400;500;700"], "serif": ["Noto Serif SC", "400;700;900"],
           "mono": ["Noto Sans SC", "400;700"], "hand": ["Ma Shan Zheng", "400"], "rounded": ["ZCOOL KuaiLe", "400"], "condensed": ["Noto Sans SC", "700;900"]},
    "tc": {"display": ["Noto Sans TC", "400;700;900"], "body": ["Noto Sans TC", "400;500;700"], "serif": ["Noto Serif TC", "400;700;900"],
           "mono": ["Noto Sans TC", "400;700"], "hand": ["Noto Sans TC", "400"], "rounded": ["Noto Sans TC", "700"], "condensed": ["Noto Sans TC", "700;900"]},
}
# Scripts with a single sensible Noto family for every role
SIMPLE = {"telugu": None, "georgian": "Noto Sans Georgian", "armenian": "Noto Sans Armenian", "ethiopic": "Noto Sans Ethiopic",
          "sinhala": "Noto Sans Sinhala", "oriya": "Noto Sans Oriya", "lao": "Noto Sans Lao", "khmer": "Noto Sans Khmer", "myanmar": "Noto Sans Myanmar"}
ROLES = ["display", "body", "serif", "mono", "hand", "rounded", "condensed"]
GENERIC = {"display": "sans-serif", "body": "sans-serif", "serif": "serif", "mono": "monospace", "hand": "cursive", "rounded": "sans-serif", "condensed": "sans-serif"}


def script_for(lang: str) -> str:
    l = (lang or "en").lower()
    return LANG_SCRIPT.get(l) or LANG_SCRIPT.get(l.split("-")[0]) or "latin"


def _fetch(url: str, retries: int = 3) -> bytes:
    if OFFLINE:
        raise OfflineError(f"VT_OFFLINE=1: refusing to download {url}")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last: Exception | None = None
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return r.read()
        except Exception as e:  # transient: rate limit, reset connection
            last = e
            time.sleep(0.5 * (2 ** attempt))
    raise last  # type: ignore[misc]


def _family_css(family: str, weights: str) -> str | None:
    base = "https://fonts.googleapis.com/css2?family=" + family.replace(" ", "+")
    tries = [f"{base}:wght@{weights}&display=block", f"{base}:wght@400;700&display=block", f"{base}&display=block"]
    for u in tries:
        try:
            return _fetch(u).decode("utf-8")
        except Exception:
            continue
    return None


def ensure_family(family: str, weights: str) -> str | None:
    """Download all woff2 files of a family into the cache; return @font-face CSS with file:// URLs."""
    key = re.sub(r"[^a-z0-9]+", "-", family.lower())
    d = CACHE_DIR / "fonts" / key
    css_file = d / "font.css"
    if css_file.exists():
        return css_file.read_text(encoding="utf-8")
    if OFFLINE:
        warn(f"font '{family}' is not in the cache and VT_OFFLINE=1 - using system fallback", font=family)
        return None
    css = _family_css(family, weights)
    if not css:
        warn(f"font '{family}' unavailable (offline?) - using system fallback", font=family)
        return None
    d.mkdir(parents=True, exist_ok=True)
    urls = sorted(set(re.findall(r"url\((https://[^)]+)\)", css)))
    files = {u: d / re.sub(r"[^A-Za-z0-9._-]", "_", u.rsplit("/", 1)[-1]) for u in urls}
    todo = [u for u, f in files.items() if not f.exists()]
    failed = set()
    if todo:  # CJK families come as 100+ unicode-range subsets per weight: fetch in parallel
        from concurrent.futures import ThreadPoolExecutor
        def get(u):
            try:
                files[u].write_bytes(_fetch(u))
            except Exception:
                failed.add(u)
        with ThreadPoolExecutor(max_workers=12) as ex:
            list(ex.map(get, todo))
    def repl(m):
        u = m.group(1)
        return m.group(0) if u in failed else f"url('{files[u].resolve().as_uri()}')"
    local = re.sub(r"url\((https://[^)]+)\)", repl, css)
    if failed:
        warn(f"font '{family}': {len(failed)} of {len(urls)} files failed to download", font=family)
    css_file.write_text(local, encoding="utf-8")
    return local


def resolve_fonts(lang: str, roles=None, overrides: dict | None = None):
    """Return (css_text, {role: 'font stack'}) for the language's script.

    overrides: {'display': 'Family Name', ...} to force brand fonts (must exist on Google Fonts).
    """
    roles = roles or ROLES
    sc = script_for(lang)
    table = FONTS.get(sc)
    if table is None:
        fam = SIMPLE.get(sc) or "Noto Sans"
        table = {r: [fam, "400;700"] for r in ROLES}
    latin = FONTS["latin"]
    css_parts, stacks, loaded = [], {}, {}
    for r in ROLES:
        fam, w = table.get(r, table["body"])
        if overrides and overrides.get(r):
            fam, w = overrides[r], "400;500;700;800;900"
        need = r in roles or r == "body"
        chain = []
        if need:
            if fam not in loaded:
                loaded[fam] = ensure_family(fam, w)
                if loaded[fam]:
                    css_parts.append(loaded[fam])
            if loaded.get(fam):
                chain.append(f"'{fam}'")
            # Latin companion for mixed-script text (numbers, brand names)
            if sc not in ("latin", "cyrillic", "greek", "vietnamese"):
                lf, lw = latin[r]
                if lf not in loaded:
                    loaded[lf] = ensure_family(lf, lw)
                    if loaded[lf]:
                        css_parts.append(loaded[lf])
                if loaded.get(lf):
                    chain.append(f"'{lf}'")
        chain += ["'Noto Sans'", "system-ui", GENERIC[r]]
        stacks[r] = ", ".join(chain)
    return "\n".join(css_parts), stacks


def all_scripts():
    """Every script key the engine knows, with one representative language code each."""
    rep = {}
    for lang, sc in LANG_SCRIPT.items():
        rep.setdefault(sc, lang)
    for sc in SIMPLE:
        rep.setdefault(sc, sc)
    rep.setdefault("latin", "en")
    return rep


def precache(scripts=None, roles=None, extra_families=None):
    """Download and cache every family used by the given scripts (default: all) for the given roles (default: all).

    Run at image build time so rendering works with no network (VT_OFFLINE=1). Returns {family: ok}.
    """
    rep = all_scripts()
    scripts = scripts or sorted(rep)
    roles = roles or ROLES
    results = {}
    for sc in scripts:
        lang = rep.get(sc, sc)
        css, stacks = resolve_fonts(lang, roles)
        for r in roles:
            fam = stacks[r].split(",")[0].strip("' ")
            results[fam] = bool(css) and f"'{fam}'" in stacks[r]
        log(f"fonts for {sc} ({lang}): " + ", ".join(sorted({stacks[r].split(',')[0].strip(chr(39) + ' ') for r in roles})))
    for fam in extra_families or []:
        results[fam] = bool(ensure_family(fam, "400;500;700;800;900"))
    missing = [f for f, ok in results.items() if not ok]
    log(f"font cache: {len(results) - len(missing)} families cached under {CACHE_DIR / 'fonts'}" + (f", missing: {missing}" if missing else ""))
    return results
