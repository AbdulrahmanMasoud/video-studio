/* workout - fitness: exercise cards with a live rep counter or interval ring, rest timers with "next up", and a finish screen. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  function ring(p, sizePx, color) {
    return VT.el(p, `width:${sizePx}px;height:${sizePx}px`, `<svg viewBox="0 0 100 100" width="100%" height="100%" style="position:absolute;inset:0;transform:rotate(-90deg)"><circle cx="50" cy="50" r="45" fill="none" stroke="rgba(255,255,255,.1)" stroke-width="6"/><circle class="a" cx="50" cy="50" r="45" fill="none" stroke="${color}" stroke-width="6" stroke-linecap="round" pathLength="1" stroke-dasharray="1"/></svg><div class="v" style="position:absolute;inset:0;display:flex;flex-direction:column;align-items:center;justify-content:center;direction:ltr"></div>`);
  }

  VT.template({
    theme: {
      palette: { bg: '#0A0A0A', deep: '#000000', ink: '#0A0A0A', paper: '#FFFFFF', accent: '#C6FF00', alt: '#FF3D71', text: '#FFFFFF', muted: 'rgba(255,255,255,.6)' },
      captions: { style: 'pill', hl: '#C6FF00', hlText: '#0A0A0A', upper: true },
      transition: 'zoom', sfx: { transition: 'whoosh', transitionGain: -15 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 40%, #1B1F12, #050505 70%)`);
      const lines = VT.el(layer, `inset:-20%;background:repeating-linear-gradient(115deg, rgba(198,255,0,.05) 0 ${0.5 * U}px, transparent ${0.5 * U}px ${7 * U}px)`);
      return (t) => { lines.style.transform = `translateX(${(t * 6 * U) % (7 * U / Math.sin(1.13))}px)`; };
    },
    scenes: {
      // {name, set, reps, at, repEvery, repTimes:[..], seconds, media, cue}
      exercise: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, land = VT.orient === 'landscape';
          const hasM = s.media && VT.hasMedia(s.media);
          const setL = s.set ? VT.el(layer, `background:${VT.col('accent')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${3.8 * U}px;padding:${0.7 * U}px ${2.4 * U}px ${1 * U}px;border-radius:${1.4 * U}px;letter-spacing:.08em;white-space:nowrap`, VT.esc(s.set)) : null;
          const name = VT.text(layer, s.name || '', { w: Z.area.w * 0.94, h: Z.head.h * 0.7, size: 9, color: '#fff', upper: true });
          const body = Z.body;
          const media = hasM ? VT.el(layer, `width:${land ? body.h * 0.9 : body.w}px;height:${land ? body.h * 0.9 : body.h * 0.5}px;border-radius:${3 * U}px;overflow:hidden`) : null;
          const img = hasM ? VT.media(media, s.media, 'left:0;top:0') : null;
          const rs = Math.min(land ? body.h * 0.85 : body.w * 0.72, hasM && !land ? body.h * 0.46 : body.h * 0.85);
          const r = ring(layer, rs, VT.col('accent'));
          const arc = r.querySelector('.a'), val = r.querySelector('.v');
          const at = VT.time(s.at, s.start + 0.4);
          const reps = s.reps || 0, secs = s.seconds || 0;
          let times = [];
          if (reps) times = (s.repTimes && s.repTimes.length ? s.repTimes : Array.from({ length: reps }, (_, i) => at + 0.6 + i * (s.repEvery || 1.2))).map((x) => VT.time(x, at));
          times.forEach((x, i) => VT.cue(x, i === times.length - 1 ? 'success' : 'beep', { gain: i === times.length - 1 ? -12 : -18 }));
          if (secs) { for (let k = 0; k < secs; k++) if (secs - k <= 3) VT.cue(at + 0.6 + k, 'beep', { gain: -16 }); VT.cue(at + 0.6 + secs, 'buzzer', { gain: -14 }); }
          VT.cue(at - 0.05, 'impact', { gain: -11 });
          return (t) => {
            const hp = P(t, s.start + 0.05, 0.4);
            let y = Z.head.y + Z.head.h / 2;
            if (setL) VT.place(setL, VT.W / 2, Z.head.y + setL.offsetHeight / 2, { s: L(0.4, 1, sp(hp)), o: C(hp * 4) });
            VT.place(name, VT.W / 2, y + (setL ? setL.offsetHeight / 2 : 0), { s: L(1.3, 1, eo(hp)), o: C(hp * 3) });
            let cx = VT.W / 2, cy = body.y + body.h / 2;
            if (media) {
              img.update(t - s.start);
              if (land) { VT.place(media, VT.W / 2 - body.w * 0.24 * VT.sign, cy, { o: C(hp * 2) }); cx = VT.W / 2 + body.w * 0.24 * VT.sign; }
              else { VT.place(media, VT.W / 2, body.y + media.offsetHeight / 2, { o: C(hp * 2) }); cy = body.y + media.offsetHeight + 2 * U + rs / 2; }
            }
            const p = P(t, at, 0.45);
            let f = 0, html = '';
            if (reps) {
              let done = 0; times.forEach((x) => { if (t >= x) done++; });
              f = done / reps;
              const last = times[done - 1];
              const bump = last != null ? L(1.3, 1, eo(P(t, last, 0.25))) : 1;
              html = `<div style="font-family:${VT.font('display')};font-weight:900;font-size:${rs * 0.36}px;line-height:1;color:#fff;transform:scale(${bump})">${VT.num(done)}</div><div style="font-family:${VT.font('display')};font-weight:800;font-size:${rs * 0.09}px;color:${VT.col('muted')}">/ ${VT.num(reps)} ${VT.esc(VT.label(s, 'reps', 'REPS'))}</div>`;
            } else if (secs) {
              const el = C((t - at - 0.6) / secs); f = el;
              html = `<div style="font-family:${VT.font('display')};font-weight:900;font-size:${rs * 0.34}px;line-height:1;color:${el > 0.8 ? VT.col('alt') : '#fff'};font-variant-numeric:tabular-nums">${VT.num(Math.ceil(secs * (1 - el)))}</div><div style="font-family:${VT.font('display')};font-weight:800;font-size:${rs * 0.09}px;color:${VT.col('muted')}">${VT.esc(VT.label(s, 'sec', 'SEC'))}</div>`;
            }
            if (val._h !== html) { val.innerHTML = html; val._h = html; }
            arc.setAttribute('stroke-dashoffset', String(1 - f));
            VT.place(r, cx, cy, { s: L(0.6, 1, sp(p)), o: C(p * 4) });
          };
        },
      },
      // {seconds, next, at}
      rest: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, secs = s.seconds || 15;
          const lab = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${10 * U}px;color:#fff;letter-spacing:.1em`, VT.esc(s.label || VT.label(s, 'rest', 'REST')));
          const rs = Math.min(z.w * 0.6, z.h * 0.42), r = ring(layer, rs, VT.col('alt'));
          const nx = s.next ? VT.el(layer, `font-family:${VT.font('display')};font-weight:800;font-size:${4.6 * U}px;color:${VT.col('muted')};white-space:nowrap`, `${VT.esc(VT.label(s, 'next', 'NEXT'))}: <span style="color:${VT.col('accent')}">${VT.esc(s.next)}</span>`) : null;
          if (nx) VT.fit(nx, z.w * 0.92);
          const at = VT.time(s.at, s.start + 0.2), span = Math.max(0.5, s.end - at - 0.3);
          VT.cue(at, 'whoosh-down', { gain: -18 });
          return (t) => {
            const f = C((t - at) / span), cy = z.y + z.h * 0.46;
            r.querySelector('.a').setAttribute('stroke-dashoffset', String(f));
            r.querySelector('.v').innerHTML = `<div style="font-family:${VT.font('display')};font-weight:900;font-size:${rs * 0.3}px;color:#fff">${VT.num(Math.ceil(secs * (1 - f)))}</div>`;
            VT.place(lab, VT.W / 2, cy - rs / 2 - 9 * U, { o: C((t - at) / 0.3) });
            VT.place(r, VT.W / 2, cy, { s: L(0.7, 1, eo(P(t, at, 0.5))) * (1 + Math.sin(t * 3) * 0.01), o: C((t - at) / 0.3) });
            if (nx) VT.place(nx, VT.W / 2, cy + rs / 2 + 7 * U, { o: C((t - at - 0.4) / 0.3) });
          };
        },
      },
      // {text, sub, at}
      done: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const trophy = VT.el(layer, `width:${34 * U}px;height:${34 * U}px`, `<svg viewBox="0 0 100 100" width="100%" height="100%"><path d="M28 12 H72 V38 A22 22 0 0 1 28 38Z" fill="${VT.col('accent')}"/><path d="M28 18 H14 V28 A14 14 0 0 0 30 42 M72 18 H86 V28 A14 14 0 0 1 70 42" stroke="${VT.col('accent')}" stroke-width="6" fill="none"/><rect x="44" y="58" width="12" height="16" fill="${VT.col('accent')}"/><rect x="30" y="74" width="40" height="12" rx="3" fill="${VT.col('accent')}"/></svg>`);
          const tt = VT.text(layer, s.text || VT.label(s, 'done', 'Workout complete!'), { w: z.w * 0.9, h: z.h * 0.25, size: 9, color: '#fff', upper: true });
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.85, size: 4.6, weight: 700, font: 'body', color: VT.col('accent') }) : null;
          const conf = Array.from({ length: 30 }, (_, i) => VT.el(layer, `width:${1.2 * U}px;height:${2.4 * U}px;background:${i % 2 ? VT.col('accent') : VT.col('alt')}`));
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'impact', { gain: -10 }); VT.cue(at + 0.1, 'success', { gain: -10 }); VT.cue(at + 0.2, 'sparkle', { gain: -16 });
          return (t) => {
            const cy = z.y + z.h * 0.4, p = P(t, at, 0.5);
            VT.place(trophy, VT.W / 2, cy, { s: L(0.2, 1, sp(p)), r: Math.sin(t * 3) * 3, o: C(p * 4) });
            const r = VT.rise(t, at + 0.3, 0.45, 4); VT.place(tt, VT.W / 2, cy + 17 * U + tt.offsetHeight / 2 + 3 * U, { y: r.y, o: r.o });
            if (sub) { const r2 = VT.rise(t, at + 0.6, 0.45, 3); VT.place(sub, VT.W / 2, cy + 17 * U + tt.offsetHeight + 8 * U, { y: r2.y, o: r2.o }); }
            conf.forEach((c, i) => { const k = t - at - VT.hash(i) * 0.3; if (k < 0) { c.style.opacity = 0; return; } const a = VT.hash(i + 5) * Math.PI * 2, v = (35 + VT.hash(i + 2) * 50) * U; VT.tf(c, { x: VT.W / 2 + Math.cos(a) * v * k, y: cy + Math.sin(a) * v * k * 0.7 + 70 * U * k * k, r: k * 500 * (VT.hash(i) - 0.5), o: C(1.8 - k) }); });
          };
        },
      },
    },
  });
})();
