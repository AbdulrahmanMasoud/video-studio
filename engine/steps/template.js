/* steps - numbered tips with a progress tracker, typed prompt cards, lists and toggles. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const ICONS = {
    robot: (c) => `<svg viewBox="0 0 400 400" width="100%" height="100%"><line x1="200" y1="70" x2="200" y2="22" stroke="${c.paper}" stroke-width="14" stroke-linecap="round"/><circle cx="200" cy="20" r="20" fill="${c.accent}"/><rect x="30" y="66" width="340" height="300" rx="90" fill="${c.deep}"/><rect x="30" y="50" width="340" height="300" rx="90" fill="${c.paper}"/><rect class="eye" x="112" y="150" width="54" height="96" rx="27" fill="${c.ink}"/><rect class="eye" x="234" y="150" width="54" height="96" rx="27" fill="${c.ink}"/><path d="M160 290 Q200 320 240 290" stroke="${c.ink}" stroke-width="14" fill="none" stroke-linecap="round"/></svg>`,
    bulb: (c) => `<svg viewBox="0 0 400 400" width="100%" height="100%"><circle cx="200" cy="170" r="120" fill="${c.accent}"/><rect x="150" y="280" width="100" height="60" rx="16" fill="${c.paper}"/><rect x="165" y="345" width="70" height="26" rx="12" fill="${c.deep}"/><path d="M170 200 L200 150 L230 200" stroke="${c.ink}" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`,
    question: (c) => `<svg viewBox="0 0 400 400" width="100%" height="100%"><circle cx="200" cy="200" r="170" fill="${c.paper}"/><path d="M150 150 Q150 95 200 95 Q255 95 255 150 Q255 190 205 210 L205 250" stroke="${c.ink}" stroke-width="34" fill="none" stroke-linecap="round"/><circle cx="205" cy="310" r="22" fill="${c.ink}"/></svg>`,
    star: (c) => `<svg viewBox="0 0 400 400" width="100%" height="100%"><path d="M200 30 L245 150 L372 155 L272 232 L308 356 L200 285 L92 356 L128 232 L28 155 L155 150Z" fill="${c.accent}" stroke="${c.deep}" stroke-width="10" stroke-linejoin="round"/></svg>`,
  };

  function card(layer, css) { return VT.el(layer, `background:${VT.col('paper')};color:${VT.col('ink')};border-radius:${3.6 * VT.U}px;box-shadow:0 ${1.6 * VT.U}px 0 ${VT.col('deep')};` + css); }
  function badge(layer, ok) {
    const U = VT.U, s = 12 * U;
    return VT.el(layer, `width:${s}px;height:${s}px;border-radius:50%;background:${VT.col(ok ? 'good' : 'bad')};display:flex;align-items:center;justify-content:center;box-shadow:0 ${U}px 0 ${VT.col('deep')}`,
      ok ? `<svg viewBox="0 0 70 70" width="55%" height="55%"><path d="M12 36 L28 52 L58 18" stroke="${VT.col('ink')}" stroke-width="12" fill="none" stroke-linecap="round" stroke-linejoin="round"/></svg>`
        : `<svg viewBox="0 0 80 80" width="50%" height="50%"><path d="M16 16 L64 64 M64 16 L16 64" stroke="#fff" stroke-width="14" stroke-linecap="round"/></svg>`);
  }

  // Card builders used inside a step. Each returns render(t).
  const CARDS = {
    prompt(c, layer, box, s) {
      const U = VT.U;
      const w = Math.min(box.w, 92 * U);
      const k = card(layer, `width:${w}px;padding:${3.6 * U}px ${4 * U}px ${5 * U}px;font-family:${VT.font('body')};font-weight:500;font-size:${4.9 * U}px;line-height:1.55;min-height:${22 * U}px`);
      k.innerHTML = `<div style="font-family:${VT.font('display')};font-weight:600;font-size:${2.6 * U}px;opacity:.55;margin-bottom:${U}px">${VT.esc(c.label || VT.label(s, 'prompt', 'Message'))}</div><div class="tx"></div>`;
      const tx = k.querySelector('.tx');
      const bad = c.bad, good = c.good || {};
      const bA = bad ? VT.time(bad.at, s.start + 0.8) : 0, bB = bad ? VT.time(bad.end, bA + 0.9) : 0;
      const gA = VT.time(good.at, bad ? bB + 0.5 : s.start + 0.8), gB = VT.time(good.end, gA + Math.max(1, (good.text || '').length * 0.05));
      const stamp = bad ? VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${6 * U}px;padding:${U}px ${3 * U}px;border:${0.8 * U}px solid ${VT.col('bad')};color:${VT.col('bad')};background:${VT.col('paper')};border-radius:${2 * U}px;white-space:nowrap`, VT.esc(bad.stamp || VT.label(s, 'unclear', 'Unclear'))) : null;
      const ok = badge(layer, true);
      const hls = (c.highlights || []).map((h) => ({ text: h.text, at: VT.time(h.at, gA) }));
      if (bad) { VT.typingCue(bA, bB); VT.cue(bB + 0.3, 'error', { gain: -13 }); VT.cue(gA - 0.1, 'scratch', { gain: -22 }); }
      VT.typingCue(gA, gB, -25);
      hls.forEach((h) => VT.cue(h.at + 0.05, 'scratch', { gain: -28, pan: 0.3 }));
      VT.cue(gB + 0.15, 'ding', { gain: -13 });
      const cx = box.x + box.w / 2, cy = box.y + box.h * 0.46;
      return (t) => {
        const r = VT.rise(t, (bad ? bA : gA) - 0.35, 0.45, 8);
        let html;
        if (bad && t < gA - 0.05) html = VT.esc(VT.type(bad.text, t, bA, bB));
        else {
          let str = VT.esc(VT.type(good.text || '', t, gA, gB));
          hls.forEach((h) => { const e = VT.esc(h.text); if (str.includes(e)) { const p = C((t - h.at) / 0.35) * 100; str = str.replace(e, `<span style="background:linear-gradient(transparent 12%,${VT.col('accent')} 12%,${VT.col('accent')} 92%,transparent 92%) no-repeat ${VT.dir === 'rtl' ? 'right' : 'left'}/${p}% 100%;border-radius:${0.6 * U}px">${e}</span>`); } });
          html = str;
        }
        tx.innerHTML = html + VT.caret(t, VT.col('bg'));
        const shake = bad && t > bB + 0.3 && t < bB + 0.55 ? Math.sin(t * 90) * 1.2 * U : 0;
        VT.place(k, cx + shake, cy, { y: r.y, o: r.o });
        if (stamp) { const p = P(t, bB + 0.3, 0.3), q = P(t, gA - 0.1, 0.2); VT.place(stamp, cx + w * 0.22 * VT.sign, cy + k.offsetHeight * 0.55, { s: L(2, 1, eo(p)), r: -10, o: C(p * 4) * (1 - q) }); }
        const pk = P(t, gB + 0.15, 0.45);
        VT.place(ok, cx - (w / 2 - 2 * U) * VT.sign, cy - k.offsetHeight / 2, { s: L(0.2, 1, sp(pk)), o: C(pk * 4) });
      };
    },
    list(c, layer, box, s) {
      const U = VT.U, items = c.items || [];
      const rows = VT.rows(VT.clampW(box, 92), Math.max(items.length, 3), 2.2).slice(0, items.length);
      const els = items.map((it, i) => {
        const e = card(layer, `display:flex;align-items:center;gap:${3 * U}px;padding:0 ${4 * U}px;font-family:${VT.font('display')};font-weight:800;`);
        e.style.width = rows[i].w + 'px'; e.style.height = Math.min(rows[i].h, 17 * U) + 'px';
        e.innerHTML = `<div style="flex:none;width:${9 * U}px;height:${9 * U}px;border-radius:${2.4 * U}px;background:${VT.col('bg')};color:${VT.col('paper')};display:flex;align-items:center;justify-content:center;font-size:${5 * U}px">${VT.esc(it.icon || VT.num(i + 1))}</div><div class="t" style="flex:1;min-width:0;font-size:${6.2 * U}px;line-height:1.15"></div>`;
        const t = e.querySelector('.t'); t.textContent = it.text; VT.fit(t, null, Math.min(rows[i].h, 17 * U) - 2 * U, 3);
        const at = VT.time(it.at, s.start + 0.6 + i * 0.5); VT.cue(at - 0.05, 'pop', { gain: -15, pan: (i % 2 ? 0.3 : -0.3) });
        return { e, at, row: rows[i], r: i % 2 ? 2 : -2 };
      });
      return (t) => els.forEach((x) => { const p = P(t, x.at - 0.12, 0.5); VT.place(x.e, x.row.x + x.row.w / 2 + (1 - eo(p)) * -40 * U * VT.sign, x.row.y + x.row.h / 2, { r: x.r * eo(p), s: L(0.9, 1, sp(p)), o: C(p * 4) }); });
    },
    toggles(c, layer, box, s) {
      const U = VT.U, items = c.items || [];
      const rows = VT.rows(VT.clampW(box, 92), Math.max(items.length, 3), 3).slice(0, items.length);
      const els = items.map((it, i) => {
        const h = Math.min(rows[i].h, 15 * U), e = card(layer, `width:${rows[i].w}px;height:${h}px;font-family:${VT.font('display')};font-weight:800;`);
        const iw = (rows[i].w - 4 * U) / 2;
        e.innerHTML = `<div class="k" style="position:absolute;top:${1.6 * U}px;width:${iw}px;height:${h - 3.2 * U}px;border-radius:${2.6 * U}px;background:${VT.col('accent')}"></div>` +
          [it.a, it.b].map((x, j) => `<div style="position:absolute;top:0;height:100%;width:${iw}px;${(j === 0) === (VT.dir === 'rtl') ? 'right' : 'left'}:${2 * U}px;display:flex;align-items:center;justify-content:center;font-size:${5.4 * U}px">${VT.esc(x)}</div>`).join('');
        const at = VT.time(it.at, s.start + 0.6 + i * 0.8), flip = VT.time(it.flipAt, at + 0.6);
        VT.cue(at - 0.08, 'pop', { gain: -15 }); VT.cue(flip + 0.05, 'click', { gain: -12 });
        return { e, k: e.querySelector('.k'), at, flip, row: rows[i], iw };
      });
      return (t) => els.forEach((x) => {
        const p = P(t, x.at - 0.12, 0.45); VT.place(x.e, x.row.x + x.row.w / 2, x.row.y + x.row.h / 2, { s: L(0.6, 1, sp(p)), o: C(p * 4) });
        const f = VT.eio(P(t, x.flip + 0.05, 0.28)); const side = VT.dir === 'rtl' ? 'right' : 'left';
        x.k.style.left = x.k.style.right = ''; x.k.style[side] = (2 * U + f * x.iw) + 'px';
      });
    },
    text(c, layer, box, s) {
      const U = VT.U, w = Math.min(box.w, 92 * U);
      const k = card(layer, `width:${w}px;padding:${5 * U}px;font-family:${VT.font('display')};font-weight:800;font-size:${7 * U}px;line-height:1.3;text-align:center`);
      k.textContent = c.text || ''; VT.fit(k, w, box.h * 0.9, 3);
      const at = VT.time(c.at, s.start + 0.6); VT.cue(at, 'pop', { gain: -15 });
      return (t) => { const p = P(t, at - 0.1, 0.5); VT.place(k, box.x + box.w / 2, box.y + box.h * 0.45, { s: L(0.8, 1, sp(p)), o: C(p * 4) }); };
    },
  };

  VT.template({
    theme: {
      palette: { bg: '#2B39E8', deep: '#1B25A6', ink: '#0F1238', paper: '#F6F4FF', accent: '#FFE04A', good: '#1FD18A', bad: '#FF5A4E', text: '#FFFFFF', muted: 'rgba(255,255,255,.78)' },
      captions: { style: 'pill', hl: '#FFE04A', hlText: '#0F1238', color: '#FFFFFF', shadow: 'rgba(15,18,56,.55)' },
      transition: 'slide', sfx: { transition: 'whoosh', transitionGain: -15 }, zones: { head: 0.22 },
    },
    background(layer) {
      const U = VT.U;
      const dots = VT.el(layer, `inset:-${8 * U}px;background-image:radial-gradient(rgba(255,255,255,.11) ${0.25 * U}px,transparent ${0.3 * U}px);background-size:${5.4 * U}px ${5.4 * U}px`);
      const glow = VT.el(layer, `width:${140 * U}px;height:${140 * U}px;border-radius:50%;background:radial-gradient(circle,rgba(130,145,255,.5),rgba(43,57,232,0) 65%)`);
      return (t) => { dots.style.transform = `translate(${(t * 0.9 * U) % (5.4 * U)}px,${(-t * 1.4 * U) % (5.4 * U)}px)`; VT.place(glow, VT.W / 2 + Math.sin(t * 0.35) * 18 * U, VT.H * 0.45 + Math.cos(t * 0.27) * 22 * U); };
    },
    scenes: {
      hook: {
        build(s, layer) {
          const U = VT.U, z = VT.Z;
          const title = VT.el(layer, `background:${VT.col('ink')};color:${VT.col('accent')};font-family:${VT.font('display')};font-weight:800;font-size:${5.6 * U}px;padding:${1.6 * U}px ${4 * U}px ${2.4 * U}px;border-radius:${3 * U}px;max-width:${z.area.w * 0.92}px;text-align:center`);
          title.textContent = s.title || ''; VT.fit(title, z.area.w * 0.92, 20 * U, 3);
          const ic = s.icon === 'none' ? null : VT.el(layer, `width:${40 * U}px;height:${40 * U}px`, (ICONS[s.icon] || ICONS.robot)(VT.pal));
          const at = VT.time(s.at, s.start);
          VT.cue(at + 0.05, 'pop-low', { gain: -10 });
          (s.beats || []).forEach((b) => VT.cue(VT.time(b.at, at), b.kind === 'confused' ? 'error' : 'sparkle', { gain: -15 }));
          return (t) => {
            const p = sp(P(t, at, 0.5));
            VT.place(title, VT.W / 2, z.head.y + z.head.h * 0.45, { s: L(0.7, 1, p), o: C((t - at) / 0.12) });
            if (ic) {
              let r = 0, s2 = 1;
              (s.beats || []).forEach((b) => { const bt = VT.time(b.at, at); if (b.kind === 'confused' && t > bt) r = L(0, -8, eo(P(t, bt, 0.3))); if (b.kind !== 'confused') s2 += 0.12 * Math.max(0, 1 - Math.abs(t - bt - 0.15) / 0.3); });
              VT.place(ic, VT.W / 2, z.body.y + z.body.h * 0.48 + Math.sin(t * 3) * U, { s: L(0.3, 1, sp(P(t, at + 0.05, 0.6))) * s2, r, o: C((t - at) / 0.1) });
              const eyes = ic.querySelectorAll('.eye'); const blink = (t % 3.1) > 2.95 ? 0.15 : 1;
              eyes.forEach((e) => { e.setAttribute('height', 96 * blink); e.setAttribute('y', 150 + 48 * (1 - blink)); });
            }
          };
        },
      },
      count: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const n = VT.el(layer, `font-family:${VT.font('display')};font-weight:900;font-size:${Math.min(60 * U, z.h * 0.45)}px;line-height:1;color:${VT.col('accent')};text-shadow:0 ${2.4 * U}px 0 ${VT.col('deep')}`, VT.esc(s.n != null ? VT.num(s.n) : '3'));
          const tx = VT.text(layer, s.text || '', { w: z.w * 0.92, size: 7.4, weight: 800, color: VT.col('text') });
          const at = VT.time(s.at, s.start + 0.4), ta = VT.time(s.textAt, at + 0.6);
          VT.cue(at - 0.8, 'riser', { gain: -22, dur: 0.8 }); VT.cue(at - 0.06, 'impact', { gain: -7 }); VT.cue(ta - 0.1, 'swoosh', { gain: -22 });
          return (t) => {
            const p = P(t, at - 0.06, 0.5), sh = t > at && t < at + 0.25 ? Math.sin(t * 120) * U * (1 - (t - at) / 0.25) : 0;
            VT.place(n, VT.W / 2 + sh, z.y + z.h * 0.4, { s: L(2.6, 1, eo(C(p * 1.6))), o: C((t - at + 0.06) / 0.08) });
            const r = VT.rise(t, ta - 0.2, 0.45, 5); VT.place(tx, VT.W / 2, z.y + z.h * 0.4 + n.offsetHeight * 0.5 + 6 * U, { y: r.y, o: r.o });
          };
        },
      },
      step: {
        build(s, layer, ctx) {
          const U = VT.U, z = VT.Z;
          const head = VT.el(layer, `width:${z.area.w}px;display:flex;flex-direction:column;align-items:center;gap:${1.8 * U}px`);
          const num = VT.el(head, `position:relative;width:${13 * U}px;height:${13 * U}px;border-radius:50%;background:${VT.col('accent')};color:${VT.col('ink')};font-family:${VT.font('display')};font-weight:900;font-size:${7.6 * U}px;display:flex;align-items:center;justify-content:center;box-shadow:0 ${U}px 0 ${VT.col('deep')}`, VT.esc(s.n != null ? (typeof s.n === 'number' ? VT.num(s.n) : s.n) : VT.num((ctx.scenes.filter((x) => x.type === 'step').indexOf(s)) + 1)));
          const tt = VT.el(head, `position:relative;font-family:${VT.font('display')};font-weight:800;font-size:${8.4 * U}px;line-height:1.15;text-align:center;color:${VT.col('text')};max-width:${z.area.w * 0.94}px`);
          tt.textContent = s.title || ''; VT.fit(tt, z.area.w * 0.94, z.head.h - 25 * U, 3);
          const box = { x: z.body.x, y: z.body.y + 2 * U, w: z.body.w, h: z.body.h - 2 * U };
          const c = s.card || {};
          const r = (CARDS[c.kind] || CARDS.text)(c, layer, box, s);
          VT.cue(s.start + 0.08, 'pop-low', { gain: -11 });
          return (t) => {
            const np = P(t, s.start + 0.05, 0.45), hp = P(t, s.start + 0.2, 0.45);
            VT.place(head, VT.W / 2, z.head.y + 8 * U + (z.head.h - 8 * U) / 2);
            num.style.transform = `scale(${L(0.2, 1, sp(np))}) rotate(${L(-90, 0, eo(np))}deg)`;
            tt.style.transform = `translateY(${(1 - eo(hp)) * 5 * U}px)`; tt.style.opacity = C(hp * 3);
            r(t);
          };
        },
      },
      outro: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full;
          const kick = s.kicker ? VT.text(layer, s.kicker, { w: z.w * 0.9, size: 12, weight: 900, color: VT.col('text') }) : null;
          const w = Math.min(z.w, 92 * U);
          const k = card(layer, `width:${w}px;padding:${5 * U}px ${4 * U}px ${6 * U}px;text-align:center`);
          k.innerHTML = (s.label ? `<div style="font-family:${VT.font('display')};font-weight:700;font-size:${4.6 * U}px;opacity:.55;margin-bottom:${U}px">${VT.esc(s.label)}</div>` : '') + `<div class="b" style="font-family:${VT.font('display')};font-weight:900;font-size:${10 * U}px;line-height:1.25"></div>`;
          const b = k.querySelector('.b');
          const cta = s.cta ? VT.text(layer, s.cta, { w: z.w * 0.9, size: 4.4, weight: 700, color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.3), ta = VT.time(s.textAt, at + 0.2), strike = VT.time(s.strikeAt, null);
          const txt = s.text || '', hl = s.highlight || '';
          if (strike != null) VT.cue(strike, 'scratch', { gain: -14 });
          VT.cue(ta - 0.1, 'impact', { gain: -15 }); VT.typingCue(ta, ta + 0.6, -24); VT.cue(ta + 0.8, 'success', { gain: -11 });
          if (cta) VT.cue(ta + 1.4, 'pop', { gain: -18 });
          return (t) => {
            let y0 = z.y + z.h * 0.45;
            if (kick) {
              const p = P(t, s.start + 0.1, 0.45), out = ei(P(t, ta - 0.25, 0.3));
              VT.place(kick, VT.W / 2, z.y + z.h * 0.3 - out * 10 * U, { s: L(0.5, 1, sp(p)), o: C(p * 4) * (1 - out) });
              if (strike != null) kick.style.textDecoration = t > strike ? `line-through ${0.8 * U}px ${VT.col('bad')}` : 'none';
            }
            const typed = VT.type(txt, t, ta, ta + Math.max(0.5, VT.graphemes(txt).length * 0.04));
            let html = VT.esc(typed);
            if (hl && typed.includes(hl)) html = html.replace(VT.esc(hl), `<span style="background:linear-gradient(transparent 12%,${VT.col('accent')} 12%,${VT.col('accent')} 92%,transparent 92%) no-repeat ${VT.dir === 'rtl' ? 'right' : 'left'}/${C((t - ta - 0.3) / 0.4) * 100}% 100%;border-radius:${U}px;padding:0 ${0.6 * U}px">${VT.esc(hl)}</span>`);
            b.innerHTML = html + VT.caret(t, VT.col('bg'));
            const fp = P(t, ta - 0.15, 0.45);
            VT.place(k, VT.W / 2, y0, { y: (1 - eo(fp)) * 12 * U, s: L(0.85, 1, sp(fp)), o: C(fp * 4) });
            if (cta) { const c = VT.rise(t, ta + 1.4, 0.5, 4); VT.place(cta, VT.W / 2, y0 + k.offsetHeight / 2 + 7 * U, { y: c.y, o: c.o }); }
          };
        },
      },
    },
    overlays: [
      function tracker(layer) {
        const steps = VT.plan.scenes.filter((s) => s.type === 'step');
        if (steps.length < 2) return null;
        const U = VT.U, z = VT.Z;
        const bar = VT.el(layer, `left:${z.area.x}px;width:${z.area.w}px;top:${z.area.y}px;display:flex;justify-content:center;gap:${1.4 * U}px;flex-wrap:nowrap`);
        const pills = steps.map((s, i) => {
          const e = VT.el(bar, `position:relative;height:${6.4 * U}px;padding:0 ${2.4 * U}px 0 ${1.2 * U}px;border-radius:${4 * U}px;display:flex;align-items:center;gap:${U}px;font-family:${VT.font('display')};font-weight:700;font-size:${3 * U}px;white-space:nowrap`,
            `<b style="width:${4.2 * U}px;height:${4.2 * U}px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:${2.5 * U}px">${VT.esc(typeof s.n === 'string' ? s.n : VT.num(i + 1))}</b>${VT.esc(s.short || '')}`);
          return { e, b: e.querySelector('b'), s };
        });
        VT.fit(bar, z.area.w, 8 * U);
        const first = steps[0].start, last = steps[steps.length - 1].end;
        return (t) => {
          const vis = t >= first && t <= last + 0.3; bar.style.opacity = vis ? eo(P(t, first, 0.4)) * (1 - ei(P(t, last, 0.3))) : 0;
          pills.forEach((p) => {
            const on = t >= p.s.start + 0.2 && t < p.s.end + 0.1, done = t >= p.s.end + 0.1;
            p.e.style.background = on ? VT.col('accent') : done ? 'rgba(255,255,255,.22)' : 'rgba(255,255,255,.12)';
            p.e.style.color = on ? VT.col('ink') : done ? '#fff' : 'rgba(255,255,255,.55)';
            p.b.style.background = on ? VT.col('ink') : done ? VT.col('good') : 'rgba(255,255,255,.18)';
            p.b.style.color = on ? VT.col('accent') : VT.col('ink');
            p.e.style.transform = `scale(${on ? L(1.2, 1, sp(P(t, p.s.start + 0.2, 0.35))) : 1})`;
          });
        };
      },
    ],
  });
})();
