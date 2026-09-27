/* review - product / app / place review: star score that fills up, pros and cons lists, and a BUY / SKIP verdict stamp. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  function list(kind) {
    return {
      build(s, layer) {
        const U = VT.U, Z = VT.Z, items = s.items || [];
        const good = kind === 'pros';
        const col = VT.col(good ? 'good' : 'bad');
        const head = VT.el(layer, `display:flex;align-items:center;gap:${2 * U}px;font-family:${VT.font('display')};font-weight:900;font-size:${8 * U}px;color:#fff;direction:${VT.dir}`,
          `<span style="width:${10 * U}px;height:${10 * U}px;border-radius:50%;background:${col};display:flex;align-items:center;justify-content:center">${VT.icon(good ? 'plus' : 'minus', '#fff', '60%')}</span>${VT.esc(s.title || VT.label(s, kind, good ? 'Pros' : 'Cons'))}`);
        const body = VT.clampW(VT.inset(Z.body, 1), 100);
        const rows = VT.rows(body, Math.max(items.length, 3), 2.2).slice(0, items.length);
        const els = items.map((it, i) => {
          const r = rows[i], h = Math.min(r.h, 14 * U);
          const e = VT.el(layer, `width:${r.w}px;height:${h}px;display:flex;align-items:center;gap:${2.4 * U}px;padding:0 ${3 * U}px;border-radius:${2.6 * U}px;background:rgba(255,255,255,.06);border-inline-start:${1 * U}px solid ${col};direction:${VT.dir}`,
            `<span style="flex:none;width:${6 * U}px;height:${6 * U}px">${VT.icon(good ? 'check' : 'x', col)}</span><span class="t" style="flex:1;min-width:0;font-family:${VT.font('display')};font-weight:800;font-size:${5.2 * U}px;color:#fff;line-height:1.15"></span>`);
          const tx = e.querySelector('.t'); tx.textContent = it.text || it; VT.fit(tx, null, h - U, 2.6);
          const at = VT.time(it.at, s.start + 0.5 + i * 0.7); VT.cue(at, good ? 'pop' : 'pop-low', { gain: -15, pan: i % 2 ? 0.3 : -0.3 });
          return { e, r, at };
        });
        return (t) => {
          const hp = P(t, s.start + 0.05, 0.4); VT.place(head, VT.W / 2, Z.head.y + Z.head.h / 2, { s: L(0.6, 1, sp(hp)), o: C(hp * 3) });
          els.forEach((x) => { const p = P(t, x.at - 0.1, 0.4); VT.place(x.e, x.r.x + x.r.w / 2 + (1 - eo(p)) * 20 * U * VT.sign, x.r.y + x.r.h / 2, { o: C(p * 3) }); });
        };
      },
    };
  }

  VT.template({
    theme: {
      palette: { bg: '#15171C', deep: '#0B0C0F', ink: '#15171C', paper: '#FFFFFF', accent: '#FFC53D', good: '#2FD08A', bad: '#FF5C5C', text: '#FFFFFF', muted: 'rgba(255,255,255,.62)' },
      captions: { style: 'pill', hl: '#FFC53D', hlText: '#15171C' },
      transition: 'slide', sfx: { transition: 'whoosh', transitionGain: -17 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 20%, #252A33, #0D0E11 70%)`);
      const s = VT.el(layer, `width:${90 * U}px;height:${90 * U}px;opacity:.05`, VT.icon('star', '#FFC53D'));
      return (t) => VT.place(s, VT.W * 0.85, VT.H * 0.2, { r: t * 8, o: 0.05 });
    },
    scenes: {
      // {product, media, rating, max, at, sub}
      score: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const max = s.max || 5, rating = +s.rating || 0;
          const hasM = s.media && VT.hasMedia(s.media);
          const ph = hasM ? VT.el(layer, `width:${Math.min(z.w * 0.7, z.h * 0.36)}px;height:${Math.min(z.w * 0.7, z.h * 0.36)}px;border-radius:${4 * U}px;overflow:hidden;box-shadow:0 ${2 * U}px ${6 * U}px rgba(0,0,0,.4)`) : null;
          const img = hasM ? VT.media(ph, s.media, 'left:0;top:0') : null;
          const name = VT.text(layer, s.product || '', { w: z.w * 0.9, h: 18 * U, size: 8, color: '#fff' });
          const big = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${24 * U}px;line-height:1;color:${VT.col('accent')};white-space:nowrap;direction:ltr;font-variant-numeric:tabular-nums`);
          const ss = Math.min(11 * U, z.w * 0.9 / Math.min(max, 10) - 1.5 * U);
          const stars = VT.el(layer, `display:flex;gap:${1.2 * U}px;direction:ltr`, Array.from({ length: Math.min(max, 10) }, () => `<div style="position:relative;width:${ss}px;height:${ss}px">${VT.icon('star', 'rgba(255,255,255,.15)')}<div class="f" style="position:absolute;left:0;top:0;height:100%;overflow:hidden;width:0">${`<div style="width:${ss}px;height:${ss}px">${VT.icon('star', VT.col('accent'))}</div>`}</div></div>`).join(''));
          const fills = Array.from(stars.querySelectorAll('.f'));
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.85, size: 4.4, weight: 600, font: 'body', color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.5), dur = 1.2;
          fills.forEach((_, i) => { if (i < Math.ceil(rating)) VT.cue(at + (i / Math.max(1, rating)) * dur, 'pop-high', { gain: -20 }); });
          VT.cue(at + dur + 0.05, 'ding', { gain: -12 });
          return (t) => {
            const total = (ph ? ph.offsetHeight + 4 * U : 0) + name.offsetHeight + 3 * U + big.offsetHeight + 3 * U + ss + (sub ? sub.offsetHeight + 4 * U : 0);
            let y = z.y + Math.max(0, (z.h - total) / 2);
            if (ph) { img.update(t - s.start); VT.place(ph, VT.W / 2, y + ph.offsetHeight / 2, { s: L(0.8, 1, sp(P(t, s.start + 0.1, 0.5))), o: C((t - s.start) / 0.3) }); y += ph.offsetHeight + 4 * U; }
            const r = VT.rise(t, s.start + 0.2, 0.45, 4); VT.place(name, VT.W / 2, y + name.offsetHeight / 2, { y: r.y, o: r.o }); y += name.offsetHeight + 3 * U;
            const f = eo(C((t - at) / dur)), cur = rating * f;
            big.innerHTML = `${VT.num(cur, 1)}<span style="font-size:.4em;color:${VT.col('muted')}">/${VT.num(max)}</span>`;
            VT.place(big, VT.W / 2, y + big.offsetHeight / 2, { s: t > at + dur ? L(1.12, 1, eo(P(t, at + dur, 0.3))) : 1, o: C((t - at + 0.2) / 0.2) }); y += big.offsetHeight + 3 * U;
            fills.forEach((e, i) => { e.style.width = C(cur - i) * 100 + '%'; });
            VT.place(stars, VT.W / 2, y + ss / 2, { o: C((t - at + 0.2) / 0.2) }); y += ss + 4 * U;
            if (sub) { const r2 = VT.rise(t, at + dur, 0.45, 3); VT.place(sub, VT.W / 2, y + sub.offsetHeight / 2, { y: r2.y, o: r2.o }); }
          };
        },
      },
      pros: list('pros'),
      cons: list('cons'),
      // {text, positive, sub, at}
      verdict: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, good = s.positive !== false;
          const st = VT.stamp(layer, s.text || (good ? VT.label(s, 'buy', 'BUY IT') : VT.label(s, 'skip', 'SKIP IT')), VT.col(good ? 'good' : 'bad'));
          st.style.fontSize = 14 * U + 'px'; st.style.borderWidth = 1.4 * U + 'px'; st.style.padding = `${1.2 * U}px ${5 * U}px ${2 * U}px`;
          VT.fit(st, z.w * 0.9);
          const kick = VT.el(layer, `font-family:${VT.font('display')};font-weight:800;font-size:${5 * U}px;color:${VT.col('muted')};letter-spacing:.2em;white-space:nowrap`, VT.esc(s.kicker || VT.label(s, 'verdict', 'VERDICT')));
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.86, size: 5, weight: 700, font: 'body', color: '#fff' }) : null;
          const at = VT.time(s.at, s.start + 0.6);
          VT.cue(at - 0.6, 'drumroll', { dur: 0.55, gain: -16 }); VT.cue(at, 'impact', { gain: -8 }); VT.cue(at + 0.05, good ? 'success' : 'buzzer', { gain: -12 });
          return (t) => {
            const cy = z.y + z.h * 0.45, p = P(t, at, 0.3);
            VT.place(kick, VT.W / 2, cy - st.offsetHeight / 2 - 8 * U, { o: C((t - s.start) / 0.3) });
            VT.place(st, VT.W / 2, cy, { s: L(3, 1, eo(p)), r: -7, o: C(p * 5) });
            if (sub) { const r = VT.rise(t, at + 0.5, 0.45, 3); VT.place(sub, VT.W / 2, cy + st.offsetHeight / 2 + 8 * U, { y: r.y, o: r.o }); }
          };
        },
      },
    },
  });
})();
