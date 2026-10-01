/** Project status helpers shared by the dashboard and the project page. */
export const STATUS_ORDER = ["created", "queued_transcribe", "transcribing", "editing", "planning", "preview_ready", "queued_render", "rendering", "done"] as const;
export type Status = (typeof STATUS_ORDER)[number] | "uploading" | "failed";
export const ACTIVE: Status[] = ["queued_transcribe", "transcribing", "editing", "planning", "queued_render", "rendering"];
export const isActive = (s: string) => (ACTIVE as string[]).includes(s);

/** Watch a running project: polls every few seconds (always, so a buffering proxy cannot stall the page) and additionally
 * subscribes to the SSE stream for faster updates. Returns an unsubscribe function. */
export function watchProject(id: string, onUpdate: (data: { status: string; progress?: number | null }) => void, onEnd?: () => void): () => void {
  let stopped = false;
  let es: EventSource | null = null;
  let timer: ReturnType<typeof setInterval> | null = null;
  const poll = () => {
    if (timer) return;
    timer = setInterval(async () => {
      try {
        const r = await fetch(`/api/projects/${id}`, { credentials: "include" });
        if (!r.ok) return;
        const p = await r.json();
        onUpdate({ status: p.status, progress: p.progress });
        if (p.status === "done" || p.status === "failed") {
          stop();
          onEnd?.();
        }
      } catch {
        /* keep polling */
      }
    }, 2500);
  };
  const stop = () => {
    stopped = true;
    es?.close();
    if (timer) clearInterval(timer);
  };
  poll();
  try {
    es = new EventSource(`/api/projects/${id}/events`, { withCredentials: true });
    es.addEventListener("status", (e) => onUpdate(JSON.parse((e as MessageEvent).data)));
    es.addEventListener("heartbeat", (e) => onUpdate(JSON.parse((e as MessageEvent).data)));
    es.addEventListener("end", () => {
      stop();
      onEnd?.();
    });
    es.onerror = () => {
      if (stopped) return;
      es?.close();
      es = null;
    };
  } catch {
    /* polling already runs */
  }
  return stop;
}
