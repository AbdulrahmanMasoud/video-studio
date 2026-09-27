/* counter - data storytelling: big numbers that count up, rings, bar charts and comparisons. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const fmt = (v, d, pre, suf) => `${pre || ''}${VT.num(v, d || 0)}${suf || ''}`;

  VT.template({
    theme: {
      palette: { bg: '#071A2E', deep: '#030C17', ink: '#071A2E', paper: '#FFFFFF', accent: '#3DDCFF', alt: '#B6FF5C', warm: '#FF8A3D', text: '#FFFFFF', muted: 'rgba(255,255,255,.62)', track: 'rgba(255,255,255,.1)' },
      captions: { style: 'pill', hl: '#3DDCFF', hlText: '#071A2E' },
      transition: 'slide', sfx: { transition: 'whoosh', transitionGain: -17 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 35%, #0E2F52, #041020 75%)`);
      const g = VT.el(layer, `inset:0;background-image:linear-gradient(rgba(61,220,255,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(61,220,255,.07) 1px,transparent 1px);background-size:${10 * U}px ${10 * U}px;mask-image:radial-gradient(ellipse at 50% 45%, #000 20%, transparent 75%);-webkit-mask-image:radial-gradient(ellipse at 50% 45%, #000 20%, transparent 75%)`);
      return (t) => { g.style.transform = `scale(${1.05 + Math.sin(t * 0.2) * 0.03})`; };
    },
    scenes: {
      // {value, prefix, suffix, decimals, label, sub, at, dur, chart: ring|bars|none, max, bars:[..], source}
      stat: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, land = VT.orient === 'landscape';
          const chart = s.chart || 'none';
          const at = VT.time(s.at, s.start + 0.3), dur = s.dur || 1.4, val = +s.value || 0, d = s.decimals || 0;
          const big = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;line-height:1;color:${VT.col('text')};white-space:nowrap;font-variant-numeric:tabular-nums;direction:ltr`);
          big.style.fontSize = (chart === 'ring' ? 17 : 26) * U + 'px';
          big.textContent = fmt(val, d, s.prefix, s.suffix);
          const maxW = chart === 'ring' ? 46 * U : z.w * 0.94; VT.fit(big, maxW);
          big.style.width = big.offsetWidth * 1.02 + 'px'; big.style.textAlign = 'center';
          const lab = s.label ? VT.text(layer, s.label, { w: Math.min(z.w * 0.9, 110 * U), h: 20 * U, size: 6.4, weight: 800, color: VT.col('accent') }) : null;
          const sub = s.sub ? VT.text(layer, s.sub, { w: Math.min(z.w * 0.86, 100 * U), size: 4.4, weight: 600, font: 'body', color: VT.col('muted') }) : null;
          const src = s.source ? VT.text(layer, s.source, { w: z.w * 0.9, size: 2.6, weight: 500, font: 'body', color: VT.col('muted') }) : null;
          let ring = null, arc = null, bars = [];
          if (chart === 'ring') {
            ring = VT.el(layer, `width:${56 * U}px;height:${56 * U}px`, `<svg viewBox="0 0 100 100" width="100%" height="100%" style="transform:rotate(-90deg)"><circle cx="50" cy="50" r="44" stroke="${VT.col('track')}" stroke-width="7" fill="none"/><circle class="a" cx="50" cy="50" r="44" stroke="${VT.col('accent')}" stroke-width="7" fill="none" stroke-linecap="round" pathLength="1" stroke-dasharray="1" stroke-dashoffset="1"/></svg>`);
            arc = ring.querySelector('.a');
          } else if (chart === 'bars') {
            const vals = s.bars && s.bars.length ? s.bars : [0.2, 0.35, 0.3, 0.5, 0.65, 1].map((x) => x * val);
            const bw = Math.min(z.w * 0.8, 90 * U), bh = land ? z.h * 0.3 : 26 * U, n = vals.length, gap = 2 * U, w1 = (bw - gap * (n - 1)) / n, mx = Math.max(...vals) || 1;
            const wrap = VT.el(layer, `width:${bw}px;height:${bh}px;direction:ltr`);
            bars = vals.map((v, i) => ({ e: VT.el(wrap, `left:${i * (w1 + gap)}px;bottom:0;width:${w1}px;height:${(v / mx) * bh}px;border-radius:${1.4 * U}px ${1.4 * U}px ${0.4 * U}px ${0.4 * U}px;background:${i === n - 1 ? VT.col('accent') : 'rgba(255,255,255,.22)'};transform-origin:50% 100%`), i }));
            ring = wrap;
          }
          VT.cue(at - 0.05, 'riser', { dur: dur, gain: -24 }); VT.cue(at + dur, 'impact', { gain: -12 }); VT.cue(at + dur + 0.02, 'ding', { gain: -15 });
          const ticks = Math.min(14, Math.round(dur * 9)); for (let i = 0; i < ticks; i++) VT.cue(at + (i / ticks) * dur * 0.95, 'tick', { gain: -28 });
          const side = land && chart !== 'none';
          if (side) [lab, sub].forEach((e) => { if (e) { e.style.textAlign = 'start'; e.style.width = z.w * 0.42 + 'px'; VT.fit(e, z.w * 0.42, 24 * U); } });
          const textH0 = (lab ? lab.offsetHeight + 2 * U : 0) + (sub ? sub.offsetHeight : 0) + (src ? 5 * U : 0);
          const ringPx = Math.min(56 * U, side ? z.h * 0.85 : z.h - textH0 - 8 * U);
          if (chart === 'ring') { ring.style.width = ring.style.height = ringPx + 'px'; big.style.fontSize = parseFloat(big.style.fontSize) * ringPx / (56 * U) + 'px'; }
          return (t) => {
            const f = eo(C((t - at) / dur)), cur = val * f;
            big.textContent = fmt(cur, d, s.prefix, s.suffix);
            // visual column (number + chart) and text column
            const vx = side ? VT.W / 2 - z.w * 0.24 * VT.sign : VT.W / 2, tx = side ? VT.W / 2 + z.w * 0.24 * VT.sign : VT.W / 2;
            const hit = t > at + dur ? L(1.08, 1, eo(P(t, at + dur, 0.35))) : 1;
            const chartH = chart === 'ring' ? ringPx : chart === 'bars' ? ring.offsetHeight + 4 * U : 0;
            const groupH = chart === 'ring' ? chartH : big.offsetHeight + chartH;
            const textH = (lab ? lab.offsetHeight + 2 * U : 0) + (sub ? sub.offsetHeight : 0);
            const totalH = side ? groupH : groupH + 5 * U + textH;
            let y = z.y + (z.h - totalH) / 2 - (chart === 'none' ? z.h * 0.04 : 0);
            const numY = chart === 'ring' ? y + chartH / 2 : y + big.offsetHeight / 2;
            VT.place(big, vx, numY, { s: L(0.6, 1, sp(P(t, at - 0.1, 0.5))) * hit, o: C((t - at + 0.1) / 0.15) });
            if (chart === 'ring') { VT.place(ring, vx, y + chartH / 2, { s: L(0.7, 1, eo(P(t, at - 0.2, 0.6))), o: C((t - at + 0.2) / 0.2) }); arc.setAttribute('stroke-dashoffset', String(1 - f * C(val / (s.max || 100)))); }
            if (chart === 'bars') {
              VT.place(ring, vx, y + big.offsetHeight + 4 * U + ring.offsetHeight / 2, { o: C((t - at + 0.1) / 0.2) });
              bars.forEach((b) => { b.e.style.transform = `scaleY(${eo(P(t, at + b.i * (dur / bars.length) * 0.7, 0.5))})`; });
            }
            let ly = side ? z.y + (z.h - textH) / 2 : y + groupH + 5 * U;
            if (lab) { const r = VT.rise(t, at + 0.35, 0.45, 4); VT.place(lab, tx, ly + lab.offsetHeight / 2, { y: r.y, o: r.o }); ly += lab.offsetHeight + 2 * U; }
            if (sub) { const r = VT.rise(t, at + dur, 0.45, 3); VT.place(sub, tx, ly + sub.offsetHeight / 2, { y: r.y, o: r.o }); }
            if (src) VT.place(src, VT.W / 2, z.y + z.h - 2 * U, { o: C((t - at - dur) / 0.4) * 0.8 });
          };
        },
      },
      // {title, items:[{label, value, prefix, suffix, decimals, highlight}], at}
      compare: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, items = s.items || [];
          const head = s.title ? VT.text(layer, s.title, { w: Z.area.w * 0.92, h: Z.head.h * 0.8, size: 7.4, color: '#fff' }) : null;
          const body = VT.clampW(VT.inset(s.title ? Z.body : Z.full, 1), 110);
          const rows = VT.rows(body, Math.max(items.length, 3), 3).slice(0, items.length);
          const mx = Math.max(...items.map((i) => +i.value || 0)) || 1;
          const at = VT.time(s.at, s.start + 0.4);
          const els = items.map((it, i) => {
            const r = rows[i], h = Math.min(r.h, 17 * U);
            const e = VT.el(layer, `width:${r.w}px;height:${h}px;direction:${VT.dir}`);
            const lab = VT.el(e, `top:0;inset-inline-start:0;font-family:${VT.font('display')};font-weight:800;font-size:${4.4 * U}px;color:#fff;white-space:nowrap`, VT.esc(it.label || ''));
            const barH = h * 0.5;
            const hl = it.highlight || (+it.value === mx);
            const track = VT.el(e, `bottom:0;inset-inline-start:0;width:100%;height:${barH}px;border-radius:${barH / 2}px;background:${VT.col('track')}`);
            const fill = VT.el(track, `top:0;bottom:0;inset-inline-start:0;width:0;border-radius:${barH / 2}px;background:${hl ? `linear-gradient(90deg,${VT.col('accent')},${VT.col('alt')})` : 'rgba(255,255,255,.35)'}`);
            const n = VT.el(e, `top:0;inset-inline-end:0;font-family:${VT.font('display')};font-weight:900;font-size:${5 * U}px;color:${hl ? VT.col('accent') : '#fff'};white-space:nowrap;direction:ltr`);
            const ia = VT.time(it.at, at + i * 0.45);
            VT.cue(ia, 'swoosh', { gain: -22 }); if (hl) VT.cue(ia + 0.9, 'ding', { gain: -16 });
            return { e, fill, n, r, it, ia, pct: (+it.value || 0) / mx };
          });
          return (t) => {
            if (head) { const r = VT.rise(t, s.start + 0.05, 0.45, 4); VT.place(head, VT.W / 2, Z.head.y + Z.head.h / 2, { y: r.y, o: r.o }); }
            els.forEach((x) => {
              const p = P(t, x.ia - 0.15, 0.4), f = eo(P(t, x.ia, 1));
              VT.place(x.e, x.r.x + x.r.w / 2, x.r.y + x.r.h / 2, { o: C(p * 3), y: (1 - eo(p)) * 3 * U });
              x.fill.style.width = x.pct * f * 100 + '%';
              x.n.textContent = fmt(x.it.value * f, x.it.decimals || 0, x.it.prefix, x.it.suffix);
            });
          };
        },
      },
    },
  });
})();
