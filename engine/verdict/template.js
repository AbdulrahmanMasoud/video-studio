/* verdict - myth vs fact: the claim gets stamped, the truth slides in, reasons stack up. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;

  function claimCard(layer, kind, text, w) {
    const U = VT.U, good = kind === 'fact';
    const c = VT.card(layer, { bg: good ? VT.col('paper') : VT.col('paper2'), fg: VT.col('ink'), css: `width:${w}px;padding:${8 * U}px ${5 * U}px ${5 * U}px;text-align:center;font-size:${6.6 * U}px;border:${0.6 * U}px solid ${good ? VT.col('fact') : VT.col('myth')}` });
    c.innerHTML = `<div class="t" style="font-family:${VT.font('display')};font-weight:800;line-height:1.22"></div>`;
    c.querySelector('.t').textContent = text || '';
    return c;
  }
  function tag(layer, text, color) {
    const U = VT.U;
    return VT.el(layer, `background:${color};color:#fff;font-family:${VT.font('display')};font-weight:900;font-size:${4.4 * U}px;letter-spacing:.06em;padding:${0.8 * U}px ${3.4 * U}px ${1.2 * U}px;border-radius:${2 * U}px;white-space:nowrap`, VT.esc(text));
  }

  VT.template({
    theme: {
      palette: { bg: '#121417', deep: '#000000', ink: '#16181D', paper: '#F5F2EA', paper2: '#EDE6DA', myth: '#FF4D4D', fact: '#22D38A', accent: '#FFD23F', text: '#FFFFFF', muted: 'rgba(255,255,255,.7)' },
      captions: { style: 'pill', hl: '#FFD23F', hlText: '#16181D' },
      transition: 'push', sfx: { transition: 'whoosh', transitionGain: -17 }, zones: { head: 0.16 },
    },
    background(layer) {
      const U = VT.U;
      VT.el(layer, `inset:0;background:linear-gradient(180deg,#191C21,#0D0F12)`);
      const red = VT.el(layer, `width:${120 * U}px;height:${120 * U}px;border-radius:50%;background:radial-gradient(circle,rgba(255,77,77,.22),rgba(255,77,77,0) 65%)`);
      const grn = VT.el(layer, `width:${120 * U}px;height:${120 * U}px;border-radius:50%;background:radial-gradient(circle,rgba(34,211,138,.2),rgba(34,211,138,0) 65%)`);
      return (t) => {
        VT.place(red, VT.W * 0.2 + Math.sin(t * 0.3) * 10 * U, VT.H * 0.25);
        VT.place(grn, VT.W * 0.8 + Math.cos(t * 0.25) * 10 * U, VT.H * 0.7);
      };
    },
    scenes: {
      claim: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, land = VT.orient !== 'portrait';
          const col = VT.clampW(VT.inset(z, 1), land ? 170 : 94);
          const slots = land ? VT.cols(col, 2, 5) : VT.rows(col, 2, 5);
          const w = land ? slots[0].w : col.w;
          const myth = claimCard(layer, 'myth', s.myth, w), fact = s.fact ? claimCard(layer, 'fact', s.fact, w) : null;
          [myth, fact].forEach((c) => c && VT.fit(c, w, slots[0].h * (land ? 0.7 : 0.92), 3));
          const mt = tag(layer, VT.label(s, 'myth', 'MYTH'), VT.col('myth')), ft = fact ? tag(layer, VT.label(s, 'fact', 'FACT'), VT.col('fact')) : null;
          const xb = VT.badge(layer, 'x', VT.col('myth'), '#fff', 13), cb = fact ? VT.badge(layer, 'check', VT.col('fact'), '#fff', 13) : null;
          const ma = VT.time(s.mythAt, s.start + 0.2), stampAt = VT.time(s.stampAt, ma + 1.1), fa = VT.time(s.factAt, stampAt + 1.2);
          VT.cue(ma, 'pop-low', { gain: -12 }); VT.cue(stampAt, 'buzzer', { gain: -13 }); VT.cue(stampAt + 0.02, 'impact', { gain: -16 });
          if (fact) { VT.cue(fa - 0.15, 'swoosh', { gain: -18 }); VT.cue(fa + 0.35, 'success', { gain: -11 }); }
          const center = { x: col.x + col.w / 2, y: col.y + col.h / 2 };
          return (t) => {
            const mp = P(t, ma, 0.5), mv = fact ? eo(P(t, fa - 0.2, 0.55)) : 0;
            const m0 = center, m1 = VT.center(slots[0]);
            const mx = L(m0.x, m1.x, mv), my = L(m0.y, m1.y, mv);
            const sh = t > stampAt && t < stampAt + 0.3 ? Math.sin(t * 90) * 1.2 * U * (1 - (t - stampAt) / 0.3) : 0;
            VT.place(myth, mx + sh, my, { s: L(0.8, 1, sp(mp)) * L(1, 0.94, mv), o: C(mp * 4) * L(1, 0.75, mv), r: L(0, land ? -1.5 : -2, mv) });
            const mh = myth.offsetHeight * L(1, 0.94, mv);
            VT.place(mt, mx, my - mh / 2, { s: L(0.4, 1, sp(P(t, ma + 0.1, 0.4))), o: C((t - ma) / 0.15) });
            const xp = P(t, stampAt, 0.35);
            VT.place(xb, mx + (w / 2 - 3 * U) * VT.sign, my - mh / 2 + 2 * U, { s: L(2.4, 1, eo(xp)), r: L(-60, -8, eo(xp)), o: C(xp * 5) });
            myth.querySelector('.t').style.textDecoration = t > stampAt ? `line-through ${0.5 * U}px ${VT.col('myth')}` : 'none';
            if (fact) {
              const fp = P(t, fa, 0.55), f1 = VT.center(slots[1]);
              VT.place(fact, f1.x + (land ? (1 - eo(fp)) * 30 * U * VT.sign : 0), f1.y + (land ? 0 : (1 - eo(fp)) * 25 * U), { s: L(0.9, 1, sp(fp)), o: C(fp * 3) });
              VT.place(ft, f1.x, f1.y - fact.offsetHeight / 2, { s: L(0.4, 1, sp(P(t, fa + 0.15, 0.4))), o: C((t - fa - 0.15) / 0.15) });
              const cp = P(t, fa + 0.35, 0.45);
              VT.place(cb, f1.x + (w / 2 - 3 * U) * VT.sign, f1.y - fact.offsetHeight / 2 + 2 * U, { s: L(0.2, 1, sp(cp)), o: C(cp * 5) });
            }
          };
        },
      },
      reason: {
        build(s, layer) {
          const U = VT.U, Z = VT.Z, pts = s.points || [];
          const head = s.title ? VT.text(layer, s.title, { w: Z.area.w * 0.92, h: Z.head.h * 0.8, size: 8, color: VT.col('text') }) : null;
          const body = VT.clampW(s.title ? Z.body : Z.full, 100);
          const rows = VT.rows(VT.inset(body, 1), Math.max(3, pts.length), 2.4).slice(0, pts.length);
          const els = pts.map((p, i) => {
            const r = rows[i], h = Math.min(r.h, 16 * U);
            const e = VT.card(layer, { css: `width:${r.w}px;height:${h}px;display:flex;align-items:center;gap:${3 * U}px;padding:0 ${3.4 * U}px` });
            e.innerHTML = `<div style="flex:none;width:${9 * U}px;height:${9 * U}px;border-radius:50%;background:${VT.col(p.kind === 'myth' ? 'myth' : 'fact')};display:flex;align-items:center;justify-content:center">${VT.icon(p.icon || (p.kind === 'myth' ? 'x' : 'check'), '#fff', '60%')}</div><div class="t" style="flex:1;min-width:0;font-family:${VT.font('display')};font-weight:800;font-size:${5.6 * U}px;line-height:1.15"></div>`;
            const tx = e.querySelector('.t'); tx.textContent = p.text || ''; VT.fit(tx, null, h - 2 * U, 2.6);
            const at = VT.time(p.at, s.start + 0.5 + i * 0.8); VT.cue(at - 0.05, 'pop', { gain: -15, pan: i % 2 ? 0.3 : -0.3 });
            return { e, r, at };
          });
          return (t) => {
            if (head) { const r = VT.rise(t, s.start + 0.05, 0.45, 4); VT.place(head, VT.W / 2, Z.head.y + Z.head.h / 2, { y: r.y, o: r.o }); }
            els.forEach((x) => { const p = P(t, x.at - 0.1, 0.45); VT.place(x.e, x.r.x + x.r.w / 2 - (1 - eo(p)) * 25 * U * VT.sign, x.r.y + x.r.h / 2, { o: C(p * 3), s: L(0.94, 1, eo(p)) }); });
          };
        },
      },
      stamp: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, good = s.kind !== 'myth';
          const st = VT.stamp(layer, s.text || (good ? VT.label(s, 'fact', 'TRUE') : VT.label(s, 'busted', 'BUSTED')), VT.col(good ? 'fact' : 'myth'));
          st.style.fontSize = 13 * U + 'px'; st.style.borderWidth = 1.4 * U + 'px'; st.style.padding = `${1.2 * U}px ${5 * U}px ${2 * U}px`;
          VT.fit(st, z.w * 0.9);
          const sub = s.sub ? VT.text(layer, s.sub, { w: z.w * 0.88, size: 5.6, weight: 700, font: 'body', color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.3);
          VT.cue(at - 0.02, 'impact', { gain: -8 }); VT.cue(at + 0.05, good ? 'success' : 'buzzer', { gain: -14 });
          return (t) => {
            const p = P(t, at, 0.3), cy = z.y + z.h * 0.44;
            VT.place(st, VT.W / 2, cy, { s: L(3, 1, eo(p)), r: -8, o: C(p * 5) });
            if (sub) { const r = VT.rise(t, at + 0.5, 0.45, 4); VT.place(sub, VT.W / 2, cy + st.offsetHeight / 2 + 8 * U, { y: r.y, o: r.o }); }
          };
        },
      },
    },
  });
})();
