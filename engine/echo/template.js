/* echo - kinetic typography. "flow" turns the spoken words into animated type automatically;
   "words" stacks hand-picked lines; "quote" frames a closing line. Captions are off: the type IS the caption. */
(function () {
  const { C, P, eo, ei, sp, L } = VT;
  const clean = (w) => String(w).toLowerCase().replace(/[^\p{L}\p{N}]/gu, '');

  // Lay out lines so each one fills the column width (classic kinetic-type justification).
  function stack(layer, lines, col, maxH, gapU) {
    const U = VT.U;
    const els = lines.map((ln) => {
      const e = VT.el(layer, `white-space:nowrap;font-family:${VT.font('display')};font-weight:900;line-height:1.02;direction:${VT.dir};text-align:center;font-size:${ln.size * U}px;color:${ln.color || VT.col('text')}`);
      if (ln.upper && VT.dir !== 'rtl') e.style.textTransform = 'uppercase';
      e.innerHTML = ln.html;
      // grow short lines toward the column width (capped), shrink long ones
      const fs = parseFloat(e.style.fontSize), w = e.scrollWidth || 1;
      e.style.fontSize = Math.min(fs * (ln.grow || 2.1), fs * (col.w / w) * 0.98) + 'px';
      return e;
    });
    const gap = gapU * U;
    let total = els.reduce((a, e) => a + e.offsetHeight, 0) + gap * (els.length - 1);
    if (total > maxH) { const k = maxH / total; els.forEach((e) => { e.style.fontSize = parseFloat(e.style.fontSize) * k + 'px'; }); total = maxH; }
    let y = -total / 2;
    return els.map((e) => { const h = e.offsetHeight; const r = { e, dy: y + h / 2 }; y += h + gap; return r; });
  }

  VT.template({
    theme: {
      palette: { bg: '#0B0B0C', deep: '#000000', ink: '#0B0B0C', paper: '#FFFFFF', accent: '#C6FF3D', alt: '#FF4FA3', text: '#FFFFFF', muted: 'rgba(255,255,255,.45)' },
      captions: { enabled: false, style: 'none' },
      transition: 'cut', sfx: { transition: null }, zones: { head: 0.12 },
    },
    background(layer) {
      const U = VT.U;
      const g = VT.el(layer, `inset:-10%;background:radial-gradient(circle at 30% 30%, rgba(198,255,61,.08), transparent 45%), radial-gradient(circle at 70% 75%, rgba(255,79,163,.08), transparent 45%)`);
      return (t) => { g.style.transform = `rotate(${t * 4}deg) scale(1.1)`; };
    },
    scenes: {
      // Spoken words become the visual. {emphasis?: ["word", ...], maxChars?, lines?}
      flow: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(VT.inset(z, 2), VT.orient === 'landscape' ? 150 : 96);
          const ws = VT.words.map((w, i) => Object.assign({ i }, w)).filter((w) => w.s >= s.start - 0.05 && w.s < s.end - 0.02);
          const emph = new Set((s.emphasis || []).map(clean));
          const maxChars = s.maxChars || (VT.joiner ? 16 : 7), maxLines = s.lines || (VT.orient === 'portrait' ? 4 : 3);
          // words -> lines -> pages
          const lines = []; let cur = [];
          ws.forEach((w, k) => {
            const len = cur.reduce((a, x) => a + x.w.length + 1, 0) + w.w.length;
            const prev = ws[k - 1];
            if (cur.length && (len > maxChars || (prev && w.s - prev.e > 0.45) || emph.has(clean(w.w)) || (cur.length && emph.has(clean(cur[cur.length - 1].w))))) { lines.push(cur); cur = []; }
            cur.push(w);
            if (/[.!?؟。！？]$/.test(w.w)) { lines.push(cur); cur = []; }
          });
          if (cur.length) lines.push(cur);
          const pages = []; let pg = [];
          lines.forEach((ln) => { pg.push(ln); const endS = /[.!?؟。！？]$/.test(ln[ln.length - 1].w); if (pg.length >= maxLines || (endS && pg.length >= 2)) { pages.push(pg); pg = []; } });
          if (pg.length) pages.push(pg);
          const built = pages.map((pgL, pi) => {
            const holder = VT.el(layer, 'inset:0');
            const specs = pgL.map((ln) => {
              const big = ln.some((w) => emph.has(clean(w.w)));
              return { size: big ? 22 : 14, upper: s.upper !== false, color: big ? VT.col('accent') : VT.col('text'),
                html: ln.map((w) => `<span style="display:inline-block">${VT.esc(w.w)}</span>`).join(VT.joiner ? ' ' : '') };
            });
            const st = stack(holder, specs, col, z.h * 0.9, 1.2);
            const spans = [];
            st.forEach((x, li) => Array.from(x.e.children).forEach((sp2, k) => spans.push({ el: sp2, w: pgL[li][k], line: x })));
            const a = pgL[0][0].s - 0.08, lastLn = pgL[pgL.length - 1], b = pi + 1 < pages.length ? pages[pi + 1][0][0].s - 0.08 : s.end + 1;
            VT.cue(a, pi % 2 ? 'swoosh' : 'whoosh', { gain: -22 });
            pgL.forEach((ln) => { if (ln.some((w) => emph.has(clean(w.w)))) VT.cue(ln.find((w) => emph.has(clean(w.w))).s - 0.02, 'impact', { gain: -14 }); });
            return { holder, st, spans, a, b, pi, lastEnd: lastLn[lastLn.length - 1].e };
          });
          return (t) => {
            const cy = z.y + z.h / 2;
            built.forEach((B) => {
              const on = t >= B.a && t < B.b;
              B.holder.style.display = on ? 'block' : 'none';
              if (!on) return;
              const zoom = 1 + (t - B.a) * 0.012;
              B.st.forEach((x) => VT.place(x.e, VT.W / 2, cy + x.dy * zoom, { s: zoom }));
              B.spans.forEach((x, k) => {
                const p = P(t, x.w.s - 0.06, 0.22);
                const dir = (B.pi + k) % 3;
                x.el.style.transform = dir === 0 ? `translateY(${(1 - eo(p)) * 5 * U}px)` : dir === 1 ? `scale(${L(1.6, 1, eo(p))})` : `translateX(${(1 - eo(p)) * -6 * U * VT.sign}px)`;
                x.el.style.opacity = C(p * 3);
                x.el.style.color = t >= x.w.s && t < x.w.e + 0.05 && x.line.e.style.color !== VT.col('accent') ? VT.col('alt') : '';
              });
            });
          };
        },
      },
      // Hand-picked lines: {items:[{text, at, style: normal|accent|huge|outline|strike, strikeAt, clear}]}
      words: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(VT.inset(z, 2), VT.orient === 'landscape' ? 150 : 96);
          const items = (s.items || []).map((it, i) => Object.assign({ i }, it, { at: VT.time(it.at, s.start + 0.3 + i * 0.6) }));
          const groups = []; let g = [];
          items.forEach((it) => { if (it.clear && g.length) { groups.push(g); g = []; } g.push(it); });
          if (g.length) groups.push(g);
          const built = groups.map((gr, gi) => {
            const holder = VT.el(layer, 'inset:0');
            const specs = gr.map((it) => ({ size: it.style === 'huge' ? 26 : it.style === 'small' ? 8 : 14, upper: s.upper !== false,
              color: it.style === 'accent' || it.style === 'huge' ? VT.col('accent') : VT.col('text'), html: VT.esc(it.text) }));
            const st = stack(holder, specs, col, z.h * 0.9, 1.4);
            st.forEach((x, k) => { const it = gr[k]; if (it.style === 'outline') { x.e.style.color = 'transparent'; x.e.style.webkitTextStroke = `${0.35 * U}px ${VT.col('text')}`; } });
            gr.forEach((it) => { VT.cue(it.at - 0.03, it.style === 'huge' ? 'impact' : 'pop-low', { gain: it.style === 'huge' ? -10 : -18 }); if (it.strikeAt) VT.cue(VT.time(it.strikeAt, it.at + 0.6), 'scratch', { gain: -16 }); });
            const a = gr[0].at - 0.05, b = gi + 1 < groups.length ? groups[gi + 1][0].at - 0.05 : Infinity;
            return { holder, st, gr, a, b };
          });
          return (t) => {
            const cy = z.y + z.h / 2;
            built.forEach((B) => {
              const on = t >= B.a && t < B.b; B.holder.style.display = on ? 'block' : 'none'; if (!on) return;
              // the stack re-centres on the lines already shown
              let k = -1; B.gr.forEach((it, j) => { if (t >= it.at - 0.05) k = j; });
              const off = (j) => (j < 0 ? 0 : -(B.st[0].dy + B.st[j].dy) / 2);
              const kp = k >= 0 ? eo(P(t, B.gr[k].at - 0.05, 0.35)) : 1;
              const shift = L(off(k - 1), off(k), kp);
              B.st.forEach((x, j) => {
                const it = B.gr[j], p = P(t, it.at - 0.05, 0.35);
                const m = it.style === 'huge' ? { s: L(2.2, 1, eo(p)) } : { y: (1 - eo(p)) * 6 * U, s: L(1.08, 1, eo(p)) };
                VT.place(x.e, VT.W / 2, cy + x.dy + shift, Object.assign(m, { o: C(p * 4) }));
                if (it.style === 'strike' || it.strikeAt) { const sa = VT.time(it.strikeAt, it.at + 0.6); x.e.style.textDecoration = t > sa ? `line-through ${0.9 * U}px ${VT.col('alt')}` : 'none'; x.e.style.opacity = t > sa ? 0.55 * C(p * 4) : C(p * 4); }
              });
            });
          };
        },
      },
      quote: {
        build(s, layer) {
          const U = VT.U, z = VT.Z.full, col = VT.clampW(VT.inset(z, 3), 90);
          const mark = VT.el(layer, `font-family:Georgia,serif;font-weight:900;font-size:${40 * U}px;line-height:.8;color:${VT.col('accent')}`, VT.dir === 'rtl' ? '”' : '“');
          const tx = VT.text(layer, s.text || '', { w: col.w, h: z.h * 0.5, size: 9, color: '#fff', lh: 1.2 });
          const au = s.author ? VT.text(layer, '— ' + s.author, { w: col.w, size: 4.6, weight: 700, font: 'body', color: VT.col('muted') }) : null;
          const at = VT.time(s.at, s.start + 0.2);
          VT.cue(at, 'sting', { gain: -16 });
          return (t) => {
            const cy = z.y + z.h * 0.5, p = P(t, at, 0.6);
            VT.place(mark, VT.W / 2, cy - tx.offsetHeight / 2 - 10 * U, { s: L(0.3, 1, sp(p)), o: C(p * 4) * 0.9 });
            tx.style.clipPath = `inset(0 0 ${(1 - eo(P(t, at + 0.15, 0.8))) * 100}% 0)`;
            VT.place(tx, VT.W / 2, cy);
            if (au) { const r = VT.rise(t, at + 0.9, 0.45, 3); VT.place(au, VT.W / 2, cy + tx.offsetHeight / 2 + 7 * U, { y: r.y, o: r.o }); }
          };
        },
      },
    },
  });
})();
