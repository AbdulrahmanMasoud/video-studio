"use client";
import { useEffect, useRef, useState } from "react";

/** Horizontal loop of template previews. Pauses when scrolled out of view (and under prefers-reduced-motion via CSS). */
export function PreviewMarquee({ names }: { names: string[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const [visible, setVisible] = useState(true);
  useEffect(() => {
    const el = ref.current;
    if (!el || typeof IntersectionObserver === "undefined") return;
    const io = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold: 0.05 });
    io.observe(el);
    return () => io.disconnect();
  }, []);
  const items = [...names, ...names];
  return (
    <div ref={ref} className="overflow-hidden" aria-hidden>
      <div className="marquee" data-paused={!visible}>
        {items.map((n, i) => (
          // eslint-disable-next-line @next/next/no-img-element
          <img key={`${n}-${i}`} src={`/previews/${n}.jpg`} alt="" className="aspect-[9/16] w-40 shrink-0 rounded-lg object-cover sm:w-48" loading={i < 8 ? "eager" : "lazy"} decoding="async" />
        ))}
      </div>
    </div>
  );
}
