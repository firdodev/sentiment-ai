import type { ApiError } from "../types";

export class RequestError extends Error {
  detail: ApiError;
  constructor(detail: ApiError) {
    super(detail.gabim);
    this.detail = detail;
  }
}

async function handle<T>(res: Response): Promise<T> {
  let data: unknown = null;
  try {
    data = await res.json();
  } catch {
    // përgjigje pa JSON (p.sh. serveri ra)
  }
  if (!res.ok) {
    const detail = (data as ApiError) ?? { gabim: `Gabim ${res.status}` };
    throw new RequestError({ ...detail, gabim: detail.gabim ?? `Gabim ${res.status}` });
  }
  return data as T;
}

export async function getJSON<T>(url: string): Promise<T> {
  try {
    return await handle<T>(await fetch(url));
  } catch (e) {
    throw toRequestError(e);
  }
}

export async function postJSON<T>(url: string, body?: unknown): Promise<T> {
  try {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    return await handle<T>(res);
  } catch (e) {
    throw toRequestError(e);
  }
}

export async function postFile<T>(url: string, file: File): Promise<T> {
  const form = new FormData();
  form.append("file", file);
  try {
    return await handle<T>(await fetch(url, { method: "POST", body: form }));
  } catch (e) {
    throw toRequestError(e);
  }
}

function toRequestError(e: unknown): RequestError {
  if (e instanceof RequestError) return e;
  return new RequestError({ gabim: "Serveri nuk përgjigjet. A është ndezur `python app.py`?" });
}
