/* recipe - cooking video: title with time/servings, ingredient checklist, numbered steps with a kitchen timer, final dish. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const mmss = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

  VT.template({
    theme: {
      palette: { bg: '#FFF4E6', deep: '#E9D5BD', ink: '#3A2418', paper: '#FFFFFF', accent: '#E8563F', alt: '#5C9E4A', text: '#3A2418', muted: 'rgba(58,36,24,.62)' },
      captions: { style: 'pill', hl: '#E8563F', hlText: '#FFFFFF', color: '#3A2418', shadow: 'rgba(255,255,255,.9)' },
      transition: 'slide', sfx: { transition: 'swoosh', transitionGain: -19 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:${VT.col('bg')}`);
      const check = VT.el(layer, `inset:-${10 * U}px;opacity:.5;background-image:linear-gradient(45deg, rgba(232,86,63,.07) 25%, transparent 25%, transparent 75%, rgba(232,86,63,.07) 75%), linear-gradient(45deg, rgba(232,86,63,.07) 25%, transparent 25%, transparent 75%, rgba(232,86,63,.07) 75%);background-size:${10 * U}px ${10 * U}px;background-position:0 0, ${5 * U}px ${5 * U}px`);
      return (t) => { check.style.transform = `translate(${(t * U) % (10 * U)}px,${(t * U) % (10 * U)}px)`; };
    },
    scenes: {
      // {text, time, servings, media, at}
      title: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const hasM = s.media && VT.hasMedia(s.media);
          const d = Math.min(z.w * 0.62, z.h * 0.4);
          const plate = VT.el(layer, `width:${d}px;height:${d}px;border-radius:50%;background:#fff;box-shadow:0 ${2 * U}px ${6 * U}px rgba(58,36,24,.18), inset 0 0 0 ${2.4 * U}px #F4EDE4;overflow:hidden`);
          if (hasM) VT.media(VT.el(plate, `inset:${2.4 * U}px;border-radius:50%;overflow:hidden`), s.media, 'left:0;top:0');
          else VT.el(plate, `inset:${6 * U}px;border-radius:50%;background:radial-gradient(circle at 35% 35%, #F7B267, ${VT.col('accent')} 70%)`);
          const tt = VT.text(layer, s.text || '', { w: z.w * 0.9, h: z.h * 0.22, size: 9, color: VT.col('ink') });
          const chips = VT.el(layer, `display:flex;gap:${2 * U}px;direction:${VT.dir}`,
            [[s.time, 'clock'], [s.servings, 'person']].filter((x) => x[0] != null).map(([v, ic]) => `<div style="display:flex;align-items:center;gap:${1 * U}px;background:#fff;border-radius:${4 * U}px;padding:${1 * U}px ${2.6 * U}px ${1.2 * U}px ${1.6 * U}px;font-family:${VT.font('display')};font-weight:800;font-size:${4 * U}px;color:${VT.col('ink')};box-shadow:0 ${0.6 * U}px ${1.6 * U}px rgba(0,0,0,.08)"><span style="width:${4.4 * U}px;height:${4.4 * U}px">${VT.icon(ic, VT.col('accent'))}</span>${VT.esc(v)}</div>`).join(''));
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -12 }); VT.cue(at + 0.6, 'ding', { gain: -18 });
          return (t) => {
            const total = d + 5 * U + tt.offsetHeight + 4 * U + chips.offsetHeight;
            let y = z.y + (z.h - total) / 2;
            const p = P(t, at, 0.6);
            VT.place(plate, VT.W / 2, y + d / 2, { s: L(0.5, 1, sp(p)), r: L(-40, 0, eo(p)) + Math.sin(t * 0.5) * 2, o: C(p * 3) }); y += d + 5 * U;
            const r = VT.rise(t, at + 0.3, 0.45, 4); VT.place(tt, VT.W / 2, y + tt.offsetHeight / 2, { y: r.y, o: r.o }); y += tt.offsetHeight + 4 * U;
            const r2 = VT.rise(t, at + 0.6, 0.45, 3); VT.place(chips, VT.W / 2, y + chips.offsetHeight / 2, { y: r2.y, o: r2.o });
          };
        },
      },
      // {title, items:[{text, qty, at}]}
      ingredients: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, items = s.items || [];
          const head = VT.text(layer, s.title || VT.label(s, 'ingredients', 'Ingredients'), { w: Z.area.w * 0.9, h: Z.head.h * 0.8, size: 8, color: VT.col('ink') });
          const cols = VT.orient === 'landscape' && items.length > 4 ? 2 : 1, per = Math.ceil(items.length / cols);
          const body = VT.clampW(VT.inset(Z.body, 1), cols === 2 ? 170 : 96);
          const cells = [].concat(...VT.cols(body, cols, 4).map((c) => VT.rows(c, Math.max(per, 4), 1.6).slice(0, per))).slice(0, items.length);
          const els = items.map((it, i) => {
            const c = cells[i], h = Math.min(c.h, 12 * U);
            const e = VT.card(layer, { bg: '#fff', fg: VT.col('ink'), shadow: 'rgba(58,36,24,.12)', sh: 0.8, r: 2.4, css: `width:${c.w}px;height:${h}px;display:flex;align-items:center;gap:${2.2 * U}px;padding:0 ${2.8 * U}px;direction:${VT.dir}` });
            e.innerHTML = `<div class="b" style="flex:none;width:${6 * U}px;height:${6 * U}px;border-radius:${1.6 * U}px;border:${0.5 * U}px solid ${VT.col('deep')};display:flex;align-items:center;justify-content:center"></div><div class="t" style="flex:1;min-width:0;font-family:${VT.font('display')};font-weight:700;font-size:${4.6 * U}px;line-height:1.1"></div>` + (it.qty ? `<div style="flex:none;font-family:${VT.font('display')};font-weight:900;font-size:${4.2 * U}px;color:${VT.col('accent')}">${VT.esc(it.qty)}</div>` : '');
            const tx = e.querySelector('.t'); tx.textContent = it.text || it; VT.fit(tx, null, h - U, 2.4);
            const at = VT.time(it.at, s.start + 0.5 + i * 0.5); VT.cue(at, 'pop', { gain: -17, pan: i % 2 ? 0.3 : -0.3 }); VT.cue(at + 0.3, 'tick', { gain: -22 });
            return { e, b: e.querySelector('.b'), c, at };
          });
          return (t) => {
            const r = VT.rise(t, s.start, 0.4, 3); VT.place(head, VT.W / 2, Z.head.y + Z.head.h / 2, { y: r.y, o: r.o });
            els.forEach((x) => {
              const p = P(t, x.at - 0.1, 0.4), ck = t >= x.at + 0.3;
              VT.place(x.e, x.c.x + x.c.w / 2 - (1 - eo(p)) * 15 * U * VT.sign, x.c.y + x.c.h / 2, { o: C(p * 3) });
              x.b.style.background = ck ? VT.col('alt') : 'transparent'; x.b.style.borderColor = ck ? VT.col('alt') : VT.col('deep');
              x.b.innerHTML = ck ? VT.icon('check', '#fff', '80%') : '';
            });
          };
        },
      },
      // {n, text, timer (seconds), media, at}
      step: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z.full;
          const n = s.n != null ? s.n : ctx.scenes.filter((x) => x.type === 'step').indexOf(s) + 1;
          const hasM = s.media && VT.hasMedia(s.media);
          const ph = hasM ? VT.el(layer, `width:${z.w}px;height:${z.h * 0.42}px;border-radius:${3 * U}px;overflow:hidden;box-shadow:0 ${1.6 * U}px ${4 * U}px rgba(0,0,0,.15)`) : null;
          const img = hasM ? VT.media(ph, s.media, 'left:0;top:0') : null;
          const num = VT.el(layer, `width:${15 * U}px;height:${15 * U}px;border-radius:50%;background:${VT.col('accent')};color:#fff;display:flex;align-items:center;justify-content:center;font-family:${VT.font('display')};font-weight:900;font-size:${8 * U}px;box-shadow:0 ${1 * U}px 0 #B8402D`, VT.esc(typeof n === 'number' ? VT.num(n) : n));
          const tx = VT.text(layer, s.text || '', { w: z.w * 0.9, h: z.h * (hasM ? 0.22 : 0.34), size: 7.4, color: VT.col('ink') });
          const secs = s.timer || 0;
          const tm = secs ? VT.el(layer, `width:${24 * U}px;height:${24 * U}px`, `<svg viewBox="0 0 100 100" width="100%" height="100%" style="position:absolute;inset:0;transform:rotate(-90deg)"><circle cx="50" cy="50" r="44" fill="#fff" stroke="${VT.col('deep')}" stroke-width="6"/><circle class="a" cx="50" cy="50" r="44" fill="none" stroke="${VT.col('accent')}" stroke-width="6" stroke-linecap="round" pathLength="1" stroke-dasharray="1"/></svg><b style="position:absolute;inset:0;display:flex;align-items:center;justify-content:center;font-family:${VT.font('display')};font-size:${6 * U}px;color:${VT.col('ink')};direction:ltr"></b>`) : null;
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -13 });
          if (secs) { VT.cue(at + 0.8, 'tick', { gain: -22 }); VT.cue(s.end - 0.3, 'ding', { gain: -14 }); }
          return (t) => {
            const total = (ph ? ph.offsetHeight + 4 * U : 0) + num.offsetHeight + 4 * U + tx.offsetHeight + (tm ? 28 * U : 0);
            let y = z.y + Math.max(0, (z.h - total) / 2);
            if (ph) { img.update(t - s.start); VT.place(ph, VT.W / 2, y + ph.offsetHeight / 2, { o: C((t - at) / 0.3) }); y += ph.offsetHeight + 4 * U; }
            const p = P(t, at, 0.45); VT.place(num, VT.W / 2, y + num.offsetHeight / 2, { s: L(0.3, 1, sp(p)), r: L(-60, 0, eo(p)), o: C(p * 4) }); y += num.offsetHeight + 4 * U;
            const r = VT.rise(t, at + 0.2, 0.45, 4); VT.place(tx, VT.W / 2, y + tx.offsetHeight / 2, { y: r.y, o: r.o }); y += tx.offsetHeight + 4 * U;
            if (tm) {
              // the timer runs visually over the scene (sped up), showing the real target time
              const f = C((t - at - 0.8) / Math.max(0.5, s.end - at - 1.2));
              tm.querySelector('.a').setAttribute('stroke-dashoffset', String(f));
              tm.querySelector('b').textContent = mmss(secs * (1 - f));
              VT.place(tm, VT.W / 2, y + 12 * U, { s: L(0.4, 1, sp(P(t, at + 0.5, 0.4))), o: C((t - at - 0.5) / 0.2), r: f >= 1 ? Math.sin(t * 40) * 4 * C((s.end - t) / 0.3) : 0 });
            }
          };
        },
      },
      // {text, sub, media, at}
      final: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const hasM = s.media && VT.hasMedia(s.media);
          const d = Math.min(z.w * 0.8, z.h * 0.55);
          const ph = VT.el(layer, `width:${d}px;height:${d}px;border-radius:${hasM ? 3 * U : d / 2}px;overflow:hidden;box-shadow:0 ${2 * U}px ${6 * U}px rgba(58,36,24,.25);background:#fff`);
          if (hasM) VT.media(ph, s.media, 'left:0;top:0'); else VT.el(ph, `inset:${6 * U}px;border-radius:50%;background:radial-gradient(circle at 35% 35%, #F7B267, ${VT.col('accent')} 70%)`);
          const tt = VT.text(layer, s.text || VT.label(s, 'final', 'Enjoy!'), { w: z.w * 0.9, h: z.h * 0.2, size: 10, color: VT.col('ink'), font: 'hand' });
          const sp2 = Array.from({ length: 10 }, (_, i) => VT.el(layer, `width:${4 * U}px;height:${4 * U}px`, VT.icon('star', i % 2 ? VT.col('accent') : '#F7B267')));
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'sparkle', { gain: -12 }); VT.cue(at + 0.2, 'success', { gain: -14 });
          return (t) => {
            const cy = z.y + z.h * 0.42, p = P(t, at, 0.6);
            VT.place(ph, VT.W / 2, cy, { s: L(0.7, 1, sp(p)) * (1 + (t - at) * 0.01), o: C(p * 3) });
            const r = VT.rise(t, at + 0.4, 0.45, 4); VT.place(tt, VT.W / 2, cy + d / 2 + tt.offsetHeight / 2 + 4 * U, { y: r.y, o: r.o, r: -2 });
            sp2.forEach((e, i) => { const a = (i / sp2.length) * Math.PI * 2 + t * 0.4, R = d * 0.62 + Math.sin(t * 2 + i) * 2 * U; VT.place(e, VT.W / 2 + Math.cos(a) * R, cy + Math.sin(a) * R, { s: L(0, 1, sp(P(t, at + 0.2 + i * 0.05, 0.4))) * (0.7 + 0.3 * Math.sin(t * 5 + i)), r: t * 60 }); });
          };
        },
      },
    },
  });
})();
