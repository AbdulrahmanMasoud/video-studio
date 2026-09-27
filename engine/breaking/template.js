/* breaking - news bulletin: red BREAKING banner, headline bar, media window, key points, LIVE badge, clock and ticker. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  VT.template({
    theme: {
      palette: { bg: '#0B1E3F', deep: '#06112A', ink: '#0B1E3F', paper: '#FFFFFF', accent: '#E0182D', alt: '#FFC400', text: '#FFFFFF', muted: 'rgba(255,255,255,.7)', bar: '#12305F' },
      captions: { style: 'boxed', color: '#FFFFFF', hl: '#FFC400', box: 'rgba(6,17,42,.9)', maxWords: 5 },
      transition: 'push', sfx: { transition: 'swoosh', transitionGain: -18 }, zones: { head: 0.14, cap: 0.13 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:linear-gradient(160deg,#143A73,#081733 70%)`);
      const g = VT.el(layer, `inset:-10%;background:repeating-linear-gradient(90deg, rgba(255,255,255,.035) 0 1px, transparent 1px ${8 * U}px), repeating-linear-gradient(0deg, rgba(255,255,255,.035) 0 1px, transparent 1px ${8 * U}px)`);
      const globe = VT.el(layer, `width:${110 * U}px;height:${110 * U}px;border-radius:50%;border:${0.3 * U}px solid rgba(255,255,255,.08);background:repeating-radial-gradient(circle, transparent 0 ${9 * U}px, rgba(255,255,255,.04) ${9 * U}px ${9.3 * U}px)`);
      return (t) => { g.style.transform = `translateX(${-(t * 2 * U) % (8 * U)}px)`; VT.place(globe, VT.W * 0.8, VT.H * 0.3, { r: t * 4 }); };
    },
    scenes: {
      // {label, title, sub, media, at}
      headline: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, land = VT.orient === 'landscape';
          const hasM = !!(s.media && VT.hasMedia(s.media));
          const tick = (VT.cfg.data && VT.cfg.data.ticker && VT.cfg.data.ticker.length) ? 8 * U : 0, avail = z.h - tick;
          const mh = land ? avail * 0.5 : avail * 0.36, mw = land ? mh * 16 / 9 : z.w;
          const win = VT.el(layer, `width:${mw}px;height:${mh}px;overflow:hidden;border-radius:${1.4 * U}px;background:linear-gradient(135deg,#1C4B8F,#0A2250);box-shadow:0 ${2 * U}px ${6 * U}px rgba(0,0,0,.4)`);
          const img = hasM ? VT.media(win, s.media, 'left:0;top:0') : null;
          if (!hasM) VT.el(win, `inset:0;display:flex;align-items:center;justify-content:center`, `<div style="width:30%;height:50%;opacity:.35">${VT.icon(s.icon || 'bolt', '#fff')}</div>`);
          const lab = VT.el(layer, `background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${5.4 * U}px;letter-spacing:.08em;padding:${1 * U}px ${3.4 * U}px ${1.4 * U}px;white-space:nowrap;transform-origin:0 50%`, VT.esc(s.label || VT.label(s, 'breaking', 'BREAKING NEWS')));
          const bw = land ? mw : z.w;
          const bar = VT.el(layer, `width:${bw}px;background:#fff;color:${VT.col('ink')};padding:${2 * U}px ${3 * U}px ${2.4 * U}px;font-family:${VT.font('display')};font-weight:900;font-size:${6.6 * U}px;line-height:1.15;border-inline-start:${1.4 * U}px solid ${VT.col('accent')}`);
          bar.textContent = s.title || ''; VT.fit(bar, bw, avail * 0.3, 3);
          const sub = s.sub ? VT.el(layer, `width:${bw}px;background:${VT.col('bar')};color:#fff;padding:${1.2 * U}px ${3 * U}px ${1.5 * U}px;font-family:${VT.font('body')};font-weight:600;font-size:${3.8 * U}px`, VT.esc(s.sub)) : null;
          if (sub) VT.fit(sub, bw, 14 * U, 2.4);
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at - 0.05, 'sting', { gain: -10 }); VT.cue(at + 0.35, 'whoosh', { gain: -18 }); VT.cue(at + 0.8, 'beep-long', { gain: -24 });
          return (t) => {
            const total = mh + 5 * U + lab.offsetHeight + bar.offsetHeight + (sub ? sub.offsetHeight : 0);
            let y = z.y + Math.max(0, (avail - total) / 2);
            const wp = P(t, at + 0.2, 0.6);
            if (img) { img.update(t - s.start); img.style.transform = `scale(${1.04 + (t - s.start) * 0.008})`; }
            VT.place(win, VT.W / 2, y + mh / 2, { s: L(1.06, 1, eo(wp)), o: C(wp * 2) }); y += mh + 5 * U;
            const x0 = VT.W / 2 - bw / 2;
            const lp = P(t, at, 0.35);
            const lx = VT.dir === 'rtl' ? x0 + bw - lab.offsetWidth / 2 : x0 + lab.offsetWidth / 2;
            VT.place(lab, lx, y + lab.offsetHeight / 2, { sx: eo(lp), o: C(lp * 4) });
            lab.style.transformOrigin = VT.dir === 'rtl' ? '100% 50%' : '0 50%';
            lab.style.background = Math.floor((t - at) * 2) % 2 && t - at < 3 ? '#B30F20' : VT.col('accent');
            y += lab.offsetHeight;
            const bp = P(t, at + 0.35, 0.45);
            VT.place(bar, VT.W / 2, y + bar.offsetHeight / 2, { x: (1 - eo(bp)) * -20 * U * VT.sign, o: C(bp * 3) }); y += bar.offsetHeight;
            if (sub) { const sp2 = P(t, at + 0.7, 0.4); VT.place(sub, VT.W / 2, y + sub.offsetHeight / 2, { o: C(sp2 * 3) }); }
          };
        },
      },
      // {n, text, at}
      point: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z.full;
          const n = s.n != null ? s.n : ctx.scenes.filter((x) => x.type === 'point').indexOf(s) + 1;
          const w = Math.min(z.w, 110 * U);
          const card = VT.el(layer, `width:${w}px;display:flex;align-items:stretch;background:#fff;color:${VT.col('ink')};border-radius:${1.2 * U}px;overflow:hidden;box-shadow:0 ${2 * U}px ${6 * U}px rgba(0,0,0,.35);direction:${VT.dir}`,
            `<div style="flex:none;width:${16 * U}px;background:${VT.col('accent')};color:#fff;display:flex;align-items:center;justify-content:center;font-family:${VT.font('display')};font-weight:900;font-size:${9 * U}px">${VT.esc(typeof n === 'number' ? VT.num(n) : n)}</div><div class="t" style="flex:1;min-width:0;padding:${3 * U}px ${3.4 * U}px;font-family:${VT.font('display')};font-weight:800;font-size:${6 * U}px;line-height:1.2"></div>`);
          const tx = card.querySelector('.t'); tx.textContent = s.text || ''; VT.fit(tx, null, z.h * 0.6, 3);
          const k = s.kicker ? VT.el(layer, `background:${VT.col('alt')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${3.6 * U}px;padding:${0.6 * U}px ${2.2 * U}px ${0.9 * U}px;white-space:nowrap;letter-spacing:.06em`, VT.esc(s.kicker)) : null;
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'beep', { gain: -20 }); VT.cue(at + 0.05, 'swoosh', { gain: -20 });
          return (t) => {
            const p = P(t, at, 0.45), cy = z.y + (z.h - ((VT.cfg.data && VT.cfg.data.ticker && VT.cfg.data.ticker.length) ? 8 * U : 0)) * 0.46;
            VT.place(card, VT.W / 2, cy, { x: (1 - eo(p)) * 25 * U * VT.sign, o: C(p * 3) });
            if (k) VT.place(k, VT.W / 2 - (w / 2 - k.offsetWidth / 2) * VT.sign, cy - card.offsetHeight / 2 - k.offsetHeight / 2, { o: C((t - at - 0.2) / 0.2) });
          };
        },
      },
    },
    overlays: [
      function chrome(layer) {
        const U = VT.U, Z = VT.Z, d = VT.cfg.data || {};
        const live = VT.el(layer, `display:flex;align-items:center;gap:${1 * U}px;background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${3.2 * U}px;padding:${0.6 * U}px ${1.8 * U}px ${0.9 * U}px;border-radius:${0.8 * U}px;letter-spacing:.1em`, `<i class="d" style="display:block;width:${1.4 * U}px;height:${1.4 * U}px;border-radius:50%;background:#fff"></i>${VT.esc(d.live || VT.label(null, 'live', 'LIVE'))}`);
        const ch = d.channel ? VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${3.6 * U}px;color:#fff;white-space:nowrap`, VT.esc(d.channel)) : null;
        const dot = live.querySelector('.d');
        const items = d.ticker || [];
        let tick = null, strip = null, tw = 0;
        const th = 6 * U;
        if (items.length) {
          tick = VT.el(layer, `left:0;right:0;height:${th}px;background:#fff;overflow:hidden;display:flex;align-items:center;direction:ltr`);
          const tag = VT.el(tick, `position:relative;flex:none;height:100%;background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${3 * U}px;display:flex;align-items:center;padding:0 ${2.4 * U}px;z-index:2`, VT.esc(d.tickerLabel || VT.label(null, 'latest', 'LATEST')));
          strip = VT.el(tick, `left:0;top:0;height:100%;display:flex;align-items:center;white-space:nowrap;font-family:${VT.font('body')};font-weight:700;font-size:${3.2 * U}px;color:${VT.col('ink')};direction:${VT.dir}`,
            (items.map((x) => `<span style="padding:0 ${3 * U}px">${VT.esc(x)}</span><span style="color:${VT.col('accent')}">■</span>`).join('')).repeat(4));
          tw = strip.scrollWidth / 4;
        }
        return (t) => {
          const o = C(t / 0.4);
          VT.place(live, Z.area.x + live.offsetWidth / 2 + (VT.dir === 'rtl' ? Z.area.w - live.offsetWidth : 0), Z.area.y + 2.5 * U, { o });
          if (ch) VT.place(ch, Z.area.x + (VT.dir === 'rtl' ? ch.offsetWidth / 2 : Z.area.w - ch.offsetWidth / 2), Z.area.y + 2.5 * U, { o });
          dot.style.opacity = Math.floor(t * 1.5) % 2 ? 0.3 : 1;
          if (tick) {
            tick.style.top = (VT.Z.cap.y - th - U) + 'px';
            strip.style.transform = `translateX(${VT.dir === 'rtl' ? ((t * 9 * U) % tw) : -((t * 9 * U) % tw)}px)`;
            tick.style.opacity = o;
          }
        };
      },
    ],
  });
})();
