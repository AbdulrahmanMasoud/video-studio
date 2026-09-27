/* quiz - question card, answer options, countdown ring and a satisfying reveal. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const LET = ['A', 'B', 'C', 'D', 'E', 'F'];

  function chip(layer, text, bg, fg) {
    const U = VT.U;
    return VT.el(layer, `background:${bg};color:${fg};font-family:${VT.font('display')};font-weight:800;font-size:${3.6 * U}px;padding:${1 * U}px ${3 * U}px ${1.4 * U}px;border-radius:${4 * U}px;white-space:nowrap`, VT.esc(text));
  }

  VT.template({
    theme: {
      palette: { bg: '#5B2BD9', deep: '#34138F', ink: '#1A0B40', paper: '#FFFFFF', accent: '#FFD23F', good: '#22C55E', bad: '#F2555A', text: '#FFFFFF', muted: 'rgba(255,255,255,.75)' },
      captions: { style: 'pill', hl: '#FFD23F', hlText: '#1A0B40', color: '#FFFFFF', shadow: 'rgba(26,11,64,.6)' },
      transition: 'zoom', sfx: { transition: 'whoosh', transitionGain: -16 }, zones: { head: 0.2 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:radial-gradient(ellipse at 50% 30%, ${VT.col('bg')}, ${VT.col('deep')} 85%)`);
      const marks = Array.from({ length: 9 }, (_, i) => VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${(10 + VT.hash(i) * 22) * U}px;color:rgba(255,255,255,.07);line-height:1`, '?'));
      return (t) => marks.forEach((m, i) => {
        const x = VT.hash(i + 3) * VT.W, y = ((VT.hash(i + 9) * VT.H - t * (8 + i * 2) * U) % (VT.H + 30 * U) + VT.H + 30 * U) % (VT.H + 30 * U) - 15 * U;
        VT.place(m, x, y, { r: Math.sin(t * 0.6 + i) * 14 });
      });
    },
    scenes: {
      question: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z.full;
          const qn = ctx.scenes.filter((x) => x.type === 'question').indexOf(s) + 1;
          const lab = chip(layer, s.label || `${VT.label(s, 'question', 'Question')} ${VT.num(qn)}`, VT.col('accent'), VT.col('ink'));
          const opts = s.options || [];
          const LET = VT.graphemes(VT.label(s, 'letters', 'ABCDEF'));
          const land = VT.orient !== 'portrait';
          const col = VT.clampW(z, land ? 150 : 94);
          const qh = land ? z.h * 0.3 : z.h * 0.3;
          const qcard = VT.card(layer, { css: `width:${col.w}px;padding:${4 * U}px ${5 * U}px;font-family:${VT.font('display')};font-weight:800;font-size:${7.2 * U}px;line-height:1.2;text-align:center` });
          qcard.textContent = s.q || s.question || ''; VT.fit(qcard, col.w, qh, 3);
          // countdown ring
          const R = 6.4 * U;
          const ring = VT.el(layer, `width:${2 * R + 2 * U}px;height:${2 * R + 2 * U}px;border-radius:50%;background:${VT.col('ink')};display:flex;align-items:center;justify-content:center;box-shadow:0 ${U}px 0 ${VT.col('deep')}`,
            `<svg viewBox="0 0 100 100" style="position:absolute;inset:0;width:100%;height:100%;transform:rotate(-90deg)"><circle cx="50" cy="50" r="42" stroke="rgba(255,255,255,.15)" stroke-width="9" fill="none"/><circle class="arc" cx="50" cy="50" r="42" stroke="${VT.col('accent')}" stroke-width="9" fill="none" stroke-linecap="round" pathLength="1" stroke-dasharray="1"/></svg><b style="position:relative;font-family:${VT.font('display')};font-size:${5.6 * U}px;color:#fff"></b>`);
          const arc = ring.querySelector('.arc'), num = ring.querySelector('b');
          // options
          const top = z.y + 8 * U + qh + 4 * U;
          const area = { x: col.x, y: top, w: col.w, h: z.y + z.h - top };
          const grid = land && opts.length === 4;
          const cells = grid ? [].concat(...VT.rows(area, 2, 2.4).map((r) => VT.cols(r, 2, 2.4))) : VT.rows(area, Math.max(opts.length, 3), 2).slice(0, opts.length);
          const at = VT.time(s.at, s.start + 0.2);
          const els = opts.map((o, i) => {
            const c = cells[i], h = Math.min(c.h, 13 * U);
            const e = VT.card(layer, { css: `width:${c.w}px;height:${h}px;display:flex;align-items:center;gap:${2.6 * U}px;padding:0 ${3 * U}px;font-family:${VT.font('display')};font-weight:800` });
            e.innerHTML = `<div class="b" style="flex:none;width:${8.4 * U}px;height:${8.4 * U}px;border-radius:${2.4 * U}px;background:${VT.col('bg')};color:#fff;display:flex;align-items:center;justify-content:center;font-size:${4.6 * U}px">${LET[i]}</div><div class="t" style="flex:1;min-width:0;font-size:${5.4 * U}px;line-height:1.15"></div>`;
            const tx = e.querySelector('.t'); tx.textContent = typeof o === 'string' ? o : o.text; VT.fit(tx, null, h - 2 * U, 2.6);
            const oa = VT.time(o.at, VT.time(s.optionsAt, at + 0.7) + i * 0.28);
            VT.cue(oa, 'pop', { gain: -17, pan: (i % 2 ? 0.25 : -0.25) });
            return { e, b: e.querySelector('.b'), c, h, oa };
          });
          const lastOpt = els.length ? els[els.length - 1].oa : at;
          const cdA = VT.time(s.countdownAt, lastOpt + 0.6), secs = s.seconds || 3;
          const rev = VT.time(s.revealAt, cdA + secs);
          const ans = s.answer == null ? 0 : s.answer;
          if (s.countdown !== false) for (let k = 0; k < secs; k++) VT.cue(cdA + (k * (rev - cdA)) / secs, k % 2 ? 'tock' : 'tick', { gain: -12 });
          VT.cue(rev, 'success', { gain: -10 }); VT.cue(rev + 0.05, 'sparkle', { gain: -18 });
          VT.cue(at, 'pop-low', { gain: -12 });
          return (t) => {
            const lp = P(t, s.start + 0.05, 0.4);
            VT.place(lab, VT.W / 2, z.y + 3.5 * U, { s: L(0.5, 1, sp(lp)), o: C(lp * 4) });
            const qp = P(t, at, 0.5);
            VT.place(qcard, VT.W / 2, z.y + 8 * U + qh / 2, { s: L(0.85, 1, sp(qp)), o: C(qp * 4) });
            // ring sits on the card's corner
            const cp = P(t, cdA - 0.3, 0.35), done = P(t, rev, 0.25);
            const f = C((t - cdA) / Math.max(0.1, rev - cdA));
            arc.setAttribute('stroke-dashoffset', String(f));
            arc.setAttribute('stroke', f > 0.66 ? VT.col('bad') : VT.col('accent'));
            num.textContent = t < rev ? VT.num(Math.max(1, Math.ceil(secs * (1 - f)))) : '✓';
            const pulse = t > cdA && t < rev ? 1 + 0.08 * Math.max(0, 1 - ((t - cdA) * secs / (rev - cdA)) % 1 * 4) : 1;
            const cx = VT.W / 2 + (qcard.offsetWidth / 2 - 2 * U) * VT.sign, cy = z.y + 8 * U + qh / 2 - qcard.offsetHeight / 2;
            if (s.countdown !== false) VT.place(ring, cx, cy, { s: L(0.2, 1, sp(cp)) * pulse * (1 - done * 0.2), o: C(cp * 4) * (1 - done) });
            else ring.style.opacity = 0;
            els.forEach((x, i) => {
              const p = P(t, x.oa - 0.1, 0.45), r = t >= rev;
              const good = i === ans;
              const shake = r && !good && t < rev + 0.3 ? Math.sin(t * 80) * 0.6 * U : 0;
              x.e.style.background = r && good ? VT.col('good') : VT.col('paper');
              x.e.style.color = r && good ? '#fff' : VT.col('ink');
              x.b.style.background = r ? (good ? '#fff' : VT.col('bad')) : VT.col('bg');
              x.b.innerHTML = r ? VT.icon(good ? 'check' : 'x', good ? VT.col('good') : '#fff', '62%') : LET[i];
              const rp = P(t, rev, 0.45);
              VT.place(x.e, x.c.x + x.c.w / 2 + (1 - eo(p)) * 30 * U * VT.sign + shake, x.c.y + x.c.h / 2,
                { s: (L(0.9, 1, sp(p))) * (r ? (good ? L(1.12, 1.04, eo(rp)) : 0.96) : 1), o: C(p * 4) * (r && !good ? L(1, 0.45, rp) : 1) });
            });
          };
        },
      },
      explain: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(z, 96);
          const k = VT.card(layer, { css: `width:${col.w}px;padding:${11 * U}px ${5 * U}px ${5 * U}px;text-align:center` });
          k.innerHTML = `<div class="h" style="font-family:${VT.font('display')};font-weight:900;font-size:${6.4 * U}px;color:${VT.col('bg')};margin-bottom:${2 * U}px"></div><div class="b" style="font-family:${VT.font('body')};font-weight:600;font-size:${5 * U}px;line-height:1.4"></div>`;
          k.querySelector('.h').textContent = s.title || VT.label(s, 'why', 'Why?');
          k.querySelector('.b').textContent = s.text || '';
          VT.fit(k, col.w, z.h * 0.8, 3);
          const ic = VT.badge(layer, s.icon || 'bolt', VT.col('accent'), VT.col('ink'), 15);
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'pop-low', { gain: -12 }); VT.cue(at + 0.25, 'sparkle', { gain: -20 });
          return (t) => {
            const p = P(t, at, 0.5), cy = z.y + z.h * 0.5;
            VT.place(k, VT.W / 2, cy, { y: (1 - eo(p)) * 10 * U, o: C(p * 3) });
            const q = P(t, at + 0.2, 0.5);
            VT.place(ic, VT.W / 2, cy - k.offsetHeight / 2, { s: L(0.2, 1, sp(q)), r: L(-40, 0, eo(q)), o: C(q * 4) });
          };
        },
      },
      score: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const big = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${Math.min(38 * U, z.h * 0.35)}px;color:${VT.col('accent')};line-height:1;text-shadow:0 ${2 * U}px 0 ${VT.col('deep')};white-space:nowrap`);
          const tx = VT.text(layer, s.text || VT.label(s, 'score', 'How many did you get?'), { w: z.w * 0.9, size: 7, color: '#fff' });
          const at = VT.time(s.at, s.start + 0.3), n = s.total || 3;
          VT.cue(at, 'drumroll', { dur: 0.8, gain: -16 }); VT.cue(at + 0.9, 'impact', { gain: -10 });
          return (t) => {
            const f = C((t - at) / 0.9); big.textContent = `${VT.num(Math.round(eo(f) * (s.score == null ? n : s.score)))}/${VT.num(n)}`;
            VT.place(big, VT.W / 2, z.y + z.h * 0.42, { s: L(0.6, 1, sp(P(t, at, 0.5))), o: C((t - at) / 0.15) });
            const r = VT.rise(t, at + 1, 0.4, 4); VT.place(tx, VT.W / 2, z.y + z.h * 0.42 + big.offsetHeight / 2 + 7 * U, { y: r.y, o: r.o });
          };
        },
      },
    },
  });
})();
