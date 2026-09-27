/*
 * Video Studio runtime (engine.js)
 * Deterministic, frame-accurate animation runtime used by every template.
 * The renderer calls window.__init(cfg) once, then window.__frame(t) for every frame.
 * Nothing here depends on wall-clock time, so the same t always produces the same pixels.
 */
(function () {
  'use strict';
  const VT = (window.VT = {});

  /* ------------------------------------------------------------------ math */
  const C = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
  const P = (t, s, d) => (d <= 0 ? (t >= s ? 1 : 0) : C((t - s) / d));
  const eo = (p) => 1 - Math.pow(1 - p, 3);
  const ei = (p) => p * p * p;
  const eio = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const eback = (p) => { const c1 = 1.7, c3 = c1 + 1; return 1 + c3 * Math.pow(p - 1, 3) + c1 * Math.pow(p - 1, 2); };
  const sp = (p) => (p <= 0 ? 0 : p >= 1 ? 1 : 1 - Math.exp(-7 * p) * Math.cos(11 * p));
  const L = (a, b, p) => a + (b - a) * p;
  const hash = (n) => { const x = Math.sin(n * 127.1 + 311.7) * 43758.5453; return x - Math.floor(x); };
  Object.assign(VT, { C, P, eo, ei, eio, eback, sp, L, hash });

  const RTL = new Set(['ar', 'fa', 'ur', 'he', 'iw', 'yi', 'ps', 'sd', 'ug', 'dv', 'ckb']);
  const NOSPACE = new Set(['zh', 'ja', 'th', 'lo', 'km', 'my', 'bo']);
  // Fractions of the frame kept clear of platform UI (top, right, bottom, left).
  const SAFE = {
    tiktok: [0.09, 0.13, 0.2, 0.04], reels: [0.09, 0.11, 0.2, 0.04], shorts: [0.08, 0.11, 0.18, 0.04],
    youtube: [0.05, 0.05, 0.06, 0.05], linkedin: [0.05, 0.05, 0.08, 0.05], x: [0.05, 0.05, 0.08, 0.05],
    none: [0.04, 0.04, 0.05, 0.04],
  };

  /* ------------------------------------------------------------- registry */
  let TPL = null;
  VT.template = (def) => { TPL = def; };
  const common = {}; // shared scene types available to every template
  VT.defineCommon = (type, def) => { common[type] = def; };

  const cues = [];
  VT.cue = (t, sfx, o = {}) => { if (t == null || !isFinite(t) || t < 0) return; cues.push(Object.assign({ t: +(+t).toFixed(3), sfx }, o)); };
  VT.typingCue = (a, b, gain = -24) => { if (b > a + 0.05) VT.cue(a, 'typing', { dur: +(b - a).toFixed(3), gain }); };

  /* ------------------------------------------------------- time references */
  // Any string "w:12", "we:12", "w:12+0.3" in the plan becomes the start/end time of word #12.
  function ref(v, words) {
    if (typeof v !== 'string') return v;
    const m = v.match(/^\s*(w|we):(\d+)\s*([+-]\s*\d*\.?\d+)?\s*$/);
    if (!m) return v;
    const w = words[+m[2]];
    if (!w) throw new Error('Plan references missing word index ' + v + ' (have ' + words.length + ' words)');
    return (m[1] === 'w' ? w.s : w.e) + (m[3] ? parseFloat(m[3].replace(/\s/g, '')) : 0);
  }
  function resolve(o, words) {
    if (Array.isArray(o)) return o.map((x) => resolve(x, words));
    if (o && typeof o === 'object') { const r = {}; for (const k in o) r[k] = resolve(o[k], words); return r; }
    return ref(o, words);
  }
  VT.time = (v, fallback) => (typeof v === 'number' && isFinite(v) ? v : fallback);

  /* ------------------------------------------------------------------- DOM */
  VT.el = (p, css = '', html = '', tag = 'div') => {
    const e = document.createElement(tag);
    // Anchor to the top-left unless the css positions the element itself. Without this, absolutely
    // positioned boxes in RTL pages would start from the right edge and VT.place() would be off.
    const hasX = /(^|;)\s*(left|right|inset[\w-]*)\s*:/.test(css), hasY = /(^|;)\s*(top|bottom|inset)\s*:/.test(css);
    e.style.cssText = 'position:absolute;' + (hasX ? '' : 'left:0;') + (hasY ? '' : 'top:0;') + css;
    if (html !== '' && html != null) e.innerHTML = html;
    p.appendChild(e);
    return e;
  };
  VT.tf = (e, o = {}) => {
    const x = o.x || 0, y = o.y || 0, s = o.s == null ? 1 : o.s, r = o.r || 0, op = o.o == null ? 1 : o.o;
    const sx = o.sx == null ? s : o.sx, sy = o.sy == null ? s : o.sy;
    e.style.transform = `translate(${x}px,${y}px) rotate(${r}deg) scale(${sx},${sy})`;
    e.style.opacity = op;
    e.style.visibility = op <= 0.001 ? 'hidden' : 'visible';
  };
  VT.esc = (s) => String(s == null ? '' : s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
  VT.font = (k) => `var(--f-${k || 'body'})`;

  // Create a text block inside box {x,y,w,h}; shrinks font until it fits.
  VT.text = (p, str, o = {}) => {
    const U = VT.U;
    const e = VT.el(p, o.css || '');
    if (o.html) e.innerHTML = str; else e.textContent = str == null ? '' : String(str);
    const st = e.style;
    st.fontFamily = VT.font(o.font || 'display');
    st.fontWeight = o.weight || 800;
    st.fontSize = (o.size || 8) * U + 'px';
    st.lineHeight = o.lh || 1.2;
    st.color = o.color || 'inherit';
    st.textAlign = o.align || 'center';
    st.direction = VT.dir;
    st.whiteSpace = o.nowrap ? 'nowrap' : 'normal';
    st.overflowWrap = 'break-word';
    if (o.ls) st.letterSpacing = o.ls;
    if (o.upper && !RTL.has(VT.base)) st.textTransform = 'uppercase';
    if (o.box) { st.left = o.box.x + 'px'; st.top = o.box.y + 'px'; st.width = o.box.w + 'px'; }
    if (o.w) st.width = o.w + 'px';
    if (o.fit !== false) VT.fit(e, o.w || (o.box && o.box.w), o.h || (o.box && o.box.h), o.min);
    if (o.box && o.valign) {
      const h = e.offsetHeight, bh = o.box.h;
      st.top = o.box.y + (o.valign === 'middle' ? (bh - h) / 2 : o.valign === 'bottom' ? bh - h : 0) + 'px';
    }
    return e;
  };
  // Shrink text until the element fits w x h (either may be null). Scales every inline font-size inside
  // the element together, so composite cards (title + body) keep their proportions.
  VT.fit = (e, w, h, min) => {
    const nodes = [e].concat(Array.from(e.querySelectorAll('*'))).filter((n) => n.style && /px$/.test(n.style.fontSize || ''));
    if (!nodes.length) { e.style.fontSize = getComputedStyle(e).fontSize; nodes.push(e); }
    const base = nodes.map((n) => parseFloat(n.style.fontSize));
    const ref = parseFloat(e.style.fontSize) || Math.max(...base);
    const lo = min ? (min * VT.U) / ref : 0.3;
    const over = () => !((w ? e.scrollWidth <= w + 1 : e.scrollWidth <= e.clientWidth + 1) && (!h || e.scrollHeight <= h + 1));
    let k = 1;
    for (let i = 0; i < 40 && over() && k > lo; i++) { k = Math.max(lo, k * 0.94); nodes.forEach((n, j) => { n.style.fontSize = base[j] * k + 'px'; }); }
    return ref * k;
  };
  // Center an element on (cx, cy) using its measured size, then apply motion.
  VT.place = (e, cx, cy, m = {}) => {
    const w = e.offsetWidth, h = e.offsetHeight;
    VT.tf(e, Object.assign({}, m, { x: cx - w / 2 + (m.x || 0), y: cy - h / 2 + (m.y || 0) }));
  };

  /* --------------------------------------------------------- text helpers */
  let segG = null;
  try { segG = new Intl.Segmenter(undefined, { granularity: 'grapheme' }); } catch (e) { segG = null; }
  VT.graphemes = (s) => (segG ? Array.from(segG.segment(String(s)), (x) => x.segment) : Array.from(String(s)));
  VT.type = (s, t, a, b) => { const g = VT.graphemes(s); const n = Math.round(C((t - a) / Math.max(0.001, b - a)) * g.length); return g.slice(0, n).join(''); };
  VT.num = (n, d = 0) => { try { return new Intl.NumberFormat(VT.numLocale, { minimumFractionDigits: d, maximumFractionDigits: d }).format(n); } catch (e) { return (+n).toFixed(d); } };
  VT.caret = (t, color) => `<span style="display:inline-block;width:.09em;height:1em;vertical-align:-.12em;margin-inline-start:.06em;background:${color || 'currentColor'};opacity:${Math.floor(t * 2.2) % 2 ? 1 : 0.15}"></span>`;
  VT.win = (t, a, b, tin = 0.35, tout = 0.3) => ({ i: eo(P(t, a, tin)), o: ei(P(t, b, tout)), on: t >= a - 1e-4 && t <= b + tout });
  VT.pop = (t, at, d = 0.45) => ({ s: L(0.35, 1, sp(P(t, at, d))), o: C((t - at) / 0.12) });
  VT.rise = (t, at, d = 0.45, dist = 6) => ({ y: (1 - eo(P(t, at, d))) * dist * VT.U, o: C((t - at) / (d * 0.5)) });
  VT.level = (t) => { const a = VT.cfg.levels; if (!a || !a.length) return 0; const i = Math.floor(t * (VT.cfg.levelsFps || 30)); return a[Math.max(0, Math.min(a.length - 1, i))] || 0; };
  VT.col = (k) => (VT.pal && VT.pal[k]) || k;
  VT.label = (s, key, fallback) => (s && s.labels && s.labels[key]) || (VT.cfg.labels && VT.cfg.labels[key]) || fallback;
  VT.wordIndexAt = (t) => { let i = -1; const w = VT.words; for (let k = 0; k < w.length; k++) { if (w[k].s <= t) i = k; else break; } return i; };

  /* ------------------------------------------------------- shared visuals */
  // Rounded card with a hard offset shadow.
  VT.card = (p, o = {}) => {
    const U = VT.U;
    return VT.el(p, `background:${o.bg || VT.col('paper')};color:${o.fg || VT.col('ink')};border-radius:${(o.r == null ? 3.6 : o.r) * U}px;` +
      (o.shadow === false ? '' : `box-shadow:0 ${(o.sh || 1.6) * U}px 0 ${o.shadow || VT.col('deep')};`) + (o.pad != null ? `padding:${o.pad * U}px;` : '') + (o.css || ''), o.html || '');
  };
  const ICON = {
    check: (c) => `<path d="M12 36 L28 52 L58 18" stroke="${c}" stroke-width="11" fill="none" stroke-linecap="round" stroke-linejoin="round"/>`,
    x: (c) => `<path d="M18 18 L52 52 M52 18 L18 52" stroke="${c}" stroke-width="11" stroke-linecap="round"/>`,
    star: (c) => `<path d="M35 6 L43 26 L64 27 L47 40 L53 61 L35 49 L17 61 L23 40 L6 27 L27 26Z" fill="${c}"/>`,
    person: (c) => `<circle cx="35" cy="24" r="12" fill="${c}"/><path d="M12 62 C12 42 58 42 58 62Z" fill="${c}"/>`,
    target: (c) => `<circle cx="35" cy="35" r="26" stroke="${c}" stroke-width="7" fill="none"/><circle cx="35" cy="35" r="12" stroke="${c}" stroke-width="7" fill="none"/>`,
    question: (c) => `<path d="M24 26 Q24 12 36 12 Q48 12 48 25 Q48 34 37 38 L37 45" stroke="${c}" stroke-width="8" fill="none" stroke-linecap="round"/><circle cx="37" cy="57" r="5" fill="${c}"/>`,
    clock: (c) => `<circle cx="35" cy="35" r="26" stroke="${c}" stroke-width="7" fill="none"/><path d="M35 20 L35 36 L46 42" stroke="${c}" stroke-width="7" fill="none" stroke-linecap="round"/>`,
    pin: (c) => `<path d="M35 64 C35 64 14 42 14 28 A21 21 0 0 1 56 28 C56 42 35 64 35 64Z" fill="${c}"/><circle cx="35" cy="28" r="8" fill="#fff"/>`,
    heart: (c) => `<path d="M35 60 C10 42 6 30 12 20 C18 10 30 12 35 22 C40 12 52 10 58 20 C64 30 60 42 35 60Z" fill="${c}"/>`,
    bolt: (c) => `<path d="M40 6 L14 40 L32 40 L28 64 L56 28 L38 28Z" fill="${c}"/>`,
    plus: (c) => `<path d="M35 14 L35 56 M14 35 L56 35" stroke="${c}" stroke-width="10" stroke-linecap="round"/>`,
    minus: (c) => `<path d="M14 35 L56 35" stroke="${c}" stroke-width="10" stroke-linecap="round"/>`,
    play: (c) => `<path d="M24 14 L58 35 L24 56Z" fill="${c}"/>`,
    fire: (c) => `<path d="M35 64 C18 64 12 50 16 38 C19 29 26 26 26 16 C34 20 40 28 38 38 C42 35 44 30 44 26 C52 32 58 42 54 52 C51 60 44 64 35 64Z" fill="${c}"/>`,
    cart: (c) => `<path d="M8 12 L18 12 L26 46 L56 46 L62 22 L22 22" stroke="${c}" stroke-width="6" fill="none" stroke-linejoin="round"/><circle cx="30" cy="56" r="5" fill="${c}"/><circle cx="52" cy="56" r="5" fill="${c}"/>`,
  };
  VT.icon = (name, color = 'currentColor', size = '100%') => `<svg viewBox="0 0 70 70" width="${size}" height="${size}">${(ICON[name] || ICON.check)(color)}</svg>`;
  VT.iconNames = Object.keys(ICON);
  // Circular badge with an icon (✓ / ✗ ...).
  VT.badge = (p, name, bg, fg, sizeU = 12) => {
    const U = VT.U, s = sizeU * U;
    return VT.el(p, `width:${s}px;height:${s}px;border-radius:50%;background:${bg};display:flex;align-items:center;justify-content:center;box-shadow:0 ${0.9 * U}px 0 ${VT.col('deep') || 'rgba(0,0,0,.35)'}`, VT.icon(name, fg, '58%'));
  };
  // Stamp label ("MYTH", "UNCLEAR"...).
  VT.stamp = (p, text, color, bg) => {
    const U = VT.U;
    return VT.el(p, `font-family:${VT.font('display')};font-weight:900;font-size:${6.2 * U}px;padding:${0.6 * U}px ${3 * U}px ${1.2 * U}px;border:${0.8 * U}px solid ${color};color:${color};background:${bg || 'transparent'};border-radius:${2 * U}px;white-space:nowrap`, VT.esc(text));
  };
  // Full-layer SVG in pixel coordinates.
  VT.svg = (p, css = '') => {
    const ns = 'http://www.w3.org/2000/svg';
    const s = document.createElementNS(ns, 'svg');
    s.setAttribute('width', VT.W); s.setAttribute('height', VT.H); s.setAttribute('viewBox', `0 0 ${VT.W} ${VT.H}`);
    s.style.cssText = 'position:absolute;left:0;top:0;overflow:visible;' + css;
    p.appendChild(s);
    s.add = (tag, attrs = {}) => { const e = document.createElementNS(ns, tag); for (const k in attrs) e.setAttribute(k, attrs[k]); s.appendChild(e); return e; };
    return s;
  };
  // Hand-drawn looking paths (deterministic wobble).
  VT.rough = {
    rect(x, y, w, h, seed = 1, j = 0.8) {
      const J = (k) => (hash(seed * 13 + k) - 0.5) * j * VT.U;
      return `M${x + J(1)} ${y + J(2)} Q${x + w / 2} ${y - J(3)} ${x + w + J(4)} ${y + J(5)} Q${x + w + J(6)} ${y + h / 2} ${x + w + J(7)} ${y + h + J(8)} Q${x + w / 2} ${y + h + J(9)} ${x + J(10)} ${y + h + J(11)} Q${x - J(12)} ${y + h / 2} ${x + J(13)} ${y - J(14) + 2}`;
    },
    line(x1, y1, x2, y2, seed = 1, j = 0.6) { const mx = (x1 + x2) / 2 + (hash(seed) - 0.5) * j * VT.U * 3, my = (y1 + y2) / 2 + (hash(seed + 7) - 0.5) * j * VT.U * 3; return `M${x1} ${y1} Q${mx} ${my} ${x2} ${y2}`; },
    arrow(x1, y1, x2, y2, seed = 1) {
      const a = Math.atan2(y2 - y1, x2 - x1), h = 3.2 * VT.U;
      return VT.rough.line(x1, y1, x2, y2, seed) + ` M${x2 - h * Math.cos(a - 0.5)} ${y2 - h * Math.sin(a - 0.5)} L${x2} ${y2} L${x2 - h * Math.cos(a + 0.5)} ${y2 - h * Math.sin(a + 0.5)}`;
    },
    ellipse(cx, cy, rx, ry, seed = 1) {
      let d = ''; const n = 28;
      for (let i = 0; i <= n + 3; i++) { const a = (i / n) * Math.PI * 2 - 0.4, k = 1 + (hash(seed + i) - 0.5) * 0.08; d += (i ? 'L' : 'M') + (cx + Math.cos(a) * rx * k).toFixed(1) + ' ' + (cy + Math.sin(a) * ry * k).toFixed(1) + ' '; }
      return d;
    },
    underline(x1, x2, y, seed = 1) { return `M${x1} ${y} Q${(x1 + x2) / 2} ${y + (hash(seed) - 0.3) * 1.5 * VT.U} ${x2} ${y - 0.4 * VT.U}`; },
  };
  // Animate a path drawing itself: call in render with progress 0..1.
  VT.drawPath = (path, p) => { if (!path._len) { path.setAttribute('pathLength', '1'); path.setAttribute('stroke-dasharray', '1'); path._len = 1; } path.setAttribute('stroke-dashoffset', String(1 - p)); };

  /* ----------------------------------------------------------------- media */
  const pending = new Set();
  // <img> fed from a still image or an extracted frame sequence (see vt.py media).
  VT.media = (p, name, css = '') => {
    const m = VT.cfg.media && VT.cfg.media[name];
    const img = VT.el(p, 'width:100%;height:100%;object-fit:cover;' + css, '', 'img');
    img.alt = '';
    img.update = () => {};
    if (!m) {
      // Placeholder so previews without footage still look intentional.
      img.style.background = `radial-gradient(circle at 50% 38%, rgba(255,255,255,.16), rgba(255,255,255,0) 55%), linear-gradient(160deg, ${VT.pal.deep || '#2a2a2a'}, ${VT.pal.ink || VT.pal.bg || '#111'})`;
      img.removeAttribute('src'); img.missing = true; return img;
    }
    if (m.fit) img.style.objectFit = m.fit;
    if (m.type === 'image') { img.src = m.src; pending.add(img); return img; }
    const fps = m.fps || VT.fps, off = m.offset || 0, count = m.count || 1, ext = m.ext || 'jpg';
    let last = -1;
    img.update = (t) => {
      const i = Math.max(0, Math.min(count - 1, Math.floor((t - off) * fps + 1e-6)));
      if (i !== last) { last = i; img.src = `${m.dir}/${String(i + 1).padStart(6, '0')}.${ext}`; pending.add(img); }
    };
    img.update(0);
    return img;
  };
  VT.hasMedia = (name) => !!(VT.cfg.media && VT.cfg.media[name]);

  /* ---------------------------------------------------------------- layout */
  function zones() {
    const W = VT.W, H = VT.H, U = VT.U;
    const pf = SAFE[VT.cfg.platform] || SAFE.none;
    const s = { t: pf[0] * H, r: pf[1] * W, b: pf[2] * H, l: pf[3] * W };
    if (VT.orient !== 'portrait') { s.r = Math.min(s.r, 0.06 * W); s.b = Math.min(s.b, 0.1 * H); s.t = Math.min(s.t, 0.07 * H); }
    // RTL right-rail stays on the right: platforms don't mirror their UI.
    const area = { x: s.l, y: s.t, w: W - s.l - s.r, h: H - s.t - s.b };
    const zc = (VT.theme && VT.theme.zones) || {};
    const capH = (zc.cap || (VT.orient === 'portrait' ? 0.13 : VT.orient === 'square' ? 0.16 : 0.18)) * H;
    const headH = (zc.head ? (VT.orient === 'portrait' ? zc.head : zc.head * 1.25) : (VT.orient === 'portrait' ? 0.15 : 0.2)) * H;
    const capOn = VT.capOn;
    const head = { x: area.x, y: area.y, w: area.w, h: headH };
    const cap = { x: area.x, y: area.y + area.h - capH, w: area.w, h: capH };
    const bodyBottom = capOn ? cap.y : area.y + area.h;
    const body = { x: area.x, y: head.y + head.h, w: area.w, h: Math.max(10 * U, bodyBottom - head.y - head.h) };
    const full = { x: area.x, y: area.y, w: area.w, h: bodyBottom - area.y };
    const colW = Math.min(area.w, VT.orient === 'landscape' ? 0.9 * H : area.w);
    const column = { x: area.x + (area.w - colW) / 2, y: full.y, w: colW, h: full.h };
    return { safe: s, area, head, body, cap, full, column };
  }
  // Split a box into n rows (with gap in U), useful for lists and stacks.
  VT.rows = (box, n, gapU = 2) => { const g = gapU * VT.U, h = (box.h - g * (n - 1)) / n; return Array.from({ length: n }, (_, i) => ({ x: box.x, y: box.y + i * (h + g), w: box.w, h })); };
  VT.cols = (box, n, gapU = 2) => { const g = gapU * VT.U, w = (box.w - g * (n - 1)) / n; return Array.from({ length: n }, (_, i) => ({ x: box.x + i * (w + g), y: box.y, w, h: box.h })); };
  VT.inset = (b, u) => ({ x: b.x + u * VT.U, y: b.y + u * VT.U, w: b.w - 2 * u * VT.U, h: b.h - 2 * u * VT.U });
  VT.center = (b) => ({ x: b.x + b.w / 2, y: b.y + b.h / 2 });
  VT.clampW = (b, maxU) => { const w = Math.min(b.w, maxU * VT.U); return { x: b.x + (b.w - w) / 2, y: b.y, w, h: b.h }; };
  VT.sub = (b, fy, fh) => ({ x: b.x, y: b.y + b.h * fy, w: b.w, h: b.h * fh });

  /* -------------------------------------------------------------- captions */
  function buildCaptions(root) {
    const th = (TPL.theme && TPL.theme.captions) || {};
    const o = Object.assign({ enabled: true, style: 'pill', position: 'auto', maxWords: 3, size: 6.4, font: 'display', weight: 800,
      color: '#FFFFFF', hl: '#FFE04A', hlText: '#111111', shadow: 'rgba(0,0,0,.45)', box: 'rgba(0,0,0,.72)', gap: 0.5, upper: false }, th, VT.cfg.captions || {});
    VT.capStyle = o;
    const words = VT.words;
    if (!o.enabled || o.style === 'none' || !words.length) return () => {};
    // chunking
    let chunks = [];
    if (Array.isArray(o.chunks) && o.chunks.length) {
      let k = 0;
      chunks = o.chunks.map((c) => { if (Array.isArray(c)) return c.map((i) => words[i]).filter(Boolean); const r = words.slice(k, k + c); k += c; return r; });
    } else {
      let cur = [];
      const maxW = o.style === 'pop' ? 1 : o.maxWords;
      const maxChars = o.maxChars || (VT.joiner ? 22 : 12);
      words.forEach((w, i) => {
        const prev = words[i - 1];
        const len = cur.reduce((a, x) => a + String(x.w).length, 0) + String(w.w).length;
        if (cur.length && (cur.length >= maxW || len > maxChars || (prev && w.s - prev.e > o.gap))) { chunks.push(cur); cur = []; }
        cur.push(w);
        if (/[.!?؟。！？،,;]$/.test(w.w) && o.style !== 'pop') { chunks.push(cur); cur = []; }
      });
      if (cur.length) chunks.push(cur);
    }
    chunks = chunks.filter((c) => c.length);
    const z = VT.Z.cap, U = VT.U;
    const box = VT.el(root, `left:${z.x + z.w * 0.03}px;width:${z.w * 0.94}px;display:flex;flex-wrap:wrap;justify-content:center;align-items:center;gap:${U * 0.8}px ${U * 1.4}px;direction:${VT.dir};text-align:center;z-index:50`);
    const pos = o.position === 'auto' ? 'bottom' : o.position;
    const place = () => {
      const h = box.offsetHeight;
      let y = pos === 'middle' ? VT.H * 0.5 - h / 2 : pos === 'top' ? VT.Z.area.y + VT.Z.area.h * 0.02 : z.y + (z.h - h) / 2;
      box.style.top = y + 'px';
    };
    const fs = (o.style === 'pop' ? o.size * 1.45 : o.size) * U;
    let lastKey = '';
    return (t) => {
      let ci = -1;
      for (let i = 0; i < chunks.length; i++) if (t >= chunks[i][0].s - 0.04) ci = i;
      const ch = chunks[ci];
      const nextS = ci + 1 < chunks.length ? chunks[ci + 1][0].s : Infinity;
      if (!ch || (t > ch[ch.length - 1].e + 0.4 && t < nextS - 0.04)) { if (lastKey !== '') { box.innerHTML = ''; lastKey = ''; } return; }
      let ai = -1; ch.forEach((w, k) => { if (w.s <= t + 0.03) ai = k; });
      const parts = ch.map((w, k) => {
        const on = k === ai, said = k <= ai;
        const pop = on ? L(1.16, 1, eo(P(t, w.s - 0.03, 0.18))) : 1;
        let css = `display:inline-block;font-family:${VT.font(o.font)};font-weight:${o.weight};font-size:${fs}px;line-height:1.25;padding:${U * 0.3}px ${U * 1.4}px ${U * 0.9}px;border-radius:${U * 1.8}px;`;
        if (o.upper && !RTL.has(VT.base)) css += 'text-transform:uppercase;';
        if (o.style === 'pill') css += on ? `background:${o.hl};color:${o.hlText};transform:scale(${pop});` : `color:${o.color};text-shadow:0 ${U * 0.5}px 0 ${o.shadow};`;
        else if (o.style === 'karaoke') css += `color:${said ? o.hl : o.color};text-shadow:0 ${U * 0.5}px 0 ${o.shadow};transform:scale(${pop});padding-inline:${U * 0.4}px;`;
        else if (o.style === 'pop') css += `background:${o.hl};color:${o.hlText};transform:scale(${L(1.35, 1, eo(P(t, w.s - 0.03, 0.2)))}) rotate(${(k % 2 ? 2 : -2)}deg);`;
        else if (o.style === 'line') css += `color:${o.color};padding-inline:${U * 0.25}px;`;
        else if (o.style === 'boxed') css += `color:${on ? o.hl : o.color};padding-inline:${U * 0.4}px;`;
        if (o.style === 'pop' && !on) return '';
        return `<span style="${css}">${VT.esc(w.w)}</span>`;
      }).filter(Boolean);
      const key = ci + ':' + ai;
      if (key !== lastKey) {
        let inner = parts.join(VT.joiner ? '' : '');
        if (o.style === 'line' || o.style === 'boxed') inner = `<span style="display:inline-flex;flex-wrap:wrap;justify-content:center;background:${o.box};border-radius:${U * 1.6}px;padding:${U * 0.6}px ${U * 1.8}px ${U * 1.1}px;gap:0 ${VT.joiner ? U * 0.9 : 0}px">${parts.join('')}</span>`;
        box.innerHTML = inner; lastKey = key; place();
      } else if (o.style === 'pill' || o.style === 'karaoke' || o.style === 'pop') {
        box.innerHTML = o.style === 'line' ? box.innerHTML : parts.join(''); place();
      }
      const cp = P(t, ch[0].s - 0.05, 0.16);
      box.style.transform = `translateY(${(1 - eo(cp)) * U * 1.5}px)`;
      box.style.opacity = C(cp * 2);
    };
  }

  /* ----------------------------------------------------------------- init */
  let bgRender = null, overlayRenders = [], capRender = null, sceneList = [];
  window.__init = async (cfg) => {
    if (!TPL) throw new Error('No template registered (template.js must call VT.template({...}))');
    VT.cfg = cfg;
    VT.W = cfg.width; VT.H = cfg.height; VT.fps = cfg.fps || 30; VT.U = Math.min(VT.W, VT.H) / 100;
    VT.lang = cfg.lang || 'en'; VT.base = VT.lang.split('-')[0].toLowerCase();
    VT.dir = cfg.dir || (RTL.has(VT.base) ? 'rtl' : 'ltr');
    VT.sign = VT.dir === 'rtl' ? -1 : 1; // multiply horizontal "forward" motion by this
    VT.joiner = NOSPACE.has(VT.base) ? '' : ' ';
    VT.numLocale = VT.lang + (cfg.numerals === 'latin' ? '-u-nu-latn' : cfg.numerals === 'native' && VT.base === 'ar' ? '-u-nu-arab' : '');
    const r = VT.W / VT.H; VT.orient = r < 0.8 ? 'portrait' : r > 1.25 ? 'landscape' : 'square';
    VT.cuts = (cfg.cuts || []).map(Number).filter((x) => isFinite(x)).sort((a, b) => a - b);
    VT.words = (cfg.words || []).map((w) => ({ w: String(w.w), s: +w.s, e: +(w.e == null ? w.s + 0.3 : w.e) }));
    VT.plan = resolve({ scenes: cfg.scenes || [], data: cfg.data || {} }, VT.words);
    const theme = TPL.theme || {};
    VT.theme = theme;
    VT.pal = Object.assign({}, theme.palette || {}, cfg.palette || {});
    VT.capOn = !!((cfg.captions ? cfg.captions.enabled !== false : true) && VT.words.length && (cfg.captions || {}).style !== 'none' && (theme.captions || {}).enabled !== false);
    const lastWord = VT.words.length ? VT.words[VT.words.length - 1].e : 0;
    const scenes = VT.plan.scenes.slice().sort((a, b) => VT.time(a.start, 0) - VT.time(b.start, 0));
    const lastScene = scenes.length ? Math.max(...scenes.map((s) => VT.time(s.end, VT.time(s.start, 0) + 2))) : 0;
    VT.dur = +(cfg.duration || Math.max(lastWord + 1.2, lastScene, 2)).toFixed(3);
    VT.Z = zones();

    document.documentElement.lang = VT.lang; document.documentElement.dir = VT.dir;
    const stage = document.getElementById('stage');
    stage.style.width = VT.W + 'px'; stage.style.height = VT.H + 'px'; stage.style.direction = VT.dir;
    const root = document.documentElement.style;
    for (const k in VT.pal) root.setProperty('--c-' + k, VT.pal[k]);
    const f = cfg.fonts || {};
    ['display', 'body', 'serif', 'mono', 'hand', 'rounded', 'condensed'].forEach((k) => root.setProperty('--f-' + k, f[k] || f.body || 'system-ui, sans-serif'));
    stage.style.background = VT.pal.bg || '#111';
    stage.style.color = VT.pal.text || '#fff';
    stage.style.fontFamily = VT.font('body');
    // Fonts load lazily in browsers; force every face to load before measuring text.
    if (document.fonts) {
      try { await Promise.all(Array.from(document.fonts).map((f) => f.load().catch(() => null))); } catch (e) { /* ignore */ }
      await document.fonts.ready;
    }

    const bgLayer = VT.el(stage, 'inset:0;overflow:hidden');
    bgRender = TPL.background ? TPL.background(bgLayer) : null;

    // scenes
    sceneList = [];
    const tin = theme.tin == null ? 0.35 : theme.tin, tout = theme.tout == null ? 0.3 : theme.tout;
    scenes.forEach((s, i) => {
      const a = VT.time(s.start, 0);
      const next = scenes[i + 1];
      const b = VT.time(s.end, next ? VT.time(next.start, VT.dur) : VT.dur);
      s.start = a; s.end = b; s.index = i;
      const def = (TPL.scenes || {})[s.type] || common[s.type];
      if (!def) throw new Error(`Scene type "${s.type}" is not defined by this template. Available: ${Object.keys(TPL.scenes || {}).concat(Object.keys(common)).join(', ')}`);
      // Build while laid out (but invisible) so text fitting and measurements work.
      const layer = VT.el(stage, 'inset:0;overflow:hidden;visibility:hidden');
      const out = def.build(s, layer, { index: i, scenes });
      layer.style.display = 'none'; layer.style.visibility = '';
      const render = typeof out === 'function' ? out : out && out.render;
      const trans = s.transition || (out && out.transition) || def.transition || theme.transition || 'slide';
      sceneList.push({ s, a, b, layer, render, trans, last: i === scenes.length - 1 });
      if (i > 0 && trans !== 'cut' && theme.sfx && theme.sfx.transition !== null) {
        VT.cue(a - 0.22, (theme.sfx && theme.sfx.transition) || 'whoosh', { gain: (theme.sfx && theme.sfx.transitionGain) || -16, pan: hash(i) * 0.8 - 0.4 });
      }
    });
    VT.sceneList = sceneList; VT.tin = tin; VT.tout = tout;

    overlayRenders = (TPL.overlays || []).map((fn) => { const layer = VT.el(stage, 'inset:0;pointer-events:none'); return fn(layer) || (() => {}); });
    const capLayer = VT.el(stage, 'inset:0;pointer-events:none;z-index:40');
    capRender = buildCaptions(capLayer);
    if (TPL.afterInit) TPL.afterInit();
    const warn = [];
    sceneList.forEach((x) => { if (x.b - x.a < 0.6) warn.push(`Scene ${x.s.index} (${x.s.type}) is only ${(x.b - x.a).toFixed(2)}s long`); });
    cues.sort((p, q) => p.t - q.t);
    return { duration: VT.dur, width: VT.W, height: VT.H, fps: VT.fps, dir: VT.dir, orient: VT.orient, cues, warnings: warn, scenes: sceneList.map((x) => ({ type: x.s.type, start: x.a, end: x.b })) };
  };

  function applyTransition(x, t) {
    const { a, b, layer, trans } = x;
    const tin = VT.tin, tout = x.last ? 0 : VT.tout;
    const visible = t >= a - 1e-4 && (x.last || t <= b + tout);
    if (!visible) { layer.style.display = 'none'; return false; }
    layer.style.display = 'block';
    const pi = a <= 0.02 ? 1 : eo(P(t, a, tin));
    const po = x.last ? 0 : ei(P(t, b, tout));
    const U = VT.U;
    let tr = '', op = 1;
    if (trans === 'cut') { op = t < b || x.last ? 1 : 0; }
    else if (trans === 'fade') { op = Math.min(C((t - a) / tin), 1 - po); if (a <= 0.02) op = 1 - po; }
    else if (trans === 'zoom') { tr = `scale(${L(1.1, 1, pi) * (1 + po * 0.08)})`; op = Math.min(pi * 1.3, 1 - po); }
    else if (trans === 'push') { const d = VT.W * 0.3 * VT.sign; tr = `translateX(${(1 - pi) * d - po * d}px)`; op = Math.min(C(pi * 1.4), 1 - po); }
    else { tr = `translateY(${(1 - pi) * 7 * U - po * 12 * U}px) scale(${1 - po * 0.05})`; op = Math.min(C(pi * 1.4), 1 - po); }
    layer.style.transform = tr; layer.style.opacity = op;
    return true;
  }

  window.__frame = async (t) => {
    if (bgRender) bgRender(t);
    for (const x of sceneList) if (applyTransition(x, t) && x.render) x.render(t, t - x.a, x.s);
    for (const r of overlayRenders) r(t);
    if (capRender) capRender(t);
    if (pending.size) { const list = Array.from(pending); pending.clear(); await Promise.all(list.map((i) => (i.decode ? i.decode().catch(() => {}) : 0))); }
    return true;
  };

  /* ---------------------------------------------------- common scene types */
  // Big statement. {text, sub?, at?}
  VT.defineCommon('text', {
    build(s, layer) {
      const z = VT.Z.full, U = VT.U;
      const box = VT.clampW(VT.inset(z, 3), 92);
      const t1 = VT.text(layer, s.text || '', { box: { x: box.x, y: box.y, w: box.w, h: box.h * 0.6 }, size: s.size || 11, weight: 900, color: VT.col('text'), fit: true });
      const t2 = s.sub ? VT.text(layer, s.sub, { w: box.w, size: 5.2, weight: 600, font: 'body', color: VT.col('muted') }) : null;
      const at = VT.time(s.at, s.start);
      if (s.cue !== false) VT.cue(at, s.sfx || 'pop', { gain: -16 });
      return (t) => {
        const cy = z.y + z.h * 0.45;
        const k = VT.pop(t, at, 0.5);
        VT.place(t1, box.x + box.w / 2, cy - (t2 ? 3 * U : 0), { s: k.s, o: k.o });
        if (t2) { const r = VT.rise(t, at + 0.25, 0.4, 3); VT.place(t2, box.x + box.w / 2, cy + t1.offsetHeight / 2 + 4 * U, { y: r.y, o: r.o }); }
      };
    },
  });
  // Full-frame image or video with optional caption line. {media, text?, kenburns?}
  VT.defineCommon('media', {
    build(s, layer) {
      const img = VT.media(layer, s.media || 'broll', 'left:0;top:0');
      const lab = s.text ? VT.text(layer, s.text, { w: VT.Z.area.w * 0.9, size: 6, weight: 800, color: '#fff', css: `background:rgba(0,0,0,.55);padding:${VT.U}px ${2 * VT.U}px;border-radius:${1.5 * VT.U}px` }) : null;
      return (t, lt) => {
        img.update(t - s.start + (s.mediaOffset || 0));
        const k = s.kenburns === false ? 1 : 1.04 + lt * 0.012;
        img.style.transform = `scale(${k})`;
        if (lab) VT.place(lab, VT.W / 2, VT.Z.body.y + VT.Z.body.h * 0.85, { o: P(lt, 0.2, 0.3) });
      };
    },
  });
})();
