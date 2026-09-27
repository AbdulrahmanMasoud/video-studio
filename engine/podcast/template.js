/* podcast - clip from a conversation: split speaker panels that light up on the active voice,
   live audio waveform, ON AIR badge, pull quotes and a solo view. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  function initials(n) { return String(n || '?').split(/\s+/).map((x) => VT.graphemes(x)[0] || '').join('').slice(0, 2).toUpperCase(); }
  function activeAt(s, t) {
    const turns = s.turns || [];
    for (const tr of turns) { const a = VT.time(tr.start, 0), b = VT.time(tr.end, 1e9); if (t >= a && t < b) return tr.who; }
    return s.speaker != null ? s.speaker : turns.length ? -1 : 0;
  }
  // Panel with footage (or an avatar), name tag and a level meter.
  function panel(layer, sp0, box, i) {
    const U = VT.U;
    const e = VT.el(layer, `left:${box.x}px;top:${box.y}px;width:${box.w}px;height:${box.h}px;border-radius:${3 * U}px;overflow:hidden;background:linear-gradient(160deg,${i ? '#2B2238' : '#22303A'},#0E0C12)`);
    let img = null;
    if (sp0.media && VT.hasMedia(sp0.media)) img = VT.media(e, sp0.media, 'left:0;top:0');
    else {
      const d = Math.min(box.w, box.h) * 0.46;
      VT.el(e, `left:${box.w / 2 - d / 2}px;top:${box.h * 0.44 - d / 2}px;width:${d}px;height:${d}px;border-radius:50%;background:${i ? '#7C5CFF' : '#FF7A59'};display:flex;align-items:center;justify-content:center;font-family:${VT.font('display')};font-weight:900;font-size:${d * 0.36}px;color:#fff`, VT.esc(initials(sp0.name)));
    }
    const ring = VT.el(e, `inset:0;border-radius:${3 * U}px;border:${0.7 * U}px solid ${VT.col('accent')};pointer-events:none`);
    const tag = VT.el(e, `left:${2 * U}px;bottom:${2 * U}px;display:flex;align-items:center;gap:${1.4 * U}px;background:rgba(0,0,0,.6);padding:${0.8 * U}px ${2 * U}px ${1.1 * U}px;border-radius:${1.6 * U}px;direction:${VT.dir}`,
      `<div class="bars" style="display:flex;align-items:center;gap:${0.35 * U}px;height:${3.4 * U}px">${Array.from({ length: 5 }, () => `<i style="display:block;width:${0.6 * U}px;height:30%;border-radius:${0.3 * U}px;background:${VT.col('accent')}"></i>`).join('')}</div>` +
      `<div><div style="font-family:${VT.font('display')};font-weight:800;font-size:${3.6 * U}px;color:#fff;white-space:nowrap">${VT.esc(sp0.name || '')}</div>${sp0.role ? `<div style="font-family:${VT.font('body')};font-size:${2.6 * U}px;color:rgba(255,255,255,.7);white-space:nowrap">${VT.esc(sp0.role)}</div>` : ''}</div>`);
    if (VT.dir === 'rtl') { tag.style.left = ''; tag.style.right = 2 * U + 'px'; }
    return { e, img, ring, bars: Array.from(tag.querySelectorAll('i')) };
  }

  VT.template({
    theme: {
      palette: { bg: '#0E0C12', deep: '#000000', ink: '#0E0C12', paper: '#F7F3EE', accent: '#FF4F5E', alt: '#7C5CFF', text: '#FFFFFF', muted: 'rgba(255,255,255,.7)' },
      captions: { style: 'boxed', color: '#FFFFFF', hl: '#FF4F5E', box: 'rgba(14,12,18,.86)', maxWords: 5 },
      transition: 'fade', sfx: { transition: null }, zones: { head: 0.1, cap: 0.14 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 0%, #2A1F33, #0E0C12 70%)`);
      return null;
    },
    scenes: {
      // {speakers:[{name, role, media}], turns:[{who, start, end}], speaker}
      split: {
        transition: 'cut',
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, sps = (s.speakers || VT.cfg.data.speakers || [{ name: 'Host' }, { name: 'Guest' }]).slice(0, 3);
          const land = VT.orient === 'landscape';
          const area = VT.inset({ x: z.x, y: z.y + 7 * U, w: z.w, h: z.h - 7 * U }, 1);
          const boxes = land ? VT.cols(area, sps.length, 2) : VT.rows(area, sps.length, 2);
          const ps = sps.map((x, i) => panel(layer, x, boxes[i], i));
          let last = -2;
          const turns = (s.turns || []).map((tr) => VT.time(tr.start, 0)).sort((a, b) => a - b);
          turns.slice(1).forEach((a) => VT.cue(a, 'click', { gain: -26 }));
          return (t) => {
            const who = activeAt(s, t), lv = VT.level(t);
            ps.forEach((p, i) => {
              const on = who === i || who === -1;
              if (p.img) { p.img.update(t); p.img.style.transform = `scale(${on ? 1.06 : 1.02})`; }
              p.ring.style.opacity = on && who !== -1 ? 1 : 0;
              p.e.style.filter = on ? 'none' : 'brightness(.55) saturate(.7)';
              p.bars.forEach((b, k) => { b.style.height = (on ? 25 + 75 * C(lv * (0.6 + 0.8 * VT.hash(k + Math.floor(t * 12)))) : 20) + '%'; });
            });
            last = who;
          };
        },
      },
      // {who, media} single speaker full frame
      solo: {
        transition: 'cut',
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, sps = s.speakers || VT.cfg.data.speakers || [{ name: 'Host' }];
          const who = s.who || 0;
          const box = VT.inset({ x: z.x, y: z.y + 7 * U, w: z.w, h: z.h - 7 * U }, 1);
          const p = panel(layer, Object.assign({}, sps[who] || {}, s.media ? { media: s.media } : {}), box, who);
          return (t, lt) => {
            const lv = VT.level(t);
            if (p.img) { p.img.update(t); p.img.style.transform = `scale(${1.04 + lt * 0.006})`; }
            p.ring.style.opacity = 0;
            p.bars.forEach((b, k) => { b.style.height = 25 + 75 * C(lv * (0.6 + 0.8 * VT.hash(k + Math.floor(t * 12)))) + '%'; });
          };
        },
      },
      // Pull quote. {text, who, at}
      quote: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(z, 94);
          const k = VT.el(layer, `width:${col.w}px;padding:${6 * U}px ${5 * U}px;border-radius:${3 * U}px;background:${VT.col('paper')};color:${VT.col('ink')};box-shadow:0 ${2 * U}px ${6 * U}px rgba(0,0,0,.5)`);
          k.innerHTML = `<div style="font-family:Georgia,serif;font-size:${16 * U}px;line-height:.6;color:${VT.col('accent')};height:${7 * U}px">“</div><div class="q" style="font-family:${VT.font('display')};font-weight:800;font-size:${6.6 * U}px;line-height:1.25"></div><div class="w" style="margin-top:${2.4 * U}px;font-family:${VT.font('body')};font-weight:700;font-size:${3.8 * U}px;color:${VT.col('accent')}"></div>`;
          k.querySelector('.q').textContent = s.text || ''; k.querySelector('.w').textContent = s.who ? '— ' + s.who : '';
          VT.fit(k, col.w, z.h * 0.85, 3);
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -14 });
          return (t) => { const p = P(t, at, 0.55); VT.place(k, VT.W / 2, z.y + z.h * 0.5, { y: (1 - eo(p)) * 8 * U, r: L(-3, -1, eo(p)), o: C(p * 3) }); };
        },
      },
    },
    overlays: [
      function onAir(layer) {
        const U = VT.U, z = VT.Z.full, d = VT.cfg.data || {};
        const e = VT.el(layer, `display:flex;align-items:center;gap:${1.6 * U}px;direction:${VT.dir}`,
          `<div style="display:flex;align-items:center;gap:${1 * U}px;background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${3 * U}px;padding:${0.6 * U}px ${1.8 * U}px ${0.9 * U}px;border-radius:${1 * U}px;letter-spacing:.08em"><i class="dot" style="display:block;width:${1.4 * U}px;height:${1.4 * U}px;border-radius:50%;background:#fff"></i>${VT.esc(d.badge || VT.label(null, 'onair', 'ON AIR'))}</div>` +
          (d.show ? `<div style="font-family:${VT.font('display')};font-weight:800;font-size:${3.6 * U}px;color:#fff;white-space:nowrap">${VT.esc(d.show)}</div>` : ''));
        const dot = e.querySelector('.dot');
        return (t) => { VT.place(e, VT.W / 2, z.y + 3.5 * U, { o: C(t / 0.4) }); dot.style.opacity = Math.floor(t * 1.4) % 2 ? 0.35 : 1; };
      },
    ],
  });
})();
