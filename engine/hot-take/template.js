/* hot-take - bold opinion: fiery kicker, slammed statement, live poll and a comment CTA. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  VT.template({
    theme: {
      palette: { bg: '#0F0D0C', deep: '#000000', ink: '#141110', paper: '#FFF7EE', accent: '#FF5A1F', hot: '#FFC23D', text: '#FFFFFF', muted: 'rgba(255,255,255,.7)', good: '#34D399', bad: '#FF4D4D' },
      captions: { style: 'pop', hl: '#FF5A1F', hlText: '#FFFFFF', maxWords: 1 },
      transition: 'zoom', sfx: { transition: 'whoosh', transitionGain: -15 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 110%, rgba(255,90,31,.45), rgba(255,90,31,0) 60%),#0F0D0C`);
      const stripes = VT.el(layer, `inset:-${40 * U}px;background:repeating-linear-gradient(-35deg, rgba(255,255,255,.035) 0 ${3 * U}px, transparent ${3 * U}px ${9 * U}px)`);
      const embers = Array.from({ length: 16 }, (_, i) => VT.el(layer, `width:${(0.5 + VT.hash(i) * 0.9) * U}px;height:${(0.5 + VT.hash(i) * 0.9) * U}px;border-radius:50%;background:${i % 3 ? '#FF7A2F' : '#FFC23D'}`));
      return (t) => {
        stripes.style.transform = `translateX(${(t * 3 * U) % (9 * U / Math.sin(0.61))}px)`;
        embers.forEach((e, i) => {
          const sp2 = 6 + VT.hash(i + 2) * 10, life = (VT.H + 20 * U) / (sp2 * U);
          const k = ((t + VT.hash(i + 5) * life) % life) / life;
          VT.tf(e, { x: VT.hash(i + 7) * VT.W + Math.sin(t * 1.3 + i) * 3 * U, y: VT.H + 10 * U - k * (VT.H + 20 * U), o: 0.8 * Math.sin(k * Math.PI) });
        });
      };
    },
    scenes: {
      take: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(z, 96);
          const kick = VT.el(layer, `display:flex;align-items:center;gap:${1.4 * U}px;background:${VT.col('accent')};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${4.4 * U}px;padding:${1 * U}px ${3.2 * U}px ${1.4 * U}px ${2 * U}px;border-radius:${2 * U}px;white-space:nowrap;letter-spacing:.02em`,
            `<span style="width:${5.4 * U}px;height:${5.4 * U}px">${VT.icon('fire', VT.col('hot'))}</span>${VT.esc(s.kicker || VT.label(s, 'kicker', 'Unpopular opinion'))}`);
          const words = String(s.text || '').split(VT.joiner === '' ? '' : /\s+/).filter(Boolean);
          const hl = (s.highlight || []).map((x) => String(x).toLowerCase());
          const box = VT.el(layer, `width:${col.w}px;text-align:center;font-family:${VT.font('display')};font-weight:900;font-size:${12 * U}px;line-height:1.08;color:#fff;direction:${VT.dir}`);
          box.innerHTML = words.map((w) => { const on = hl.some((h) => w.toLowerCase().replace(/[^\p{L}\p{N}]/gu, '') === h.replace(/[^\p{L}\p{N}]/gu, '')); return `<span style="display:inline-block;${on ? `color:${VT.col('hot')};` : ''}">${VT.esc(w)}</span>`; }).join(VT.joiner ? ' ' : '');
          if (s.upper !== false) box.style.textTransform = VT.dir === 'rtl' ? 'none' : 'uppercase';
          VT.fit(box, col.w, z.h * 0.62, 5);
          const spans = Array.from(box.children);
          const at = VT.time(s.at, s.start + 0.5), per = s.stagger || Math.min(0.22, Math.max(0.08, (s.dur || 1.8) / Math.max(1, spans.length)));
          VT.cue(s.start + 0.05, 'riser', { dur: Math.max(0.3, at - s.start - 0.05), gain: -24 }); VT.cue(at - 0.03, 'impact', { gain: -9 }); VT.cue(s.start + 0.1, 'sting', { gain: -18 });
          spans.forEach((sp2, i) => { if (i && i % 3 === 0) VT.cue(at + i * per, 'pop-low', { gain: -22 }); });
          return (t) => {
            const kp = P(t, s.start + 0.05, 0.4);
            const cy = z.y + z.h * 0.52;
            VT.place(kick, VT.W / 2, cy - box.offsetHeight / 2 - 8 * U, { s: L(0.4, 1, sp(kp)), r: L(-10, -3, eo(kp)), o: C(kp * 4) });
            VT.place(box, VT.W / 2, cy, { s: 1 + Math.max(0, 0.04 - (t - at) * 0.02) });
            spans.forEach((e, i) => { const p = P(t, at + i * per, 0.3); e.style.transform = `translateY(${(1 - eo(p)) * 4 * U}px) scale(${L(1.5, 1, eo(p))})`; e.style.opacity = C(p * 3); });
          };
        },
      },
      poll: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, opts = s.options || [];
          const head = VT.text(layer, s.question || '', { w: Z.area.w * 0.92, h: Z.head.h * 0.85, size: 7.6, color: '#fff' });
          const body = VT.clampW(VT.inset(Z.body, 1), 100);
          const rows = VT.rows(body, Math.max(opts.length, 3), 3).slice(0, opts.length);
          const at = VT.time(s.at, s.start + 0.4);
          const max = Math.max(...opts.map((o) => o.pct || 0));
          const els = opts.map((o, i) => {
            const r = rows[i], h = Math.min(r.h, 14 * U);
            const e = VT.el(layer, `width:${r.w}px;height:${h}px;border-radius:${3 * U}px;background:rgba(255,255,255,.1);overflow:hidden;border:${0.35 * U}px solid rgba(255,255,255,.18)`);
            const fill = VT.el(e, `top:0;bottom:0;${VT.dir === 'rtl' ? 'right' : 'left'}:0;width:0;background:${o.pct === max ? `linear-gradient(90deg,${VT.col('accent')},${VT.col('hot')})` : 'rgba(255,255,255,.28)'}`);
            const lab = VT.el(e, `inset:0;display:flex;align-items:center;justify-content:space-between;padding:0 ${3.4 * U}px;font-family:${VT.font('display')};font-weight:800;font-size:${5.2 * U}px;color:#fff`, `<span class="l"></span><span class="n" style="font-size:${5.8 * U}px"></span>`);
            lab.querySelector('.l').textContent = o.label || ''; VT.fit(lab.querySelector('.l'), r.w - 26 * U, h);
            const oa = VT.time(o.at, at + i * 0.25);
            VT.cue(oa, 'pop', { gain: -17 });
            return { e, fill, n: lab.querySelector('.n'), r, h, oa, pct: o.pct || 0, win: o.pct === max };
          });
          const fillAt = VT.time(s.fillAt, (els.length ? els[els.length - 1].oa : at) + 0.5);
          VT.cue(fillAt, 'riser', { dur: 1, gain: -22 }); VT.cue(fillAt + 1.05, 'ding', { gain: -12 });
          return (t) => {
            const hr = VT.rise(t, s.start + 0.05, 0.45, 4); VT.place(head, VT.W / 2, Z.head.y + Z.head.h / 2, { y: hr.y, o: hr.o });
            els.forEach((x) => {
              const p = P(t, x.oa - 0.1, 0.4), f = eo(P(t, fillAt, 1));
              VT.place(x.e, x.r.x + x.r.w / 2, x.r.y + x.r.h / 2, { s: L(0.9, 1, sp(p)) * (x.win && t > fillAt + 1 ? L(1.06, 1.03, eo(P(t, fillAt + 1, 0.4))) : 1), o: C(p * 3) });
              x.fill.style.width = x.pct * f + '%';
              x.n.textContent = VT.num(Math.round(x.pct * f)) + '%';
            });
          };
        },
      },
      cta: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const ic = VT.el(layer, `width:${24 * U}px;height:${24 * U}px;border-radius:${6 * U}px;background:${VT.col('accent')};display:flex;align-items:center;justify-content:center;box-shadow:0 ${1.6 * U}px 0 #7A2305`,
            `<svg viewBox="0 0 70 70" width="62%" height="62%"><path d="M10 14 H60 V46 H30 L18 58 V46 H10Z" fill="#fff" stroke="#fff" stroke-width="4" stroke-linejoin="round"/><circle cx="24" cy="30" r="4" fill="${VT.col('accent')}"/><circle cx="35" cy="30" r="4" fill="${VT.col('accent')}"/><circle cx="46" cy="30" r="4" fill="${VT.col('accent')}"/></svg>`);
          const tx = VT.text(layer, s.text || VT.label(s, 'cta', 'Agree or disagree?'), { w: z.w * 0.9, h: z.h * 0.3, size: 10, color: '#fff' });
          const sub = VT.text(layer, s.sub || VT.label(s, 'ctaSub', 'Tell me in the comments'), { w: z.w * 0.9, size: 5.4, weight: 700, font: 'body', color: VT.col('hot') });
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-high', { gain: -12 }); VT.cue(at + 0.5, 'notify', { gain: -14 });
          return (t) => {
            const cy = z.y + z.h * 0.46, p = P(t, at, 0.5);
            VT.place(ic, VT.W / 2, cy - tx.offsetHeight / 2 - 16 * U, { s: L(0.2, 1, sp(p)), r: Math.sin(t * 5) * 4, y: Math.sin(t * 3) * U, o: C(p * 4) });
            const r = VT.rise(t, at + 0.2, 0.45, 5); VT.place(tx, VT.W / 2, cy, { y: r.y, o: r.o });
            const r2 = VT.rise(t, at + 0.55, 0.45, 4); VT.place(sub, VT.W / 2, cy + tx.offsetHeight / 2 + 6 * U, { y: r2.y, o: r2.o });
          };
        },
      },
    },
  });
})();
