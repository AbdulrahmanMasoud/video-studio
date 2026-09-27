/* flash-sale - loud promo: shaking discount, live countdown clock, product tiles, promo-code CTA. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const pad2 = (n) => String(n).padStart(2, '0');

  VT.template({
    theme: {
      palette: { bg: '#FF2E4D', deep: '#B3001E', ink: '#1A0A10', paper: '#FFFFFF', accent: '#FFE14D', alt: '#1A0A10', text: '#FFFFFF', muted: 'rgba(255,255,255,.85)' },
      captions: { style: 'pop', hl: '#FFE14D', hlText: '#1A0A10', maxWords: 1 },
      transition: 'zoom', sfx: { transition: 'whoosh', transitionGain: -14 }, zones: { head: 0.14 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:${VT.col('bg')}`);
      const burst = VT.el(layer, `left:50%;top:45%;width:${240 * U}px;height:${240 * U}px;margin:-${120 * U}px 0 0 -${120 * U}px;background:repeating-conic-gradient(rgba(255,255,255,.1) 0 10deg, transparent 10deg 20deg);border-radius:50%`);
      const tape = [0, 1].map((i) => VT.el(layer, `left:-20%;width:140%;height:${7 * U}px;background:${VT.col('accent')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${3.6 * U}px;display:flex;align-items:center;white-space:nowrap;overflow:hidden;letter-spacing:.1em`, `<span class="s">${(VT.esc((VT.cfg.data && VT.cfg.data.tape) || 'SALE • SALE • LIMITED TIME • ') + ' ').repeat(14)}</span>`));
      return (t) => {
        burst.style.transform = `rotate(${t * 10}deg)`;
        tape.forEach((e, i) => {
          e.style.top = (i ? VT.H - 7 * U - 1 * U : U) + 'px';
          e.style.transform = `rotate(${i ? -2 : 2}deg)`;
          e.querySelector('.s').style.transform = `translateX(${(i ? 1 : -1) * ((t * 12 * U) % (60 * U))}px)`;
        });
      };
    },
    scenes: {
      // {kicker, value, prefix, suffix, timer:{seconds}, fine, at}
      sale: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const kick = VT.el(layer, `background:${VT.col('ink')};color:${VT.col('accent')};font-family:${VT.font('display')};font-weight:900;font-size:${5.6 * U}px;padding:${1 * U}px ${3.6 * U}px ${1.5 * U}px;border-radius:${2 * U}px;white-space:nowrap;letter-spacing:.04em`, VT.esc(s.kicker || VT.label(s, 'flash', 'FLASH SALE')));
          const big = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;line-height:.9;color:${VT.col('accent')};white-space:nowrap;text-shadow:0 ${2 * U}px 0 ${VT.col('deep')};direction:ltr;text-align:center`,
            `<span style="font-size:${40 * U}px">${VT.esc((s.prefix || '') + (s.value != null ? VT.num(s.value) : '50'))}</span><span style="font-size:${18 * U}px">${VT.esc(s.suffix == null ? '%' : s.suffix)}</span>`);
          VT.fit(big, z.w * 0.95);
          const off = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${10 * U}px;color:#fff;letter-spacing:.06em;white-space:nowrap`, VT.esc(s.word || VT.label(s, 'off', 'OFF')));
          const secs = (s.timer && s.timer.seconds) || 0;
          const timer = secs ? VT.el(layer, `display:flex;gap:${1.2 * U}px;direction:ltr`, [0, 1, 2].map(() => `<div style="background:${VT.col('ink')};color:#fff;border-radius:${1.6 * U}px;padding:${1 * U}px ${1.6 * U}px;font-family:${VT.font('display')};font-weight:900;font-size:${7 * U}px;min-width:${14 * U}px;text-align:center;font-variant-numeric:tabular-nums"></div>`).join('')) : null;
          const fine = s.fine ? VT.text(layer, s.fine, { w: z.w * 0.85, size: 3.2, weight: 600, font: 'body', color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.3);
          VT.cue(s.start + 0.05, 'riser', { dur: Math.max(0.2, at - s.start - 0.05), gain: -20 }); VT.cue(at - 0.02, 'boom', { gain: -8 }); VT.cue(at + 0.35, 'cash', { gain: -14 });
          if (timer) for (let k = 1; k < 6; k++) VT.cue(at + 0.6 + k, 'tick', { gain: -24 });
          return (t) => {
            const cy = z.y + z.h * 0.42;
            const kp = P(t, s.start + 0.05, 0.35); VT.place(kick, VT.W / 2, cy - big.offsetHeight / 2 - 8 * U, { s: L(0.4, 1, sp(kp)), r: -3, o: C(kp * 4) });
            const p = P(t, at, 0.35), sh = t > at && t < at + 0.35 ? Math.sin(t * 110) * 1.4 * U * (1 - (t - at) / 0.35) : 0;
            VT.place(big, VT.W / 2 + sh, cy, { s: L(3, 1, eo(p)) * (1 + Math.sin(t * 6) * 0.015), r: -4, o: C(p * 6) });
            VT.place(off, VT.W / 2, cy + big.offsetHeight / 2 + 4 * U, { s: L(0.3, 1, sp(P(t, at + 0.25, 0.4))), r: -4, o: C((t - at - 0.25) / 0.1) });
            let y = cy + big.offsetHeight / 2 + off.offsetHeight + 10 * U;
            if (timer) {
              const left = Math.max(0, secs - Math.max(0, t - at - 0.6));
              const hh = Math.floor(left / 3600), mm = Math.floor((left % 3600) / 60), ss = Math.floor(left % 60);
              const cells = timer.children; cells[0].textContent = pad2(hh); cells[1].textContent = pad2(mm); cells[2].textContent = pad2(ss);
              const tp = P(t, at + 0.6, 0.4); VT.place(timer, VT.W / 2, y + timer.offsetHeight / 2, { y: (1 - eo(tp)) * 5 * U, o: C(tp * 3) });
              y += timer.offsetHeight + 4 * U;
            }
            if (fine) VT.place(fine, VT.W / 2, Math.min(y + fine.offsetHeight / 2, z.y + z.h - fine.offsetHeight / 2), { o: C((t - at - 1) / 0.4) });
          };
        },
      },
      // {items:[{name, price, old, media}], currency, at}
      items: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, items = (s.items || []).slice(0, 4);
          const n = items.length || 1, cols = VT.orient === 'landscape' ? Math.min(4, n) : Math.min(2, n), rowsN = Math.ceil(n / cols);
          const grid = [].concat(...VT.rows(VT.inset(z, 2), rowsN, 3).map((r) => VT.cols(r, cols, 3))).slice(0, n);
          const at = VT.time(s.at, s.start + 0.2), cur = s.currency || '$';
          const els = items.map((it, i) => {
            const g = grid[i];
            const e = VT.card(layer, { bg: '#fff', fg: VT.col('ink'), shadow: VT.col('deep'), css: `width:${g.w}px;height:${g.h}px;overflow:hidden` });
            const ph = VT.el(e, `left:0;right:0;top:0;height:62%;background:linear-gradient(135deg,#FFE9EC,#FFD2D9);display:flex;align-items:center;justify-content:center`);
            if (it.media && VT.hasMedia(it.media)) VT.media(ph, it.media, 'left:0;top:0');
            else ph.innerHTML = `<div style="width:40%;height:60%">${VT.icon(it.icon || 'cart', VT.col('bg'))}</div>`;
            VT.el(e, `left:${2 * U}px;right:${2 * U}px;top:64%;font-family:${VT.font('display')};font-weight:800;font-size:${3.8 * U}px;line-height:1.1;white-space:nowrap;overflow:hidden;text-overflow:ellipsis`, VT.esc(it.name || ''));
            VT.el(e, `left:${2 * U}px;right:${2 * U}px;bottom:${2 * U}px;display:flex;align-items:baseline;gap:${1.4 * U}px;font-family:${VT.font('display')};direction:ltr`,
              `<b style="font-size:${5.6 * U}px;color:${VT.col('bg')}">${VT.esc(cur + it.price)}</b>` + (it.old != null ? `<s style="font-size:${3.4 * U}px;opacity:.5">${VT.esc(cur + it.old)}</s>` : ''));
            const tag = it.old != null ? VT.el(e, `top:${1.6 * U}px;inset-inline-end:${1.6 * U}px;background:${VT.col('accent')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${3.4 * U}px;padding:${0.5 * U}px ${1.6 * U}px ${0.8 * U}px;border-radius:${1.4 * U}px;direction:ltr`, `-${Math.round((1 - it.price / it.old) * 100)}%`) : null;
            const ia = VT.time(it.at, at + i * 0.3); VT.cue(ia, 'pop-high', { gain: -15, pan: (i % 2 ? 0.3 : -0.3) });
            return { e, g, ia, i };
          });
          return (t) => els.forEach((x) => { const p = P(t, x.ia, 0.45); VT.place(x.e, x.g.x + x.g.w / 2, x.g.y + x.g.h / 2, { s: L(0.5, 1, sp(p)), r: (x.i % 2 ? 2 : -2) * (1 - eo(p)), o: C(p * 4) }); });
        },
      },
      // {text, code, sub, at}
      cta: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const tx = VT.text(layer, s.text || VT.label(s, 'cta', 'Use code'), { w: z.w * 0.9, h: z.h * 0.25, size: 8.4, color: '#fff' });
          const code = VT.el(layer, `background:#fff;color:${VT.col('ink')};border:${0.7 * U}px dashed ${VT.col('ink')};border-radius:${2.4 * U}px;padding:${2 * U}px ${5 * U}px;font-family:${VT.font('display')};font-weight:900;font-size:${9 * U}px;letter-spacing:.12em;white-space:nowrap;direction:ltr`, VT.esc(s.code || 'SALE50'));
          VT.fit(code, z.w * 0.9);
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.85, size: 4.4, weight: 700, font: 'body', color: VT.col('accent') }) : null;
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -12 }); VT.cue(at + 0.5, 'coin', { gain: -12 });
          return (t) => {
            const cy = z.y + z.h * 0.45;
            const r = VT.rise(t, at, 0.4, 4); VT.place(tx, VT.W / 2, cy - code.offsetHeight / 2 - tx.offsetHeight / 2 - 4 * U, { y: r.y, o: r.o });
            const p = P(t, at + 0.5, 0.45); VT.place(code, VT.W / 2, cy, { s: L(1.8, 1, eo(p)) * (1 + Math.sin(t * 5) * 0.02), r: -2, o: C(p * 5) });
            if (sub) { const r2 = VT.rise(t, at + 0.9, 0.4, 3); VT.place(sub, VT.W / 2, cy + code.offsetHeight / 2 + 6 * U, { y: r2.y, o: r2.o }); }
          };
        },
      },
    },
  });
})();
