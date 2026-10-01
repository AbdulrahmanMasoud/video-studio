/** Direct-to-S3 upload with the presigned POST policy from the API; reports progress via XHR. */
import { api, type Presign } from "./api";

export async function presignInput(file: File): Promise<Presign> {
  return api<Presign>("/uploads/presign", { method: "POST", json: { filename: file.name, content_type: file.type || "application/octet-stream", size: file.size } });
}

export async function presignAsset(projectId: string, file: File): Promise<Presign> {
  return api<Presign>(`/projects/${projectId}/assets/presign`, { method: "POST", json: { filename: file.name, content_type: file.type, size: file.size } });
}

export function uploadToS3(post: Presign, file: File, onProgress?: (fraction: number) => void): Promise<void> {
  return new Promise((resolve, reject) => {
    const form = new FormData();
    for (const [k, v] of Object.entries(post.fields)) form.append(k, v);
    form.append("file", file);
    const xhr = new XMLHttpRequest();
    xhr.open("POST", post.url, true);
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable && onProgress) onProgress(e.loaded / e.total);
    };
    xhr.onload = () => (xhr.status >= 200 && xhr.status < 300 ? resolve() : reject(new Error(`upload failed (${xhr.status})`)));
    xhr.onerror = () => reject(new Error("upload failed (network)"));
    xhr.send(form);
  });
}

/** Duration of an audio/video file via the browser's media element (client-side ≤ 10 min check). */
export function mediaDuration(file: File): Promise<number | null> {
  return new Promise((resolve) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement(file.type.startsWith("video/") ? "video" : "audio");
    el.preload = "metadata";
    const done = (v: number | null) => {
      URL.revokeObjectURL(url);
      resolve(v);
    };
    el.onloadedmetadata = () => done(Number.isFinite(el.duration) ? el.duration : null);
    el.onerror = () => done(null);
    el.src = url;
  });
}
